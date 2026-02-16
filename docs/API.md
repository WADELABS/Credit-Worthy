# CredStack API Documentation

**Version:** 1.0  
**Base URL:** `http://localhost:5000/api`  
**Authentication:** JWT Bearer Token  
**Interactive Docs:** `http://localhost:5000/api/docs` (Swagger UI)

## 🚀 Interactive API Explorer

The easiest way to explore and test the API is through the **Swagger UI** interface:

1. Start the application: `python app.py`
2. Navigate to: **http://localhost:5000/api/docs**
3. Click "Authorize" and enter your JWT token in format: `Bearer YOUR_TOKEN`
4. Try out any endpoint directly from your browser
5. View detailed request/response schemas and examples

## Quick Start

```bash
# 1. Register
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123","name":"John Doe"}'

# 2. Login (get token)
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123"}'

# 3. Use token for authenticated requests
curl -X GET http://localhost:5000/api/v1/credit/score \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Authentication Endpoints

### POST /api/v1/auth/register
Create new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "Password123",
  "name": "John Doe"
}
```

**Password requirements:**
- At least 8 characters
- Must contain at least one letter
- Must contain at least one number

**Response (201):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 1,
  "message": "User registered successfully"
}
```

### POST /api/v1/auth/login
Authenticate user and get JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "Password123"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 1,
  "message": "Login successful"
}
```

**Error responses:**
- **401**: Invalid credentials or account locked
- **429**: Rate limit exceeded (max 10 requests/minute)

### POST /api/v1/auth/token/refresh
Refresh JWT token (requires auth).

**Headers:**
```
Authorization: Bearer YOUR_CURRENT_TOKEN
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 1,
  "message": "Token refreshed successfully"
}
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

**Query params:**
- `account_type`: Filter by type (credit_card, loan, mortgage)
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)

**Example:** `GET /api/v1/credit/accounts?account_type=credit_card&page=1`

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
    "due_date": 10,
    "last_updated": "2024-01-15T08:00:00"
  }
]
```

## Automation Endpoints

### GET /api/v1/automation/rules
List automation rules (requires auth).

**Query params:**
- `active_only` (boolean): Show only active rules
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)

**Response (200):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "automation_type": "statement_alert",
    "is_active": true,
    "configuration": "Alert 3 days before",
    "created_at": "2024-01-01T08:00:00",
    "last_run": "2024-01-14T08:00:00"
  }
]
```

### POST /api/v1/automation/rules
Create automation rule (requires auth).

**Request:**
```json
{
  "type": "dispute_tracker",
  "configuration": "Follow up every 14 days"
}
```

**Valid automation types:**
- `autopay_reminder`
- `statement_alert`
- `monthly_report`
- `weekly_scan`
- `dispute_tracker`
- `credit_builder`
- `inquiry_alert`
- `monthly_task`

**Response (201):**
```json
{
  "id": 3,
  "message": "Automation rule created successfully"
}
```

### GET /api/v1/automation/rules/{id}
Get specific automation rule (requires auth).

**Response (200):**
```json
{
  "id": 1,
  "user_id": 1,
  "automation_type": "statement_alert",
  "is_active": true,
  "configuration": "Alert 3 days before",
  "created_at": "2024-01-01T08:00:00",
  "last_run": "2024-01-14T08:00:00"
}
```

### PUT /api/v1/automation/rules/{id}
Update automation rule (requires auth).

**Request:**
```json
{
  "is_active": false,
  "configuration": "Updated configuration"
}
```

**Response (200):**
```json
{
  "message": "Automation rule updated successfully"
}
```

### DELETE /api/v1/automation/rules/{id}
Delete automation rule (requires auth).

**Response (200):**
```json
{
  "message": "Automation rule deleted successfully"
}
```

## Dispute Endpoints

### GET /api/v1/disputes
List disputes (requires auth).

**Query params:**
- `status`: Filter by status (pending, in_progress, resolved, rejected)
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)

**Example:** `GET /api/v1/disputes?status=pending&page=1&per_page=10`

**Response (200):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "bureau": "Experian",
    "account_name": "Chase Credit Card",
    "creditor": "ABC Bank",
    "reason": "Incorrect balance",
    "dispute_date": "2024-01-10",
    "date_filed": "2024-01-10",
    "follow_up_date": "2024-01-24",
    "date_resolved": null,
    "status": "pending",
    "outcome": null,
    "notes": "Balance should be $0",
    "created_at": "2024-01-10T10:00:00"
  }
]
```

