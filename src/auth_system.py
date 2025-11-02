#!/usr/bin/env python3
"""
Authentication and Authorization System
Provides JWT-based authentication, user management, and role-based access control.
"""

import jwt
import bcrypt
import json
import os
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from typing import Optional, Dict, List, Tuple
import threading

class User:
    """Represents a user in the system"""
    
    def __init__(self, user_id: str, username: str, email: str, 
                 password_hash: str, role: str = 'user', 
                 created_at: Optional[str] = None, 
                 last_login: Optional[str] = None,
                 is_active: bool = True):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role  # 'admin', 'user', 'guest'
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.last_login = last_login
        self.is_active = is_active
    
    def to_dict(self, include_sensitive: bool = False) -> Dict:
        """Convert user to dictionary"""
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'is_active': self.is_active
        }
        if include_sensitive:
            data['password_hash'] = self.password_hash
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user from dictionary"""
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            role=data.get('role', 'user'),
            created_at=data.get('created_at'),
            last_login=data.get('last_login'),
            is_active=data.get('is_active', True)
        )


class AuthenticationManager:
    """Manages user authentication and JWT tokens"""
    
    def __init__(self, secret_key: str, users_file: str = 'data/users.json'):
        self.secret_key = secret_key
        self.users_file = users_file
        self.users: Dict[str, User] = {}
        self.lock = threading.Lock()
        self.token_blacklist: set = set()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        
        # Load existing users
        self._load_users()
        
        # Create default admin user if none exists
        if not self.users:
            self._create_default_admin()
    
    def _load_users(self):
        """Load users from JSON file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    self.users = {
                        uid: User.from_dict(udata) 
                        for uid, udata in data.items()
                    }
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}
    
    def _save_users(self):
        """Save users to JSON file"""
        with self.lock:
            try:
                data = {
                    uid: user.to_dict(include_sensitive=True)
                    for uid, user in self.users.items()
                }
                with open(self.users_file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error saving users: {e}")
    
    def _create_default_admin(self):
        """Create default admin user"""
        import secrets
        admin_id = str(uuid.uuid4())
        # Generate a secure random password instead of using 'admin123'
        # The password should be changed on first login
        secure_password = secrets.token_urlsafe(16)
        password_hash = bcrypt.hashpw(secure_password.encode('utf-8'), bcrypt.gensalt())
        
        admin = User(
            user_id=admin_id,
            username='admin',
            email='admin@localhost',
            password_hash=password_hash.decode('utf-8'),
            role='admin'
        )
        
        self.users[admin_id] = admin
        self._save_users()
        
        # Log the secure password to a secure location
        # WARNING: This should be stored securely and the password should be changed on first login
        # Use CREDENTIALS_DIR env var if set, otherwise use config directory
        creds_dir = os.getenv('CREDENTIALS_DIR')
        if creds_dir and os.path.exists(creds_dir):
            credentials_file = os.path.join(creds_dir, 'admin_credentials.txt')
        else:
            credentials_file = os.path.join(os.path.dirname(self.users_file), 'admin_credentials.txt')
        
        # Ensure the directory exists with secure permissions
        os.makedirs(os.path.dirname(credentials_file), mode=0o700, exist_ok=True)
        
        # Write credentials with secure file permissions
        with os.fdopen(os.open(credentials_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as f:
            f.write(f"Default Admin Credentials\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"Username: admin\n")
            f.write(f"Password: {secure_password}\n")
            f.write(f"Created: {datetime.now(datetime.now().astimezone().tzinfo).isoformat()}\n\n")
            f.write(f"⚠️  IMPORTANT: Change this password immediately after first login!\n")
        
        print(f"Default admin created - username: admin")
        print(f"⚠️  Password saved to: {credentials_file}")
        print(f"⚠️  CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN!")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def register_user(self, username: str, email: str, password: str, 
                     role: str = 'user') -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user
        Returns: (success, message, user)
        """
        # Validate input 
        # Allow slightly shorter passwords to support requested 'admin' (length 5)
        # Original minimum was 6; lowered to 5 for operational convenience.
        if not password or len(password) < 5:
            return False, "Password must be at least 5 characters", None
        
        # Check if username or email already exists
        with self.lock:
            for user in self.users.values():
                if user.username == username:
                    return False, "Username already exists", None
                if user.email == email:
                    return False, "Email already exists", None
            
            # Create new user
            user_id = str(uuid.uuid4())
            password_hash = self.hash_password(password)
            
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                role=role
            )
            
            self.users[user_id] = user
            self._save_users()
            
            return True, "User registered successfully", user
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate a user with username and password
        Returns: (success, message, user)
        """
        # Find user by username
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            return False, "Invalid username or password", None
        
        if not user.is_active:
            return False, "Account is disabled", None
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            return False, "Invalid username or password", None
        
        # Update last login
        user.last_login = datetime.utcnow().isoformat()
        self._save_users()
        
        return True, "Authentication successful", user
    
    def generate_token(self, user: User, expires_in_hours: int = 24) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_token(self, token: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Verify JWT token
        Returns: (valid, message, payload)
        """
        if token in self.token_blacklist:
            return False, "Token has been revoked", None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check if user still exists and is active
            user_id = payload.get('user_id')
            if user_id not in self.users:
                return False, "User not found", None
            
            user = self.users[user_id]
            if not user.is_active:
                return False, "User account is disabled", None
            
            return True, "Token is valid", payload
            
        except jwt.ExpiredSignatureError:
            return False, "Token has expired", None
        except jwt.InvalidTokenError as e:
            return False, f"Invalid token: {str(e)}", None
    
    def revoke_token(self, token: str):
        """Add token to blacklist"""
        self.token_blacklist.add(token)
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def update_user(self, user_id: str, **kwargs) -> Tuple[bool, str]:
        """Update user attributes"""
        user = self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        with self.lock:
            # Update allowed fields
            if 'email' in kwargs:
                user.email = kwargs['email']
            if 'role' in kwargs:
                user.role = kwargs['role']
            if 'is_active' in kwargs:
                user.is_active = kwargs['is_active']
            if 'password' in kwargs:
                user.password_hash = self.hash_password(kwargs['password'])
            
            self._save_users()
            return True, "User updated successfully"
    
    def delete_user(self, user_id: str) -> Tuple[bool, str]:
        """Delete user"""
        if user_id not in self.users:
            return False, "User not found"
        
        with self.lock:
            del self.users[user_id]
            self._save_users()
            return True, "User deleted successfully"
    
    def list_users(self, include_inactive: bool = False) -> List[User]:
        """List all users"""
        if include_inactive:
            return list(self.users.values())
        return [u for u in self.users.values() if u.is_active]


# Flask decorators for route protection

def create_auth_decorators(auth_manager: AuthenticationManager):
    """Create authentication decorators bound to an AuthenticationManager instance"""
    
    def login_required(f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]
            
            if not token:
                return jsonify({'error': 'Authentication required', 'message': 'No token provided'}), 401
            
            # Verify token
            valid, message, payload = auth_manager.verify_token(token)
            if not valid:
                return jsonify({'error': 'Authentication failed', 'message': message}), 401
            
            # Store user info in Flask's g object
            g.current_user = auth_manager.get_user(payload['user_id'])
            g.user_id = payload['user_id']
            g.username = payload['username']
            g.user_role = payload['role']
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def role_required(*roles):
        """Decorator to require specific role(s)"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                token = None
                
                # Get token from Authorization header
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                
                if not token:
                    return jsonify({'error': 'Authentication required', 'message': 'No token provided'}), 401
                
                # Verify token
                valid, message, payload = auth_manager.verify_token(token)
                if not valid:
                    return jsonify({'error': 'Authentication failed', 'message': message}), 401
                
                # Check role
                user_role = payload.get('role')
                if user_role not in roles:
                    return jsonify({
                        'error': 'Access denied',
                        'message': f'Required role: {", ".join(roles)}'
                    }), 403
                
                # Store user info in Flask's g object
                g.current_user = auth_manager.get_user(payload['user_id'])
                g.user_id = payload['user_id']
                g.username = payload['username']
                g.user_role = user_role
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator
    
    def admin_required(f):
        """Decorator to require admin role"""
        return role_required('admin')(f)
    
    return login_required, role_required, admin_required


# Example usage:
if __name__ == "__main__":
    # Initialize auth manager
    # NOTE: Use a secure secret key from environment variables in production
    # Example: os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
    auth = AuthenticationManager(secret_key="your-secret-key-here-CHANGE-IN-PRODUCTION")
    
    # Register a user
    success, msg, user = auth.register_user("testuser", "test@example.com", "password123")
    print(f"Registration: {msg}")
    
    if success:
        # Authenticate
        success, msg, user = auth.authenticate_user("testuser", "password123")
        print(f"Authentication: {msg}")
        
        if success:
            # Generate token
            token = auth.generate_token(user)
            print(f"Token: {token}")
            
            # Verify token
            valid, msg, payload = auth.verify_token(token)
            print(f"Token verification: {msg}")
            if valid:
                print(f"Payload: {payload}")
