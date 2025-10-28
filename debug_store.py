#!/usr/bin/env python3
"""
Debug test for program store directly
"""

import sys
import os
sys.path.append('src')

from program_store import ProgramStore

def test_store_multiple_files():
    """Test the store_multiple_files method directly"""
    print("🔍 Testing store_multiple_files directly")
    
    # Create a ProgramStore instance
    store = ProgramStore()
    
    # Create some test file data
    files_data = [
        {
            'filename': 'hello.txt',
            'content': b'Hello World!',
            'relative_path': 'hello.txt'
        },
        {
            'filename': 'main.py',
            'content': b'print("Hello from Python!")',
            'relative_path': 'main.py'
        }
    ]
    
    try:
        result = store.store_multiple_files(files_data, "TestProject", "Test description")
        print("✅ Success!")
        print(f"Project info: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_store_multiple_files()