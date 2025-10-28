#!/usr/bin/env python3
"""
WebSocket support for real-time updates and notifications.
Provides real-time communication between server and clients.
"""

import json
import time
import uuid
import threading
from typing import Dict, List, Set, Any, Optional, Callable
from datetime import datetime
import logging
from functools import wraps
from collections import defaultdict

try:
    from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    # Mock classes for when SocketIO is not available
    class SocketIO:
        def __init__(self, *args, **kwargs):
            pass
        def on(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    
    def emit(*args, **kwargs):
        pass
    
    def join_room(*args, **kwargs):
        pass
    
    def leave_room(*args, **kwargs):
        pass
    
    def disconnect(*args, **kwargs):
        pass

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manage WebSocket connections and real-time updates."""
    
    def __init__(self, app=None):
        self.app = app
        self.socketio = None
        self.connected_clients = {}
        self.client_subscriptions = defaultdict(set)
        self.subscription_clients = defaultdict(set)
        self.message_handlers = {}
        self.client_lock = threading.Lock()
        
        if SOCKETIO_AVAILABLE and app:
            self.socketio = SocketIO(
                app,
                cors_allowed_origins="*",
                ping_timeout=60,
                ping_interval=25,
                logger=logger,
                engineio_logger=logger
            )
            self._setup_event_handlers()
        else:
            logger.warning("SocketIO not available or app not provided - WebSocket features disabled")
    
    def _setup_event_handlers(self):
        """Setup WebSocket event handlers."""
        if not self.socketio:
            return
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection."""
            client_id = self._generate_client_id()
            
            with self.client_lock:
                self.connected_clients[client_id] = {
                    'session_id': client_id,
                    'connected_at': datetime.now().isoformat(),
                    'subscriptions': set(),
                    'user_agent': None,
                    'ip_address': None,
                }
            
            # Send welcome message with client ID
            emit('connected', {
                'client_id': client_id,
                'server_time': datetime.now().isoformat(),
                'features': self._get_available_features()
            })
            
            logger.info(f"WebSocket client connected: {client_id}")
            
            # Notify other components
            self._emit_system_event('client_connected', {
                'client_id': client_id,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            client_id = self._get_client_id_from_session()
            
            if client_id:
                with self.client_lock:
                    if client_id in self.connected_clients:
                        # Remove from all subscriptions
                        subscriptions = self.connected_clients[client_id]['subscriptions'].copy()
                        for subscription in subscriptions:
                            self.unsubscribe_client(client_id, subscription)
                        
                        del self.connected_clients[client_id]
                
                logger.info(f"WebSocket client disconnected: {client_id}")
                
                # Notify other components
                self._emit_system_event('client_disconnected', {
                    'client_id': client_id,
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Handle subscription requests."""
            client_id = self._get_client_id_from_session()
            if not client_id:
                emit('error', {'message': 'Invalid session'})
                return
            
            topics = data.get('topics', [])
            if not isinstance(topics, list):
                topics = [topics]
            
            for topic in topics:
                if self._is_valid_topic(topic):
                    self.subscribe_client(client_id, topic)
                    emit('subscribed', {'topic': topic})
                else:
                    emit('error', {'message': f'Invalid topic: {topic}'})
        
        @self.socketio.on('unsubscribe')
        def handle_unsubscribe(data):
            """Handle unsubscription requests."""
            client_id = self._get_client_id_from_session()
            if not client_id:
                emit('error', {'message': 'Invalid session'})
                return
            
            topics = data.get('topics', [])
            if not isinstance(topics, list):
                topics = [topics]
            
            for topic in topics:
                self.unsubscribe_client(client_id, topic)
                emit('unsubscribed', {'topic': topic})
        
        @self.socketio.on('ping')
        def handle_ping(data):
            """Handle ping requests."""
            emit('pong', {
                'timestamp': datetime.now().isoformat(),
                'echo': data.get('echo', {})
            })
        
        # Custom message handlers
        @self.socketio.on('custom_message')
        def handle_custom_message(data):
            """Handle custom messages."""
            message_type = data.get('type')
            if message_type in self.message_handlers:
                try:
                    response = self.message_handlers[message_type](data)
                    if response:
                        emit('custom_response', response)
                except Exception as e:
                    logger.error(f"Custom message handler failed: {e}")
                    emit('error', {'message': 'Message processing failed'})
    
    def _generate_client_id(self) -> str:
        """Generate unique client ID."""
        return str(uuid.uuid4())
    
    def _get_client_id_from_session(self) -> Optional[str]:
        """Get client ID from current session."""
        # This would need to be implemented based on how you store session info
        # For now, we'll use a simple approach
        import flask
        if hasattr(flask, 'request'):
            return getattr(flask.request, 'sid', None)
        return None
    
    def _is_valid_topic(self, topic: str) -> bool:
        """Validate subscription topic."""
        valid_topics = [
            'system_status',
            'file_operations',
            'command_output',
            'tunnel_status',
            'performance_metrics',
            'security_alerts',
            'backup_progress',
            'notifications'
        ]
        return topic in valid_topics
    
    def _get_available_features(self) -> List[str]:
        """Get list of available WebSocket features."""
        return [
            'real_time_notifications',
            'file_upload_progress',
            'command_streaming',
            'system_monitoring',
            'tunnel_status_updates'
        ]
    
    def subscribe_client(self, client_id: str, topic: str):
        """Subscribe client to a topic."""
        with self.client_lock:
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['subscriptions'].add(topic)
                self.client_subscriptions[client_id].add(topic)
                self.subscription_clients[topic].add(client_id)
                
                # Join SocketIO room for the topic
                if self.socketio:
                    join_room(topic)
                
                logger.debug(f"Client {client_id} subscribed to {topic}")
    
    def unsubscribe_client(self, client_id: str, topic: str):
        """Unsubscribe client from a topic."""
        with self.client_lock:
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['subscriptions'].discard(topic)
                self.client_subscriptions[client_id].discard(topic)
                self.subscription_clients[topic].discard(client_id)
                
                # Leave SocketIO room for the topic
                if self.socketio:
                    leave_room(topic)
                
                logger.debug(f"Client {client_id} unsubscribed from {topic}")
    
    def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """Broadcast message to all clients subscribed to a topic."""
        if not self.socketio:
            return
        
        enhanced_message = {
            **message,
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'message_id': str(uuid.uuid4())
        }
        
        self.socketio.emit('topic_message', enhanced_message, room=topic)
        logger.debug(f"Broadcasted message to topic {topic}: {len(self.subscription_clients[topic])} clients")
    
    def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to a specific client."""
        if not self.socketio or client_id not in self.connected_clients:
            return
        
        enhanced_message = {
            **message,
            'timestamp': datetime.now().isoformat(),
            'message_id': str(uuid.uuid4())
        }
        
        self.socketio.emit('direct_message', enhanced_message, room=client_id)
        logger.debug(f"Sent direct message to client {client_id}")
    
    def broadcast_system_notification(self, notification_type: str, title: str, 
                                    message: str, severity: str = 'info', 
                                    data: Optional[Dict] = None):
        """Broadcast system notification to all connected clients."""
        notification = {
            'type': notification_type,
            'title': title,
            'message': message,
            'severity': severity,
            'data': data or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.broadcast_to_topic('notifications', notification)
    
    def _emit_system_event(self, event_type: str, data: Dict[str, Any]):
        """Emit system event to interested components."""
        system_message = {
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.broadcast_to_topic('system_status', system_message)
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register custom message handler."""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered message handler for type: {message_type}")
    
    def get_connected_clients(self) -> Dict[str, Any]:
        """Get information about connected clients."""
        with self.client_lock:
            return {
                'count': len(self.connected_clients),
                'clients': {
                    client_id: {
                        'connected_at': info['connected_at'],
                        'subscriptions': list(info['subscriptions'])
                    }
                    for client_id, info in self.connected_clients.items()
                }
            }
    
    def get_topic_statistics(self) -> Dict[str, Any]:
        """Get statistics about topic subscriptions."""
        with self.client_lock:
            return {
                topic: len(clients)
                for topic, clients in self.subscription_clients.items()
            }

# Real-time update decorators and utilities

def websocket_emit(topic: str, message_key: str = None):
    """Decorator to emit WebSocket messages from function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if websocket_manager and websocket_manager.socketio:
                # Determine message content
                if message_key and isinstance(result, dict):
                    message_content = result.get(message_key, result)
                else:
                    message_content = result
                
                # Emit to topic
                websocket_manager.broadcast_to_topic(topic, {
                    'function': func.__name__,
                    'result': message_content
                })
            
            return result
        return wrapper
    return decorator

def notify_clients(notification_type: str, title: str, severity: str = 'info'):
    """Decorator to send notifications based on function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Send success notification
                if websocket_manager:
                    websocket_manager.broadcast_system_notification(
                        notification_type,
                        title,
                        f"Operation completed successfully",
                        'success',
                        {'function': func.__name__, 'result': result}
                    )
                
                return result
                
            except Exception as e:
                # Send error notification
                if websocket_manager:
                    websocket_manager.broadcast_system_notification(
                        notification_type,
                        f"{title} Failed",
                        f"Operation failed: {str(e)}",
                        'error',
                        {'function': func.__name__, 'error': str(e)}
                    )
                
                raise
        return wrapper
    return decorator

class ProgressTracker:
    """Track and broadcast progress updates."""
    
    def __init__(self, operation_id: str, total_steps: int, title: str = "Operation"):
        self.operation_id = operation_id
        self.total_steps = total_steps
        self.current_step = 0
        self.title = title
        self.start_time = time.time()
        self.completed = False
    
    def update(self, step: int, message: str = ""):
        """Update progress."""
        self.current_step = step
        
        progress_data = {
            'operation_id': self.operation_id,
            'title': self.title,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'percentage': round((self.current_step / self.total_steps) * 100, 1),
            'message': message,
            'elapsed_time': round(time.time() - self.start_time, 1)
        }
        
        if websocket_manager:
            websocket_manager.broadcast_to_topic('progress_updates', progress_data)
    
    def complete(self, message: str = "Operation completed"):
        """Mark operation as completed."""
        self.current_step = self.total_steps
        self.completed = True
        
        completion_data = {
            'operation_id': self.operation_id,
            'title': self.title,
            'completed': True,
            'message': message,
            'total_time': round(time.time() - self.start_time, 1)
        }
        
        if websocket_manager:
            websocket_manager.broadcast_to_topic('progress_updates', completion_data)
    
    def error(self, error_message: str):
        """Mark operation as failed."""
        self.completed = True
        
        error_data = {
            'operation_id': self.operation_id,
            'title': self.title,
            'error': True,
            'message': error_message,
            'elapsed_time': round(time.time() - self.start_time, 1)
        }
        
        if websocket_manager:
            websocket_manager.broadcast_to_topic('progress_updates', error_data)

# Global WebSocket manager instance
websocket_manager: Optional[WebSocketManager] = None

def initialize_websocket_manager(app=None) -> Optional[WebSocketManager]:
    """Initialize the WebSocket manager."""
    global websocket_manager
    
    if SOCKETIO_AVAILABLE and app:
        websocket_manager = WebSocketManager(app)
        logger.info("WebSocket manager initialized")
    else:
        logger.warning("WebSocket manager not available - real-time features disabled")
        websocket_manager = None
    
    return websocket_manager

def get_websocket_manager() -> Optional[WebSocketManager]:
    """Get the global WebSocket manager."""
    return websocket_manager

# Utility functions for common real-time updates

def emit_file_operation(operation: str, filename: str, success: bool, details: Dict = None):
    """Emit file operation update."""
    if websocket_manager:
        websocket_manager.broadcast_to_topic('file_operations', {
            'operation': operation,
            'filename': filename,
            'success': success,
            'details': details or {}
        })

def emit_command_output(command: str, output: str, exit_code: int = None):
    """Emit command execution output."""
    if websocket_manager:
        websocket_manager.broadcast_to_topic('command_output', {
            'command': command,
            'output': output,
            'exit_code': exit_code
        })

def emit_tunnel_status(service: str, status: str, public_url: str = None):
    """Emit tunnel status update."""
    if websocket_manager:
        websocket_manager.broadcast_to_topic('tunnel_status', {
            'service': service,
            'status': status,
            'public_url': public_url
        })

def emit_performance_metrics(metrics: Dict[str, Any]):
    """Emit performance metrics update."""
    if websocket_manager:
        websocket_manager.broadcast_to_topic('performance_metrics', metrics)

def emit_security_alert(alert_type: str, message: str, severity: str = 'warning', details: Dict = None):
    """Emit security alert."""
    if websocket_manager:
        websocket_manager.broadcast_to_topic('security_alerts', {
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'details': details or {}
        })