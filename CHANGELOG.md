# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-28

### Added
- **JWT Authentication System** - Complete user authentication with role-based access control
  - User registration and login
  - JWT token generation and verification
  - Password hashing with bcrypt
  - Role-based decorators (@login_required, @admin_required)
  - User management endpoints
  - Password change functionality
  - Token revocation on logout
  
- **Voice Chat Feature** - WebRTC-based voice communication
  - Single persistent voice room
  - Host always present in room
  - Microphone access with echo cancellation
  - Real-time participant tracking
  - WebRTC peer-to-peer connections
  
- **8 New Authentication Endpoints:**
  - POST /api/auth/register
  - POST /api/auth/login
  - POST /api/auth/logout
  - GET /api/auth/me
  - GET /api/auth/users
  - PUT /api/auth/users/<id>
  - DELETE /api/auth/users/<id>
  - POST /api/auth/change-password
  
- **3 New Voice Chat Endpoints:**
  - POST /api/voice-chat/create
  - POST /api/voice-chat/join/<room_id>
  - POST /api/voice-chat/leave/<room_id>/<participant_id>

### Changed
- Updated Flask to 3.1+
- Enhanced security with JWT tokens
- Improved user session management
- Voice chat now uses single persistent room model
- Updated README with new features

### Security
- Added JWT token-based authentication
- Implemented bcrypt password hashing
- Added role-based access control
- Enhanced input validation
- Added token blacklist for logout

## [1.0.0] - 2025-10-XX

### Added
- **Core REST API** - 40+ endpoints for data and file management
- **Data Storage System** - Thread-safe JSON key-value store
- **File Management** - Upload/download with 5GB quota
- **Program Execution** - Run scripts and multi-file projects
- **Command Execution** - Interactive and non-interactive terminal
- **Persistent Terminal Sessions** - Long-running terminal access
- **Tunnel Support** - Ngrok, Localtunnel, Cloudflared integration
- **Web Interface** - Modern dashboard with drag-and-drop
- **Monitoring System** - Prometheus metrics and health checks
- **Backup System** - Automated backups with integrity verification
- **Security Features** - Rate limiting, CSRF protection, input validation
- **Performance Optimization** - Two-tier caching (Redis + Memory)
- **WebSocket Support** - Real-time updates
- **Enhanced Logging** - Structured logging with rotation
- **Error Handling** - Comprehensive error management
- **API Documentation** - Swagger/OpenAPI support

### Core Endpoints
- Data Storage: GET/POST/DELETE /api/data
- File Operations: POST/GET/DELETE /api/files/*
- Program Management: POST/GET/DELETE /api/programs/*
- Command Execution: POST /api/execute
- Terminal Sessions: POST/GET/DELETE /api/terminal/*
- Tunnel Management: POST/GET /api/{ngrok,localtunnel,cloudflared}/*
- Health & Metrics: GET /health, /metrics
- Dashboard: GET /dashboard

### Documentation
- Complete API reference
- Architecture documentation
- Storage systems guide
- Getting started guide
- Installation scripts

### Deployment
- Docker support with docker-compose
- Kubernetes manifests
- Production configurations
- Nginx reverse proxy setup
- Automated deployment scripts

## [0.1.0] - Initial Development

### Added
- Basic Flask server
- Simple data storage
- File upload functionality
- Command execution
- Basic web interface

---

## Version Guidelines

### Major Version (X.0.0)
- Breaking API changes
- Major feature additions
- Architecture changes
- Incompatible updates

### Minor Version (1.X.0)
- New features (backward compatible)
- New endpoints
- Enhanced functionality
- Performance improvements

### Patch Version (1.0.X)
- Bug fixes
- Security patches
- Documentation updates
- Minor improvements

## Upcoming Features

### Planned for 2.1.0
- Voice chat recording
- Webhook notifications
- Global search functionality
- File versioning system

### Planned for 3.0.0
- PostgreSQL migration
- Enhanced API rate limiting
- OAuth2 support
- Advanced analytics dashboard

## Links

- [GitHub Repository](https://github.com/yourusername/webserver)
- [Documentation](./docs/)
- [API Reference](./docs/API_REFERENCE.md)
- [Contributing Guide](./CONTRIBUTING.md)
