# StockSense Authentication Service - Frontend API Contract

This backend microservice handles user registration, authentication, 3-step OTP password recovery, session verification, and token generation for the StockSense Inventory Management System.

All requests accept and return `application/json`.

**Base URL**: `http://localhost:8081/api/v1/auth`

---

## 1. Sign Up (Register)

Creates a new warehouse user account and automatically returns the JWT bearer token and redirection URL to the Python Inventory Dashboard.

- **URL**: `/register`
- **Method**: `POST`
- **Public**: Yes

### Request Body:
```json
{
  "username": "warehouse_staff",
  "email": "staff@stocksense.com",
  "password": "Password123@",
  "fullName": "Alex Mercer"
}
```
*Validation Rules:*
- `username`: 3–64 characters, unique
- `email`: Valid RFC 5322 email format, unique
- `password`: Minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 number, and 1 special symbol
- `fullName`: Required, 2–128 characters

### Response (`201 Created`):
```json
{
  "success": true,
  "message": "Account registered successfully.",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400,
    "dashboardUrl": "http://localhost:8000/dashboard",
    "user": {
      "id": 1,
      "username": "warehouse_staff",
      "email": "staff@stocksense.com",
      "fullName": "Alex Mercer",
      "createdAt": "2026-09-26T12:00:00"
    }
  },
  "timestamp": "2026-09-26T12:00:00"
}
```

---

## 2. Sign In (Login)

Authenticates user credentials (accepts either `username` or `email`).

- **URL**: `/login`
- **Method**: `POST`
- **Public**: Yes

### Request Body:
```json
{
  "usernameOrEmail": "warehouse_staff",
  "password": "Password123@"
}
```

### Response (`200 OK`):
```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400,
    "dashboardUrl": "http://localhost:8000/dashboard",
    "user": {
      "id": 1,
      "username": "warehouse_staff",
      "email": "staff@stocksense.com",
      "fullName": "Alex Mercer",
      "createdAt": "2026-09-26T12:00:00"
    }
  },
  "timestamp": "2026-09-26T12:00:00"
}
```

> **Frontend Redirection:** Upon receiving `200 OK`, store `data.token` (in `localStorage` or state) and redirect the browser to `data.dashboardUrl` (default: `http://localhost:8000/dashboard`).

### Brute-Force & Lockout Policy:
- 5 consecutive failed login attempts lock the account for 15 minutes (`HTTP 423 Locked`).
- Failed attempts decrement the remaining attempt counter returned in the error message.
- Users can unlock their account immediately by completing the OTP password reset flow.

---

## 3. OTP-Based Password Recovery (3-Step Lifecycle)

```
[User enters Email] ──► Step 1: POST /forgot-password
                                 │ (User receives 6-digit OTP code)
                                 ▼
[User inputs 6-digit OTP] ──► Step 2: POST /verify-otp
                                 │ (Server validates & returns resetToken)
                                 ▼
[User sets New Password] ──► Step 3: POST /reset-password
                                 │ (Password updated, redirects to login)
```

### Step 3.1: Request OTP (`/forgot-password`)
Dispatches a 6-digit numeric verification OTP code to the registered email address.

- **URL**: `/forgot-password`
- **Method**: `POST`
- **Public**: Yes

```json
{
  "email": "staff@stocksense.com"
}
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "OTP verification code has been dispatched to your email address.",
  "data": null,
  "timestamp": "2026-09-26T12:00:00"
}
```
*(Rate limit: 60-second cooldown between consecutive OTP requests for the same email).*

---

### Step 3.2: Verify OTP (`/verify-otp`)
The user inputs the 6-digit numeric OTP code. The server returns a one-time cryptographic `resetToken` (valid for 5 minutes).

- **URL**: `/verify-otp`
- **Method**: `POST`
- **Public**: Yes

```json
{
  "email": "staff@stocksense.com",
  "otp": "123456"
}
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "OTP verified successfully. You may now reset your password.",
  "data": {
    "resetToken": "a3f89e4c8b2167d4...982a",
    "email": "staff@stocksense.com"
  },
  "timestamp": "2026-09-26T12:00:00"
}
```
*(Security policy: Maximum 3 failed attempts before OTP is invalidated).*

---

### Step 3.3: Set New Password (`/reset-password`)
Submit the new password along with the verified `resetToken`.

- **URL**: `/reset-password`
- **Method**: `POST`
- **Public**: Yes

```json
{
  "email": "staff@stocksense.com",
  "resetToken": "a3f89e4c8b2167d4...982a",
  "newPassword": "NewSecurePassword123!"
}
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "Password reset successfully. Please log in with your new password.",
  "data": null,
  "timestamp": "2026-09-26T12:00:00"
}
```

---

## 4. Current User Profile (`/me`)

Retrieve authenticated profile information using the JWT Bearer token.

- **URL**: `/me`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <token>`

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "User profile retrieved successfully.",
  "data": {
    "id": 1,
    "username": "warehouse_staff",
    "email": "staff@stocksense.com",
    "fullName": "Alex Mercer",
    "createdAt": "2026-09-26T12:00:00"
  },
  "timestamp": "2026-09-26T12:00:00"
}
```

---

## 5. Logout (`/logout`)

Stateless logout signal. Frontend removes token from client storage.

- **URL**: `/logout`
- **Method**: `POST`
- **Public**: Yes

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "Logged out successfully.",
  "data": null,
  "timestamp": "2026-09-26T12:00:00"
}
```

---

## 6. Service Health (`/health`)

Ping to verify microservice status and operational engines.

- **URL**: `/health`
- **Method**: `GET`
- **Public**: Yes

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "StockSense Auth Service is operational.",
  "data": {
    "service": "StockSense Auth Service (Java 21 / Spring Boot)",
    "status": "UP",
    "integrationTarget": "Python Inventory Management Backend",
    "securityEngine": "HMAC-SHA256 / BCrypt(12)"
  },
  "timestamp": "2026-09-26T12:00:00"
}
```

---

## Standard Error Format

All error responses follow this predictable contract:

```json
{
  "success": false,
  "message": "Invalid credentials. 4 attempt(s) remaining.",
  "data": null,
  "timestamp": "2026-09-26T12:00:00"
}
```

For validation errors (`HTTP 400 Bad Request`), `data` provides per-field errors:
```json
{
  "success": false,
  "message": "Validation failed",
  "data": {
    "email": "Invalid email format",
    "password": "Password must be at least 8 characters"
  },
  "timestamp": "2026-09-26T12:00:00"
}
```
