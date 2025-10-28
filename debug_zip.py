#!/usr/bin/env python3
"""
Debug test for zip file upload
"""

import requests
import tempfile
import zipfile

def test_simple_zip():
    """Test with a simple zip file"""
    print("🔍 Debug: Testing simple zip upload")
    
    # Create a simple zip with one text file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        with zipfile.ZipFile(tmp, 'w') as zipf:
            zipf.writestr('hello.txt', 'Hello World!')
            zipf.writestr('main.py', 'print("Hello from Python!")')
        
        zip_path = tmp.name
    
    try:
        # Upload the zip file
        with open(zip_path, 'rb') as f:
            files = {'files[]': ('simple.zip', f, 'application/zip')}
            data = {'project_name': 'SimpleTest', 'description': 'Simple test project'}
            
            response = requests.post(
                'http://localhost:8000/api/programs/upload-multiple',
                files=files,
                data=data
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        import os
        os.unlink(zip_path)

if __name__ == "__main__":
    test_simple_zip()