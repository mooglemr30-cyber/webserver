"""
Production-grade data storage module with enhanced reliability, performance, and monitoring.
"""

import json
import os
import sqlite3
import threading
import time
import shutil
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Tuple
from contextlib import contextmanager
from pathlib import Path
import hashlib
import fcntl

# Set up logging
logger = logging.getLogger(__name__)

class ProductionDataStore:
    """Production-grade data storage with backup, monitoring, and recovery."""
    
    def __init__(self, 
                 data_file: str = 'data/storage.json',
                 backup_enabled: bool = True,
                 backup_interval: int = 3600,
                 max_backups: int = 24,
                 enable_sqlite: bool = True,
                 sqlite_db: str = 'data/storage.db'):
        """Initialize production data store."""
        
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        self.backup_enabled = backup_enabled
        self.backup_interval = backup_interval
        self.max_backups = max_backups
        self.enable_sqlite = enable_sqlite
        self.sqlite_db = sqlite_db
        
        # Threading lock for concurrent access
        self._lock = threading.RLock()
        
        # Performance metrics
        self.metrics = {
            'reads': 0,
            'writes': 0,
            'errors': 0,
            'backup_count': 0,
            'last_backup': None,
            'avg_read_time': 0,
            'avg_write_time': 0
        }
        
        # Initialize storage
        self._setup_storage()
        
        # Start background backup thread if enabled
        if self.backup_enabled:
            self._start_backup_thread()
    
    def _setup_storage(self) -> None:
        """Set up storage directories and files."""
        # Create directories
        for path in [self.data_dir, f"{self.data_dir}/backups", f"{self.data_dir}/temp"]:
            if path and not os.path.exists(path):
                os.makedirs(path, mode=0o750)
        
        # Initialize JSON storage
        self._load_json_data()
        
        # Initialize SQLite if enabled
        if self.enable_sqlite:
            self._setup_sqlite()
    
    def _setup_sqlite(self) -> None:
        """Set up SQLite database for structured data."""
        try:
            with sqlite3.connect(self.sqlite_db, timeout=30.0) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS kv_store (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        checksum TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_updated_at ON kv_store(updated_at)
                ''')
                
                conn.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_timestamp 
                    AFTER UPDATE ON kv_store
                    FOR EACH ROW
                    BEGIN
                        UPDATE kv_store SET updated_at = CURRENT_TIMESTAMP 
                        WHERE key = NEW.key;
                    END
                ''')
                
                conn.commit()
                logger.info("SQLite database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            self.enable_sqlite = False
    
    def _load_json_data(self) -> None:
        """Load data from JSON file with error recovery."""
        try:
            if os.path.exists(self.data_file):
                with self._file_lock(self.data_file, 'r'):
                    with open(self.data_file, 'r', encoding='utf-8') as f:
                        self.data = json.load(f)
                logger.info(f"Loaded {len(self.data)} items from {self.data_file}")
            else:
                self.data = {}
                self._save_json_data()
                logger.info("Created new data store")
                
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load data file {self.data_file}: {e}")
            
            # Try to recover from backup
            if self._recover_from_backup():
                logger.info("Successfully recovered data from backup")
            else:
                logger.warning("Creating new empty data store")
                self.data = {}
                self._save_json_data()
            
            self.metrics['errors'] += 1
    
    def _save_json_data(self) -> None:
        """Save data to JSON file with atomic writes."""
        temp_file = f"{self.data_file}.tmp"
        
        try:
            # Write to temporary file first
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic move
            if os.name == 'nt':  # Windows
                if os.path.exists(self.data_file):
                    os.remove(self.data_file)
            
            os.rename(temp_file, self.data_file)
            
            # Set appropriate permissions
            os.chmod(self.data_file, 0o640)
            
            logger.debug(f"Saved {len(self.data)} items to {self.data_file}")
            
        except IOError as e:
            logger.error(f"Failed to save data file {self.data_file}: {e}")
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise
    
    @contextmanager
    def _file_lock(self, filename: str, mode: str = 'r'):
        """File locking context manager for concurrent access."""
        if os.name == 'nt':  # Windows - no fcntl
            with open(filename, mode, encoding='utf-8') as f:
                yield f
        else:  # Unix-like systems
            with open(filename, mode, encoding='utf-8') as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    yield f
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def get(self, key: str, use_sqlite: bool = None) -> Optional[Any]:
        """Get a value by key with performance tracking."""
        start_time = time.time()
        
        try:
            with self._lock:
                if use_sqlite is None:
                    use_sqlite = self.enable_sqlite
                
                if use_sqlite and self.enable_sqlite:
                    result = self._get_from_sqlite(key)
                    if result is not None:
                        return result
                
                # Fallback to JSON storage
                result = self.data.get(key)
                
                # Update metrics
                self.metrics['reads'] += 1
                read_time = time.time() - start_time
                self.metrics['avg_read_time'] = (
                    (self.metrics['avg_read_time'] * (self.metrics['reads'] - 1) + read_time) / 
                    self.metrics['reads']
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting key '{key}': {e}")
            self.metrics['errors'] += 1
            return None
    
    def _get_from_sqlite(self, key: str) -> Optional[Any]:
        """Get value from SQLite database."""
        try:
            with sqlite3.connect(self.sqlite_db, timeout=30.0) as conn:
                cursor = conn.execute(
                    'SELECT value, checksum FROM kv_store WHERE key = ?', 
                    (key,)
                )
                row = cursor.fetchone()
                
                if row:
                    value_str, stored_checksum = row
                    
                    # Verify checksum
                    calculated_checksum = hashlib.sha256(value_str.encode()).hexdigest()
                    if calculated_checksum != stored_checksum:
                        logger.warning(f"Checksum mismatch for key '{key}' in SQLite")
                        return None
                    
                    return json.loads(value_str)
                
                return None
                
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Error getting key '{key}' from SQLite: {e}")
            return None
    
    def set(self, key: str, value: Any, use_sqlite: bool = None) -> bool:
        """Set a value with performance tracking and dual storage."""
        start_time = time.time()
        
        try:
            with self._lock:
                # Always update JSON storage
                self.data[key] = value
                self._save_json_data()
                
                # Update SQLite if enabled
                if use_sqlite is None:
                    use_sqlite = self.enable_sqlite
                
                if use_sqlite and self.enable_sqlite:
                    self._set_to_sqlite(key, value)
                
                # Update metrics
                self.metrics['writes'] += 1
                write_time = time.time() - start_time
                self.metrics['avg_write_time'] = (
                    (self.metrics['avg_write_time'] * (self.metrics['writes'] - 1) + write_time) / 
                    self.metrics['writes']
                )
                
                logger.debug(f"Set key '{key}' with value type {type(value).__name__}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting key '{key}': {e}")
            self.metrics['errors'] += 1
            return False
    
    def _set_to_sqlite(self, key: str, value: Any) -> None:
        """Set value in SQLite database."""
        try:
            value_str = json.dumps(value, ensure_ascii=False)
            checksum = hashlib.sha256(value_str.encode()).hexdigest()
            
            with sqlite3.connect(self.sqlite_db, timeout=30.0) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO kv_store (key, value, checksum)
                    VALUES (?, ?, ?)
                ''', (key, value_str, checksum))
                conn.commit()
                
        except (sqlite3.Error, json.JSONEncodeError) as e:
            logger.error(f"Error setting key '{key}' in SQLite: {e}")
    
    def delete(self, key: str, use_sqlite: bool = None) -> bool:
        """Delete a key-value pair from both storages."""
        try:
            with self._lock:
                existed_in_json = key in self.data
                
                if existed_in_json:
                    del self.data[key]
                    self._save_json_data()
                
                # Delete from SQLite if enabled
                if use_sqlite is None:
                    use_sqlite = self.enable_sqlite
                
                existed_in_sqlite = False
                if use_sqlite and self.enable_sqlite:
                    existed_in_sqlite = self._delete_from_sqlite(key)
                
                result = existed_in_json or existed_in_sqlite
                
                if result:
                    logger.debug(f"Deleted key '{key}'")
                
                return result
                
        except Exception as e:
            logger.error(f"Error deleting key '{key}': {e}")
            self.metrics['errors'] += 1
            return False
    
    def _delete_from_sqlite(self, key: str) -> bool:
        """Delete key from SQLite database."""
        try:
            with sqlite3.connect(self.sqlite_db, timeout=30.0) as conn:
                cursor = conn.execute('DELETE FROM kv_store WHERE key = ?', (key,))
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error deleting key '{key}' from SQLite: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all stored data (combined from both sources)."""
        try:
            with self._lock:
                result = self.data.copy()
                
                # Merge SQLite data if enabled
                if self.enable_sqlite:
                    sqlite_data = self._get_all_from_sqlite()
                    result.update(sqlite_data)
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting all data: {e}")
            self.metrics['errors'] += 1
            return {}
    
    def _get_all_from_sqlite(self) -> Dict[str, Any]:
        """Get all data from SQLite."""
        try:
            with sqlite3.connect(self.sqlite_db, timeout=30.0) as conn:
                cursor = conn.execute('SELECT key, value FROM kv_store')
                
                result = {}
                for key, value_str in cursor.fetchall():
                    try:
                        result[key] = json.loads(value_str)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse value for key '{key}' from SQLite")
                
                return result
                
        except sqlite3.Error as e:
            logger.error(f"Error getting all data from SQLite: {e}")
            return {}
    
    def backup_data(self) -> bool:
        """Create a backup of the current data."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"{self.data_dir}/backups"
            
            # Backup JSON file
            if os.path.exists(self.data_file):
                json_backup = f"{backup_dir}/storage_{timestamp}.json"
                shutil.copy2(self.data_file, json_backup)
                
                # Compress backup
                os.system(f"gzip {json_backup}")
                logger.info(f"Created JSON backup: {json_backup}.gz")
            
            # Backup SQLite database
            if self.enable_sqlite and os.path.exists(self.sqlite_db):
                sqlite_backup = f"{backup_dir}/storage_{timestamp}.db"
                shutil.copy2(self.sqlite_db, sqlite_backup)
                
                os.system(f"gzip {sqlite_backup}")
                logger.info(f"Created SQLite backup: {sqlite_backup}.gz")
            
            # Clean up old backups
            self._cleanup_old_backups(backup_dir)
            
            self.metrics['backup_count'] += 1
            self.metrics['last_backup'] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            self.metrics['errors'] += 1
            return False
    
    def _cleanup_old_backups(self, backup_dir: str) -> None:
        """Remove old backup files."""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)  # Keep 30 days
            
            for filename in os.listdir(backup_dir):
                if filename.startswith('storage_') and filename.endswith('.gz'):
                    filepath = os.path.join(backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        logger.debug(f"Removed old backup: {filename}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def _recover_from_backup(self) -> bool:
        """Recover data from the most recent backup."""
        try:
            backup_dir = f"{self.data_dir}/backups"
            if not os.path.exists(backup_dir):
                return False
            
            # Find most recent JSON backup
            json_backups = [f for f in os.listdir(backup_dir) 
                           if f.startswith('storage_') and f.endswith('.json.gz')]
            
            if not json_backups:
                return False
            
            latest_backup = max(json_backups)
            backup_path = os.path.join(backup_dir, latest_backup)
            
            # Decompress and load backup
            os.system(f"gunzip -c {backup_path} > {self.data_file}.recovery")
            
            with open(f"{self.data_file}.recovery", 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # Replace current file with recovery
            os.rename(f"{self.data_file}.recovery", self.data_file)
            
            logger.info(f"Recovered data from backup: {latest_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover from backup: {e}")
            return False
    
    def _start_backup_thread(self) -> None:
        """Start background backup thread."""
        def backup_worker():
            while True:
                time.sleep(self.backup_interval)
                if self.backup_enabled:
                    self.backup_data()
        
        backup_thread = threading.Thread(target=backup_worker, daemon=True)
        backup_thread.start()
        logger.info(f"Started backup thread (interval: {self.backup_interval}s)")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance and operational metrics."""
        with self._lock:
            return {
                **self.metrics,
                'storage_size': len(self.data),
                'data_file_size': os.path.getsize(self.data_file) if os.path.exists(self.data_file) else 0,
                'sqlite_enabled': self.enable_sqlite,
                'backup_enabled': self.backup_enabled
            }
    
    def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """Perform health check on the data store."""
        issues = []
        
        try:
            # Test JSON storage
            test_key = f"__health_check_{int(time.time())}"
            self.set(test_key, "test_value")
            value = self.get(test_key)
            self.delete(test_key)
            
            if value != "test_value":
                issues.append("JSON storage read/write test failed")
            
            # Test SQLite if enabled
            if self.enable_sqlite:
                try:
                    with sqlite3.connect(self.sqlite_db, timeout=5.0) as conn:
                        conn.execute('SELECT 1').fetchone()
                except sqlite3.Error as e:
                    issues.append(f"SQLite connectivity issue: {e}")
            
            # Check disk space
            disk_usage = shutil.disk_usage(self.data_dir)
            free_space_pct = (disk_usage.free / disk_usage.total) * 100
            
            if free_space_pct < 10:
                issues.append(f"Low disk space: {free_space_pct:.1f}% free")
            
            # Check backup status
            if self.backup_enabled and self.metrics['last_backup']:
                last_backup = datetime.fromisoformat(self.metrics['last_backup'])
                if datetime.now() - last_backup > timedelta(hours=25):  # Allow some buffer
                    issues.append("Backup is overdue")
            
            return len(issues) == 0, {
                'issues': issues,
                'metrics': self.get_metrics(),
                'disk_free_pct': free_space_pct
            }
            
        except Exception as e:
            return False, {'error': str(e), 'issues': issues}
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            if hasattr(self, 'backup_enabled') and self.backup_enabled:
                self.backup_data()
        except:
            pass  # Ignore errors during cleanup