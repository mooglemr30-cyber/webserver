"""
API client module for test project
"""

import json

class APIClient:
    """Simple API client"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get(self, endpoint):
        """Simulate GET request"""
        return {"status": "success", "endpoint": endpoint}
    
    def post(self, endpoint, data):
        """Simulate POST request"""
        return {
            "status": "success", 
            "endpoint": endpoint, 
            "data": data
        }
    
    def format_response(self, response):
        """Format API response"""
        return json.dumps(response, indent=2)