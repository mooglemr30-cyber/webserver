# API Reference

**Version**: 2.0.0  
**Base URL**: `http://localhost:8000`  
**Content Type**: `application/json`

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Data Storage API](#data-storage-api)
6. [File Management API](#file-management-api)
7. [Program Management API](#program-management-api)
8. [Command Execution API](#command-execution-api)
9. [Tunnel Management API](#tunnel-management-api)
10. [System API](#system-api)
11. [WebSocket API](#websocket-api)

## Overview

The Localhost Web Server provides a comprehensive REST API for data storage, file management, program execution, and system operations. All endpoints return JSON responses with consistent structure.

### Standard Response Format

#### Success Response
```json
{
  "success": true,
  "data": { /* endpoint-specific data */ },
  "request_id": "abc123",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "request_id": "abc123",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "details": { /* optional error details */ }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 413 | Payload Too Large | File or request too large |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

## Authentication

### CSRF Protection

For state-changing operations (POST, PUT, DELETE), CSRF tokens are required.

**Headers**:
```
X-CSRF-Token: your-csrf-token-here
```

To obtain a CSRF token:
```javascript
// Stored in session on first page load
const csrfToken = sessionStorage.getItem('csrf_token');
```

### Session Authentication (Optional)

If authentication is enabled:

**Headers**:
```
X-Session-ID: your-session-id-here
```

**Cookie**:
```
session_id=your-session-id-here
```

## Rate Limiting

Rate limits are enforced per IP address with different limits for different endpoint types.

### Rate Limit Tiers

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| API | 100 requests | 1 minute |
| Upload | 10 requests | 1 minute |
| Command | 20 requests | 1 minute |
| Auth | 5 requests | 5 minutes |
| Tunnel | 5 requests | 5 minutes |

### Rate Limit Headers

Responses include rate limit information:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded Response

**Status**: `429 Too Many Requests`

```json
{
  "success": false,
  "error": "Rate limit exceeded. Please try again later.",
  "retry_after": 60,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## Error Handling

### Error Structure

```json
{
  "success": false,
  "error": "User-friendly error message",
  "error_id": "err_1234567890_1234",
  "category": "validation",
  "suggestions": [
    "Check input format and required fields",
    "Ensure data types are correct"
  ],
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Error Categories

- `validation`: Input validation errors
- `authentication`: Auth-related errors
- `authorization`: Permission errors
- `not_found`: Resource not found
- `rate_limit`: Rate limit exceeded
- `system`: Internal server errors
- `network`: Network-related errors
- `database`: Database errors
- `file_system`: File operation errors
- `external_service`: External service errors

---

## Data Storage API

### Get All Data

Retrieve all stored key-value pairs.

**Endpoint**: `GET /api/data`

**Response**:
```json
{
  "success": true,
  "data": {
    "user_preferences": { "theme": "dark" },
    "app_settings": { "notifications": true }
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl http://localhost:8000/api/data
```

---

### Store Data

Store a key-value pair.

**Endpoint**: `POST /api/data`

**Headers**:
```
Content-Type: application/json
X-CSRF-Token: your-csrf-token
```

**Request Body**:
```json
{
  "key": "user_preferences",
  "value": {
    "theme": "dark",
    "language": "en"
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Data stored successfully",
  "key": "user_preferences",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/data \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"key": "settings", "value": {"theme": "dark"}}'
```

**Errors**:
- `400`: Missing key or value
- `500`: Storage error

---

### Get Data by Key

Retrieve a specific value by key.

**Endpoint**: `GET /api/data/<key>`

**Parameters**:
- `key` (path): The key to retrieve

**Response**:
```json
{
  "success": true,
  "key": "user_preferences",
  "value": {
    "theme": "dark",
    "language": "en"
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl http://localhost:8000/api/data/user_preferences
```

**Errors**:
- `404`: Key not found
- `500`: Storage error

---

### Delete Data

Delete a key-value pair.

**Endpoint**: `DELETE /api/data/<key>`

**Headers**:
```
X-CSRF-Token: your-csrf-token
```

**Parameters**:
- `key` (path): The key to delete

**Response**:
```json
{
  "success": true,
  "message": "Data deleted successfully",
  "key": "user_preferences",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/data/user_preferences \
  -H "X-CSRF-Token: your-token"
```

**Errors**:
- `404`: Key not found
- `500`: Storage error

---

## File Management API

### Upload File

Upload a file to the server.

**Endpoint**: `POST /api/files/upload`

**Headers**:
```
Content-Type: multipart/form-data
X-CSRF-Token: your-csrf-token
```

**Request**: Multipart form with file field named `file`

**Response**:
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "filename": "document_1640995200.pdf",
  "original_name": "document.pdf",
  "size": 1048576,
  "url": "/api/files/download/document_1640995200.pdf",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/files/upload \
  -H "X-CSRF-Token: your-token" \
  -F "file=@/path/to/file.pdf"
```

**Constraints**:
- Max file size: 100MB per file
- Max total storage: 5GB (configurable)
- Blocked extensions: .exe, .com, .bat, .cmd, .vbs, .jar, .msi

**Errors**:
- `400`: No file provided, invalid filename
- `413`: File too large or quota exceeded
- `500`: Storage error

---

### List Files

List all uploaded files with metadata.

**Endpoint**: `GET /api/files/list`

**Response**:
```json
{
  "success": true,
  "files": [
    {
      "filename": "document_1640995200.pdf",
      "original_name": "document.pdf",
      "size": 1048576,
      "size_mb": 1.0,
      "uploaded_at": "2024-01-01T12:00:00.000Z",
      "mime_type": "application/pdf",
      "hash": "abc123..."
    }
  ],
  "count": 1,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl http://localhost:8000/api/files/list
```

---

### Download File

Download a specific file.

**Endpoint**: `GET /api/files/download/<filename>`

**Parameters**:
- `filename` (path): The file to download

**Response**: Binary file data with appropriate Content-Type header

**Example**:
```bash
curl -O http://localhost:8000/api/files/download/document_1640995200.pdf
```

**Errors**:
- `404`: File not found
- `500`: Read error

---

### Delete File

Delete an uploaded file.

**Endpoint**: `DELETE /api/files/delete/<filename>`

**Headers**:
```
X-CSRF-Token: your-csrf-token
```

**Parameters**:
- `filename` (path): The file to delete

**Response**:
```json
{
  "success": true,
  "message": "File deleted successfully",
  "filename": "document_1640995200.pdf",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/files/delete/document_1640995200.pdf \
  -H "X-CSRF-Token: your-token"
```

**Errors**:
- `404`: File not found
- `500`: Delete error

---

### Get Storage Info

Get file storage information and quota usage.

**Endpoint**: `GET /api/files/storage-info`

**Response**:
```json
{
  "success": true,
  "storage": {
    "used_bytes": 52428800,
    "used_mb": 50.0,
    "used_gb": 0.049,
    "max_bytes": 5368709120,
    "max_gb": 5.0,
    "available_bytes": 5316280320,
    "usage_percent": 0.98,
    "file_count": 10
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl http://localhost:8000/api/files/storage-info
```

---

## Program Management API

### Upload Program

Upload a single program/script file.

**Endpoint**: `POST /api/programs/upload`

**Headers**:
```
Content-Type: multipart/form-data
X-CSRF-Token: your-csrf-token
```

**Request**: Multipart form with file field named `file`

**Response**:
```json
{
  "success": true,
  "message": "Program uploaded successfully",
  "program_id": "program_1640995200",
  "filename": "script.py",
  "original_name": "my_script.py",
  "size": 2048,
  "storage_path": "data/programs/program_1640995200/",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/programs/upload \
  -H "X-CSRF-Token: your-token" \
  -F "file=@script.py"
```

**Errors**:
- `400`: No file provided
- `500`: Storage error

---

### Upload ZIP Project

Upload a ZIP file containing multiple project files.

**Endpoint**: `POST /api/programs/upload-zip`

**Headers**:
```
Content-Type: multipart/form-data
X-CSRF-Token: your-csrf-token
```

**Request**: Multipart form with:
- `file`: ZIP file
- `project_name` (optional): Custom project name

**Response**:
```json
{
  "success": true,
  "message": "Project uploaded successfully",
  "project_id": "project_1640995200",
  "project_name": "my_project",
  "files": ["main.py", "utils.py", "config.json"],
  "file_count": 3,
  "main_file": "main.py",
  "storage_path": "data/programs/project_1640995200/",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/programs/upload-zip \
  -H "X-CSRF-Token: your-token" \
  -F "file=@project.zip" \
  -F "project_name=my_project"
```

**ZIP Structure Requirements**:
- Must contain valid files
- Maintains directory structure
- Automatically detects main file (looks for main.py, app.py, etc.)

**Errors**:
- `400`: No file provided, invalid ZIP
- `500`: Extraction or storage error

---

### List Programs

List all uploaded programs and projects.

**Endpoint**: `GET /api/programs/list`

**Response**:
```json
{
  "success": true,
  "programs": [
    {
      "program_id": "program_1640995200",
      "filename": "script.py",
      "original_name": "my_script.py",
      "type": "single",
      "size": 2048,
      "upload_time": "2024-01-01T12:00:00.000Z",
      "execution_count": 5,
      "last_executed": "2024-01-01T13:00:00.000Z"
    },
    {
      "program_id": "project_1640995201",
      "filename": "my_project",
      "type": "project",
      "file_count": 3,
      "main_file": "main.py",
      "size": 10240,
      "upload_time": "2024-01-01T12:30:00.000Z",
      "execution_count": 2,
      "last_executed": "2024-01-01T14:00:00.000Z"
    }
  ],
  "count": 2,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl http://localhost:8000/api/programs/list
```

---

### Execute Program

Execute a single program file with traditional arguments.

**Endpoint**: `POST /api/programs/execute/<filename>`

**Headers**:
```
Content-Type: application/json
X-CSRF-Token: your-csrf-token
```

**Parameters**:
- `filename` (path): Program filename or program_id

**Request Body**:
```json
{
  "arguments": "--input data.txt --output result.txt",
  "sudo_password": "optional-password",
  "timeout": 30
}
```

**Response**:
```json
{
  "success": true,
  "command": "python script.py --input data.txt --output result.txt",
  "stdout": "Processing complete\nResults saved to result.txt\n",
  "stderr": "",
  "return_code": 0,
  "execution_time": 2.5,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/programs/execute/script.py \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"arguments": "--verbose"}'
```

**Errors**:
- `404`: Program not found
- `400`: Invalid arguments
- `500`: Execution error

---

### Execute Project Terminal Command

Execute a command in the context of a project directory (terminal mode).

**Endpoint**: `POST /api/programs/execute-terminal/<project_id>`

**Headers**:
```
Content-Type: application/json
X-CSRF-Token: your-csrf-token
```

**Parameters**:
- `project_id` (path): Project ID

**Request Body**:
```json
{
  "command": "python main.py --process",
  "sudo_password": "optional-password"
}
```

**Response**:
```json
{
  "success": true,
  "command": "python main.py --process",
  "stdout": "Processing started\nCompleted successfully\n",
  "stderr": "",
  "return_code": 0,
  "working_directory": "/app/data/programs/project_1640995200",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/programs/execute-terminal/project_1640995200 \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"command": "python main.py"}'
```

**Features**:
- Runs command in project directory
- Accesses all project files
- Supports chaining commands
- Environment variables preserved

**Errors**:
- `404`: Project not found
- `400`: Invalid command
- `500`: Execution error

---

### Set Project Main File

Set the main executable file for a project.

**Endpoint**: `POST /api/programs/project/<project_id>/set-main`

**Headers**:
```
Content-Type: application/json
X-CSRF-Token: your-csrf-token
```

**Request Body**:
```json
{
  "main_file": "app.py"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Main file updated successfully",
  "project_id": "project_1640995200",
  "main_file": "app.py",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/programs/project/project_1640995200/set-main \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"main_file": "app.py"}'
```

---

### Delete Program

Delete a program or project.

**Endpoint**: `DELETE /api/programs/delete/<filename>`

**Headers**:
```
X-CSRF-Token: your-csrf-token
```

**Parameters**:
- `filename` (path): Program filename or program_id/project_id

**Response**:
```json
{
  "success": true,
  "message": "Program deleted successfully",
  "program_id": "program_1640995200",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/programs/delete/program_1640995200 \
  -H "X-CSRF-Token: your-token"
```

**Errors**:
- `404`: Program not found
- `500`: Delete error

---

### Get Program Storage Info

Get program storage information.

**Endpoint**: `GET /api/programs/storage-info`

**Response**:
```json
{
  "success": true,
  "storage": {
    "total_programs": 15,
    "total_projects": 5,
    "total_files": 50,
    "total_size": 10485760,
    "total_size_mb": 10.0,
    "program_types": {
      "python": 8,
      "bash": 4,
      "javascript": 3
    }
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

---

## Command Execution API

### Execute Command

Execute a non-interactive system command.

**Endpoint**: `POST /api/execute`

**Headers**:
```
Content-Type: application/json
X-CSRF-Token: your-csrf-token
```

**Request Body**:
```json
{
  "command": "ls -la /tmp",
  "sudo_password": "optional-password",
  "timeout": 30
}
```

**Response**:
```json
{
  "success": true,
  "command": "ls -la /tmp",
  "stdout": "total 40\ndrwxrwxrwt ...",
  "stderr": "",
  "return_code": 0,
  "execution_time": 0.1,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"command": "pwd"}'
```

**Security Notes**:
- Dangerous commands are blocked (rm -rf /, dd, mkfs, etc.)
- Commands are validated before execution
- Timeout prevents long-running processes
- Consider command whitelisting in production

**Errors**:
- `400`: Invalid or dangerous command
- `500`: Execution error
- `408`: Timeout

---

### Start Interactive Session

Start an interactive command session with PTY support.

**Endpoint**: `POST /api/execute/interactive`

**Headers**:
```
Content-Type: application/json
X-CSRF-Token: your-csrf-token
```

**Request Body**:
```json
{
  "command": "python",
  "sudo_password": "optional-password"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Interactive session started",
  "session_id": "session-abc123",
  "command": "python",
  "waiting_for_input": true,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/execute/interactive \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"command": "python"}'
```

**Use Cases**:
- Python REPL
- Database CLIs (psql, mysql)
- Interactive scripts
- SSH sessions

---

### Send Input to Session

Send input to an interactive session.

**Endpoint**: `POST /api/execute/send-input`

**Headers**:
```
Content-Type: application/json
X-CSRF-Token: your-csrf-token
```

**Request Body**:
```json
{
  "session_id": "session-abc123",
  "input": "print('Hello World')\n"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "session-abc123",
  "output": "Hello World\n>>> ",
  "waiting_for_input": true,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/execute/send-input \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"session_id": "session-abc123", "input": "exit()\n"}'
```

**Notes**:
- Always include newline (`\n`) for line-based input
- Check `waiting_for_input` to know if session needs more input
- Sessions have 1-hour idle timeout

---

### Terminate Session

Terminate an interactive session.

**Endpoint**: `POST /api/execute/terminate-session`

**Headers**:
```
Content-Type: application/json
X-CSRF-Token: your-csrf-token
```

**Request Body**:
```json
{
  "session_id": "session-abc123"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Session terminated",
  "session_id": "session-abc123",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/execute/terminate-session \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"session_id": "session-abc123"}'
```

---

## Tunnel Management API

### Ngrok Tunnel

#### Start Ngrok
**Endpoint**: `POST /api/ngrok/start`

**Request Body**:
```json
{
  "subdomain": "my-app",
  "auth_token": "ngrok-auth-token"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Ngrok tunnel started",
  "public_url": "https://my-app.ngrok.io",
  "service": "ngrok",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### Stop Ngrok
**Endpoint**: `POST /api/ngrok/stop`

**Response**:
```json
{
  "success": true,
  "message": "Ngrok tunnel stopped",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### Ngrok Status
**Endpoint**: `GET /api/ngrok/status`

**Response**:
```json
{
  "success": true,
  "status": "running",
  "public_url": "https://my-app.ngrok.io",
  "service": "ngrok",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

---

### Localtunnel

#### Start Localtunnel
**Endpoint**: `POST /api/localtunnel/start`

**Request Body**:
```json
{
  "subdomain": "my-app"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Localtunnel started",
  "public_url": "https://my-app.loca.lt",
  "service": "localtunnel",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### Stop Localtunnel
**Endpoint**: `POST /api/localtunnel/stop`

#### Localtunnel Status
**Endpoint**: `GET /api/localtunnel/status`

---

### Cloudflared Tunnel

#### Start Cloudflared
**Endpoint**: `POST /api/cloudflared/start`

**Response**:
```json
{
  "success": true,
  "message": "Cloudflared tunnel started",
  "public_url": "https://abc123.trycloudflare.com",
  "service": "cloudflared",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### Stop Cloudflared
**Endpoint**: `POST /api/cloudflared/stop`

#### Cloudflared Status
**Endpoint**: `GET /api/cloudflared/status`

---

## System API

### Health Check

Basic health check endpoint.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "2.0.0"
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

---

### Prometheus Metrics

Prometheus-compatible metrics endpoint.

**Endpoint**: `GET /metrics`

**Response**: Plain text Prometheus metrics format

**Example**:
```bash
curl http://localhost:8000/metrics
```

**Metrics Included**:
- `http_requests_total`: Total HTTP requests by method, endpoint, status
- `http_request_latency_seconds`: Request latency histogram

---

### API v1 Health Check

Enhanced health check with detailed status.

**Endpoint**: `GET /api/v1/health`

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00.000Z",
    "version": "2.0.0",
    "services": {
      "data_store": "operational",
      "file_store": "operational",
      "program_store": "operational"
    }
  }
}
```

---

### Dashboard Data

Get comprehensive dashboard data.

**Endpoint**: `GET /api/v1/dashboard`

**Response**:
```json
{
  "success": true,
  "data": {
    "storage": {
      "total_programs": 15,
      "total_projects": 5,
      "total_size": 10485760
    },
    "totals": {
      "programs": 15,
      "projects": 5,
      "files": 30,
      "size_bytes": 10485760
    },
    "recent_programs": [...],
    "recent_requests": [...],
    "server_time": "2024-01-01T12:00:00.000Z"
  }
}
```

---

## WebSocket API

### Connection

**URL**: `ws://localhost:8000/socket.io/`

**Protocol**: Socket.IO

### Events

#### Client → Server

**connect**: Establish connection
```javascript
socket.on('connect', function() {
  console.log('Connected:', socket.id);
});
```

**subscribe**: Subscribe to topic
```javascript
socket.emit('subscribe', {
  topics: ['system_status', 'file_operations']
});
```

**unsubscribe**: Unsubscribe from topic
```javascript
socket.emit('unsubscribe', {
  topics: ['system_status']
});
```

**ping**: Heartbeat
```javascript
socket.emit('ping', {echo: 'test'});
```

#### Server → Client

**connected**: Connection established
```javascript
socket.on('connected', function(data) {
  // data.client_id
  // data.server_time
  // data.features
});
```

**subscribed**: Subscription confirmed
```javascript
socket.on('subscribed', function(data) {
  // data.topic
});
```

**topic_message**: Topic broadcast
```javascript
socket.on('topic_message', function(message) {
  // message.topic
  // message.data
  // message.timestamp
});
```

**notification**: System notification
```javascript
socket.on('notification', function(notification) {
  // notification.type
  // notification.title
  // notification.message
  // notification.severity
});
```

### Available Topics

- `system_status`: System health and status updates
- `file_operations`: File upload/download/delete events
- `command_output`: Command execution output
- `tunnel_status`: Tunnel service status changes
- `performance_metrics`: Performance metrics updates
- `security_alerts`: Security event notifications
- `backup_progress`: Backup operation progress
- `notifications`: General notifications

---

## Code Examples

### Python

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Store data
response = requests.post(
    f"{BASE_URL}/api/data",
    json={
        "key": "settings",
        "value": {"theme": "dark"}
    },
    headers={"X-CSRF-Token": "your-token"}
)
print(response.json())

# Get data
response = requests.get(f"{BASE_URL}/api/data/settings")
data = response.json()
print(data['value'])

# Upload file
with open('file.txt', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/api/files/upload",
        files={'file': f},
        headers={"X-CSRF-Token": "your-token"}
    )
print(response.json())

# Execute command
response = requests.post(
    f"{BASE_URL}/api/execute",
    json={"command": "ls -la"},
    headers={"X-CSRF-Token": "your-token"}
)
result = response.json()
print(result['stdout'])
```

### JavaScript

```javascript
// Fetch API
async function storeData(key, value) {
  const response = await fetch('http://localhost:8000/api/data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': getCsrfToken()
    },
    body: JSON.stringify({ key, value })
  });
  return response.json();
}

async function executeCommand(command) {
  const response = await fetch('http://localhost:8000/api/execute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': getCsrfToken()
    },
    body: JSON.stringify({ command })
  });
  return response.json();
}

// Upload file
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/api/files/upload', {
    method: 'POST',
    headers: {
      'X-CSRF-Token': getCsrfToken()
    },
    body: formData
  });
  return response.json();
}

// WebSocket connection
const socket = io('http://localhost:8000');

socket.on('connect', () => {
  console.log('Connected');
  socket.emit('subscribe', {
    topics: ['system_status', 'notifications']
  });
});

socket.on('notification', (notification) => {
  console.log('Notification:', notification);
  showNotification(notification.message, notification.severity);
});
```

### cURL

```bash
# Store data
curl -X POST http://localhost:8000/api/data \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"key": "settings", "value": {"theme": "dark"}}'

# Get data
curl http://localhost:8000/api/data/settings

# Upload file
curl -X POST http://localhost:8000/api/files/upload \
  -H "X-CSRF-Token: your-token" \
  -F "file=@/path/to/file.txt"

# List files
curl http://localhost:8000/api/files/list

# Execute command
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"command": "ls -la"}'

# Start tunnel
curl -X POST http://localhost:8000/api/ngrok/start \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{"subdomain": "my-app", "auth_token": "token"}'
```

---

## Best Practices

### 1. Error Handling

Always check the `success` field:
```javascript
const response = await fetch('/api/data');
const result = await response.json();

if (result.success) {
  // Handle success
  console.log(result.data);
} else {
  // Handle error
  console.error(result.error);
  console.log('Suggestions:', result.suggestions);
}
```

### 2. Rate Limiting

Implement exponential backoff for rate limits:
```javascript
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const response = await fetch(url, options);
    
    if (response.status !== 429) {
      return response;
    }
    
    const delay = Math.pow(2, i) * 1000; // Exponential backoff
    await new Promise(resolve => setTimeout(resolve, delay));
  }
  throw new Error('Max retries exceeded');
}
```

### 3. CSRF Tokens

Store and include CSRF tokens:
```javascript
// Get token on page load
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

// Include in all state-changing requests
fetch('/api/data', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrfToken
  },
  body: JSON.stringify(data)
});
```

### 4. File Uploads

Handle large file uploads with progress:
```javascript
function uploadFileWithProgress(file) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percent = (e.loaded / e.total) * 100;
        updateProgressBar(percent);
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error('Upload failed'));
      }
    });
    
    const formData = new FormData();
    formData.append('file', file);
    
    xhr.open('POST', '/api/files/upload');
    xhr.setRequestHeader('X-CSRF-Token', getCsrfToken());
    xhr.send(formData);
  });
}
```

### 5. Interactive Sessions

Properly manage interactive sessions:
```javascript
class InteractiveSession {
  constructor(command) {
    this.sessionId = null;
    this.command = command;
  }
  
  async start() {
    const response = await fetch('/api/execute/interactive', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken()
      },
      body: JSON.stringify({ command: this.command })
    });
    
    const result = await response.json();
    this.sessionId = result.session_id;
    return result;
  }
  
  async sendInput(input) {
    const response = await fetch('/api/execute/send-input', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken()
      },
      body: JSON.stringify({
        session_id: this.sessionId,
        input: input + '\n'
      })
    });
    
    return response.json();
  }
  
  async terminate() {
    const response = await fetch('/api/execute/terminate-session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken()
      },
      body: JSON.stringify({ session_id: this.sessionId })
    });
    
    return response.json();
  }
}

// Usage
const session = new InteractiveSession('python');
await session.start();
await session.sendInput('print("Hello")');
await session.sendInput('exit()');
await session.terminate();
```

---

## API Versioning

Currently on **v1**. Future versions will maintain backward compatibility:

- **v1**: Current API (prefix: `/api/v1/`)
- **v2**: Planned (improved consistency, new features)

Legacy endpoints without version prefix are maintained for compatibility.

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **JSON**: `http://localhost:8000/api/openapi.json`

---

## Support

For issues or questions:
- Check documentation: `/docs` directory
- View logs: `data/logs/`
- Health check: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`
