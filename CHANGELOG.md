# Changelog

All notable changes to CredStack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Password-based authentication system with bcrypt hashing
- User registration with email and password
- JWT token authentication for API access
- API token generation for long-lived authentication
- Account lockout after failed login attempts
- Rate limiting on authentication endpoints
- CSRF protection with Flask-WTF
- Security headers (X-Frame-Options, HSTS, X-XSS-Protection, X-Content-Type-Options)
- Comprehensive RESTful API (v1) with the following endpoints:
  - Authentication: `/api/auth/register`, `/api/auth/login`, `/api/auth/token/refresh`, `/api/auth/api-token`
  - Credit data: `/api/v1/credit/score`, `/api/v1/credit/accounts`
  - Automation: `/api/v1/automation/rules`
  - Disputes: `/api/v1/disputes`, `/api/v1/disputes/{id}`
  - User profile: `/api/v1/user/profile`
- Enhanced disputes table with additional fields:
  - `creditor` - Name of the creditor
  - `reason` - Reason for dispute
  - `date_filed` - Date dispute was filed
  - `date_resolved` - Date dispute was resolved
  - `outcome` - Final outcome of dispute
- Database migration scripts:
  - `001_add_password_fields.py` - Adds authentication fields to users table
  - `002_enhance_disputes.py` - Enhances disputes table with new fields
- Comprehensive test suite:
  - `tests/test_auth.py` - 24 authentication tests
  - `tests/test_api.py` - 25 API endpoint tests
  - `tests/test_validation.py` - 22 input validation tests
  - Tests for SQL injection prevention
  - Tests for XSS prevention
  - Tests for data isolation between users
- API documentation (`docs/API.md`) with:
  - Complete endpoint reference
  - Request/response examples
  - Code examples in Python, JavaScript, and curl
  - Rate limiting information
  - Authentication guide
- Contributing guidelines (`CONTRIBUTING.md`)
- This changelog

### Changed
- Updated `setup.py` to create users table with authentication fields
- Updated `setup.py` to create disputes table with enhanced fields
- Modified login flow to use password authentication instead of email-only
- Updated index page to support password login
- Enhanced `.env.example` with JWT_SECRET_KEY

### Security
- All passwords are now hashed using bcrypt (never stored in plain text)
- Minimum password requirements: 8+ characters with letters and numbers
- Account lockout mechanism: Progressive lockout after 3+ failed attempts (5 min → 15 min → 30 min → 1 hour → 24 hours)
- JWT tokens expire after 24 hours
- Rate limiting on sensitive endpoints
- SQL injection prevention through parameterized queries
- XSS prevention through template auto-escaping
- CSRF protection enabled on all forms
- Security headers added to all responses

### Dependencies Added
- `flask-login` - Session management
- `flask-wtf` - CSRF protection
- `bcrypt` - Password hashing
- `pyjwt` - JWT token generation and validation
- `flask-limiter` - Rate limiting
- `pytest` - Testing framework
- `pytest-cov` - Test coverage reporting
- `pytest-mock` - Mocking support for tests

## [1.0.0] - 2024-01-01

### Added
- Initial release of CredStack
- Flask web application for credit automation
- SQLite database with tables for users, accounts, automations, reminders, and disputes
- Dashboard view showing:
  - Credit health score
  - Account list with balances and utilization
  - Active automations
  - Upcoming reminders
  - Active disputes
- Account management:
  - Add credit card accounts
  - Track balances and credit limits
  - Set statement and due dates
- Automation features:
  - Statement date alerts
  - Utilization tracking
  - Configurable lead time for alerts
- Dispute tracking:
  - File disputes with credit bureaus
  - Track dispute status
  - Set follow-up dates
- Reminder system:
  - Automated reminder generation
  - Reminder completion tracking
- Setup wizard for initial configuration
- YAML-based configuration (`config.yaml`)
- Email-only authentication (demo mode)
- Glass morphism UI design
- Local-first architecture with SQLite database

### Security
- No external API dependencies
- Local database storage only
- Data sovereignty and privacy-focused design

---

## Version History

- **[Unreleased]** - Comprehensive security and feature improvements
- **[1.0.0]** - 2024-01-01 - Initial release

---

## Migration Guide

### Upgrading to Unreleased from 1.0.0

#### Database Migration

Run the migration scripts to update your database schema:

```bash
# Add authentication fields
python migrations/001_add_password_fields.py

# Enhance disputes table
python migrations/002_enhance_disputes.py
```

#### Set Password for Existing Users

Existing users created with email-only authentication will need to set a password:

1. Log in with your email (legacy mode)
2. You'll be prompted to set a password
3. Enter and confirm your new password
4. Your account is now secured with password authentication

#### Update Environment Variables

Add the new JWT secret key to your `.env` file:

```bash
JWT_SECRET_KEY=your-jwt-secret-key-change-this-to-different-random-string
```

#### Update Dependencies

```bash
pip install -r requirements.txt
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Support

- **Issues:** https://github.com/WADELABS/Credit-Worthy/issues
- **Documentation:** See `README.md` and `docs/` folder
- **Email:** support@credstack.com
