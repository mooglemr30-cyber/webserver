# AI Intelligence System

## Overview
This project uses an AI Intelligence system with MongoDB/TinyDB for persistent memory and learning.

## Features
- Conversation storage and retrieval
- Context management across sessions
- Learning system with searchable topics
- Memory management (Copilot Memory integration)
- Task tracking and status updates
- Decision logging for AI improvements

## Backend
- **Primary**: MongoDB (if configured)
- **Fallback**: TinyDB (automatic, no setup needed)

## Quick Start
```python
from src.ai_intelligence import get_ai_intelligence

# Initialize AI Intelligence
ai = get_ai_intelligence()

# Store context
ai.store_context("project_state", {"status": "active"})

# Retrieve context
context = ai.get_context("project_state")

# Store learnings
ai.store_learning("Topic", "Learning content", importance=5)

# Search learnings
learnings = ai.search_learnings(query="keyword")
```

## Configuration
Set `MONGODB_URI` environment variable for MongoDB, or use TinyDB automatically.

See `AI_INTELLIGENCE_SETUP.md` for complete documentation.
