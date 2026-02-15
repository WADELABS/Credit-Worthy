# Contributing to CredStack

Thank you for your interest in contributing to CredStack! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/WADELABS/Credit-Worthy.git
   cd Credit-Worthy
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   python setup.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Run tests**
   ```bash
   pytest
   ```

## Project Structure

```
Credit-Worthy/
├── app.py              # Main Flask application
├── auth.py             # Authentication module
├── automation.py       # Automation logic
├── database.py         # Database utilities
├── setup.py            # Database initialization
├── migrations/         # Database migrations
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── tests/              # Test suite
├── workers/            # Background workers
└── docs/               # Documentation
```

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/WADELABS/Credit-Worthy/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version)
   - Screenshots if applicable

### Suggesting Features

1. Check [existing feature requests](https://github.com/WADELABS/Credit-Worthy/issues?q=is%3Aissue+label%3Aenhancement)
2. Create a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Potential implementation approach

### Code Contributions

#### Branching Strategy

- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Urgent production fixes

#### Pull Request Process

1. **Fork the repository** and create a new branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Write or update tests** for your changes

4. **Run the test suite**
   ```bash
   pytest
   pytest --cov=. --cov-report=html  # With coverage
   ```

5. **Update documentation** if needed

6. **Commit your changes** with clear messages
   ```bash
   git commit -m "feat: add user profile editing"
   ```

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request** with:
   - Clear title and description
   - Link to related issues
   - Screenshots/videos for UI changes
   - Test coverage information

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Maximum line length: 100 characters

### Example

```python
def calculate_credit_utilization(balance, credit_limit):
    """
    Calculate credit utilization percentage.
    
    Args:
        balance (float): Current balance
        credit_limit (float): Credit limit
    
    Returns:
        float: Utilization percentage (0-100)
    """
    if credit_limit <= 0:
        return 0
    return (balance / credit_limit) * 100
```

### Testing Standards

- Write unit tests for all new functions
- Maintain at least 80% code coverage
- Use descriptive test names
- Follow AAA pattern: Arrange, Act, Assert

```python
def test_password_validation_requires_minimum_length():
    """Test that passwords must meet minimum length requirement"""
    # Arrange
    short_password = "short"
    
    # Act
    is_valid, error = validate_password(short_password)
    
    # Assert
    assert not is_valid
    assert "at least" in error
```

### Security Guidelines

1. **Never commit secrets** to the repository
2. **Use environment variables** for sensitive data
3. **Hash passwords** using bcrypt
4. **Validate all user inputs**
5. **Use parameterized queries** to prevent SQL injection
6. **Escape HTML output** to prevent XSS
7. **Implement rate limiting** on authentication endpoints
8. **Use HTTPS** in production

## Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(auth): add password reset functionality

Implemented password reset flow via email with secure tokens.
Tokens expire after 1 hour.

Closes #42
```

```
fix(api): correct dispute status update logic

Fixed issue where resolved disputes were not properly
setting the date_resolved field.
```

## Documentation

### Code Documentation

- Add docstrings to all functions, classes, and modules
- Update README.md for major changes
- Update API.md for API changes
- Add inline comments for complex logic

### API Documentation

When adding or modifying API endpoints, update `docs/API.md` with:
- Endpoint path and method
- Request/response examples
- Authentication requirements
- Error responses

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_auth.py::TestAuthentication::test_login_success
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Name test functions as `test_*`
- Use fixtures for common setup
- Mock external dependencies

## Code Review

All contributions require code review before merging:

1. **Automated checks must pass** (tests, linting)
2. **At least one approval** from a maintainer
3. **All conversations resolved**
4. **Up to date with base branch**

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass and coverage is adequate
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Commit messages are clear
- [ ] Changes are focused and minimal

## Getting Help

- **Documentation:** Check the README.md and docs/ folder
- **Issues:** Search existing issues or create a new one
- **Discussions:** Use GitHub Discussions for questions
- **Email:** support@credstack.com

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes for major contributions

Thank you for contributing to CredStack!
