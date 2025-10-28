# Contributing to Localhost Web Server

Thank you for your interest in contributing! This guide is designed for both human developers and AI coding assistants.

## 🤖 For AI Coding Assistants

This project is designed to be easily maintained and upgraded by AI systems. Here's what you need to know:

### Project Structure Understanding

1. **Read These First:**
   - `README.md` - Project overview and features
   - `docs/PROJECT_COMPLETE.md` - Complete codebase documentation
   - `docs/ARCHITECTURE.md` - System architecture
   - `docs/API_REFERENCE.md` - All API endpoints

2. **Key Files to Understand:**
   - `src/app.py` - Main Flask application (3000+ lines)
   - `src/auth_system.py` - JWT authentication system
   - `src/data_store.py` - Data storage layer
   - `src/file_store.py` - File management
   - `src/program_store.py` - Program execution
   - `src/security.py` - Security features
   - `src/monitoring.py` - Metrics and monitoring

### Making Changes

1. **Before Starting:**
   ```bash
   # Read the relevant documentation
   cat docs/PROJECT_COMPLETE.md
   
   # Check current state
   git status
   git log --oneline -10
   
   # Create a branch
   git checkout -b feature/your-feature-name
   ```

2. **During Development:**
   - Follow existing code patterns
   - Update tests for new features
   - Update documentation in `docs/`
   - Add API documentation for new endpoints

3. **Testing Your Changes:**
   ```bash
   # Run test suite
   python test_all_features.py
   python test_comprehensive.py
   
   # Test specific features
   python test_flask_minimal.py
   python test_program.py
   
   # Start server for manual testing
   source .venv/bin/activate
   python src/app.py
   ```

4. **Documentation Updates:**
   - Update `README.md` if adding major features
   - Update `docs/API_REFERENCE.md` for new endpoints
   - Update `docs/ARCHITECTURE.md` for architectural changes
   - Keep `docs/PROJECT_COMPLETE.md` synchronized

### Code Style Guidelines

- **Python:** PEP 8 compliant
- **Line Length:** Max 120 characters
- **Docstrings:** Google style
- **Type Hints:** Use where appropriate
- **Error Handling:** Comprehensive try-except blocks
- **Logging:** Use structured logging

### Security Considerations

⚠️ **CRITICAL:** This server is designed for localhost/trusted environments.

When adding features:
- Validate all user inputs
- Use parameterized queries
- Sanitize file paths
- Implement rate limiting
- Add authentication where needed
- Never expose sensitive data in logs

### Common Tasks for AI Assistants

#### Adding a New API Endpoint

```python
# In src/app.py

@app.post('/api/your-endpoint')
@login_required  # If authentication needed
def your_endpoint():
    """
    Brief description of endpoint.
    
    Request Body:
        {
            "field": "value"
        }
    
    Returns:
        {
            "success": true,
            "data": {...}
        }
    """
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('field'):
            return api_error('Missing field', 400)
        
        # Process
        result = process_data(data)
        
        # Return
        return api_ok({'result': result})
        
    except Exception as e:
        return api_error(f'Error: {str(e)}', 500)
```

#### Adding Authentication to Existing Endpoint

```python
# Before:
@app.get('/api/data')
def get_data():
    return api_ok(data_store.get_all())

# After:
@app.get('/api/data')
@login_required  # Add this decorator
def get_data():
    # Access user info via g.current_user
    return api_ok(data_store.get_all())
```

#### Adding a New Feature Module

1. Create `src/your_feature.py`
2. Follow existing module patterns
3. Add imports to `src/app.py`
4. Register routes in `src/app.py`
5. Add tests in `tests/`
6. Document in `docs/API_REFERENCE.md`

### Upgrade Patterns

#### Database Migration (JSON → PostgreSQL)

```python
# 1. Install SQLAlchemy
# 2. Create models in src/models.py
# 3. Create migration script
# 4. Preserve existing data
# 5. Update store classes
# 6. Test thoroughly
```

#### Adding New Authentication Methods

```python
# 1. Extend auth_system.py
# 2. Add new decorators
# 3. Create endpoints
# 4. Update documentation
# 5. Maintain backward compatibility
```

### Pull Request Checklist

- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Security implications considered
- [ ] Performance impact assessed
- [ ] Error handling comprehensive
- [ ] Logging appropriate

### Running the Full Test Suite

```bash
# Activate environment
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python test_comprehensive.py

# Check test coverage
python -m pytest --cov=src tests/
```

### Deployment Considerations

When making changes that affect deployment:

1. **Docker:** Update `production/docker/Dockerfile.production`
2. **Kubernetes:** Update manifests in `production/k8s/`
3. **Dependencies:** Update `requirements.txt`
4. **Environment:** Update `.env.template`
5. **Configuration:** Update `data/config/` templates

## 👥 For Human Contributors

### Getting Started

1. Fork the repository
2. Clone your fork
3. Create a virtual environment
4. Install dependencies
5. Make your changes
6. Test thoroughly
7. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/webserver.git
cd webserver

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python src/app.py
```

### Reporting Issues

When reporting bugs, include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs from `data/logs/`

### Feature Requests

Feature requests should include:
- Clear description
- Use case
- Proposed implementation (optional)
- Impact on existing features

## 📝 Code Review Process

1. **Automated Checks:**
   - Tests must pass
   - Code style compliance
   - No security vulnerabilities

2. **Manual Review:**
   - Code quality
   - Architecture fit
   - Documentation completeness

3. **Approval:**
   - At least one maintainer approval
   - All feedback addressed

## 🔄 Release Process

1. Update version in `src/app.py`
2. Update `CHANGELOG.md`
3. Tag release: `git tag v1.x.x`
4. Push tag: `git push origin v1.x.x`
5. Create GitHub release
6. Update documentation

## 📚 Additional Resources

- **API Testing:** Use Postman collection in `docs/`
- **Architecture Diagrams:** See `docs/ARCHITECTURE.md`
- **Examples:** Check `tests/` directory
- **Community:** GitHub Discussions

## 🤝 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow project guidelines

## 📧 Contact

- **Issues:** GitHub Issues
- **Security:** See SECURITY.md
- **General:** GitHub Discussions

---

**Thank you for contributing to Localhost Web Server!** 🚀
