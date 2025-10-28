"""
Utility functions for the test project
"""

def helper_function():
    """A simple helper function"""
    return "Helper function executed successfully!"

def calculate_sum(a, b):
    """Calculate sum of two numbers"""
    return a + b

def process_data(data):
    """Process some data"""
    return [item.upper() for item in data if isinstance(item, str)]