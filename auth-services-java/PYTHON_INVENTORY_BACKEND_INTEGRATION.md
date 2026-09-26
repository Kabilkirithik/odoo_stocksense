# StockSense Python Inventory Backend Integration Guide

This guide describes how the Python Inventory Management Backend interacts with the Java Authentication Service.

---

## Architecture Overview

```
 [Frontend Web App]
         │
         ├── 1. POST /api/v1/auth/login ─────────────► [Java Auth Service :8081]
         │                                                     │
         │◄── 2. Returns JWT Access Token + Refresh Token ─────┘
         │
         ▼ 3. Requests with 'Authorization: Bearer <token>'
 [Python Inventory Backend :8000]
         │
         ├── Fast Local Verification (via PyJWT + Shared Secret)
         └── OR Remote Introspection (POST :8081/api/v1/auth/validate)
```

---

## 1. Local Token Verification (Recommended)

Since the Java Auth Service signs JWTs using standard RFC 7519 HMAC-SHA256, your Python backend can verify tokens **in memory with zero network calls** (< 0.1ms latency).

### Requirements:
```bash
pip install pyjwt requests
```

### Environment Variables:
```bash
JWT_SECRET="StockSenseProductionSecureSecretKeyMinimum256BitsLongForHmacSha256!"
```

### Python Code (FastAPI):
```python
import jwt
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

JWT_SECRET = "StockSenseProductionSecureSecretKeyMinimum256BitsLongForHmacSha256!"

def authenticate_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            issuer="stocksense-auth-service"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token signature")

@app.get("/api/v1/inventory/dashboard")
def dashboard(current_user: dict = Depends(authenticate_user)):
    return {
        "message": f"Welcome {current_user['name']} to the Inventory Dashboard",
        "userId": current_user["sub"],
        "email": current_user["email"]
    }
```

---

## 2. Remote Token Introspection Endpoint

If your Python backend needs to verify whether a user's account has been locked or disabled in real time, call the Java Auth Service directly:

- **Endpoint**: `POST http://localhost:8081/api/v1/auth/validate`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Success Response (`200 OK`):
```json
{
  "valid": true,
  "userId": 1,
  "username": "warehouse_staff",
  "email": "staff@stocksense.com",
  "fullName": "Alex Mercer",
  "expiresAt": 1758882900,
  "error": null
}
```

### Failure Response (`401 Unauthorized`):
```json
{
  "valid": false,
  "userId": null,
  "username": null,
  "email": null,
  "fullName": null,
  "expiresAt": null,
  "error": "Invalid, expired, or tampered token."
}
```

---

## 3. JWT Claims Specification

Every JWT issued by this service contains the following standard claims:

| Claim | Type | Description |
|---|---|---|
| `sub` | String | Unique User ID in database |
| `username` | String | Unique username |
| `email` | String | User's verified email |
| `name` | String | User's full display name |
| `iss` | String | Always `"stocksense-auth-service"` |
| `iat` | Long | Issued-at UNIX timestamp (seconds) |
| `exp` | Long | Expiration UNIX timestamp (15 minutes from issue) |
