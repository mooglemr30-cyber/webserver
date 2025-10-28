#!/usr/bin/env python3
"""
Backup and restore system for the web server.
Provides automated backups, restore functionality, and data migration.
"""

import os
import json
import shutil
import tarfile
import gzip
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import threading
import schedule

logger = logging.getLogger(__name__)

class BackupManager:
    """Comprehensive backup and restore management."""
    
    def __init__(self, backup_dir: str = 'data/backups', config_manager=None):
        self.backup_dir = backup_dir
        self.config = config_manager
        self.backup_lock = threading.Lock()
        
        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)
        
        # Initialize backup scheduler if enabled
        if self.config and self.config.get('maintenance.backup_enabled', True):
            self._setup_backup_schedule()
    
    def _setup_backup_schedule(self):
        """Setup automatic backup scheduling."""
        interval_hours = self.config.get('maintenance.backup_interval_hours', 24)
        
        # Schedule automatic backups
        schedule.every(interval_hours).hours.do(self._scheduled_backup)
        
        # Start scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info(f"Backup scheduler started: every {interval_hours} hours")
    
    def _scheduled_backup(self):
        """Perform scheduled automatic backup."""
        try:
            backup_path = self.create_backup(backup_type='scheduled')
            logger.info(f"Scheduled backup created: {backup_path}")
            
            # Clean up old backups
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"Scheduled backup failed: {str(e)}")
    
    def create_backup(self, backup_type: str = 'manual', description: str = '') -> str:
        """Create a comprehensive backup of all server data."""
        with self.backup_lock:
            try:
                # Generate backup filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"backup_{backup_type}_{timestamp}.tar.gz"
                backup_path = os.path.join(self.backup_dir, backup_name)
                
                # Prepare backup metadata
                metadata = {
                    'version': '2.0.0',
                    'backup_type': backup_type,
                    'description': description,
                    'created_at': datetime.now().isoformat(),
                    'server_version': self.config.get('version', '2.0.0') if self.config else '2.0.0',
                    'included_components': [],
                    'file_count': 0,
                    'total_size': 0,
                }
                
                # Create backup archive
                with tarfile.open(backup_path, 'w:gz') as tar:
                    
                    # 1. Backup data storage
                    if os.path.exists('data/storage.json'):
                        tar.add('data/storage.json', arcname='storage.json')
                        metadata['included_components'].append('data_storage')
                        logger.debug("Added data storage to backup")
                    
                    # 2. Backup file storage
                    if os.path.exists('data/files'):
                        tar.add('data/files', arcname='files')
                        metadata['included_components'].append('file_storage')
                        logger.debug("Added file storage to backup")
                    
                    # 3. Backup program storage
                    if os.path.exists('data/programs'):
                        tar.add('data/programs', arcname='programs')
                        metadata['included_components'].append('program_storage')
                        logger.debug("Added program storage to backup")
                    
                    # 4. Backup configuration
                    if os.path.exists('data/config'):
                        tar.add('data/config', arcname='config')
                        metadata['included_components'].append('configuration')
                        logger.debug("Added configuration to backup")
                    
                    # 5. Backup logs (recent only)
                    if os.path.exists('data/logs'):
                        # Only backup recent logs (last 7 days)
                        log_backup_path = 'data/logs_recent'
                        self._prepare_recent_logs(log_backup_path)
                        
                        if os.path.exists(log_backup_path):
                            tar.add(log_backup_path, arcname='logs')
                            metadata['included_components'].append('logs')
                            shutil.rmtree(log_backup_path)  # Clean up temp directory
                            logger.debug("Added recent logs to backup")
                    
                    # 6. Backup user data
                    if os.path.exists('data/users.json'):
                        tar.add('data/users.json', arcname='users.json')
                        metadata['included_components'].append('user_data')
                        logger.debug("Added user data to backup")
                    
                    # 7. Add metadata
                    metadata_json = json.dumps(metadata, indent=2)
                    metadata_info = tarfile.TarInfo('metadata.json')
                    metadata_info.size = len(metadata_json.encode())
                    tar.addfile(metadata_info, fileobj=io.BytesIO(metadata_json.encode()))
                    
                    # Update file count and size
                    metadata['file_count'] = len(tar.getnames())
                
                # Calculate final backup size and checksum
                backup_size = os.path.getsize(backup_path)
                checksum = self._calculate_checksum(backup_path)
                
                # Update metadata with final information
                metadata['total_size'] = backup_size
                metadata['checksum'] = checksum
                
                # Save backup information
                self._save_backup_info(backup_name, metadata)
                
                logger.info(f"Backup created successfully: {backup_path}")
                logger.info(f"Backup size: {backup_size / (1024*1024):.2f} MB")
                logger.info(f"Components: {', '.join(metadata['included_components'])}")
                
                return backup_path
                
            except Exception as e:
                logger.error(f"Backup creation failed: {str(e)}")
                raise
    
    def _prepare_recent_logs(self, temp_dir: str):
        """Prepare recent logs for backup (last 7 days)."""
        if not os.path.exists('data/logs'):
            return
        
        os.makedirs(temp_dir, exist_ok=True)
        cutoff_time = time.time() - (7 * 24 * 3600)  # 7 days ago
        
        for log_file in os.listdir('data/logs'):
            log_path = os.path.join('data/logs', log_file)
            if os.path.isfile(log_path) and os.path.getmtime(log_path) > cutoff_time:
                shutil.copy2(log_path, temp_dir)
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _save_backup_info(self, backup_name: str, metadata: Dict[str, Any]):
        """Save backup information to index."""
        info_file = os.path.join(self.backup_dir, 'backup_index.json')
        
        # Load existing index
        backup_index = {}
        if os.path.exists(info_file):
            try:
                with open(info_file, 'r') as f:
                    backup_index = json.load(f)
            except:
                backup_index = {}
        
        # Add new backup info
        backup_index[backup_name] = metadata
        
        # Save updated index
        with open(info_file, 'w') as f:
            json.dump(backup_index, f, indent=2)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        info_file = os.path.join(self.backup_dir, 'backup_index.json')
        
        if not os.path.exists(info_file):
            return []
        
        try:
            with open(info_file, 'r') as f:
                backup_index = json.load(f)
            
            # Convert to list and sort by creation time
            backups = []
            for backup_name, metadata in backup_index.items():
                backup_path = os.path.join(self.backup_dir, backup_name)
                
                # Check if backup file still exists
                if os.path.exists(backup_path):
                    metadata['filename'] = backup_name
                    metadata['file_exists'] = True
                    metadata['file_size'] = os.path.getsize(backup_path)
                else:
                    metadata['filename'] = backup_name
                    metadata['file_exists'] = False
                    metadata['file_size'] = 0
                
                backups.append(metadata)
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    def restore_backup(self, backup_name: str, components: Optional[List[str]] = None, 
                      overwrite: bool = False) -> Tuple[bool, str]:
        """Restore from a backup."""
        with self.backup_lock:
            try:
                backup_path = os.path.join(self.backup_dir, backup_name)
                
                if not os.path.exists(backup_path):
                    return False, f"Backup file not found: {backup_name}"
                
                # Verify backup integrity
                if not self._verify_backup(backup_path):
                    return False, "Backup file is corrupted"
                
                # Create restore point
                restore_point = self._create_restore_point()
                
                try:
                    # Extract backup
                    with tarfile.open(backup_path, 'r:gz') as tar:
                        # Read metadata
                        metadata = self._read_backup_metadata(tar)
                        
                        if components is None:
                            components = metadata.get('included_components', [])
                        
                        logger.info(f"Starting restore of components: {components}")
                        
                        # Restore each component
                        for component in components:
                            success = self._restore_component(tar, component, overwrite)
                            if not success:
                                logger.warning(f"Failed to restore component: {component}")
                        
                        logger.info(f"Restore completed from backup: {backup_name}")
                        return True, "Restore completed successfully"
                        
                except Exception as e:
                    # Restore failed, revert to restore point
                    logger.error(f"Restore failed, reverting: {str(e)}")
                    self._revert_to_restore_point(restore_point)
                    return False, f"Restore failed: {str(e)}"
                
            except Exception as e:
                logger.error(f"Restore operation failed: {str(e)}")
                return False, f"Restore operation failed: {str(e)}"
    
    def _verify_backup(self, backup_path: str) -> bool:
        """Verify backup file integrity."""
        try:
            # Check if it's a valid tar.gz file
            with tarfile.open(backup_path, 'r:gz') as tar:
                # Verify it contains metadata
                if 'metadata.json' not in tar.getnames():
                    return False
                
                # Try to extract metadata
                metadata_file = tar.extractfile('metadata.json')
                if metadata_file:
                    json.loads(metadata_file.read().decode())
                
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}")
            return False
    
    def _read_backup_metadata(self, tar: tarfile.TarFile) -> Dict[str, Any]:
        """Read metadata from backup archive."""
        try:
            metadata_file = tar.extractfile('metadata.json')
            if metadata_file:
                return json.loads(metadata_file.read().decode())
            return {}
        except Exception as e:
            logger.error(f"Failed to read backup metadata: {str(e)}")
            return {}
    
    def _create_restore_point(self) -> str:
        """Create a restore point before restoration."""
        restore_point_name = f"restore_point_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.create_backup(backup_type='restore_point', description='Auto-created before restore')
    
    def _revert_to_restore_point(self, restore_point_path: str):
        """Revert to a restore point."""
        if os.path.exists(restore_point_path):
            restore_point_name = os.path.basename(restore_point_path)
            success, message = self.restore_backup(restore_point_name, overwrite=True)
            if success:
                logger.info("Successfully reverted to restore point")
            else:
                logger.error(f"Failed to revert to restore point: {message}")
    
    def _restore_component(self, tar: tarfile.TarFile, component: str, overwrite: bool) -> bool:
        """Restore a specific component from backup."""
        try:
            component_mapping = {
                'data_storage': {'archive_path': 'storage.json', 'restore_path': 'data/storage.json'},
                'file_storage': {'archive_path': 'files', 'restore_path': 'data/files'},
                'program_storage': {'archive_path': 'programs', 'restore_path': 'data/programs'},
                'configuration': {'archive_path': 'config', 'restore_path': 'data/config'},
                'logs': {'archive_path': 'logs', 'restore_path': 'data/logs_restored'},
                'user_data': {'archive_path': 'users.json', 'restore_path': 'data/users.json'},
            }
            
            if component not in component_mapping:
                logger.warning(f"Unknown component: {component}")
                return False
            
            mapping = component_mapping[component]
            archive_path = mapping['archive_path']
            restore_path = mapping['restore_path']
            
            # Check if component exists in backup
            if archive_path not in tar.getnames():
                # For directories, check if any files start with the path
                dir_files = [name for name in tar.getnames() if name.startswith(archive_path + '/')]
                if not dir_files and archive_path not in tar.getnames():
                    logger.warning(f"Component {component} not found in backup")
                    return False
            
            # Create parent directory if needed
            parent_dir = os.path.dirname(restore_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Handle existing files/directories
            if os.path.exists(restore_path):
                if not overwrite:
                    backup_existing = f"{restore_path}.backup_{int(time.time())}"
                    if os.path.isdir(restore_path):
                        shutil.move(restore_path, backup_existing)
                    else:
                        shutil.copy2(restore_path, backup_existing)
                    logger.info(f"Backed up existing {restore_path} to {backup_existing}")
                else:
                    if os.path.isdir(restore_path):
                        shutil.rmtree(restore_path)
                    else:
                        os.remove(restore_path)
            
            # Extract component
            if archive_path in tar.getnames():
                # Single file
                tar.extract(archive_path, path='.')
                if archive_path != restore_path:
                    shutil.move(archive_path, restore_path)
            else:
                # Directory - extract all files that start with archive_path
                for member in tar.getmembers():
                    if member.name.startswith(archive_path + '/'):
                        tar.extract(member, path='.')
                
                # Move to correct location
                if archive_path != restore_path and os.path.exists(archive_path):
                    shutil.move(archive_path, restore_path)
            
            logger.info(f"Restored component: {component}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore component {component}: {str(e)}")
            return False
    
    def delete_backup(self, backup_name: str) -> Tuple[bool, str]:
        """Delete a backup file."""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            # Remove backup file
            os.remove(backup_path)
            
            # Update backup index
            info_file = os.path.join(self.backup_dir, 'backup_index.json')
            if os.path.exists(info_file):
                try:
                    with open(info_file, 'r') as f:
                        backup_index = json.load(f)
                    
                    if backup_name in backup_index:
                        del backup_index[backup_name]
                    
                    with open(info_file, 'w') as f:
                        json.dump(backup_index, f, indent=2)
                        
                except Exception as e:
                    logger.warning(f"Failed to update backup index: {str(e)}")
            
            logger.info(f"Deleted backup: {backup_name}")
            return True, "Backup deleted successfully"
            
        except Exception as e:
            logger.error(f"Failed to delete backup: {str(e)}")
            return False, f"Failed to delete backup: {str(e)}"
    
    def _cleanup_old_backups(self):
        """Clean up old backups based on retention policy."""
        try:
            retention_days = self.config.get('maintenance.backup_retention_days', 7) if self.config else 7
            cutoff_time = datetime.now() - timedelta(days=retention_days)
            
            backups = self.list_backups()
            deleted_count = 0
            
            for backup in backups:
                if backup['backup_type'] == 'scheduled':  # Only auto-delete scheduled backups
                    backup_time = datetime.fromisoformat(backup['created_at'])
                    if backup_time < cutoff_time:
                        success, message = self.delete_backup(backup['filename'])
                        if success:
                            deleted_count += 1
                            logger.debug(f"Deleted old backup: {backup['filename']}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backup(s)")
                
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup system statistics."""
        try:
            backups = self.list_backups()
            
            total_size = sum(backup.get('file_size', 0) for backup in backups)
            backup_types = {}
            
            for backup in backups:
                backup_type = backup.get('backup_type', 'unknown')
                if backup_type not in backup_types:
                    backup_types[backup_type] = 0
                backup_types[backup_type] += 1
            
            return {
                'total_backups': len(backups),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'backup_types': backup_types,
                'oldest_backup': backups[-1]['created_at'] if backups else None,
                'newest_backup': backups[0]['created_at'] if backups else None,
                'backup_directory': self.backup_dir,
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup statistics: {str(e)}")
            return {}

# Import fix for BytesIO
import io

# Global backup manager instance
backup_manager = None

def initialize_backup_manager(config_manager=None):
    """Initialize the global backup manager."""
    global backup_manager
    backup_manager = BackupManager(config_manager=config_manager)
    return backup_manager

def create_backup(backup_type: str = 'manual', description: str = '') -> str:
    """Create a backup using the global backup manager."""
    if backup_manager is None:
        raise RuntimeError("Backup manager not initialized")
    return backup_manager.create_backup(backup_type, description)

def list_backups() -> List[Dict[str, Any]]:
    """List all backups using the global backup manager."""
    if backup_manager is None:
        raise RuntimeError("Backup manager not initialized")
    return backup_manager.list_backups()

def restore_backup(backup_name: str, components: Optional[List[str]] = None, 
                  overwrite: bool = False) -> Tuple[bool, str]:
    """Restore a backup using the global backup manager."""
    if backup_manager is None:
        raise RuntimeError("Backup manager not initialized")
    return backup_manager.restore_backup(backup_name, components, overwrite)