# Repository Information

## 🎯 Purpose
This repository contains a comprehensive Flask-based web server designed for localhost operations with advanced features including JWT authentication, voice chat, file management, and program execution.

## 🤖 AI-Friendly Repository

This repository is **specifically designed to be maintained and upgraded by AI coding assistants**. All documentation, code structure, and workflows are optimized for AI comprehension and contribution.

### For AI Assistants:
- Start with `CONTRIBUTING.md` for contribution guidelines
- Review `docs/PROJECT_COMPLETE.md` for full codebase understanding
- Check `docs/ARCHITECTURE.md` for system design
- Use `docs/API_REFERENCE.md` for endpoint documentation
- Follow patterns in existing code for consistency

## 📊 Repository Stats

- **Language:** Python 3.8+
- **Framework:** Flask 3.1+
- **Lines of Code:** ~15,000+
- **Modules:** 18+
- **API Endpoints:** 50+
- **Documentation Pages:** 10+

## 🔑 Key Features

1. **JWT Authentication** - Secure user management
2. **Voice Chat** - WebRTC-based communication
3. **File Management** - 5GB storage with integrity checks
4. **Program Execution** - Sandboxed script running
5. **Multi-Tunnel Support** - Ngrok, Localtunnel, Cloudflared
6. **Real-time Monitoring** - Prometheus metrics
7. **Comprehensive API** - RESTful with OpenAPI docs

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd webserver
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run server
python src/app.py
```

## 📁 Repository Structure

```
webserver/
├── src/                  # Source code
│   ├── app.py           # Main application
│   ├── auth_system.py   # Authentication
│   └── ...              # Other modules
├── docs/                # Documentation
├── tests/               # Test files
├── production/          # Deployment configs
├── .github/             # GitHub workflows & templates
└── data/                # Runtime data (gitignored)
```

## 🤝 Contributing

See `CONTRIBUTING.md` for detailed guidelines. We welcome contributions from:
- Human developers
- AI coding assistants
- Automated systems

## 📝 License

MIT License - See `LICENSE` file

## 🔗 Links

- **Issues:** [GitHub Issues](../../issues)
- **Pull Requests:** [GitHub PRs](../../pulls)
- **Discussions:** [GitHub Discussions](../../discussions)
- **Documentation:** [docs/](./docs/)

## 📈 Changelog

See `CHANGELOG.md` for version history and updates.

## 🏷️ Version

Current Version: **2.0.0** (October 2025)

## 🎖️ Badges

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)
![AI Friendly](https://img.shields.io/badge/AI-Friendly-purple.svg)
![Maintained](https://img.shields.io/badge/maintained-yes-brightgreen.svg)

## 🎯 Use Cases

- **Local Development Server** - Test web applications locally
- **File Sharing** - Share files on local network
- **Remote Command Execution** - Run commands securely
- **Voice Communication** - Team voice chat
- **Program Execution** - Run scripts remotely
- **API Testing** - Test REST APIs
- **Learning Platform** - Learn Flask development

## 🔒 Security

⚠️ **Important:** This server is designed for localhost/trusted networks. Use tunnels carefully.

For security issues, please see `SECURITY.md` (create if needed).

## 💡 Future Plans

See `CHANGELOG.md` for upcoming features in version 2.1.0 and 3.0.0.
