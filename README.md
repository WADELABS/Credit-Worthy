# CredStack: Production-Ready Credit Optimization Platform 🛡️

> **"Stop guessing, start automating."**

[![CI/CD](https://github.com/WADELABS/Credit-Worthy/actions/workflows/ci.yml/badge.svg)](https://github.com/WADELABS/Credit-Worthy/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

CredStack is a precision-engineered, production-ready platform for automated credit optimization. Moving beyond simple tracking, it provides enterprise-grade authentication, comprehensive API access, and robust automation to maximize your credit health while maintaining absolute data sovereignty.

## ✨ What's New

### 🔐 Enterprise Security
- **Password-based authentication** with bcrypt hashing
- **JWT token support** for API access
- **Rate limiting** and account lockout protection
- **CSRF protection** on all forms
- **Security headers** (HSTS, X-Frame-Options, etc.)

### 🚀 RESTful API (v1)
- **Interactive Swagger UI** at `/api/docs` for easy API exploration
- Complete REST API with JWT authentication
- OpenAPI/Swagger specification with full request/response schemas
- Endpoints for credit data, automation, disputes, and user management
- Pagination, filtering, and sorting on list endpoints
- Rate limiting and comprehensive error handling
- Full API documentation with examples

### 🧪 Production-Ready Testing
- 70+ comprehensive tests covering:
  - Authentication flows
  - API endpoints
  - Input validation
  - SQL injection prevention
  - XSS prevention
  - Data isolation
- CI/CD pipeline with automated testing

### 📚 Complete Documentation
- **API Documentation** - Full REST API reference
- **Contributing Guidelines** - Development best practices
- **Changelog** - Version history and migration guide

## 🏛️ Architectural Ethos

CredStack operates as an active automation substrate that employs heuristic logic to manage credit utilization before it impacts your financial profile.

### 🧠 Utilization Management Heuristics
- **Proactive Signals**: Alerts triggered before statement close dates
- **Configurable Thresholds**: Target <10% utilization for optimal credit scores
- **Automated Workflows**: Reduce reported balances to maintain credit health

### 🛡️ Privacy Architecture & Data Sovereignty
- **Local-Only Storage**: SQLite database at `database/credstack.db`
- **Zero-Cloud Footprint**: No external APIs or third-party telemetry
- **Hermetic Execution**: All processing runs locally on your hardware
- **Multi-User Support**: Complete data isolation between users

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/WADELABS/Credit-Worthy.git
   cd Credit-Worthy
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (SECRET_KEY, JWT_SECRET_KEY)
   ```

4. **Initialize database**
   ```bash
   python setup.py
   ```

5. **Run migrations (for existing databases)**
   ```bash
   python migrations/001_add_password_fields.py
   python migrations/002_enhance_disputes.py
   ```

6. **Start the application**
   ```bash
   python app.py
   ```

7. **Access the dashboard**
   Open your browser to `http://localhost:5000`

### First Time Setup

1. Navigate to `http://localhost:5000`
2. Click "Register here" to create an account
3. Enter your email, password, and name
4. You'll be automatically logged in to your dashboard

## 📋 Features

### Dashboard
- **Credit Health Score**: Real-time credit score calculation
- **Account Management**: Track credit cards, loans, and other accounts
- **Utilization Monitoring**: Automatic utilization percentage calculations
- **Active Disputes**: Track disputes with credit bureaus
- **Upcoming Reminders**: Never miss important dates

### Automation
- **Statement Alerts**: Notifications before statement close dates
- **Utilization Tracking**: Monitor credit utilization automatically
- **Dispute Follow-ups**: Automated reminders for dispute resolution
- **Configurable Rules**: Customize automation behavior

### Dispute Tracking
- File disputes with credit bureaus (Experian, Equifax, TransUnion)
- Track dispute status (pending, in_progress, resolved, rejected)
- Automatic follow-up date calculation
- Comprehensive dispute history

### API Access
- **Interactive Swagger UI** at `http://localhost:5000/api/docs`
- **RESTful API v1** with JWT authentication
- **Complete OpenAPI/Swagger specification** with request/response schemas
- **Endpoints** for:
  - Authentication (register, login, token refresh)
  - User profile management
  - Credit score and account information
  - Dispute tracking and management
  - Automation rule configuration
- **Rate limiting** for security
- **Pagination and filtering** on list endpoints
- **Comprehensive documentation** with examples

### Security Features
- Bcrypt password hashing (never store plain text)
- Account lockout after failed login attempts
- CSRF protection on all forms
- Security headers on all responses
- Input validation and sanitization
- SQL injection prevention
- XSS prevention

## 📖 Documentation

- **[API Documentation (Swagger UI)](http://localhost:5000/api/docs)** - Interactive API explorer (when running locally)
- **[API Reference Guide](docs/API.md)** - Complete REST API reference with examples
- **[Contributing Guide](CONTRIBUTING.md)** - Development guidelines
- **[Changelog](CHANGELOG.md)** - Version history and updates

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_auth.py

# Run with coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Coverage
- **test_auth.py**: 24 authentication tests
- **test_api.py**: 25 API endpoint tests  
- **test_validation.py**: 22 input validation tests
- **Total**: 70+ comprehensive tests

## 🔧 Configuration

### Environment Variables (`.env`)

```env
# Flask Configuration
SECRET_KEY=your-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-change-this
FLASK_ENV=production

# Database
DATABASE_URL=sqlite:///database/credstack.db

# Notifications (optional)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
SENDGRID_API_KEY=your-sendgrid-key
```

### Automation Configuration (`config.yaml`)

```yaml
automation:
  utilization:
    target_maximum: 10.0      # Target utilization %
    warning_threshold: 30.0   # Warning threshold
    neutralization_lead_time_days: 3
```

## 🔐 API Usage

### Interactive Documentation

The easiest way to explore the API is through the **Swagger UI** interface:

1. Start the application: `python app.py`
2. Navigate to: `http://localhost:5000/api/docs`
3. Use the "Authorize" button to authenticate with your JWT token
4. Try out endpoints directly from the browser

### Quick Example

```python
import requests

# Register and get token
response = requests.post(
    'http://localhost:5000/api/v1/auth/register',
    json={
        'email': 'user@example.com',
        'password': 'Password123',
        'name': 'John Doe'
    }
)
token = response.json()['token']

# Set up authentication header
headers = {'Authorization': f'Bearer {token}'}

# Get credit score
response = requests.get(
    'http://localhost:5000/api/v1/credit/score',
    headers=headers
)
print(response.json())
# Output: {'score': 720, 'utilization': 15.5, 'date': '2024-01-15', 'accounts_count': 3}

# Create a dispute
response = requests.post(
    'http://localhost:5000/api/v1/disputes',
    headers=headers,
    json={
        'bureau': 'Experian',
        'creditor': 'Chase Bank',
        'reason': 'Incorrect balance',
        'notes': 'Balance should be $0 after payment'
    }
)
print(response.json())
# Output: {'id': 1, 'message': 'Dispute created successfully', 'follow_up_date': '2024-01-29'}

# List automation rules
response = requests.get(
    'http://localhost:5000/api/v1/automation/rules',
    headers=headers
)
print(response.json())
```

### API Endpoints Overview

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/token/refresh` - Refresh JWT token

#### User Profile
- `GET /api/v1/users/profile` - Get current user profile
- `PUT /api/v1/users/profile` - Update user profile

#### Credit Information
- `GET /api/v1/credit/score` - Get estimated credit score
- `GET /api/v1/credit/accounts` - List credit accounts

#### Disputes
- `GET /api/v1/disputes` - List disputes (with filtering)
- `POST /api/v1/disputes` - Create new dispute
- `GET /api/v1/disputes/{id}` - Get specific dispute
- `PUT /api/v1/disputes/{id}` - Update dispute
- `DELETE /api/v1/disputes/{id}` - Delete dispute

#### Automation Rules
- `GET /api/v1/automation/rules` - List automation rules
- `POST /api/v1/automation/rules` - Create automation rule
- `GET /api/v1/automation/rules/{id}` - Get specific rule
- `PUT /api/v1/automation/rules/{id}` - Update rule
- `DELETE /api/v1/automation/rules/{id}` - Delete rule

For detailed API documentation with request/response schemas, see the **[Swagger UI](http://localhost:5000/api/docs)** or **[docs/API.md](docs/API.md)**.

## 🛠️ Technology Stack

- **Backend**: Python 3.8+ / Flask
- **Database**: SQLite (local-first architecture)
- **Authentication**: Flask-Login, bcrypt, PyJWT
- **API Documentation**: Flask-RESTX (OpenAPI/Swagger)
- **Security**: Flask-WTF (CSRF), Flask-Limiter (rate limiting)
- **Testing**: pytest, pytest-cov, pytest-mock
- **UI**: Glassmorphism design with responsive layout
- **CI/CD**: GitHub Actions

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Setting up your development environment
- Coding standards and best practices
- Submitting pull requests
- Running tests

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔒 Security

### Reporting Security Issues

Please report security vulnerabilities to: security@credstack.com

Do not open public issues for security vulnerabilities.

### Security Features

- All passwords hashed with bcrypt
- JWT tokens with expiration
- Rate limiting on authentication endpoints
- Account lockout after failed attempts
- CSRF protection
- SQL injection prevention
- XSS prevention through template auto-escaping

## 📊 Project Status

- ✅ **Production-ready** authentication system
- ✅ **Comprehensive** REST API
- ✅ **70+ tests** with CI/CD pipeline
- ✅ **Complete** documentation
- 🚧 **In progress**: Visual documentation (screenshots, demo video)

## 🙏 Acknowledgments

Built with precision engineering principles as part of the WADELABS suite.

---

**Questions?** Open an issue or check our [documentation](docs/).

*CredStack - Automating credit optimization with precision and privacy.*