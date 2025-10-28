"""
Data storage module for the web server.
Provides simple JSON-based data persistence.
"""

import json
import os
import tempfile
import fcntl
from typing import Any, Dict, Optional

class DataStore:
    """Simple JSON-based data storage."""
    
    def __init__(self, data_file: str = 'data/storage.json'):
        """Initialize the data store with a file path."""
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Create data directory if it doesn't exist
        if self.data_dir and not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Load existing data or create empty store
        self._load_data()
    
    def _load_data(self) -> None:
        """Load data from the JSON file."""
        try:
            if os.path.exists(self.data_file):
                # Use a shared lock when reading to avoid racing with a writer
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                        content = f.read().strip()
                        # Handle empty files gracefully
                        self.data = json.loads(content) if content else {}
                    finally:
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        except Exception:
                            pass
            else:
                self.data = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load data file {self.data_file}: {e}")
            self.data = {}
    
    def _save_data(self) -> None:
        """Save data to the JSON file."""
        try:
            # Ensure directory exists
            if self.data_dir and not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir, exist_ok=True)

            # Acquire an exclusive lock using the target file as the lock handle
            # Create file if it doesn't exist yet
            lock_dir = self.data_dir or os.path.dirname(self.data_file) or '.'
            os.makedirs(lock_dir, exist_ok=True)
            with open(self.data_file, 'a+', encoding='utf-8') as lock_file:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                except Exception:
                    # If we can't lock, proceed best-effort rather than crash
                    pass

                # Write to a temp file then atomically replace
                base_name = os.path.basename(self.data_file)
                tmp_fd, tmp_path = tempfile.mkstemp(prefix=f".{base_name}.", dir=lock_dir, text=True)
                try:
                    with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                        json.dump(self.data, f, indent=2, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())

                    # Atomic replace ensures readers never see a partial file
                    os.replace(tmp_path, self.data_file)
                finally:
                    # In case of exception before replace
                    if os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
        except IOError as e:
            print(f"Error: Could not save data file {self.data_file}: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value by key."""
        return self.data.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value for a key."""
        self.data[key] = value
        self._save_data()
    
    def delete(self, key: str) -> bool:
        """Delete a key-value pair. Returns True if key existed."""
        if key in self.data:
            del self.data[key]
            self._save_data()
            return True
        return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all stored data."""
        return self.data.copy()
    
    def clear(self) -> None:
        """Clear all data."""
        self.data = {}
        self._save_data()
    
    def keys(self) -> list:
        """Get all keys."""
        return list(self.data.keys())
    
    def size(self) -> int:
        """Get the number of stored items."""
        return len(self.data)