### POST /api/v1/disputes
Create dispute (requires auth).

**Request:**
```json
{
  "bureau": "TransUnion",
  "account_name": "Credit Card",
  "creditor": "XYZ Credit Card",
  "reason": "Account not mine",
  "notes": "Never opened this account"
}
```

**Valid bureaus:** Experian, Equifax, TransUnion

**Response (201):**
```json
{
  "id": 2,
  "message": "Dispute created successfully",
  "follow_up_date": "2024-01-29"
}
```

### GET /api/v1/disputes/{id}
Get dispute details (requires auth).

**Response (200):**
```json
{
  "id": 1,
  "user_id": 1,
  "bureau": "Experian",
  "account_name": "Chase Credit Card",
  "creditor": "ABC Bank",
  "reason": "Incorrect balance",
  "dispute_date": "2024-01-10",
  "date_filed": "2024-01-10",
  "follow_up_date": "2024-01-24",
  "date_resolved": null,
  "status": "pending",
  "outcome": null,
  "notes": "Balance should be $0",
  "created_at": "2024-01-10T10:00:00"
}
```

### PUT /api/v1/disputes/{id}
Update dispute (requires auth).

**Request:**
```json
{
  "status": "resolved",
  "outcome": "Removed from report",
  "notes": "Bureau confirmed removal"
}
```

**Valid statuses:** pending, in_progress, resolved, rejected

**Response (200):**
```json
{
  "message": "Dispute updated successfully"
}
```

### DELETE /api/v1/disputes/{id}
Delete dispute (requires auth).

**Response (200):**
```json
{
  "message": "Dispute deleted successfully"
}
```

## User Profile Endpoints

### GET /api/v1/users/profile
Get user profile (requires auth).

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+15551234567",
  "notification_preference": "email",
  "automation_level": "basic",
  "created_at": "2024-01-01T08:00:00",
  "last_login": "2024-01-15T10:30:00"
}
```

### PUT /api/v1/users/profile
Update profile (requires auth).

**Request:**
```json
{
  "name": "Jane Doe",
  "phone": "+15559876543",
  "notification_preference": "sms"
}
```

**Valid notification preferences:**
- `email` - Email only
- `sms` - SMS only
- `both` - Email and SMS
- `calendar` - Calendar integration

**Response (200):**
```json
{
  "message": "Profile updated successfully"
}
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
    'http://localhost:5000/api/v1/auth/login',
    json={'email': 'user@example.com', 'password': 'Password123'}
)
token = response.json()['token']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}

# Get credit score
response = requests.get(
    'http://localhost:5000/api/v1/credit/score',
    headers=headers
)
print(response.json())

# Create a dispute
response = requests.post(
    'http://localhost:5000/api/v1/disputes',
    headers=headers,
    json={
        'bureau': 'Experian',
        'creditor': 'Chase Bank',
        'reason': 'Incorrect balance',
        'notes': 'Balance should be $0'
    }
)
print(response.json())

# List automation rules with pagination
response = requests.get(
    'http://localhost:5000/api/v1/automation/rules?page=1&per_page=10',
    headers=headers
)
print(response.json())
```

## JavaScript Example

```javascript
// Login
const loginResponse = await fetch('http://localhost:5000/api/v1/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'Password123'
  })
});
const {token} = await loginResponse.json();

// Make authenticated request
const headers = {'Authorization': `Bearer ${token}`};

// Get credit score
const scoreResponse = await fetch('http://localhost:5000/api/v1/credit/score', {
  headers
});
const scoreData = await scoreResponse.json();
console.log(scoreData);

// Create a dispute
const disputeResponse = await fetch('http://localhost:5000/api/v1/disputes', {
  method: 'POST',
  headers: {
    ...headers,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    bureau: 'Experian',
    creditor: 'Chase Bank',
    reason: 'Incorrect balance',
    notes: 'Balance should be $0'
  })
});
const disputeData = await disputeResponse.json();
console.log(disputeData);
```

---

**Last Updated:** 2024-02-15  
**Support:** https://github.com/WADELABS/Credit-Worthy/issues
