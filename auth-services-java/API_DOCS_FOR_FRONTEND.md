# StockSense Authentication Service - Frontend API Contract

This backend microservice handles all authentication, user identity, OTP password reset lifecycle, and session management for the StockSense Inventory Management System.

All requests accept and return `application/json`.

**Base URL**: `http://localhost:8081/api/v1/auth`

---

## 1. Sign Up (Register)

Create a new user account. Upon successful signup, tokens and user details are returned along with the target Inventory Dashboard URL.

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
*Password requirements: Minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special symbol.*

### Response (201 Created):
```json
{
  "success": true,
  "message": "Account registered successfully.",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "4x9Abc...78==",
    "tokenType": "Bearer",
    "expiresIn": 900,
    "redirectUrl": "http://localhost:8000/dashboard",
    "user": {
      "id": 1,
      "username": "warehouse_staff",
      "email": "staff@stocksense.com",
      "fullName": "Alex Mercer"
    }
  },
  "timestamp": "2026-09-26T12:00:00Z"
}
```

---

## 2. Sign In (Login)

Authenticate with either username or email.

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

### Response (200 OK):
```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "4x9Abc...78==",
    "tokenType": "Bearer",
    "expiresIn": 900,
    "redirectUrl": "http://localhost:8000/dashboard",
    "user": {
      "id": 1,
      "username": "warehouse_staff",
      "email": "staff@stocksense.com",
      "fullName": "Alex Mercer"
    }
  },
  "timestamp": "2026-09-26T12:00:00Z"
}
```

> **Frontend Redirection**: Upon receiving `200 OK`, store `accessToken` (e.g. in Memory or Secure Storage) and redirect the user's browser to `data.redirectUrl` (default: `http://localhost:8000/dashboard`).

### Brute Force Protection:
- 5 consecutive failed login attempts will lock the account for 15 minutes.
- The user can unlock their account immediately by performing an OTP-based password reset.

---

## 3. OTP-Based Password Reset (3-Step Flow)

### Step 3.1: Request OTP
Dispatches a 6-digit numeric OTP to the user's email address.

- **URL**: `/forgot-password`
- **Method**: `POST`
- **Public**: Yes

```json
{
  "email": "staff@stocksense.com"
}
```

#### Response (200 OK):
```json
{
  "success": true,
  "message": "OTP has been sent to your registered email address.",
  "data": null,
  "timestamp": "2026-09-26T12:00:00Z"
}
```
*(Rate limit: 60-second cooldown between consecutive OTP requests for the same email).*

---

### Step 3.2: Verify OTP
The user enters the 6-digit OTP code received in email. The server returns a one-time `resetToken` (valid for 5 minutes).

- **URL**: `/verify-otp`
- **Method**: `POST`
- **Public**: Yes

```json
{
  "email": "staff@stocksense.com",
  "otp": "535057"
}
```

#### Response (200 OK):
```json
{
  "success": true,
  "message": "OTP verified successfully. You may now reset your password.",
  "data": {
    "resetToken": "a3f89e4c8b21...982a",
    "email": "staff@stocksense.com"
  },
  "timestamp": "2026-09-26T12:00:00Z"
}
```
*(Security policy: Max 3 failed attempts before OTP is permanently revoked).*

---

### Step 3.3: Set New Password
Submit the new password along with the `resetToken`.

- **URL**: `/reset-password`
- **Method**: `POST`
- **Public**: Yes

```json
{
  "email": "staff@stocksense.com",
  "resetToken": "a3f89e4c8b21...982a",
  "newPassword": "NewPassword123!"
}
```

#### Response (200 OK):
```json
{
  "success": true,
  "message": "Password reset successfully. Please log in with your new password.",
  "data": null,
  "timestamp": "2026-09-26T12:00:00Z"
}
```
*(All active refresh tokens across all sessions are automatically revoked).*

---

## 4. Refresh Token (Token Rotation)

Exchange an existing refresh token for a fresh short-lived access token and a newly rotated refresh token.

- **URL**: `/refresh`
- **Method**: `POST`
- **Public**: Yes

```json
{
  "refreshToken": "4x9Abc...78=="
}
```

#### Response (200 OK):
```json
{
  "success": true,
  "message": "Token refreshed successfully.",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "newRotatedToken...==",
    "tokenType": "Bearer",
    "expiresIn": 900,
    "redirectUrl": "http://localhost:8000/dashboard",
    "user": { ... }
  }
}
```

---

## 5. Logout

- **URL**: `/logout`
- **Method**: `POST`
- **Public**: Yes

```json
{
  "refreshToken": "newRotatedToken...=="
}
```

---

## 6. Current User Profile

- **URL**: `/me`
- **Method**: `GET`
- **Header**: `Authorization: Bearer <accessToken>`

#### Response (200 OK):
```json
{
  "success": true,
  "message": "Profile retrieved.",
  "data": {
    "id": 1,
    "username": "warehouse_staff",
    "email": "staff@stocksense.com",
    "fullName": "Alex Mercer"
  }
}
```

---

## Standard Error Format

All error responses return structured JSON:

```json
{
  "success": false,
  "message": "Validation failed",
  "data": {
    "email": "Email must be valid",
    "password": "Password must contain at least 8 characters..."
  },
  "timestamp": "2026-09-26T12:00:00Z"
}
```
