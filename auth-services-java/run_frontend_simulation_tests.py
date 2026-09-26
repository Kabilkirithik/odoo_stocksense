#!/usr/bin/env python3
"""
StockSense Authentication Service - Comprehensive Frontend E2E Simulation Test Suite
Mimics realistic user behaviors, frontend API calls, edge cases, and cybersecurity defenses.
"""

import sys
import time
import json
import base64
import re
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8081/api/v1/auth"
LOG_FILE = "/Users/kabil/.gemini/antigravity-ide/brain/6f192dc9-0fc4-458f-a468-176df491964d/.system_generated/tasks/task-553.log"

# ANSI Terminal Styling
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

tests_passed = 0
tests_failed = 0


def log_test(title: str, success: bool, details: str = ""):
    global tests_passed, tests_failed
    symbol = f"{GREEN}✔ PASS{RESET}" if success else f"{RED}✘ FAIL{RESET}"
    if success:
        tests_passed += 1
    else:
        tests_failed += 1
    print(f"[{symbol}] {BOLD}{title}{RESET}")
    if details:
        print(f"       {details}")


def make_request(method: str, endpoint: str, payload: dict = None, token: str = None) -> tuple:
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            return status, body
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {"error": str(e)}
        return status, body
    except Exception as e:
        return 0, {"error": str(e)}


def extract_otp_from_log(email: str) -> str:
    """Reads the latest OTP dispatched to the specified email from service logs."""
    try:
        with open(LOG_FILE, "r") as f:
            content = f.read()
        # Find all occurrences of OTP notifications
        pattern = re.compile(rf"\[EMAIL OTP NOTIFICATION\] To: {re.escape(email)}[\s\S]*?Your StockSense verification code is: (\d{{6}})")
        matches = pattern.findall(content)
        if matches:
            return matches[-1]
    except Exception as e:
        print(f"Warning: could not read OTP log: {e}")
    return None


