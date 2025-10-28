#!/usr/bin/env python3
"""
Performance optimization module for the web server.
Provides caching, database optimization, and async operations.
"""

import os
import sqlite3
import json
import time
import gzip
import hashlib
import threading
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import logging
from functools import wraps
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced caching system with Redis and memory fallback."""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379/0', 
                 memory_cache_size: int = 1000, use_redis: bool = True):
        self.memory_cache = {}
        self.memory_cache_access = {}
        self.memory_cache_size = memory_cache_size
        self.memory_lock = threading.Lock()
        self.use_redis = use_redis
        
        # Try to connect to Redis
        self.redis_client = None
        if REDIS_AVAILABLE and use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, 
                                                  decode_responses=True,
                                                  socket_timeout=1,
                                                  socket_connect_timeout=1)
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory cache only")
                self.redis_client = None
        else:
            logger.info("Redis not available or disabled, using memory cache only")
    
    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace."""
        return f"{namespace}:{key}"
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set cache value - simplified API for compatibility."""
        return self.set_with_namespace("default", key, value, ttl)
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value - simplified API for compatibility."""
        return self.get_from_namespace("default", key)
    
    def set_with_namespace(self, namespace: str, key: str, value: Any, 
            ttl: int = 300, compress: bool = False) -> bool:
        """Set cache value with optional compression."""
        try:
            cache_key = self._generate_key(namespace, key)
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value, default=str)
            else:
                serialized = str(value)
            
            # Compress if requested and data is large
            if compress and len(serialized) > 1024:
                serialized = gzip.compress(serialized.encode()).decode('latin1')
                cache_key += ':compressed'
            
            # Try Redis first
            if self.redis_client:
                try:
                    return self.redis_client.setex(cache_key, ttl, serialized)
                except Exception as e:
                    logger.warning(f"Redis set failed: {e}, falling back to memory")
            
            # Fallback to memory cache
            with self.memory_lock:
                self.memory_cache[cache_key] = {
                    'value': serialized,
                    'expires': time.time() + ttl,
                    'compressed': compress and len(serialized) > 1024
                }
                self.memory_cache_access[cache_key] = time.time()
                
                # Cleanup old entries if cache is full
                if len(self.memory_cache) > self.memory_cache_size:
                    self._cleanup_memory_cache()
                
                return True
                
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False
    
    def get_from_namespace(self, namespace: str, key: str) -> Optional[Any]:
        """Get cache value."""
        try:
            cache_key = self._generate_key(namespace, key)
            compressed_key = cache_key + ':compressed'
            
            # Try Redis first
            if self.redis_client:
                try:
                    # Check both compressed and uncompressed keys
                    value = self.redis_client.get(compressed_key)
                    if value is not None:
                        # Decompress
                        value = gzip.decompress(value.encode('latin1')).decode()
                    else:
                        value = self.redis_client.get(cache_key)
                    
                    if value is not None:
                        # Try to parse as JSON
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            return value
                            
                except Exception as e:
                    logger.warning(f"Redis get failed: {e}, trying memory cache")
            
            # Try memory cache
            with self.memory_lock:
                # Check compressed key first
                if compressed_key in self.memory_cache:
                    entry = self.memory_cache[compressed_key]
                elif cache_key in self.memory_cache:
                    entry = self.memory_cache[cache_key]
                else:
                    return None
                
                # Check expiration
                if entry['expires'] < time.time():
                    del self.memory_cache[cache_key]
                    if compressed_key in self.memory_cache:
                        del self.memory_cache[compressed_key]
                    return None
                
                # Update access time
                self.memory_cache_access[cache_key] = time.time()
                
                value = entry['value']
                
                # Decompress if needed
                if entry.get('compressed', False):
                    value = gzip.decompress(value.encode('latin1')).decode()
                
                # Try to parse as JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
                    
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete cache entry."""
        try:
            cache_key = self._generate_key(namespace, key)
            compressed_key = cache_key + ':compressed'
            
            # Try Redis first
            if self.redis_client:
                try:
                    deleted = self.redis_client.delete(cache_key, compressed_key)
                    if deleted > 0:
                        return True
                except Exception as e:
                    logger.warning(f"Redis delete failed: {e}")
            
            # Try memory cache
            with self.memory_lock:
                deleted = False
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
                    deleted = True
                if compressed_key in self.memory_cache:
                    del self.memory_cache[compressed_key]
                    deleted = True
                if cache_key in self.memory_cache_access:
                    del self.memory_cache_access[cache_key]
                
                return deleted
                
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            return False
    
    def clear_namespace(self, namespace: str) -> bool:
        """Clear all entries in a namespace."""
        try:
            # Redis
            if self.redis_client:
                try:
                    pattern = f"{namespace}:*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis clear namespace failed: {e}")
            
            # Memory cache
            with self.memory_lock:
                keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"{namespace}:")]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    if key in self.memory_cache_access:
                        del self.memory_cache_access[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Clear namespace failed: {e}")
            return False
    
    def _cleanup_memory_cache(self):
        """Clean up old entries from memory cache."""
        current_time = time.time()
        
        # Remove expired entries
        expired_keys = [
            k for k, v in self.memory_cache.items() 
            if v['expires'] < current_time
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
            if key in self.memory_cache_access:
                del self.memory_cache_access[key]
        
        # If still too many entries, remove least recently accessed
        if len(self.memory_cache) > self.memory_cache_size:
            sorted_by_access = sorted(
                self.memory_cache_access.items(),
                key=lambda x: x[1]
            )
            
            remove_count = len(self.memory_cache) - self.memory_cache_size + 100
            for key, _ in sorted_by_access[:remove_count]:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                del self.memory_cache_access[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'redis_available': self.redis_client is not None,
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_max_size': self.memory_cache_size,
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_info'] = {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                }
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")
        
        return stats

class DatabaseManager:
    """SQLite database manager for improved performance."""
    
    def __init__(self, db_path: str = 'data/webserver.db'):
        self.db_path = db_path
        self.connection_pool = {}
        self.pool_lock = threading.Lock()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            # Create tables
            conn.execute('''
                CREATE TABLE IF NOT EXISTS data_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_metadata (
                    filename TEXT PRIMARY KEY,
                    original_name TEXT NOT NULL,
                    mime_type TEXT,
                    size INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS program_metadata (
                    filename TEXT PRIMARY KEY,
                    original_name TEXT NOT NULL,
                    program_type TEXT,
                    size INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    execution_count INTEGER DEFAULT 0,
                    last_executed TIMESTAMP,
                    description TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    client_ip TEXT,
                    details TEXT,
                    success BOOLEAN
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_file_uploaded_at ON file_metadata(uploaded_at)')
            
            conn.commit()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with optimizations."""
        thread_id = threading.get_ident()
        
        with self.pool_lock:
            if thread_id not in self.connection_pool:
                conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=30
                )
                
                # Performance optimizations
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=10000')
                conn.execute('PRAGMA temp_store=MEMORY')
                conn.execute('PRAGMA mmap_size=268435456')  # 256MB
                
                # Enable foreign keys and row factory
                conn.execute('PRAGMA foreign_keys=ON')
                conn.row_factory = sqlite3.Row
                
                self.connection_pool[thread_id] = conn
            
            return self.connection_pool[thread_id]
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def close_connections(self):
        """Close all database connections."""
        with self.pool_lock:
            for conn in self.connection_pool.values():
                conn.close()
            self.connection_pool.clear()

