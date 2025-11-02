# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by:

1. **DO NOT** open a public issue
2. Email the maintainers directly (if email is configured in repository)
3. Or open a private security advisory on GitHub

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We aim to respond within 48 hours and provide a fix within 7 days for critical issues.

## Security Best Practices

### For Deployment

1. **Environment Variables**
   - Never commit `.env` files to version control
   - Use strong, randomly generated secrets for `JWT_SECRET_KEY` and `CSRF_SECRET_KEY`
   - Generate secrets using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

2. **Default Credentials**
   - Change the default admin password immediately after first login
   - The password is stored in `data/config/admin_credentials.txt`
   - Delete this file after changing the password

3. **Privileged Execution**
   - Only enable privileged execution if absolutely necessary
   - Store the privileged passphrase securely
   - Set `CREDENTIALS_DIR` environment variable to a secure location
   - Regularly audit privileged command logs

4. **Network Security**
   - Use HTTPS in production (reverse proxy like Nginx with Let's Encrypt)
   - Enable authentication (`AUTH_ENABLED=true`)
   - Configure rate limiting appropriately
   - Restrict file upload extensions and sizes

5. **Tunnel Security**
   - Be cautious when exposing your server via tunnels
   - Always use authentication when tunnels are active
   - Monitor tunnel access logs
   - Consider using Cloudflared for production (enterprise-grade)

### For Development

1. **Dependencies**
   - Regularly update dependencies to patch security vulnerabilities
   - Run `safety check` before deploying
   - Use version constraints in `requirements.txt`

2. **Code Security**
   - Never use `eval()` or `exec()` with user input
   - Always validate and sanitize user input
   - Use parameterized queries for database operations
   - Implement proper error handling (don't leak sensitive info)

3. **File Handling**
   - Validate file types and extensions
   - Enforce size limits
   - Store uploaded files outside the web root
   - Use virus scanning for uploaded files in production

4. **Command Execution**
   - Validate and sanitize all command inputs
   - Use allowlists instead of denylists
   - Set appropriate timeouts
   - Log all command executions

## Security Features

The webserver includes several built-in security features:

- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Configurable rate limits on all endpoints
- **CSRF Protection**: Cross-Site Request Forgery protection
- **Input Validation**: Comprehensive input validation and sanitization
- **File Security**: Extension blacklist, size limits, checksum verification
- **Command Security**: Dangerous command blocking, timeout protection
- **Audit Logging**: All security-relevant events are logged

## Security Checklist for Production

- [ ] Change all default passwords
- [ ] Set strong JWT and CSRF secret keys
- [ ] Enable authentication (`AUTH_ENABLED=true`)
- [ ] Configure HTTPS (use reverse proxy)
- [ ] Set appropriate rate limits
- [ ] Disable debug mode (`FLASK_DEBUG=False`)
- [ ] Set `FLASK_ENV=production`
- [ ] Review and restrict file upload permissions
- [ ] Enable security logging
- [ ] Set up regular backups
- [ ] Configure firewall rules
- [ ] Review privileged execution configuration
- [ ] Update all dependencies to latest stable versions
- [ ] Run security scans (safety, bandit)
- [ ] Review tunnel configurations if used

## Known Security Considerations

1. **Privileged Execution**: The privileged execution feature allows sudo commands. Only enable if necessary and protect the passphrase carefully.

2. **Command Execution**: The command execution feature allows running system commands. Use with caution and always enable authentication.

3. **File Uploads**: Large file uploads can lead to DoS. Configure appropriate limits.

4. **Tunnels**: Public tunnels expose your server to the internet. Always use authentication when tunnels are active.

## Security Updates

Security updates are prioritized and released as soon as possible. Check the [CHANGELOG](CHANGELOG.md) for security-related updates.
