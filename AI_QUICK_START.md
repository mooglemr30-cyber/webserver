# Quick Start: AI Intelligence System

## What Was Done

The Copilot Memory extension (`yaotsakpo.copilot-memory`) is now fully integrated with an AI Intelligence system using MongoDB/TinyDB.

## Quick Start

### Option 1: Use TinyDB (Recommended for Testing)
```bash
cd /home/admin1/Documents/webserver
source .venv/bin/activate
python test_ai_intelligence.py
```

### Option 2: Full Setup with MongoDB Options
```bash
cd /home/admin1/Documents/webserver
./setup_ai_intelligence.sh
```

## What's Available

### 1. AI Intelligence Manager
```python
from src.ai_intelligence import get_ai_intelligence

ai = get_ai_intelligence()

# Store conversations
ai.store_conversation("id", "user message", "ai response")

# Manage context
ai.store_context("key", {"data": "value"})
context = ai.get_context("key")

# Store learnings
ai.store_learning("topic", "content", importance=5)
learnings = ai.search_learnings(query="keyword")

# Track tasks
ai.store_task("task_id", "description", status="pending")
ai.update_task_status("task_id", "completed")

# Log decisions
ai.store_decision("context", "decision", "reasoning")
```

### 2. Backend Options
- **TinyDB** (default): No setup required, stores in `data/ai/intelligence.json`
- **MongoDB Atlas**: Free cloud database
- **Docker MongoDB**: Local MongoDB server
- **Custom MongoDB**: Your own MongoDB instance

### 3. Configuration
Edit `data/config/ai_config.json` or set environment variable:
```bash
export MONGODB_URI="mongodb://localhost:27017/"
```

## Files

- **Core Module**: `src/ai_intelligence.py`
- **Test Script**: `test_ai_intelligence.py`
- **Setup Script**: `setup_ai_intelligence.sh`
- **Documentation**: `AI_INTELLIGENCE_SETUP.md`
- **Configuration**: `data/config/ai_config.json`

## Test Results

✓ All tests passed successfully
- Conversations: Working
- Context: Working
- Learnings: Working
- Memories: Working
- Tasks: Working
- Decisions: Working
- Export: Working

Backend: TinyDB (automatic fallback)
Data file: `data/ai/intelligence.json`

## Next Steps

1. Run the test: `python test_ai_intelligence.py`
2. Read full docs: `AI_INTELLIGENCE_SETUP.md`
3. Integrate into your Flask app
4. (Optional) Set up MongoDB for production use

Everything is ready to use!
