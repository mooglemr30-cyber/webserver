#!/usr/bin/env python3
"""
Example Flask integration with AI Intelligence System
Shows how to integrate the AI Intelligence Manager into your Flask app
"""

from flask import Flask, request, jsonify
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_intelligence import get_ai_intelligence

app = Flask(__name__)

# Initialize AI Intelligence Manager
ai = get_ai_intelligence()

@app.route('/api/ai/conversation', methods=['POST'])
def store_conversation():
    """Store a conversation exchange."""
    data = request.json
    
    conv_id = ai.store_conversation(
        conversation_id=data.get('conversation_id', 'unknown'),
        user_message=data.get('user_message', ''),
        ai_response=data.get('ai_response', ''),
        metadata=data.get('metadata', {})
    )
    
    return jsonify({
        'status': 'success',
        'conversation_id': conv_id
    })

@app.route('/api/ai/context', methods=['POST'])
def store_context():
    """Store context information."""
    data = request.json
    
    success = ai.store_context(
        context_key=data.get('key'),
        context_data=data.get('data', {}),
        tags=data.get('tags', [])
    )
    
    return jsonify({'status': 'success' if success else 'error'})

@app.route('/api/ai/context/<key>', methods=['GET'])
def get_context(key):
    """Retrieve context by key."""
    context = ai.get_context(key)
    
    if context:
        return jsonify({
            'status': 'success',
            'context': context
        })
    else:
        return jsonify({
            'status': 'not_found'
        }), 404

@app.route('/api/ai/learning', methods=['POST'])
def store_learning():
    """Store a learning item."""
    data = request.json
    
    success = ai.store_learning(
        topic=data.get('topic', ''),
        learning_content=data.get('content', ''),
        importance=data.get('importance', 1),
        tags=data.get('tags', [])
    )
    
    return jsonify({'status': 'success' if success else 'error'})

@app.route('/api/ai/learnings/search', methods=['GET'])
def search_learnings():
    """Search learnings."""
    query = request.args.get('q')
    tags = request.args.getlist('tag')
    limit = int(request.args.get('limit', 10))
    
    learnings = ai.search_learnings(
        query=query,
        tags=tags if tags else None,
        limit=limit
    )
    
    return jsonify({
        'status': 'success',
        'count': len(learnings),
        'learnings': learnings
    })

@app.route('/api/ai/memory', methods=['POST'])
def store_memory():
    """Store a memory item."""
    data = request.json
    
    success = ai.store_memory(
        memory_type=data.get('type', 'general'),
        memory_content=data.get('content', {}),
        retention_priority=data.get('priority', 1)
    )
    
    return jsonify({'status': 'success' if success else 'error'})

@app.route('/api/ai/memories', methods=['GET'])
def get_memories():
    """Get recent memories."""
    memory_type = request.args.get('type')
    limit = int(request.args.get('limit', 20))
    
    memories = ai.get_recent_memories(
        memory_type=memory_type,
        limit=limit
    )
    
    return jsonify({
        'status': 'success',
        'count': len(memories),
        'memories': memories
    })

@app.route('/api/ai/task', methods=['POST'])
def store_task():
    """Store a task."""
    data = request.json
    
    success = ai.store_task(
        task_id=data.get('task_id'),
        task_description=data.get('description', ''),
        status=data.get('status', 'pending'),
        metadata=data.get('metadata', {})
    )
    
    return jsonify({'status': 'success' if success else 'error'})

@app.route('/api/ai/task/<task_id>/status', methods=['PUT'])
def update_task(task_id):
    """Update task status."""
    data = request.json
    
    success = ai.update_task_status(
        task_id=task_id,
        status=data.get('status', 'pending')
    )
    
    return jsonify({'status': 'success' if success else 'error'})

@app.route('/api/ai/tasks', methods=['GET'])
def get_tasks():
    """Get tasks."""
    status = request.args.get('status')
    
    tasks = ai.get_tasks(status=status)
    
    return jsonify({
        'status': 'success',
        'count': len(tasks),
        'tasks': tasks
    })

@app.route('/api/ai/decision', methods=['POST'])
def store_decision():
    """Store an AI decision."""
    data = request.json
    
    success = ai.store_decision(
        decision_context=data.get('context', ''),
        decision_made=data.get('decision', ''),
        reasoning=data.get('reasoning', ''),
        outcome=data.get('outcome')
    )
    
    return jsonify({'status': 'success' if success else 'error'})

@app.route('/api/ai/stats', methods=['GET'])
def get_stats():
    """Get AI Intelligence statistics."""
    stats = ai.get_stats()
    
    return jsonify({
        'status': 'success',
        'stats': stats
    })

@app.route('/api/ai/export', methods=['POST'])
def export_data():
    """Export AI Intelligence data."""
    output_path = request.json.get('output_path', 'data/ai/export.json')
    
    success = ai.export_data(output_path)
    
    return jsonify({
        'status': 'success' if success else 'error',
        'output_path': output_path if success else None
    })

@app.route('/')
def index():
    """API documentation."""
    return jsonify({
        'name': 'AI Intelligence API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/ai/conversation': 'Store a conversation',
            'POST /api/ai/context': 'Store context',
            'GET /api/ai/context/<key>': 'Get context by key',
            'POST /api/ai/learning': 'Store a learning',
            'GET /api/ai/learnings/search': 'Search learnings',
            'POST /api/ai/memory': 'Store a memory',
            'GET /api/ai/memories': 'Get recent memories',
            'POST /api/ai/task': 'Store a task',
            'PUT /api/ai/task/<id>/status': 'Update task status',
            'GET /api/ai/tasks': 'Get tasks',
            'POST /api/ai/decision': 'Store a decision',
            'GET /api/ai/stats': 'Get statistics',
            'POST /api/ai/export': 'Export data'
        }
    })

if __name__ == '__main__':
    print("Starting AI Intelligence API...")
    print(f"Backend: {ai.get_stats()['backend']}")
    print(f"Database: {ai.get_stats()['database']}")
    print("\nAPI Documentation: http://localhost:5000/")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        ai.close()
