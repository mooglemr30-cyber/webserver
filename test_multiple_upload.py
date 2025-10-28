#!/usr/bin/env python3
"""
Test script for multiple file upload functionality
"""

import requests
import os
import zipfile
import tempfile

def create_test_zip():
    """Create a zip file with the test project"""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files from test_project directory
            base_dir = '/home/tom/Documents/webserver/test_project'
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, base_dir)
                    zipf.write(file_path, arc_path)
        return tmp.name

def test_multiple_upload():
    """Test multiple file upload functionality"""
    print("🚀 Testing Multiple File Upload Functionality")
    print("=" * 50)
    
    # Create test zip file
    zip_path = create_test_zip()
    print(f"Created test zip: {zip_path}")
    
    try:
        # Test uploading the project
        with open(zip_path, 'rb') as f:
            files = {'files[]': ('test_project.zip', f, 'application/zip')}
            data = {'project_name': 'TestProject', 'description': 'Test project for multiple file upload'}
            
            response = requests.post(
                'http://localhost:8000/api/programs/upload-multiple',
                files=files,
                data=data
            )
            
            print(f"Upload response status: {response.status_code}")
            print(f"Upload response: {response.json()}")
            
        # Test getting program list
        try:
            response = requests.get('http://localhost:8000/api/programs/list')
            print(f"Programs list status: {response.status_code}")
            if response.status_code == 200:
                print(f"Programs list: {response.json()}")
            else:
                print(f"Programs list error: {response.text}")
        except Exception as e:
            print(f"Error getting programs list: {e}")
        
        # Test getting project details (try to extract project name from the upload response)
        # The file was uploaded as a zip, so we need to use the extracted project name
        try:
            response = requests.get('http://localhost:8000/api/programs/project/test_project/files')
            print(f"Project files status: {response.status_code}")
            if response.status_code == 200:
                print(f"Project files: {response.json()}")
            else:
                print(f"Project files error: {response.text}")
        except Exception as e:
            print(f"Error getting project files: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        os.unlink(zip_path)

if __name__ == "__main__":
    test_multiple_upload()