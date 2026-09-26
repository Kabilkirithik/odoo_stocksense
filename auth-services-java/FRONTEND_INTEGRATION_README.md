# Frontend Integration Guide for StockSense Authentication

This guide demonstrates how to integrate any modern web frontend (**React, Next.js, Vite, Vue, Angular, or Vanilla JS**) with the **Java Spring Boot Authentication Microservice**.

---

## ⚡ Quick Reference

- **Auth Service Base URL**: `http://localhost:8081/api/v1/auth`
- **Inventory Backend URL**: `http://localhost:8000`
- **Drop-in JavaScript SDK**: [`frontend-integration/authService.js`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/frontend-integration/authService.js)
- **TypeScript Declarations**: [`frontend-integration/authService.d.ts`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/frontend-integration/authService.d.ts)
- **Complete REST API Docs**: [`API_DOCS_FOR_FRONTEND.md`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/API_DOCS_FOR_FRONTEND.md)

---

## 📦 Option 1: Drop-in JavaScript / TypeScript SDK (`authService.js`)

Copy [`frontend-integration/authService.js`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/frontend-integration/authService.js) into your frontend project's `src/services/` or `src/utils/` directory.

### 1. Sign Up (Register)
```javascript
import StockSenseAuth from './services/authService';

try {
  const data = await StockSenseAuth.register({
    username: "warehouse_alex",
    email: "alex@stocksense.com",
    password: "SecurePassword123!",
    fullName: "Alex Mercer"
  });

  // Automatically stores session token in localStorage!
  // Redirect to Python Inventory Dashboard:
  window.location.href = data.redirectUrl; // e.g. "http://localhost:8000/dashboard"
} catch (error) {
  console.error("Signup failed:", error.message);
}
```

### 2. Sign In (Login)
```javascript
import StockSenseAuth from './services/authService';

try {
  const data = await StockSenseAuth.login({
    usernameOrEmail: "warehouse_alex", // Accepts either username or email
    password: "SecurePassword123!"
  });

  // Automatically stores token in localStorage and redirects
  window.location.href = data.redirectUrl;
} catch (error) {
  alert(error.message); // Handles wrong credentials, remaining attempts counter, or locked accounts
}
```

### 3. Password Reset Flow (3-Step OTP)

```javascript
// Step 3.1: Request 6-digit OTP to be emailed
await StockSenseAuth.requestOtp("alex@stocksense.com");
// Show OTP entry input in UI

// Step 3.2: Verify OTP and receive temporary resetToken
const { resetToken } = await StockSenseAuth.verifyOtp("alex@stocksense.com", "123456");

// Step 3.3: Submit new password with resetToken
await StockSenseAuth.resetPassword({
  email: "alex@stocksense.com",
  resetToken: resetToken,
  newPassword: "BrandNewPassword2026!"
});
alert("Password updated! Redirecting to login...");
window.location.href = '/login';
```

### 4. Calling the Python Inventory Backend (`authFetch`)
`StockSenseAuth.authFetch` automatically attaches `Authorization: Bearer <token>` to requests and redirects to `/login` if token expires (401):

```javascript
// Automatically attaches Bearer token:
const response = await StockSenseAuth.authFetch('http://localhost:8000/api/v1/inventory/items');
const inventoryData = await response.json();
```

### 5. Session Utilities
```javascript
// Check if user is logged in
if (StockSenseAuth.isAuthenticated()) {
  const user = StockSenseAuth.getCurrentUser();
  console.log("Logged in as:", user.fullName);
}

// Log out
await StockSenseAuth.logout();
window.location.href = '/login';
```

---

## 🛠️ Option 2: Direct `fetch` / `axios` Integration

If building custom API wrappers without the SDK:

### Login Example:
```javascript
async function handleLogin(usernameOrEmail, password) {
  const response = await fetch('http://localhost:8081/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ usernameOrEmail, password })
  });
  const result = await response.json();

  if (response.ok && result.success) {
    // 1. Store token
    localStorage.setItem('stocksense_token', result.data.token);
    localStorage.setItem('stocksense_user', JSON.stringify(result.data.user));

    // 2. Redirect to Inventory Dashboard
    window.location.href = result.data.dashboardUrl;
  } else {
    alert(result.message);
  }
}
```

---

## 🌐 Configuring Base URLs via Environment Variables

The SDK automatically detects your frontend environment:

| Frontend Framework | Environment Variable File (`.env`) | Variable Name |
| :--- | :--- | :--- |
| **Vite** / Vue | `.env` / `.env.local` | `VITE_AUTH_URL=http://localhost:8081/api/v1/auth` |
| **Next.js** | `.env.local` | `NEXT_PUBLIC_AUTH_URL=http://localhost:8081/api/v1/auth` |
| **Create React App** | `.env` | `REACT_APP_AUTH_URL=http://localhost:8081/api/v1/auth` |
| **Vanilla JS** | Global object | `window.__STOCKSENSE_AUTH_URL__ = "http://localhost:8081/api/v1/auth"` |

---

## 🛡️ Security & Account Locking
- **Brute-Force Protection**: 5 consecutive invalid login attempts temporarily lock the account for 15 minutes.
- **Instant Unlock**: Users can unlock their account immediately by completing the 3-step OTP password reset.
- **Zero Exposed Secrets**: The frontend only communicates over standard HTTP JSON with the authentication service. Database credentials and passwords are strictly hidden on the backend.
