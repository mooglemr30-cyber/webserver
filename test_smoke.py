#!/usr/bin/env python3
"""
Smoke tests for the webserver using Flask test client.
This script loads src/app.py as a module (with DISABLE_TUNNEL_AUTO=1) and runs a sequence of API tests:
 - GET /health
 - GET /api/mobile/config
 - GET /api/mobile/tunnel/status
 - Register a test user
 - Login the test user
 - Data CRUD: POST /api/data, GET /api/data, GET /api/data/<key>, DELETE /api/data/<key>

Run: python test_smoke.py
"""
import os
import sys
import json
import traceback
from importlib import util
from types import ModuleType

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(ROOT, 'src', 'app.py')

# Ensure we don't auto-start tunnel or modify system during tests
os.environ['DISABLE_TUNNEL_AUTO'] = '1'

# Load module from path
spec = util.spec_from_file_location('web_app_module', APP_PATH)
web = util.module_from_spec(spec)
# Insert root into sys.path so imports inside app.py that use relative imports work
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
try:
    spec.loader.exec_module(web)
except Exception as e:
    print('ERROR: Failed to import app module:')
    traceback.print_exc()
    sys.exit(2)

# The Flask app object should be named `app` in module
if not hasattr(web, 'app'):
    print('ERROR: app object not found in module')
    sys.exit(3)

app = web.app
client = app.test_client()

results = {}

def run_get(path):
    resp = client.get(path)
    try:
        body = resp.get_json()
    except Exception:
        body = resp.data.decode('utf-8', errors='replace')
    return resp.status_code, body

def run_post(path, data=None, headers=None):
    headers = headers or {}
    resp = client.post(path, json=data, headers=headers)
    try:
        body = resp.get_json()
    except Exception:
        body = resp.data.decode('utf-8', errors='replace')
    return resp.status_code, body

print('Running smoke tests against in-memory Flask test client...')

# 1) Health
code, body = run_get('/health')
results['health'] = {'status_code': code, 'body': body}
print('GET /health ->', code)

# 2) Mobile config
code, body = run_get('/api/mobile/config')
results['mobile_config'] = {'status_code': code, 'body': body}
print('GET /api/mobile/config ->', code)

# 3) Tunnel status
code, body = run_get('/api/mobile/tunnel/status')
results['tunnel_status'] = {'status_code': code, 'body': body}
print('GET /api/mobile/tunnel/status ->', code)

# 4) Register test user
username = 'smoke_test_user'
password = 'smoke-password-123'
email = 'smoke@example.local'
code, body = run_post('/api/auth/register', {'username': username, 'email': email, 'password': password})
results['register'] = {'status_code': code, 'body': body}
print('POST /api/auth/register ->', code)

# 5) Login test user
code, body = run_post('/api/auth/login', {'username': username, 'password': password})
results['login'] = {'status_code': code, 'body': body}
print('POST /api/auth/login ->', code)

auth_token = None
if isinstance(body, dict) and body.get('success') and body.get('data') and body['data'].get('token'):
    auth_token = body['data']['token']
elif isinstance(body, dict) and body.get('token'):
    auth_token = body.get('token')

# 6) Data CRUD
headers = {}
if auth_token:
    headers['Authorization'] = f'Bearer {auth_token}'

# POST /api/data
test_key = 'smoke_key'
code, body = run_post('/api/data', {'key': test_key, 'value': {'foo': 'bar'}}, headers=headers)
results['data_post'] = {'status_code': code, 'body': body}
print('POST /api/data ->', code)

# GET /api/data
code, body = run_get('/api/data')
results['data_get_all'] = {'status_code': code, 'body': body}
print('GET /api/data ->', code)

# GET /api/data/<key>
code, body = run_get(f'/api/data/{test_key}')
results['data_get_key'] = {'status_code': code, 'body': body}
print(f'GET /api/data/{test_key} ->', code)

# DELETE /api/data/<key>
resp = client.delete(f'/api/data/{test_key}', headers=headers)
try:
    del_body = resp.get_json()
except Exception:
    del_body = resp.data.decode('utf-8', errors='replace')
results['data_delete'] = {'status_code': resp.status_code, 'body': del_body}
print(f'DELETE /api/data/{test_key} ->', resp.status_code)

# Summarize
print('\nSMOKE TEST RESULTS:')
print(json.dumps(results, indent=2, default=str))

# Exit code: 0 if health and config OK, else 1
ok = (results['health']['status_code'] == 200 and results['mobile_config']['status_code'] == 200)
sys.exit(0 if ok else 1)

