"""
File storage module for the web server.
Provides file upload, download, and management with storage quotas.
"""

import os
import json
import shutil
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib

class FileStore:
    """File storage with quota management."""
    
    def __init__(self, storage_dir: str = 'data/files', max_size_gb: float = 5.0):
        """Initialize the file store with storage directory and size limit."""
        self.storage_dir = storage_dir
        self.max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)  # Convert GB to bytes
        self.metadata_file = os.path.join(storage_dir, '.file_metadata.json')
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        
        # Load or create metadata
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load file metadata from disk."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
        except (json.JSONDecodeError, IOError):
            self.metadata = {}
    
    def _save_metadata(self) -> None:
        """Save file metadata to disk."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving metadata: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate SHA256 hash of file for integrity checking."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except IOError:
            return ""
    
    def get_storage_info(self) -> Dict:
        """Get storage usage information."""
        total_size = 0
        file_count = 0
        
        # Calculate actual storage usage
        for root, dirs, files in os.walk(self.storage_dir):
            for file in files:
                if file != '.file_metadata.json':  # Exclude metadata file
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
        
        return {
            'used_bytes': total_size,
            'used_mb': round(total_size / (1024 * 1024), 2),
            'used_gb': round(total_size / (1024 * 1024 * 1024), 3),
            'max_bytes': self.max_size_bytes,
            'max_gb': round(self.max_size_bytes / (1024 * 1024 * 1024), 1),
            'available_bytes': self.max_size_bytes - total_size,
            'usage_percent': round((total_size / self.max_size_bytes) * 100, 1),
            'file_count': file_count,
            # Add aliases for frontend compatibility
            'total_files': file_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
    
    def can_store_file(self, file_size: int) -> Tuple[bool, str]:
        """Check if a file can be stored within quota limits."""
        storage_info = self.get_storage_info()
        
        if file_size > storage_info['available_bytes']:
            return False, f"Not enough space. Need {round(file_size / (1024*1024), 2)}MB, but only {round(storage_info['available_bytes'] / (1024*1024), 2)}MB available."
        
        return True, "OK"
    
    def store_file(self, file_data: bytes, filename: str, original_name: str = None) -> Tuple[bool, str, str]:
        """Store a file with metadata tracking."""
        try:
            # Check storage quota
            can_store, message = self.can_store_file(len(file_data))
            if not can_store:
                return False, message, ""
            
            # Sanitize filename
            safe_filename = self._sanitize_filename(filename)
            file_path = os.path.join(self.storage_dir, safe_filename)
            
            # Handle duplicate filenames
            counter = 1
            base_name, ext = os.path.splitext(safe_filename)
            while os.path.exists(file_path):
                safe_filename = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(self.storage_dir, safe_filename)
                counter += 1
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Store metadata
            file_hash = self._get_file_hash(file_path)
            self.metadata[safe_filename] = {
                'original_name': original_name or filename,
                'size': len(file_data),
                'uploaded_at': datetime.now().isoformat(),
                'hash': file_hash,
                'mime_type': self._guess_mime_type(filename)
            }
            self._save_metadata()
            
            return True, f"File '{safe_filename}' stored successfully", safe_filename
            
        except Exception as e:
            return False, f"Error storing file: {str(e)}", ""
    
    def get_file(self, filename: str) -> Tuple[bool, bytes, Dict]:
        """Retrieve a file and its metadata."""
        try:
            safe_filename = self._sanitize_filename(filename)
            file_path = os.path.join(self.storage_dir, safe_filename)
            
            if not os.path.exists(file_path):
                return False, b"", {"error": "File not found"}
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            metadata = self.metadata.get(safe_filename, {})
            
            return True, file_data, metadata
            
        except Exception as e:
            return False, b"", {"error": str(e)}
    
    def delete_file(self, filename: str) -> Tuple[bool, str]:
        """Delete a file and its metadata."""
        try:
            safe_filename = self._sanitize_filename(filename)
            file_path = os.path.join(self.storage_dir, safe_filename)
            
            if not os.path.exists(file_path):
                return False, "File not found"
            
            # Remove file
            os.remove(file_path)
            
            # Remove metadata
            if safe_filename in self.metadata:
                del self.metadata[safe_filename]
                self._save_metadata()
            
            return True, f"File '{safe_filename}' deleted successfully"
            
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"
    
    def list_files(self) -> List[Dict]:
        """List all stored files with metadata."""
        files = []
        
        for filename in os.listdir(self.storage_dir):
            if filename == '.file_metadata.json':
                continue
                
            file_path = os.path.join(self.storage_dir, filename)
            if os.path.isfile(file_path):
                metadata = self.metadata.get(filename, {})
                file_stat = os.stat(file_path)
                
                files.append({
                    'filename': filename,
                    'original_name': metadata.get('original_name', filename),
                    'size': file_stat.st_size,
                    'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                    'uploaded_at': metadata.get('uploaded_at', 'Unknown'),
                    'mime_type': metadata.get('mime_type', 'application/octet-stream'),
                    'hash': metadata.get('hash', '')
                })
        
        # Sort by upload date (newest first)
        files.sort(key=lambda x: x['uploaded_at'], reverse=True)
        return files
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal and other issues."""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def _guess_mime_type(self, filename: str) -> str:
        """Guess MIME type based on file extension."""
        ext = os.path.splitext(filename)[1].lower()
        
        mime_types = {
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.pdf': 'application/pdf',
            '.zip': 'application/zip',
            '.tar': 'application/x-tar',
            '.gz': 'application/gzip',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.svg': 'image/svg+xml',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        return mime_types.get(ext, 'application/octet-stream')