def run_all_tests():
    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}{CYAN}   StockSense Auth Service - Frontend Simulation & Security Test Suite   {RESET}")
    print(f"{BOLD}{CYAN}   Target: {BASE_URL}                                               {RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")

    # -------------------------------------------------------------------------
    # TEST 1: Service Health Check
    # -------------------------------------------------------------------------
    status, body = make_request("GET", "/health")
    log_test("1. Service Health & Cryptographic Engine Probe",
             status == 200 and body.get("data", {}).get("status") == "UP",
             f"Status: {status} | Engine: {body.get('data', {}).get('securityEngine')}")

    # -------------------------------------------------------------------------
    # TEST 2: Successful User Registration
    # -------------------------------------------------------------------------
    timestamp = int(time.time())
    username = f"sarah_{timestamp}"
    email = f"sarah_{timestamp}@stocksense.com"
    password = "SecureP@ssword2026!"
    fullName = "Sarah Jenkins (Warehouse Lead)"

    reg_payload = {
        "username": username,
        "email": email,
        "password": password,
        "fullName": fullName
    }
    status, body = make_request("POST", "/register", reg_payload)
    token = body.get("data", {}).get("token")
    dashboard_url = body.get("data", {}).get("dashboardUrl")

    log_test("2. User Signup with Valid Details",
             status == 201 and token is not None,
             f"Created user: {username} | Dashboard Redirect: {dashboard_url}")

    # -------------------------------------------------------------------------
    # TEST 3: Duplicate Registration Defense
    # -------------------------------------------------------------------------
    status, body = make_request("POST", "/register", reg_payload)
    log_test("3. Reject Duplicate Username/Email Registration",
             status == 400 and not body.get("success"),
             f"HTTP {status} -> {body.get('message')}")

    # -------------------------------------------------------------------------
    # TEST 4: Input Validation (Short Password & Malformed Email)
    # -------------------------------------------------------------------------
    invalid_payload = {
        "username": "usr",
        "email": "invalid-email-string",
        "password": "123",
        "fullName": ""
    }
    status, body = make_request("POST", "/register", invalid_payload)
    log_test("4. Input Validation (Rejection of Weak Credentials)",
             status == 400,
             f"HTTP {status} -> {body.get('message')}")

    # -------------------------------------------------------------------------
    # TEST 5: Login with Username
    # -------------------------------------------------------------------------
    login_user_payload = {
        "usernameOrEmail": username,
        "password": password
    }
    status, body = make_request("POST", "/login", login_user_payload)
    login_token = body.get("data", {}).get("token")
    log_test("5. User Login using Username",
             status == 200 and login_token is not None,
             f"Authenticated as: {body.get('data', {}).get('user', {}).get('fullName')}")

    # -------------------------------------------------------------------------
    # TEST 6: Login with Email
    # -------------------------------------------------------------------------
    login_email_payload = {
        "usernameOrEmail": email,
        "password": password
    }
    status, body = make_request("POST", "/login", login_email_payload)
    log_test("6. User Login using Email Address",
             status == 200 and body.get("data", {}).get("token") is not None,
             f"Authenticated with email: {email}")

    # -------------------------------------------------------------------------
    # TEST 7: Invalid Password & Brute-Force Remaining Counter
    # -------------------------------------------------------------------------
    bad_login_payload = {
        "usernameOrEmail": username,
        "password": "WrongPassword!"
    }
    status, body = make_request("POST", "/login", bad_login_payload)
    log_test("7. Bad Password Rejection & Attempt Counter",
             status == 401 and "remaining" in body.get("message", "").lower(),
             f"HTTP {status} -> {body.get('message')}")

    # -------------------------------------------------------------------------
    # TEST 8: Authenticated Profile Retrieval (/me)
    # -------------------------------------------------------------------------
    status, body = make_request("GET", "/me", token=token)
    profile = body.get("data", {})
    log_test("8. Access Protected Route (/me) with Bearer Token",
             status == 200 and profile.get("username") == username,
             f"Profile: ID={profile.get('id')} | Email={profile.get('email')}")

    # -------------------------------------------------------------------------
    # TEST 9: Unauthenticated Route Access (Missing Token)
    # -------------------------------------------------------------------------
    status, body = make_request("GET", "/me")
    log_test("9. Reject Unauthorized Route Access (No Token)",
             status in [401, 403],
             f"HTTP {status} Access Denied as expected")

    # -------------------------------------------------------------------------
    # TEST 10: Forged Signature Token Rejection
    # -------------------------------------------------------------------------
    tampered_token = token[:-5] + "XXXXX"
    status, body = make_request("GET", "/me", token=tampered_token)
    log_test("10. Reject Cryptographically Tampered JWT Token",
             status in [401, 403],
             f"HTTP {status} Tampered signature was immediately rejected")

    # -------------------------------------------------------------------------
    # TEST 11: "alg": "none" Forged Token Attack Defense
    # -------------------------------------------------------------------------
    fake_header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
    fake_payload = base64.urlsafe_b64encode(b'{"sub":"1","username":"admin","exp":9999999999}').decode().rstrip("=")
    none_alg_token = f"{fake_header}.{fake_payload}."
    status, body = make_request("GET", "/me", token=none_alg_token)
    log_test("11. Neutralize 'alg': 'none' JWT Signature Bypass Attack",
             status in [401, 403],
             f"HTTP {status} 'none' algorithm token blocked")

    # -------------------------------------------------------------------------
    # TEST 12: Python Backend Token Validation Endpoint (/validate)
    # -------------------------------------------------------------------------
    status, body = make_request("POST", "/validate", {"token": token})
    log_test("12. Remote Token Introspection for Python Inventory Backend",
             status == 200 and body.get("valid") is True,
             f"Validated user '{body.get('username')}' (Valid: {body.get('valid')})")

    # -------------------------------------------------------------------------
    # TEST 13: Password Reset Flow (OTP Dispatch)
    # -------------------------------------------------------------------------
    forgot_payload = {"email": email}
    status, body = make_request("POST", "/forgot-password", forgot_payload)
    log_test("13a. Request Password Reset OTP",
             status == 200,
             f"HTTP {status} -> {body.get('message')}")

    # -------------------------------------------------------------------------
    # TEST 13b: User Enumeration Prevention on Non-Existent Email
    # -------------------------------------------------------------------------
    status_fake, body_fake = make_request("POST", "/forgot-password", {"email": "nonexistent@test.com"})
    log_test("13b. User Enumeration Defense (Identical Generic Response)",
             status_fake == 200 and body_fake.get("message") == body.get("message"),
             "Non-existent email received exact same response")

    # -------------------------------------------------------------------------
    # TEST 13c: Verify with Invalid OTP (Failed Attempt Counter)
    # -------------------------------------------------------------------------
    bad_otp_payload = {"email": email, "otp": "000000"}
    status, body = make_request("POST", "/verify-otp", bad_otp_payload)
    log_test("13c. Reject False OTP & Decrement Remaining Attempts",
             status == 400 and "attempt(s) remaining" in body.get("message", "").lower(),
             f"HTTP {status} -> {body.get('message')}")

    # -------------------------------------------------------------------------
    # TEST 13d: Successful OTP Verification & Reset Token Issuance
    # -------------------------------------------------------------------------
    valid_otp = extract_otp_from_log(email)
    if valid_otp:
        status, body = make_request("POST", "/verify-otp", {"email": email, "otp": valid_otp})
        reset_token = body.get("data", {}).get("resetToken")
        log_test("13d. Verify Valid 6-digit OTP & Issue One-Time Reset Token",
                 status == 200 and reset_token is not None,
                 f"Dispatched OTP: {valid_otp} | Issued ResetToken: {reset_token[:16]}...")

        # ---------------------------------------------------------------------
        # TEST 13e: Password Reset using Reset Token
        # ---------------------------------------------------------------------
        new_password = "BrandNewPassword2026!"
        reset_payload = {
            "email": email,
            "resetToken": reset_token,
            "newPassword": new_password
        }
        status, body = make_request("POST", "/reset-password", reset_payload)
        log_test("13e. Reset Password with One-Time Reset Token",
                 status == 200,
                 f"HTTP {status} -> {body.get('message')}")

        # ---------------------------------------------------------------------
        # TEST 13f: Verify Old Password No Longer Works
        # ---------------------------------------------------------------------
        status, body = make_request("POST", "/login", {"usernameOrEmail": username, "password": password})
        log_test("13f. Confirm Old Password is Inactive",
                 status == 401,
                 f"HTTP {status} Old password rejected")

        # ---------------------------------------------------------------------
        # TEST 13g: Verify New Password Works
        # ---------------------------------------------------------------------
        status, body = make_request("POST", "/login", {"usernameOrEmail": username, "password": new_password})
        log_test("13g. Login Successfully with Newly Reset Password",
                 status == 200 and body.get("data", {}).get("token") is not None,
                 f"HTTP {status} Logged in with new credentials")
    else:
        log_test("13d-g. OTP Workflow", False, "Could not extract OTP from log")

    # -------------------------------------------------------------------------
    # TEST 14: User Logout
    # -------------------------------------------------------------------------
    status, body = make_request("POST", "/logout", token=token)
    log_test("14. User Logout & Audit Event Recording",
             status == 200,
             f"HTTP {status} -> {body.get('message')}")

    # -------------------------------------------------------------------------
    # SUMMARY REPORT
    # -------------------------------------------------------------------------
    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}Test Execution Summary:{RESET}")
    print(f"Total Tests Run : {tests_passed + tests_failed}")
    print(f"{GREEN}Tests Passed    : {tests_passed}{RESET}")
    if tests_failed > 0:
        print(f"{RED}Tests Failed    : {tests_failed}{RESET}")
    else:
        print(f"{GREEN}All tests passed with zero errors! Service is fully operational.{RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")

    return 0 if tests_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
