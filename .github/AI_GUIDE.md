# AI Assistant Quick Reference Guide

## 🤖 Welcome, AI Assistant!

This guide helps you quickly understand and work with this codebase.

## 📚 Essential Reading Order

1. **Start Here:** `README.md` - Project overview
2. **Architecture:** `docs/ARCHITECTURE.md` - System design
3. **Complete Reference:** `docs/PROJECT_COMPLETE.md` - Full codebase map
4. **API Docs:** `docs/API_REFERENCE.md` - All endpoints
5. **Contributing:** `CONTRIBUTING.md` - How to contribute

## 🎯 Quick Facts

- **Framework:** Flask 3.1+
- **Auth:** JWT with bcrypt
- **Database:** JSON files (migration to PostgreSQL planned)
- **Real-time:** WebSockets + WebRTC
- **Tunneling:** Ngrok, Localtunnel, Cloudflared
- **Monitoring:** Prometheus metrics

## 🗂️ Critical Files

| File | Purpose | Lines |
|------|---------|-------|
| `src/app.py` | Main Flask app | 3000+ |
| `src/auth_system.py` | JWT authentication | 420+ |
| `src/data_store.py` | Data storage | 130+ |
| `src/file_store.py` | File management | 300+ |
| `src/program_store.py` | Program execution | 400+ |
| `src/security.py` | Security features | 800+ |

## 🔑 Common Patterns

### Adding New Endpoint

```python
@app.post('/api/your-endpoint')
@login_required  # If auth needed
def your_endpoint():
    """Endpoint description."""
    try:
        data = request.get_json()
        # Validate
        if not data.get('required_field'):
            return api_error('Missing field', 400)
        # Process
        result = process_data(data)
        # Return
        return api_ok({'result': result})
    except Exception as e:
        return api_error(str(e), 500)
```

### Response Format

```python
# Success
api_ok({'key': 'value'})

# Error
api_error('Error message', status_code)
```

### Authentication

```python
# Require login
@login_required
def endpoint():
    user = g.current_user
    ...

# Require admin
@admin_required
def endpoint():
    ...

# Require specific role
@role_required('admin', 'user')
def endpoint():
    ...
```

## 📝 Documentation Updates

When you make changes, update:

1. **API Reference:** `docs/API_REFERENCE.md`
2. **Changelog:** `CHANGELOG.md`
3. **README:** If major feature
4. **Inline Docs:** Docstrings and comments

## 🧪 Testing

```bash
# Run tests
python test_all_features.py
python test_comprehensive.py

# Test specific feature
python test_flask_minimal.py
```

## 🔒 Security Checklist

- [ ] Validate all inputs
- [ ] Use prepared statements/sanitization
- [ ] Add authentication if needed
- [ ] Check authorization
- [ ] Sanitize file paths
- [ ] Rate limit if exposed
- [ ] No secrets in code
- [ ] Proper error handling

## 📦 Dependencies

To add a dependency:
1. Add to `requirements.txt`
2. Document why needed
3. Check security (safety scan)
4. Update install docs

## 🎨 Code Style

- **PEP 8** compliant
- **120 char** line length
- **Type hints** where useful
- **Docstrings** for all functions
- **Comments** for complex logic

## 🚀 Deployment

Files to check:
- `production/docker/Dockerfile.production`
- `production/k8s/*.yaml`
- `production/scripts/deploy.sh`

## 📊 Current State

### Completed (v2.0.0)
- ✅ JWT authentication
- ✅ Voice chat (WebRTC)
- ✅ File management
- ✅ Program execution
- ✅ Multi-tunnel support
- ✅ Monitoring

### In Progress
- 🔄 Test coverage
- 🔄 PostgreSQL migration

### Planned (v2.1.0)
- ⏳ Voice chat recording
- ⏳ Webhook notifications
- ⏳ Global search
- ⏳ File versioning

### Planned (v3.0.0)
- ⏳ PostgreSQL backend
- ⏳ OAuth2 support
- ⏳ Enhanced rate limiting

## 🐛 Common Issues

### Redis Connection Failed
- **Cause:** Redis not running
- **Fix:** Uses memory cache fallback automatically
- **Note:** Non-critical, server runs fine

### Module Not Found
- **Cause:** Missing dependency
- **Fix:** Check venv, install from requirements.txt

### Permission Denied
- **Cause:** File permissions or sudo needed
- **Fix:** Check file ownership, use sudo commands carefully

## 🔧 Maintenance Tasks

### Weekly
- Check logs in `data/logs/`
- Review open issues
- Update dependencies

### Monthly
- Run security scans
- Update documentation
- Review performance metrics

### As Needed
- Respond to issues
- Review PRs
- Update dependencies for security

## 💡 Quick Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
python src/app.py

# Test
python test_comprehensive.py

# Check
flake8 src/
pytest tests/ --cov=src
```

## 🎯 Your Mission

As an AI assistant, your goals are:

1. **Maintain Quality:** Follow patterns, write tests, document
2. **Enhance Features:** Add requested features correctly
3. **Fix Bugs:** Identify and fix issues thoroughly
4. **Improve Docs:** Keep documentation accurate
5. **Security First:** Always consider security implications
6. **Backward Compatible:** Don't break existing functionality

## 📞 Getting Help

- **Documentation:** Check `docs/` directory
- **Examples:** Look at existing code
- **Patterns:** Follow established patterns
- **Issues:** Create GitHub issue if stuck

## ✅ Checklist for Every Change

- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Security considered
- [ ] Performance checked
- [ ] Error handling added
- [ ] Logged appropriately

## 🎓 Learning Resources

Within this repo:
- `docs/ARCHITECTURE.md` - System design patterns
- `docs/STORAGE_SYSTEMS.md` - Data architecture
- `src/` - Well-commented source code
- `tests/` - Example usage patterns

## 🌟 Success Criteria

Your changes are successful when:
1. All tests pass
2. No new security issues
3. Documentation is updated
4. Code follows style guide
5. No breaking changes (or well documented)
6. Reviewers approve

---

**Remember:** You're maintaining a system used by real developers. Quality matters!

**Happy coding!** 🚀
