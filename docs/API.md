# CredStack API Documentation

**Version:** 1.0  
**Base URL:** `http://localhost:5000/api`  
**Authentication:** JWT Bearer Token

## Quick Start

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# 2. Login (get token)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# 3. Use token for authenticated requests
curl -X GET http://localhost:5000/api/v1/credit/score \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Authentication Endpoints

### POST /api/auth/register
Create new user account.

**Request:**
```json
{"email": "user@example.com", "password": "password123", "name": "John Doe"}
```

**Response (201):**
```json
{"message": "Account created successfully", "user_id": 1, "token": "eyJ..."}
```

### POST /api/auth/login
Authenticate user.

**Request:**
```json
{"email": "user@example.com", "password": "password123"}
```

**Response (200):**
```json
{"message": "Login successful", "user_id": 1, "token": "eyJ..."}
```

### POST /api/auth/token/refresh
Refresh JWT token (requires auth).

**Response (200):**
```json
{"token": "eyJ..."}
```

### GET|POST /api/auth/api-token
Get or generate long-lived API token (requires auth).

**Response (200):**
```json
{"api_token": "xK9mP2nQ5rT8vW4yB7dF0hJ3lN6pS1uX"}
```

## Credit Data Endpoints

### GET /api/v1/credit/score
Get credit health score (requires auth).

**Response (200):**
```json
{"score": 750, "utilization": 15.5, "date": "2024-01-15", "accounts_count": 3}
```

### GET /api/v1/credit/accounts
List all credit accounts (requires auth).

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Chase Freedom",
    "account_type": "credit_card",
    "balance": 150.00,
    "credit_limit": 5000.00,
    "statement_date": 15,
    "due_date": 10
  }
]
```

## Automation Endpoints

### GET /api/v1/automation/rules
List automation rules (requires auth).

**Response (200):**
```json
[
  {
    "id": 1,
    "automation_type": "statement_alert",
    "is_active": 1,
    "configuration": "Alert 3 days before",
    "last_run": "2024-01-14T08:00:00"
  }
]
```

### POST /api/v1/automation/rules
Create automation rule (requires auth).

**Request:**
```json
{"type": "dispute_tracker", "configuration": "Follow up every 14 days"}
```

**Response (201):**
```json
{"id": 3, "message": "Automation rule created"}
```

## Dispute Endpoints

### GET /api/v1/disputes
List disputes (requires auth).

**Query params:** `?status=pending|in_progress|resolved|rejected`

**Response (200):**
```json
[
  {
    "id": 1,
    "bureau": "Experian",
    "creditor": "ABC Bank",
    "reason": "Incorrect balance",
    "dispute_date": "2024-01-10",
    "status": "pending",
    "notes": "Balance should be $0"
  }
]
```

### POST /api/v1/disputes
Create dispute (requires auth).

**Request:**
```json
{
  "bureau": "TransUnion",
  "creditor": "XYZ Credit Card",
  "reason": "Account not mine",
  "notes": "Never opened this account"
}
```

**Response (201):**
```json
{"id": 2, "message": "Dispute created", "follow_up_date": "2024-01-29"}
```

### GET /api/v1/disputes/{id}
Get dispute details (requires auth).

### PUT /api/v1/disputes/{id}
Update dispute (requires auth).

**Request:**
```json
{"status": "resolved", "outcome": "Removed from report"}
```

### DELETE /api/v1/disputes/{id}
Delete dispute (requires auth).

## User Profile Endpoints

### GET /api/v1/user/profile
Get user profile (requires auth).

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+15551234567",
  "notification_preference": "email",
  "automation_level": "basic"
}
```

### PUT /api/v1/user/profile
Update profile (requires auth).

**Request:**
```json
{"name": "Jane Doe", "phone": "+15559876543", "notification_preference": "sms"}
```

## Error Responses

All errors return JSON with an `error` key:

- **400 Bad Request:** `{"error": "Email and password are required"}`
- **401 Unauthorized:** `{"error": "Authentication token is missing"}`
- **403 Forbidden:** `{"error": "Account locked until 2024-01-15 10:45"}`
- **404 Not Found:** `{"error": "Dispute not found"}`
- **429 Too Many Requests:** `{"error": "Rate limit exceeded"}`

## Rate Limiting

- **Login:** 10 requests/minute
- **Register:** 3 requests/hour
- **Other:** 200 requests/day, 50 requests/hour

## Authentication

Include JWT token in `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens expire after 24 hours. Use `/api/auth/token/refresh` to renew.

## Python Example

```python
import requests

# Login
response = requests.post(
    'http://localhost:5000/api/auth/login',
    json={'email': 'user@example.com', 'password': 'password123'}
)
token = response.json()['token']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:5000/api/v1/credit/score',
    headers=headers
)
print(response.json())
```

## JavaScript Example

```javascript
// Login
const loginResponse = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const {token} = await loginResponse.json();

// Make authenticated request
const scoreResponse = await fetch('http://localhost:5000/api/v1/credit/score', {
  headers: {'Authorization': `Bearer ${token}`}
});
const data = await scoreResponse.json();
console.log(data);
```

---

**Last Updated:** 2024-02-15  
**Support:** https://github.com/WADELABS/Credit-Worthy/issues
