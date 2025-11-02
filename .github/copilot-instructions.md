# GitHub Copilot Instructions

## Project Overview
This is a comprehensive Flask-based web server for localhost data storage, file management, program execution, and command execution with JWT authentication.

## Code Style Guidelines
- Follow PEP 8 Python style guidelines
- Use type hints for function parameters and return values
- Add docstrings for all classes and public methods
- Keep functions focused and under 50 lines when possible
- Use meaningful variable names

## Security Best Practices
- Never hardcode secrets, passwords, or API keys
- Use environment variables for configuration (see .env.example)
- Always validate and sanitize user input
- Use parameterized queries for database operations
- Implement rate limiting on all public endpoints
- Log security-relevant events

## Testing Guidelines
- Write unit tests for new features
- Test error handling and edge cases
- Use pytest for test framework
- Maintain test coverage above 80%

## Documentation Requirements
- Update README.md for major feature changes
- Add docstrings with parameter descriptions
- Update API documentation in docs/API_REFERENCE.md
- Include usage examples in docstrings

## Common Patterns
- Use the existing DataStore, FileStore, and ProgramStore classes
- Implement rate limiting using the RateLimiter class
- Use the InputValidator for all user inputs
- Follow the authentication decorator pattern for protected routes
- Use structured logging via the logging_manager

## Dependencies
- Keep requirements.txt updated with version constraints
- Test compatibility with Python 3.8+
- Prefer stable, well-maintained packages
- Document any new dependencies in the PR description
