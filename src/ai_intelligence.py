#!/usr/bin/env python3
"""
AI Intelligence Module with MongoDB/TinyDB Integration
Provides intelligent context storage, learning, and memory for AI agents
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import MongoDB, fall back to TinyDB if unavailable
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("MongoDB not available, using TinyDB as fallback")

try:
    from tinydb import TinyDB, Query
    TINYDB_AVAILABLE = True
except ImportError:
    TINYDB_AVAILABLE = False
    logger.warning("TinyDB not available")


class AIIntelligenceManager:
    """
    Manages AI intelligence storage and retrieval using MongoDB or TinyDB.
    Integrates with Copilot Memory extension for persistent AI context.
    """
    
    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        database_name: str = "ai_intelligence",
        fallback_db_path: str = "data/ai/intelligence.json"
    ):
        """
        Initialize AI Intelligence Manager.
        
        Args:
            mongo_uri: MongoDB connection string (e.g., "mongodb://localhost:27017/")
            database_name: Name of the MongoDB database
            fallback_db_path: Path for TinyDB fallback storage
        """
        self.database_name = database_name
        self.fallback_db_path = fallback_db_path
        self.use_mongodb = False
        self.db = None
        self.collections = {}
        
        # Try to connect to MongoDB first
        if mongo_uri and MONGODB_AVAILABLE:
            try:
                self.client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000
                )
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client[database_name]
                self.use_mongodb = True
                logger.info(f"Connected to MongoDB: {database_name}")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"MongoDB connection failed: {e}. Using TinyDB fallback.")
                self._init_tinydb()
        else:
            self._init_tinydb()
        
        # Initialize collections/tables
        self._init_storage()
    
    def _init_tinydb(self):
        """Initialize TinyDB as fallback storage."""
        if not TINYDB_AVAILABLE:
            raise RuntimeError("Neither MongoDB nor TinyDB is available")
        
        # Ensure directory exists
        Path(self.fallback_db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = TinyDB(self.fallback_db_path)
        logger.info(f"Using TinyDB storage: {self.fallback_db_path}")
    
    def _init_storage(self):
        """Initialize storage collections/tables."""
        if self.use_mongodb:
            # MongoDB collections
            self.collections = {
                'conversations': self.db['conversations'],
                'context': self.db['context'],
                'learnings': self.db['learnings'],
                'memories': self.db['memories'],
                'tasks': self.db['tasks'],
                'decisions': self.db['decisions'],
            }
        else:
            # TinyDB tables
            self.collections = {
                'conversations': self.db.table('conversations'),
                'context': self.db.table('context'),
                'learnings': self.db.table('learnings'),
                'memories': self.db.table('memories'),
                'tasks': self.db.table('tasks'),
                'decisions': self.db.table('decisions'),
            }
    
    def store_conversation(
        self,
        conversation_id: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Store a conversation exchange."""
        conversation = {
            'conversation_id': conversation_id,
            'user_message': user_message,
            'ai_response': ai_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {}
        }
        
        try:
            if self.use_mongodb:
                result = self.collections['conversations'].insert_one(conversation)
                return str(result.inserted_id)
            else:
                doc_id = self.collections['conversations'].insert(conversation)
                return str(doc_id)
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            return None
    
    def store_context(
        self,
        context_key: str,
        context_data: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store AI context information."""
        context = {
            'key': context_key,
            'data': context_data,
            'tags': tags or [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            if self.use_mongodb:
                self.collections['context'].update_one(
                    {'key': context_key},
                    {'$set': context},
                    upsert=True
                )
            else:
                ContextQuery = Query()
                existing = self.collections['context'].search(ContextQuery.key == context_key)
                if existing:
                    self.collections['context'].update(context, ContextQuery.key == context_key)
                else:
                    self.collections['context'].insert(context)
            return True
        except Exception as e:
            logger.error(f"Error storing context: {e}")
            return False
    
    def get_context(self, context_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve context by key."""
        try:
            if self.use_mongodb:
                result = self.collections['context'].find_one({'key': context_key})
                return result.get('data') if result else None
            else:
                ContextQuery = Query()
                results = self.collections['context'].search(ContextQuery.key == context_key)
                return results[0].get('data') if results else None
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return None
    
    def store_learning(
        self,
        topic: str,
        learning_content: str,
        importance: int = 1,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store a learning item."""
        learning = {
            'topic': topic,
            'content': learning_content,
            'importance': importance,
            'tags': tags or [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'access_count': 0
        }
        
        try:
            if self.use_mongodb:
                self.collections['learnings'].insert_one(learning)
            else:
                self.collections['learnings'].insert(learning)
            return True
        except Exception as e:
            logger.error(f"Error storing learning: {e}")
            return False
    
    def search_learnings(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search learnings by query or tags."""
        try:
            if self.use_mongodb:
                search_filter = {}
                if query:
                    search_filter['$or'] = [
                        {'topic': {'$regex': query, '$options': 'i'}},
                        {'content': {'$regex': query, '$options': 'i'}}
                    ]
                if tags:
                    search_filter['tags'] = {'$in': tags}
                
                results = self.collections['learnings'].find(search_filter).sort('importance', -1).limit(limit)
                return list(results)
            else:
                LearningQuery = Query()
                results = self.collections['learnings'].all()
                
                if query:
                    query_lower = query.lower()
                    results = [r for r in results if 
                             query_lower in r.get('topic', '').lower() or 
                             query_lower in r.get('content', '').lower()]
                
                if tags:
                    results = [r for r in results if 
                             any(tag in r.get('tags', []) for tag in tags)]
                
                # Sort by importance
                results.sort(key=lambda x: x.get('importance', 0), reverse=True)
                return results[:limit]
        except Exception as e:
            logger.error(f"Error searching learnings: {e}")
            return []
    
    def store_memory(
        self,
        memory_type: str,
        memory_content: Dict[str, Any],
        retention_priority: int = 1
    ) -> bool:
        """Store a memory item (for Copilot Memory integration)."""
        memory = {
            'type': memory_type,
            'content': memory_content,
            'retention_priority': retention_priority,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'access_count': 0,
            'last_accessed': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            if self.use_mongodb:
                self.collections['memories'].insert_one(memory)
            else:
                self.collections['memories'].insert(memory)
            return True
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def get_recent_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent memories."""
        try:
            if self.use_mongodb:
                query = {'type': memory_type} if memory_type else {}
                results = self.collections['memories'].find(query).sort('timestamp', -1).limit(limit)
                return list(results)
            else:
                MemoryQuery = Query()
                if memory_type:
                    results = self.collections['memories'].search(MemoryQuery.type == memory_type)
                else:
                    results = self.collections['memories'].all()
                
                # Sort by timestamp
                results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                return results[:limit]
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    def store_task(
        self,
        task_id: str,
        task_description: str,
        status: str = "pending",
        metadata: Optional[Dict] = None
    ) -> bool:
        """Store a task."""
        task = {
            'task_id': task_id,
            'description': task_description,
            'status': status,
            'metadata': metadata or {},
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            if self.use_mongodb:
                self.collections['tasks'].update_one(
                    {'task_id': task_id},
                    {'$set': task},
                    upsert=True
                )
            else:
                TaskQuery = Query()
                existing = self.collections['tasks'].search(TaskQuery.task_id == task_id)
                if existing:
                    self.collections['tasks'].update(task, TaskQuery.task_id == task_id)
                else:
                    self.collections['tasks'].insert(task)
            return True
        except Exception as e:
            logger.error(f"Error storing task: {e}")
            return False
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status."""
        try:
            if self.use_mongodb:
                self.collections['tasks'].update_one(
                    {'task_id': task_id},
                    {'$set': {
                        'status': status,
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }}
                )
            else:
                TaskQuery = Query()
                self.collections['tasks'].update(
                    {
                        'status': status,
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    },
                    TaskQuery.task_id == task_id
                )
            return True
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False
    
    def get_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks, optionally filtered by status."""
        try:
            if self.use_mongodb:
                query = {'status': status} if status else {}
                results = self.collections['tasks'].find(query).sort('created_at', -1)
                return list(results)
            else:
                TaskQuery = Query()
                if status:
                    results = self.collections['tasks'].search(TaskQuery.status == status)
                else:
                    results = self.collections['tasks'].all()
                
                results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                return results
        except Exception as e:
            logger.error(f"Error retrieving tasks: {e}")
            return []
    
    def store_decision(
        self,
        decision_context: str,
        decision_made: str,
        reasoning: str,
        outcome: Optional[str] = None
    ) -> bool:
        """Store an AI decision for learning."""
        decision = {
            'context': decision_context,
            'decision': decision_made,
            'reasoning': reasoning,
            'outcome': outcome,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            if self.use_mongodb:
                self.collections['decisions'].insert_one(decision)
            else:
                self.collections['decisions'].insert(decision)
            return True
        except Exception as e:
            logger.error(f"Error storing decision: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get intelligence statistics."""
        stats = {
            'backend': 'MongoDB' if self.use_mongodb else 'TinyDB',
            'database': self.database_name,
        }
        
        try:
            for name, collection in self.collections.items():
                if self.use_mongodb:
                    count = collection.count_documents({})
                else:
                    count = len(collection.all())
                stats[f'{name}_count'] = count
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
        
        return stats

    # -----------------------------
    # Document Ingestion / Idea Generation
    # -----------------------------

    def ingest_document(self, text: str, source_path: str, tags: Optional[List[str]] = None) -> bool:
        """Ingest a raw document's text into learnings.

        Splits text into paragraphs, stores each as a learning with a reference
        to the source path. Returns True on any successful insert.
        """
        if not text.strip():
            return False
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        inserted = False
        base_tags = tags or []
        for p in paragraphs:
            ok = self.store_learning(
                topic=os.path.basename(source_path)[:120],
                learning_content=p[:10000],
                importance=1,
                tags=list(set(base_tags + ['doc', 'ingested']))
            )
            inserted = inserted or ok
        # Memory trace for provenance
        self.store_memory(
            'ingestion',
            {
                'source': source_path,
                'paragraphs': len(paragraphs),
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            retention_priority=1
        )
        return inserted

    def generate_ideas(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Generate simple improvement ideas based on current learnings and decisions.

        Heuristic approach: look for frequency of certain keywords and propose
        ideas; can be replaced with LLM later.
        """
        learnings = self.search_learnings(limit=200)
        decisions = []
        if self.use_mongodb:
            try:
                decisions = list(self.collections['decisions'].find({}).limit(200))
            except Exception:
                decisions = []
        else:
            try:
                decisions = self.collections['decisions'].all()[:200]
            except Exception:
                decisions = []

        corpus = ' '.join([l.get('content', '') for l in learnings])
        keywords = {
            'performance': 'Consider profiling critical paths and adding caching layers.',
            'security': 'Review authentication flows and ensure token revocation is robust.',
            'path': 'Centralize any remaining hard-coded paths using path_config.',
            'memory': 'Implement aging/decay for low-priority memories to maintain relevance.',
            'tunnel': 'Add health checks for active tunnels and auto-restart on failures.'
        }
        ideas = []
        lower = corpus.lower()
        for k, suggestion in keywords.items():
            if k in lower:
                ideas.append({'topic': k, 'suggestion': suggestion})
        if not ideas:
            ideas.append({'topic': 'general', 'suggestion': 'Expand scanning to include code comments and TODO markers.'})

        # Store generated ideas as learnings with higher importance
        for idea in ideas:
            self.store_learning(
                topic=f"idea:{idea['topic']}",
                learning_content=idea['suggestion'],
                importance=2,
                tags=['idea', 'auto-generated']
            )
        self.store_memory('idea_generation', {'count': len(ideas)}, retention_priority=1)
        return ideas
    
    def export_data(self, output_path: str) -> bool:
        """Export all intelligence data to JSON."""
        try:
            export_data = {
                'exported_at': datetime.now(timezone.utc).isoformat(),
                'backend': 'MongoDB' if self.use_mongodb else 'TinyDB',
                'collections': {}
            }
            
            for name, collection in self.collections.items():
                if self.use_mongodb:
                    data = list(collection.find({}, {'_id': 0}))
                else:
                    data = collection.all()
                export_data['collections'][name] = data
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported intelligence data to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear a specific collection."""
        try:
            if collection_name in self.collections:
                if self.use_mongodb:
                    self.collections[collection_name].delete_many({})
                else:
                    self.collections[collection_name].truncate()
                logger.info(f"Cleared collection: {collection_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
    
    def close(self):
        """Close database connections."""
        try:
            if self.use_mongodb and hasattr(self, 'client'):
                self.client.close()
                logger.info("Closed MongoDB connection")
            elif not self.use_mongodb and self.db:
                self.db.close()
                logger.info("Closed TinyDB connection")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


# Global instance
_ai_intelligence = None


def get_ai_intelligence(
    mongo_uri: Optional[str] = None,
    database_name: str = "ai_intelligence"
) -> AIIntelligenceManager:
    """Get or create global AI Intelligence Manager instance."""
    global _ai_intelligence
    
    if _ai_intelligence is None:
        # Try to get MongoDB URI from environment
        if mongo_uri is None:
            mongo_uri = os.environ.get('MONGODB_URI')
        
        _ai_intelligence = AIIntelligenceManager(
            mongo_uri=mongo_uri,
            database_name=database_name
        )
    
    return _ai_intelligence
