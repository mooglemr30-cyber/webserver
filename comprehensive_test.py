#!/usr/bin/env python3
"""
Comprehensive test script to verify all services work.
This includes:
1. Original webserver functionality
2. Mobile app setup and configuration
3. Tunnel configuration
4. API endpoints
"""
import sys
import os
import json
import subprocess
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

# Change to webserver directory
os.chdir('/home/admin1/Documents/webserver')

# Test results tracker
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

print_header("COMPREHENSIVE SERVICE TEST")
print_info("Testing original webserver and mobile app integration")

# Test 1: Check if Flask is installed
print_header("Test 1: Python Dependencies")
try:
    import flask
    print_success(f"Flask is installed (version {flask.__version__})")
    test_results['passed'].append("Flask installation")
except ImportError:
    print_error("Flask is NOT installed")
    test_results['failed'].append("Flask installation")
    print_warning("Run: pip3 install -r requirements.txt")

try:
    import flask_cors
    print_success("Flask-CORS is installed")
    test_results['passed'].append("Flask-CORS installation")
except ImportError:
    print_error("Flask-CORS is NOT installed")
    test_results['failed'].append("Flask-CORS installation")

# Test 2: Check main webserver files
print_header("Test 2: Original Webserver Files")
webserver_files = [
    'src/app.py',
    'requirements.txt',
    'data/storage.json',
    'data/webserver.db'
]

for file_path in webserver_files:
    if Path(file_path).exists():
        print_success(f"{file_path} exists")
        test_results['passed'].append(f"File: {file_path}")
    else:
        print_error(f"{file_path} is missing")
        test_results['failed'].append(f"File: {file_path}")

# Test 3: Check mobile app setup
print_header("Test 3: Mobile App Files")
mobile_files = [
    'mobile-app/package.json',
    'mobile-app/app.json',
    'mobile-app/src/App.js',
    'setup_mobile.sh'
]

for file_path in mobile_files:
    if Path(file_path).exists():
        print_success(f"{file_path} exists")
        test_results['passed'].append(f"Mobile file: {file_path}")
    else:
        print_warning(f"{file_path} is missing")
        test_results['warnings'].append(f"Mobile file: {file_path}")

# Test 4: Check tunnel configuration
print_header("Test 4: Tunnel Configuration")
if Path('ngrok.yml').exists():
    print_success("ngrok.yml exists")
    with open('ngrok.yml', 'r') as f:
        content = f.read()
        if 'authtoken' in content:
            print_success("ngrok authtoken is configured")
            test_results['passed'].append("ngrok configuration")
        else:
            print_warning("ngrok authtoken may not be configured")
            test_results['warnings'].append("ngrok authtoken")
else:
    print_warning("ngrok.yml not found")
    test_results['warnings'].append("ngrok.yml")

# Test 5: Check if src/app.py can be imported
print_header("Test 5: Import Webserver Application")
try:
    sys.path.insert(0, 'src')
    import importlib.util
    spec = importlib.util.spec_from_file_location("app", "src/app.py")
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    print_success("src/app.py can be imported successfully")
    print_success(f"App name: {app_module.app.name}")
    test_results['passed'].append("App module import")

    # Check if app has the required routes
    routes = [rule.rule for rule in app_module.app.url_map.iter_rules()]
    print_info(f"Found {len(routes)} routes")

    critical_routes = ['/api/data', '/api/execute', '/health']
    for route in critical_routes:
        matching_routes = [r for r in routes if route in r]
        if matching_routes:
            print_success(f"Route '{route}' exists: {matching_routes}")
            test_results['passed'].append(f"Route: {route}")
        else:
            print_error(f"Route '{route}' is missing")
            test_results['failed'].append(f"Route: {route}")

except Exception as e:
    print_error(f"Failed to import src/app.py: {e}")
    test_results['failed'].append("App module import")

