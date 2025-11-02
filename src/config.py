#!/usr/bin/env python3
"""
Configuration management for the web server.
Handles environment-specific settings, feature toggles, and user preferences.
"""

import os
import json
import secrets
from typing import Any, Dict, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, config_dir: str = 'data/config'):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'server_config.json')
        self.user_prefs_file = os.path.join(config_dir, 'user_preferences.json')
        self.feature_flags_file = os.path.join(config_dir, 'feature_flags.json')
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Load configurations
        self.config = self._load_server_config()
        self.user_preferences = self._load_user_preferences()
        self.feature_flags = self._load_feature_flags()
    
    def _load_server_config(self) -> Dict[str, Any]:
        """Load server configuration."""
        default_config = {
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'debug': True,
                'secret_key': secrets.token_hex(32),
                'max_content_length': 100 * 1024 * 1024,  # 100MB
                'session_timeout': 7200,  # 2 hours
                'cleanup_interval': 3600,  # 1 hour
            },
            'security': {
                'rate_limiting_enabled': True,
                'csrf_protection_enabled': True,
                'authentication_required': False,
                'secure_headers_enabled': True,
                'input_validation_strict': True,
                'file_upload_scanning': True,
                'command_whitelist_enabled': False,
                'session_ip_validation': False,
            },
            'storage': {
                'max_file_size': 100 * 1024 * 1024,  # 100MB per file
                'max_total_storage': 5 * 1024 * 1024 * 1024,  # 5GB total
                'allowed_file_types': [
                    'text/*', 'image/*', 'application/pdf',
                    'application/json', 'application/xml',
                    'application/zip', 'application/tar',
                ],
                'cleanup_old_files_days': 30,
                'enable_file_versioning': False,
                'enable_file_encryption': False,
            },
            'tunnels': {
                'ngrok': {
                    'enabled': True,
                    'config_path': 'ngrok.yml',
                    'default_subdomain': None,
                    'auth_token_required': True,
                },
                'localtunnel': {
                    'enabled': True,
                    'subdomain_prefix': 'webserver',
                    'custom_host': None,
                },
                'cloudflared': {
                    'enabled': True,
                    'config_path': None,
                    'tunnel_name': None,
                },
                'auto_start': False,
                'preferred_service': 'localtunnel',
            },
            'logging': {
                'level': 'INFO',
                'max_file_size': 10 * 1024 * 1024,  # 10MB
                'backup_count': 5,
                'log_to_file': True,
                'log_to_console': True,
                'security_logging': True,
                'audit_logging': True,
            },
            'performance': {
                'enable_caching': True,
                'cache_timeout': 300,  # 5 minutes
                'enable_compression': True,
                'enable_async': False,
                'max_workers': 4,
            },
            'maintenance': {
                'backup_enabled': True,
                'backup_interval_hours': 24,
                'backup_retention_days': 7,
                'auto_cleanup_enabled': True,
                'metrics_collection': True,
            },
            'ai_intelligence': {
                'enabled': True,
                'mongodb_uri': None,  # Set to MongoDB URI or leave None for TinyDB fallback
                'database_name': 'ai_intelligence',
                'store_conversations': True,
                'store_context': True,
                'store_learnings': True,
                'auto_learning_enabled': True,
                'memory_retention_days': 90,
                'max_memories': 10000,
            },
            'created_at': datetime.now().isoformat(),
            'version': '2.0.0',
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults (in case new settings were added)
                self._deep_merge(default_config, loaded_config)
                return loaded_config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return default_config
        else:
            # Save default config
            self._save_server_config(default_config)
            return default_config
    
    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences."""
        default_prefs = {
            'ui': {
                'theme': 'dark',
                'language': 'en',
                'timezone': 'UTC',
                'items_per_page': 20,
                'auto_refresh': True,
                'refresh_interval': 30,
                'show_hidden_files': False,
                'enable_animations': True,
                'keyboard_shortcuts': True,
            },
            'terminal': {
                'font_family': 'monospace',
                'font_size': 14,
                'line_height': 1.2,
                'cursor_style': 'block',
                'enable_sound': False,
                'history_size': 1000,
                'auto_complete': True,
            },
            'editor': {
                'theme': 'dark',
                'font_size': 14,
                'tab_size': 4,
                'word_wrap': True,
                'line_numbers': True,
                'syntax_highlighting': True,
                'auto_save': True,
            },
            'notifications': {
                'enabled': True,
                'sound_enabled': False,
                'desktop_notifications': True,
                'email_notifications': False,
                'webhook_notifications': False,
            },
            'accessibility': {
                'high_contrast': False,
                'large_text': False,
                'screen_reader_support': False,
                'reduced_motion': False,
            },
        }
        
        if os.path.exists(self.user_prefs_file):
            try:
                with open(self.user_prefs_file, 'r') as f:
                    loaded_prefs = json.load(f)
                self._deep_merge(default_prefs, loaded_prefs)
                return loaded_prefs
            except Exception as e:
                logger.error(f"Error loading user preferences: {e}")
                return default_prefs
        else:
            self._save_user_preferences(default_prefs)
            return default_prefs
    
    def _load_feature_flags(self) -> Dict[str, Any]:
        """Load feature flags for gradual rollouts."""
        default_flags = {
            'experimental_ui': {
                'enabled': False,
                'description': 'New experimental user interface',
                'rollout_percentage': 0,
            },
            'advanced_file_preview': {
                'enabled': True,
                'description': 'Preview files in the browser',
                'rollout_percentage': 100,
            },
            'real_time_updates': {
                'enabled': False,
                'description': 'WebSocket-based real-time updates',
                'rollout_percentage': 0,
            },
            'api_v2': {
                'enabled': False,
                'description': 'New API version with improved features',
                'rollout_percentage': 0,
            },
            'advanced_analytics': {
                'enabled': False,
                'description': 'Detailed usage analytics and metrics',
                'rollout_percentage': 0,
            },
            'plugin_system': {
                'enabled': False,
                'description': 'Plugin architecture for extensibility',
                'rollout_percentage': 0,
            },
            'multi_user_support': {
                'enabled': False,
                'description': 'Multiple user accounts and permissions',
                'rollout_percentage': 0,
            },
            'backup_restore': {
                'enabled': True,
                'description': 'Automated backup and restore functionality',
                'rollout_percentage': 100,
            },
        }
        
        if os.path.exists(self.feature_flags_file):
            try:
                with open(self.feature_flags_file, 'r') as f:
                    loaded_flags = json.load(f)
                self._deep_merge(default_flags, loaded_flags)
                return loaded_flags
            except Exception as e:
                logger.error(f"Error loading feature flags: {e}")
                return default_flags
        else:
            self._save_feature_flags(default_flags)
            return default_flags
    
    def _deep_merge(self, target: Dict, source: Dict) -> Dict:
        """Deep merge two dictionaries."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
        return target
    
    def _save_server_config(self, config: Dict[str, Any]):
        """Save server configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving server config: {e}")
    
    def _save_user_preferences(self, prefs: Dict[str, Any]):
        """Save user preferences."""
        try:
            with open(self.user_prefs_file, 'w') as f:
                json.dump(prefs, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
    
    def _save_feature_flags(self, flags: Dict[str, Any]):
        """Save feature flags."""
        try:
            with open(self.feature_flags_file, 'w') as f:
                json.dump(flags, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving feature flags: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        target = self.config
        
        try:
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            
            target[keys[-1]] = value
            
            if save:
                self._save_server_config(self.config)
            
            return True
        except Exception as e:
            logger.error(f"Error setting config {key}: {e}")
            return False
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference value."""
        keys = key.split('.')
        value = self.user_preferences
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_user_preference(self, key: str, value: Any, save: bool = True) -> bool:
        """Set user preference value."""
        keys = key.split('.')
        target = self.user_preferences
        
        try:
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            
            target[keys[-1]] = value
            
            if save:
                self._save_user_preferences(self.user_preferences)
            
            return True
        except Exception as e:
            logger.error(f"Error setting user preference {key}: {e}")
            return False
    
    def is_feature_enabled(self, feature_name: str, user_id: Optional[str] = None) -> bool:
        """Check if a feature is enabled for a user."""
        if feature_name not in self.feature_flags:
            return False
        
        flag = self.feature_flags[feature_name]
        
        if not flag.get('enabled', False):
            return False
        
        rollout_percentage = flag.get('rollout_percentage', 100)
        
        if rollout_percentage >= 100:
            return True
        
        if rollout_percentage <= 0:
            return False
        
        # Use user_id for consistent rollout (same user always gets same result)
        if user_id:
            import hashlib
            hash_value = int(hashlib.md5(f"{feature_name}:{user_id}".encode()).hexdigest()[:8], 16)
            return (hash_value % 100) < rollout_percentage
        
        # Random rollout for anonymous users
        import random
        return random.randint(0, 99) < rollout_percentage
    
    def set_feature_flag(self, feature_name: str, enabled: bool, rollout_percentage: int = 100, save: bool = True) -> bool:
        """Set feature flag state."""
        try:
            if feature_name not in self.feature_flags:
                self.feature_flags[feature_name] = {
                    'description': f'Feature flag for {feature_name}',
                }
            
            self.feature_flags[feature_name]['enabled'] = enabled
            self.feature_flags[feature_name]['rollout_percentage'] = max(0, min(100, rollout_percentage))
            
            if save:
                self._save_feature_flags(self.feature_flags)
            
            return True
        except Exception as e:
            logger.error(f"Error setting feature flag {feature_name}: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration data."""
        return {
            'server_config': self.config,
            'user_preferences': self.user_preferences,
            'feature_flags': self.feature_flags,
        }
    
    def export_config(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Export configuration for backup/sharing."""
        export_data = {
            'version': self.config.get('version', '2.0.0'),
            'exported_at': datetime.now().isoformat(),
            'config': self.config.copy(),
            'user_preferences': self.user_preferences.copy(),
            'feature_flags': self.feature_flags.copy(),
        }
        
        if not include_sensitive:
            # Remove sensitive data
            sensitive_keys = ['secret_key', 'auth_token', 'password']
            self._remove_sensitive_data(export_data['config'], sensitive_keys)
        
        return export_data
    
    def import_config(self, import_data: Dict[str, Any], overwrite: bool = False) -> bool:
        """Import configuration from backup/sharing."""
        try:
            if 'config' in import_data:
                if overwrite:
                    self.config = import_data['config']
                else:
                    self._deep_merge(self.config, import_data['config'])
                self._save_server_config(self.config)
            
            if 'user_preferences' in import_data:
                if overwrite:
                    self.user_preferences = import_data['user_preferences']
                else:
                    self._deep_merge(self.user_preferences, import_data['user_preferences'])
                self._save_user_preferences(self.user_preferences)
            
            if 'feature_flags' in import_data:
                if overwrite:
                    self.feature_flags = import_data['feature_flags']
                else:
                    self._deep_merge(self.feature_flags, import_data['feature_flags'])
                self._save_feature_flags(self.feature_flags)
            
            return True
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            return False
    
    def _remove_sensitive_data(self, data: Dict, sensitive_keys: list):
        """Remove sensitive data from configuration."""
        for key, value in list(data.items()):
            if isinstance(value, dict):
                self._remove_sensitive_data(value, sensitive_keys)
            elif any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                data[key] = '[REDACTED]'
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return any issues."""
        issues = []
        warnings = []
        
        # Validate server settings
        if self.get('server.port', 8000) < 1024 and os.geteuid() != 0:
            warnings.append("Port < 1024 requires root privileges")
        
        if self.get('server.debug', False):
            warnings.append("Debug mode enabled - not recommended for production")
        
        if self.get('security.authentication_required', False) is False:
            warnings.append("Authentication is disabled - server is publicly accessible")
        
        # Validate storage settings
        max_storage = self.get('storage.max_total_storage', 0)
        if max_storage > 50 * 1024 * 1024 * 1024:  # 50GB
            warnings.append("Storage limit is very high - ensure sufficient disk space")
        
        # Validate logging settings
        if not self.get('logging.log_to_file', True) and not self.get('logging.log_to_console', True):
            issues.append("All logging is disabled - debugging will be difficult")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
        }

# Global configuration instance
config = ConfigManager()