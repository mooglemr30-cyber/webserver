"""
Database module for test project
"""

class Database:
    """Simple database class"""
    
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        """Get value by key"""
        return self.data.get(key)
    
    def set(self, key, value):
        """Set value for key"""
        self.data[key] = value
    
    def delete(self, key):
        """Delete key"""
        if key in self.data:
            del self.data[key]
            return True
        return False