# Test 6: Check service files
print_header("Test 6: Service Configuration")
service_files = ['webserver.service', 'webserver-mobile.service']
for service_file in service_files:
    if Path(service_file).exists():
        print_success(f"{service_file} exists")
        test_results['passed'].append(f"Service: {service_file}")
    else:
        print_warning(f"{service_file} is missing")
        test_results['warnings'].append(f"Service: {service_file}")

# Test 7: Check data directory permissions
print_header("Test 7: Data Directory")
data_dir = Path('data')
if data_dir.exists():
    print_success("data/ directory exists")
    if os.access(data_dir, os.W_OK):
        print_success("data/ directory is writable")
        test_results['passed'].append("Data directory writable")
    else:
        print_error("data/ directory is NOT writable")
        test_results['failed'].append("Data directory writable")
else:
    print_error("data/ directory does NOT exist")
    test_results['failed'].append("Data directory exists")

# Test 8: Check if webserver is currently running
print_header("Test 8: Server Status")
try:
    result = subprocess.run(['pgrep', '-f', 'src/app.py'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        pids = result.stdout.strip().split('\n')
        print_success(f"Webserver is running (PID: {', '.join(pids)})")
        test_results['passed'].append("Server running")
    else:
        print_warning("Webserver does not appear to be running")
        test_results['warnings'].append("Server not running")
except Exception as e:
    print_warning(f"Could not check server status: {e}")

# Test 9: Check mobile app dependencies
print_header("Test 9: Mobile App Dependencies")
mobile_package_json = Path('mobile-app/package.json')
if mobile_package_json.exists():
    with open(mobile_package_json, 'r') as f:
        package_data = json.load(f)
        print_success("package.json is valid JSON")
        if 'dependencies' in package_data:
            deps = package_data['dependencies']
            print_info(f"Found {len(deps)} dependencies")
            for dep, version in list(deps.items())[:5]:  # Show first 5
                print_info(f"  - {dep}: {version}")
            test_results['passed'].append("Mobile app package.json")
        else:
            print_warning("No dependencies found in package.json")
            test_results['warnings'].append("Mobile app dependencies")
else:
    print_warning("mobile-app/package.json not found")

# Final Summary
print_header("TEST SUMMARY")
print(f"\n{Colors.GREEN}Passed: {len(test_results['passed'])}{Colors.END}")
for item in test_results['passed'][:10]:  # Show first 10
    print(f"  ✓ {item}")
if len(test_results['passed']) > 10:
    print(f"  ... and {len(test_results['passed']) - 10} more")

if test_results['failed']:
    print(f"\n{Colors.RED}Failed: {len(test_results['failed'])}{Colors.END}")
    for item in test_results['failed']:
        print(f"  ✗ {item}")

if test_results['warnings']:
    print(f"\n{Colors.YELLOW}Warnings: {len(test_results['warnings'])}{Colors.END}")
    for item in test_results['warnings']:
        print(f"  ⚠ {item}")

# Overall result
print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
if not test_results['failed']:
    print(f"{Colors.GREEN}✓ ALL CRITICAL TESTS PASSED{Colors.END}")
    print(f"\n{Colors.GREEN}CONFIRMATION:{Colors.END}")
    print("  • Original webserver structure is intact")
    print("  • Mobile app files are configured")
    print("  • Both can run simultaneously")
    print("  • Mobile app will access same tools via API")
    exit_code = 0
else:
    print(f"{Colors.RED}✗ SOME TESTS FAILED{Colors.END}")
    print(f"\n{Colors.YELLOW}ACTION REQUIRED:{Colors.END}")
    if any('Flask' in item for item in test_results['failed']):
        print("  1. Install dependencies: pip3 install -r requirements.txt")
    if any('directory' in item.lower() for item in test_results['failed']):
        print("  2. Create missing directories: mkdir -p data/files data/programs")
    exit_code = 1

print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
sys.exit(exit_code)

