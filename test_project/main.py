#!/usr/bin/env python3
"""
Main application file for test project
"""

def main():
    print("Hello from main.py!")
    print("Testing multiple file upload functionality")
    
    # Import other modules
    from utils import helper_function
    from config import get_config
    
    print(f"Helper result: {helper_function()}")
    print(f"Config: {get_config()}")

if __name__ == "__main__":
    main()