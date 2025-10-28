"""
Configuration settings for the test project
"""

import os

def get_config():
    """Get configuration settings"""
    return {
        "app_name": "Test Project",
        "version": "1.0.0",
        "debug": True,
        "environment": os.getenv("ENV", "development")
    }

# Constants
MAX_CONNECTIONS = 100
TIMEOUT = 30
API_VERSION = "v1"