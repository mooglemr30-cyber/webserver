# Localhost Web Server Project

This workspace contains a Flask-based web server for localhost data storage and command execution.

## Project Overview
- **Type**: Python Flask web application
- **Purpose**: Local web server with REST API for data storage and command execution
- **Port**: 8000 (http://localhost:8000)

## Key Features
- REST API endpoints for data CRUD operations
- Command execution capability (with security warnings)
- JSON-based data persistence
- Web interface for testing
- CORS enabled for cross-origin requests

## Development Guidelines
- Use the configured Python virtual environment
- Server runs in debug mode for development
- Data is stored in JSON format in the `data/` directory
- Command execution has a 30-second timeout for safety

## Security Notes
- Command execution endpoint is potentially dangerous
- Only use in trusted local environment
- Consider restricting commands in production use

## API Endpoints
- GET /api/data - Retrieve all data
- POST /api/data - Store new data
- GET /api/data/<key> - Get data by key
- DELETE /api/data/<key> - Delete data by key
- POST /api/execute - Execute system commands
- GET /health - Health check

Work through tasks systematically and keep communication concise.