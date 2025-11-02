# AI Intelligence System with MongoDB/TinyDB Integration

## Overview

This system provides intelligent context storage, learning, and memory capabilities for AI agents, integrated with the Copilot Memory extension.

## Features

- **Conversation Storage**: Store and retrieve AI-human conversations
- **Context Management**: Persistent context storage across sessions
- **Learning System**: Store and search learnings by topic and tags
- **Memory Management**: Integration with Copilot Memory extension
- **Task Tracking**: Track AI tasks and their status
- **Decision Logging**: Log AI decisions for learning and improvement
- **Flexible Backend**: Supports MongoDB or TinyDB (automatic fallback)

## Installation

### Prerequisites

Already installed:
- Python 3.8+
- pymongo
- tinydb

### Quick Start

1. **Using TinyDB (No Setup Required)**
   ```bash
   # TinyDB works out of the box - no database server needed!
   python test_ai_intelligence.py
   ```

2. **Using MongoDB (Optional)**
   
   **Option A: MongoDB Atlas (Cloud - Recommended)**
   - Sign up at https://www.mongodb.com/cloud/atlas
   - Create a free cluster
   - Get your connection string
   - Set environment variable:
     ```bash
     export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
     ```

   **Option B: Local MongoDB**
   - Install Docker:
     ```bash
     docker run -d -p 27017:27017 --name mongodb mongo:latest
     export MONGODB_URI="mongodb://localhost:27017/"
     ```

## Configuration

### Environment Variables

```bash
# MongoDB connection (optional)
export MONGODB_URI="mongodb://localhost:27017/"

# Or for MongoDB Atlas
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/"
```

### Configuration File

Edit `data/config/ai_config.json`:

```json
{
  "ai_intelligence": {
    "enabled": true,
    "mongodb": {
      "uri": null,
      "database": "ai_intelligence"
    },
    "tinydb": {
      "path": "data/ai/intelligence.json"
    },
    "settings": {
      "memory_retention_days": 90,
      "max_memories": 10000
    }
  }
}
```

## Usage

### Basic Usage

```python
from src.ai_intelligence import get_ai_intelligence

# Initialize (auto-detects MongoDB or uses TinyDB)
ai = get_ai_intelligence()

# Store a conversation
ai.store_conversation(
    conversation_id="conv_001",
    user_message="How do I use this?",
    ai_response="Here's how...",
    metadata={"session": "demo"}
)

# Store context
ai.store_context(
    context_key="project_setup",
    context_data={"status": "in_progress"},
    tags=["setup"]
)

# Retrieve context
context = ai.get_context("project_setup")

# Store learnings
ai.store_learning(
    topic="Best Practices",
    learning_content="Always validate input data",
    importance=5,
    tags=["security", "best-practices"]
)

# Search learnings
learnings = ai.search_learnings(query="security", limit=10)

# Store memories
ai.store_memory(
    memory_type="project_state",
    memory_content={"last_action": "deploy"},
    retention_priority=3
)

# Track tasks
ai.store_task(
    task_id="task_001",
    task_description="Complete feature X",
    status="pending"
)

# Update task
ai.update_task_status("task_001", "completed")

# Log decisions
ai.store_decision(
    decision_context="Architecture choice",
    decision_made="Use microservices",
    reasoning="Better scalability"
)

# Get statistics
stats = ai.get_stats()
print(stats)

# Close connection
ai.close()
```

### Integration with Flask App

Add to `src/app.py`:

```python
from ai_intelligence import get_ai_intelligence

# Initialize in app setup
ai_intelligence = get_ai_intelligence()

# Use in routes
@app.route('/api/store_context', methods=['POST'])
def store_context():
    data = request.json
    ai_intelligence.store_context(
        context_key=data['key'],
        context_data=data['data'],
        tags=data.get('tags', [])
    )
    return jsonify({"status": "success"})
```

## Copilot Memory Integration

The system integrates with the Copilot Memory extension (`yaotsakpo.copilot-memory`):

1. **Automatic Memory Storage**: AI interactions are stored automatically
2. **Context Persistence**: Project context is maintained across sessions
3. **Learning from History**: Past decisions inform future actions

### Memory Directory

The extension uses `/memories` directory to store:
- Project state
- Task progress
- AI learnings
- Decision history

## Testing

Run the test script to verify everything works:

```bash
python test_ai_intelligence.py
```

This will:
- Test all AI intelligence features
- Create sample data
- Display statistics
- Export data for inspection

## Architecture

### Backend Selection

1. **MongoDB** (if available and configured)
   - Production-ready
   - Scalable
   - Rich querying

2. **TinyDB** (automatic fallback)
   - No setup required
   - File-based (JSON)
   - Perfect for development

### Collections/Tables

- `conversations`: AI-human conversations
- `context`: Project context data
- `learnings`: Stored learnings by topic
- `memories`: Memory items for Copilot
- `tasks`: Task tracking
- `decisions`: AI decision logs

## API Reference

### AIIntelligenceManager

#### Methods

- `store_conversation(conversation_id, user_message, ai_response, metadata=None)`
- `store_context(context_key, context_data, tags=None)`
- `get_context(context_key)`
- `store_learning(topic, learning_content, importance=1, tags=None)`
- `search_learnings(query=None, tags=None, limit=10)`
- `store_memory(memory_type, memory_content, retention_priority=1)`
- `get_recent_memories(memory_type=None, limit=20)`
- `store_task(task_id, task_description, status="pending", metadata=None)`
- `update_task_status(task_id, status)`
- `get_tasks(status=None)`
- `store_decision(decision_context, decision_made, reasoning, outcome=None)`
- `get_stats()`
- `export_data(output_path)`
- `clear_collection(collection_name)`
- `close()`

## Advanced Configuration

### MongoDB Atlas Setup

1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free account
3. Create a new cluster (M0 Free tier)
4. Create a database user
5. Whitelist your IP (or use 0.0.0.0/0 for testing)
6. Get connection string
7. Set environment variable:
   ```bash
   export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
   ```

### Docker MongoDB Setup

```bash
# Start MongoDB
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  -v mongodb_data:/data/db \
  mongo:latest

# Set URI
export MONGODB_URI="mongodb://admin:password@localhost:27017/"
```

## Troubleshooting

### Issue: "MongoDB connection failed"
**Solution**: System automatically falls back to TinyDB. Check logs for details.

### Issue: "Neither MongoDB nor TinyDB is available"
**Solution**: Reinstall dependencies:
```bash
pip install pymongo tinydb
```

### Issue: Permission denied on data/ai/
**Solution**: Create directory:
```bash
mkdir -p data/ai
chmod 755 data/ai
```

## Performance Tips

1. **Use MongoDB for production** - Better performance with large datasets
2. **Regular cleanup** - Set `memory_retention_days` appropriately
3. **Indexing** - MongoDB automatically indexes for better search
4. **Exports** - Regularly export data for backups

## Security

- MongoDB connections use authentication by default
- TinyDB files are stored in `data/ai/` (add to .gitignore)
- No sensitive data should be stored in context/memories
- Use environment variables for credentials

## Support

- Copilot Memory Extension: https://marketplace.visualstudio.com/items?itemName=yaotsakpo.copilot-memory
- MongoDB Documentation: https://docs.mongodb.com/
- TinyDB Documentation: https://tinydb.readthedocs.io/

## License

Same as main project license.
