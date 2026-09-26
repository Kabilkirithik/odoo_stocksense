"""
StockSense Authentication Client for Python Inventory Management Backend.

This module provides two ways to authenticate incoming requests from the frontend:
1. Fast Local JWT verification (zero network latency, sub-millisecond execution).
2. Remote Introspection via Java Auth Service (POST /api/v1/auth/validate).
"""

import os
import time
import requests
import jwt
from typing import Optional, Dict, Any


JAVA_AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8081/api/v1/auth")
JWT_SECRET = os.getenv("JWT_SECRET", "StockSenseProductionSecureSecretKeyMinimum256BitsLongForHmacSha256!")
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "stocksense-auth-service"


class StockSenseAuthClient:
    """
    Python Client for StockSense Auth Service.
    """

    def __init__(self, auth_url: str = JAVA_AUTH_SERVICE_URL, secret: str = JWT_SECRET):
        self.auth_url = auth_url.rstrip("/")
        self.secret = secret

    def verify_token_locally(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token locally using HMAC-SHA256 and shared secret.
        Zero network latency, perfect for high-throughput inventory operations.

        :param token: Bearer JWT string without 'Bearer ' prefix
        :return: Decoded claims dictionary
        :raises: jwt.PyJWTError if invalid or expired
        """
        payload = jwt.decode(
            token,
            self.secret,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["sub", "username", "email", "exp"]}
        )
        return payload

    def verify_token_remotely(self, token: str) -> Dict[str, Any]:
        """
        Validate token by calling Java Auth Service.
        Checks database lock status and current user enablement.

        :param token: Bearer JWT string without 'Bearer ' prefix
        :return: Dictionary containing user details or error
        """
        try:
            resp = requests.post(
                f"{self.auth_url}/validate",
                json={"token": token},
                headers={"Content-Type": "application/json"},
                timeout=3.0
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"valid": False, "error": resp.json().get("error", "Unauthorized")}
        except requests.RequestException as e:
            return {"valid": False, "error": f"Auth service unreachable: {str(e)}"}


# ====================================================================
# FastAPI Example Middleware / Dependency
# ====================================================================
"""
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="StockSense Inventory Backend")
security = HTTPBearer()
auth_client = StockSenseAuthClient()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        # Option 1: Fast local validation
        user = auth_client.verify_token_locally(token)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

@app.get("/api/v1/inventory/items")
def get_inventory_items(user: dict = Depends(get_current_user)):
    return {
        "status": "success",
        "authenticated_user": user["username"],
        "items": [
            {"sku": "SKU-1001", "name": "Warehouse Shelf Bracket", "quantity": 1420},
            {"sku": "SKU-1002", "name": "Barbell Bar Storage Rack", "quantity": 85}
        ]
    }
"""

# ====================================================================
# Flask Example Decorator
# ====================================================================
"""
from functools import wraps
from flask import Flask, request, jsonify, g

flask_app = Flask(__name__)
auth_client = StockSenseAuthClient()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        
        token = auth_header.split(" ")[1]
        try:
            user = auth_client.verify_token_locally(token)
            g.current_user = user
        except Exception as e:
            return jsonify({"error": f"Authentication failed: {str(e)}"}), 401
        return f(*args, **kwargs)
    return decorated_function
"""
