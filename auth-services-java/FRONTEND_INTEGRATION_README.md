# Frontend Integration Guide for StockSense Authentication

Welcome! This guide explains how to connect your **JavaScript / TypeScript frontend** (React, Vue, Vite, Next.js, or Vanilla JS) with the **Java Spring Boot Authentication Microservice**.

---

## 🚀 Quick Reference

- **Auth Service Base URL**: `http://localhost:8081/api/v1/auth`
- **Python Inventory Backend URL**: `http://localhost:8000` (or `http://localhost:5000`)
- **Ready-to-use JS Module**: [`frontend-integration/authService.js`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/frontend-integration/authService.js)

---

## 📦 Option A: Use the Drop-in JavaScript Helper (`authService.js`)

Copy [`authService.js`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/frontend-integration/authService.js) into your frontend `src/services/` or `src/utils/` folder:

```javascript
import StockSenseAuth from './services/authService';

// 1. Sign Up
const data = await StockSenseAuth.register({
  username: "warehouse_alex",
  email: "alex@stocksense.com",
  password: "Password123@",
  fullName: "Alex Mercer"
});
// Automatically saves tokens and returns data.redirectUrl!
window.location.href = data.redirectUrl; // Redirect to Inventory Dashboard

// 2. Sign In
const loginData = await StockSenseAuth.login({
  usernameOrEmail: "warehouse_alex",
  password: "Password123@"
});
window.location.href = loginData.redirectUrl; // Redirect to Inventory Dashboard

// 3. Make an authenticated call to the Python Inventory Backend
const response = await StockSenseAuth.authFetch('http://localhost:8000/api/v1/inventory/items');
const items = await response.json();
```

---

## 🛠️ Option B: Using Direct `fetch()` or `axios`

If you prefer writing your own API service, here are the exact endpoints and request/response specifications:

### 1. Sign Up (Register)
- **POST** `http://localhost:8081/api/v1/auth/register`
- **Headers**: `Content-Type: application/json`

```javascript
async function handleSignup(username, email, password, fullName) {
  const res = await fetch('http://localhost:8081/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password, fullName })
  });
  const result = await res.json();

  if (res.ok && result.success) {
    // 1. Store tokens
    localStorage.setItem('access_token', result.data.accessToken);
    localStorage.setItem('refresh_token', result.data.refreshToken);

    // 2. Redirect to Inventory Dashboard (URL provided by backend)
    window.location.href = result.data.redirectUrl; // "http://localhost:8000/dashboard"
  } else {
    // Show error message
    alert(result.message);
  }
}
```

> **Password Policy**: Minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 number, and 1 special symbol.

---

### 2. Sign In (Login) & Dashboard Redirection
- **POST** `http://localhost:8081/api/v1/auth/login`
- **Headers**: `Content-Type: application/json`

```javascript
async function handleLogin(usernameOrEmail, password) {
  try {
    const res = await fetch('http://localhost:8081/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usernameOrEmail, password })
    });
    const result = await res.json();

    if (res.ok && result.success) {
      // 1. Store tokens securely
      localStorage.setItem('access_token', result.data.accessToken);
      localStorage.setItem('refresh_token', result.data.refreshToken);

      // 2. Redirect to Inventory Dashboard
      window.location.href = result.data.redirectUrl;
    } else {
      // Handles wrong credentials or locked account
      alert(result.message);
    }
  } catch (err) {
    alert("Unable to connect to authentication server.");
  }
}
```

> **Security Note on Account Locking**: If 5 consecutive failed login attempts occur, the service locks the account for 15 minutes (`HTTP 423 Locked`). The user can immediately unlock the account using the OTP password reset flow.

---

### 3. OTP-Based Password Reset (3 Easy Steps)

```
[User enters Email] ──► Step 1: POST /forgot-password
                                 │ (User receives 6-digit OTP in Email)
                                 ▼
[User inputs 6-digit OTP] ──► Step 2: POST /verify-otp
                                 │ (Server validates & returns resetToken)
                                 ▼
[User sets New Password] ──► Step 3: POST /reset-password
                                 │ (Password updated, redirects to login)
```

#### Step 1: Request OTP
```javascript
// POST /api/v1/auth/forgot-password
const res = await fetch('http://localhost:8081/api/v1/auth/forgot-password', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: userEmail })
});
const result = await res.json();
// Show "OTP sent to your email" and show OTP input screen
```
*(Rate limit: 60-second cooldown between requests).*

#### Step 2: Verify 6-Digit OTP
```javascript
// POST /api/v1/auth/verify-otp
const res = await fetch('http://localhost:8081/api/v1/auth/verify-otp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: userEmail,
    otp: "535057" // 6 numeric digits entered by user
  })
});
const result = await res.json();

if (res.ok && result.success) {
  const resetToken = result.data.resetToken;
  // Save resetToken in component state and show New Password screen!
}
```
*(Security policy: Max 3 attempts before OTP expires).*

#### Step 3: Set New Password
```javascript
// POST /api/v1/auth/reset-password
const res = await fetch('http://localhost:8081/api/v1/auth/reset-password', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: userEmail,
    resetToken: resetToken,       // From Step 2
    newPassword: "NewSecurePassword123!"
  })
});
const result = await res.json();

if (res.ok && result.success) {
  alert("Password reset successfully! Please log in.");
  window.location.href = '/login';
}
```

---

### 4. Calling the Python Inventory Backend

When the frontend communicates with the Python Inventory Backend (`http://localhost:8000`), simply attach the JWT access token in the `Authorization` header:

```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/inventory/items', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

if (response.status === 401) {
  // Token has expired -> Trigger refresh token flow or redirect to /login
}
```

---

## 🌐 CORS Setup

The Java Auth Service is already configured to accept CORS requests from:
- `http://localhost:3000` (React default)
- `http://localhost:5173` (Vite / Vue default)
- `http://localhost:8000` (Python inventory backend)
- `http://localhost:5000`

If your frontend runs on a different port, set the environment variable:
```bash
export CORS_ALLOWED_ORIGINS="http://localhost:4200,http://localhost:8080"
```

---

## 📋 Standard Error Handling

All failed responses have standard structure:

```json
{
  "success": false,
  "message": "Invalid username/email or password. 4 attempt(s) remaining.",
  "data": null,
  "timestamp": "2026-09-26T12:00:00Z"
}
```

For validation errors (`HTTP 400`), `data` contains field-specific feedback:
```json
{
  "success": false,
  "message": "Validation failed",
  "data": {
    "email": "Email must be valid",
    "password": "Password must contain at least 8 characters including uppercase, lowercase, number, and special character"
  }
}
```
Display `data.email` or `data.password` directly under the respective input fields.