class AsyncFileManager:
    """Asynchronous file operations for better performance."""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def read_file_async(self, file_path: str) -> Optional[bytes]:
        """Read file asynchronously."""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Async file read failed: {e}")
            return None
    
    async def write_file_async(self, file_path: str, content: bytes) -> bool:
        """Write file asynchronously."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            return True
        except Exception as e:
            logger.error(f"Async file write failed: {e}")
            return False
    
    def read_file_threaded(self, file_path: str) -> bytes:
        """Read file in thread pool."""
        def _read():
            with open(file_path, 'rb') as f:
                return f.read()
        
        future = self.executor.submit(_read)
        return future.result(timeout=30)
    
    def write_file_threaded(self, file_path: str, content: bytes) -> bool:
        """Write file in thread pool."""
        def _write():
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(content)
            return True
        
        future = self.executor.submit(_write)
        return future.result(timeout=30)

class CompressionManager:
    """Handle response compression for better performance."""
    
    @staticmethod
    def compress_response(data: Union[str, bytes], 
                         compression_level: int = 6) -> bytes:
        """Compress response data."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return gzip.compress(data, compresslevel=compression_level)
    
    @staticmethod
    def should_compress(content_type: str, size: int) -> bool:
        """Determine if content should be compressed."""
        compressible_types = [
            'text/', 'application/json', 'application/javascript',
            'application/xml', 'image/svg+xml'
        ]
        
        # Only compress if larger than 1KB and compressible type
        return size > 1024 and any(content_type.startswith(t) for t in compressible_types)

# Decorators for performance optimization

def cache_result(namespace: str, key_func=None, ttl: int = 300, compress: bool = False):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Use function name and hash of arguments
                arg_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func.__name__}:{hashlib.md5(arg_str.encode()).hexdigest()}"
            
            # Try to get from cache
            result = cache_manager.get(namespace, cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(namespace, cache_key, result, ttl=ttl, compress=compress)
            
            return result
        return wrapper
    return decorator

def async_background(func):
    """Decorator to run function in background thread."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        def run_async():
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Background task failed: {e}")
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
        return thread
    return wrapper

def measure_performance(logger_name: str = 'performance'):
    """Decorator to measure function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                perf_logger = logging.getLogger(logger_name)
                perf_logger.info(f"{func.__name__} completed in {duration:.3f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                perf_logger = logging.getLogger(logger_name)
                perf_logger.warning(f"{func.__name__} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator

# Global instances
cache_manager = CacheManager()
database_manager = DatabaseManager()
async_file_manager = AsyncFileManager()
compression_manager = CompressionManager()

def initialize_performance_managers(config_manager=None):
    """Initialize performance managers with configuration."""
    global cache_manager, database_manager, async_file_manager
    
    if config_manager:
        # Redis configuration
        redis_url = config_manager.get('performance.redis_url', 'redis://localhost:6379/0')
        cache_size = config_manager.get('performance.memory_cache_size', 1000)
        cache_manager = CacheManager(redis_url, cache_size)
        
        # Database configuration
        db_path = config_manager.get('performance.database_path', 'data/webserver.db')
        database_manager = DatabaseManager(db_path)
        
        # Async file manager configuration
        max_workers = config_manager.get('performance.max_workers', 4)
        async_file_manager = AsyncFileManager(max_workers)
    
    return cache_manager, database_manager, async_file_manager

def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics."""
    return {
        'cache_stats': cache_manager.get_stats(),
        'database_path': database_manager.db_path,
        'database_connections': len(database_manager.connection_pool),
        'async_threads': async_file_manager.executor._threads if hasattr(async_file_manager.executor, '_threads') else 0,
    }