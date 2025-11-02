#!/usr/bin/env python3
"""
Example usage of AI Intelligence Manager with Copilot Memory integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_intelligence import get_ai_intelligence
import json
from datetime import datetime

def main():
    """Demonstrate AI Intelligence features."""
    
    print("=== AI Intelligence System Demo ===\n")
    
    # Initialize AI Intelligence Manager
    # It will use TinyDB by default (MongoDB if URI provided)
    ai = get_ai_intelligence()
    
    print(f"✓ Connected to {ai.get_stats()['backend']} backend\n")
    
    # 1. Store a conversation
    print("1. Storing conversation...")
    conv_id = ai.store_conversation(
        conversation_id="conv_001",
        user_message="How do I set up MongoDB for AI intelligence?",
        ai_response="You can use the AI Intelligence Manager which supports both MongoDB and TinyDB...",
        metadata={"source": "copilot-chat", "session": "demo"}
    )
    print(f"   ✓ Stored conversation: {conv_id}\n")
    
    # 2. Store context information
    print("2. Storing context...")
    ai.store_context(
        context_key="project_setup",
        context_data={
            "project_name": "webserver",
            "language": "python",
            "database": "mongodb/tinydb",
            "features": ["ai_intelligence", "copilot_memory"]
        },
        tags=["setup", "configuration"]
    )
    print("   ✓ Context stored\n")
    
    # 3. Retrieve context
    print("3. Retrieving context...")
    context = ai.get_context("project_setup")
    print(f"   ✓ Retrieved: {json.dumps(context, indent=2)}\n")
    
    # 4. Store learnings
    print("4. Storing learnings...")
    ai.store_learning(
        topic="MongoDB Setup",
        learning_content="MongoDB can be replaced with TinyDB for simpler deployments without a separate database server",
        importance=5,
        tags=["database", "deployment", "best-practices"]
    )
    ai.store_learning(
        topic="AI Memory Management",
        learning_content="Use the Copilot Memory extension to persist context across sessions",
        importance=4,
        tags=["ai", "memory", "best-practices"]
    )
    print("   ✓ Learnings stored\n")
    
    # 5. Search learnings
    print("5. Searching learnings...")
    learnings = ai.search_learnings(query="MongoDB", limit=5)
    print(f"   ✓ Found {len(learnings)} learnings:")
    for learning in learnings:
        print(f"      - {learning['topic']}: {learning['content'][:50]}...")
    print()
    
    # 6. Store memories (for Copilot Memory integration)
    print("6. Storing memories...")
    ai.store_memory(
        memory_type="project_state",
        memory_content={
            "last_action": "setup_ai_intelligence",
            "completed_tasks": ["install_pymongo", "create_ai_module"],
            "timestamp": datetime.now().isoformat()
        },
        retention_priority=3
    )
    print("   ✓ Memory stored\n")
    
    # 7. Get recent memories
    print("7. Retrieving recent memories...")
    memories = ai.get_recent_memories(limit=5)
    print(f"   ✓ Found {len(memories)} memories:")
    for memory in memories:
        print(f"      - {memory['type']}: {memory.get('timestamp', 'N/A')}")
    print()
    
    # 8. Store and track tasks
    print("8. Storing tasks...")
    ai.store_task(
        task_id="task_001",
        task_description="Configure MongoDB for production",
        status="pending",
        metadata={"priority": "high", "assigned_to": "ai_agent"}
    )
    ai.store_task(
        task_id="task_002",
        task_description="Test AI intelligence integration",
        status="in_progress"
    )
    print("   ✓ Tasks stored\n")
    
    # 9. Update task status
    print("9. Updating task...")
    ai.update_task_status("task_002", "completed")
    print("   ✓ Task updated\n")
    
    # 10. Get tasks
    print("10. Retrieving tasks...")
    pending_tasks = ai.get_tasks(status="pending")
    print(f"    ✓ Pending tasks: {len(pending_tasks)}")
    for task in pending_tasks:
        print(f"       - {task['task_id']}: {task['description']}")
    print()
    
    # 11. Store AI decisions
    print("11. Storing AI decision...")
    ai.store_decision(
        decision_context="Choosing database backend",
        decision_made="Use TinyDB as fallback when MongoDB unavailable",
        reasoning="Provides resilience and doesn't require external dependencies",
        outcome="successful"
    )
    print("    ✓ Decision logged\n")
    
    # 12. Get system statistics
    print("12. System Statistics:")
    stats = ai.get_stats()
    for key, value in stats.items():
        print(f"    - {key}: {value}")
    print()
    
    # 13. Export data
    print("13. Exporting data...")
    export_path = "data/ai/intelligence_export.json"
    ai.export_data(export_path)
    print(f"    ✓ Data exported to {export_path}\n")
    
    print("=== Demo Complete ===")
    print("\nThe AI Intelligence system is now ready for use!")
    print("It will automatically use TinyDB unless you set MONGODB_URI environment variable.")
    
    # Clean up
    ai.close()

if __name__ == "__main__":
    main()
