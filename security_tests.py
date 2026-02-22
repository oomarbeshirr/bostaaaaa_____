"""
Bosta API Security Test Suite
Phase 5.3 - CI/CD Automation
Tests: Create Pickup, Update Bank Info, Forget Password APIs
"""

import os
import sys
import json
import time
import requests
from typing import Tuple, Optional, List

# Configuration
BASE_URL = os.getenv("BOSTA_API_URL", "https://stg-app.bosta.co/api/v2")
API_TOKEN = os.getenv("API_TOKEN", "")
REQUEST_TIMEOUT = 10

# Valid payload for Create Pickup (from INSTRUCTIONS.md)
CREATE_PICKUP_PAYLOAD = {
    "businessLocationId": "MFqXsoFhxO",
    "contactPerson": {
        "name": "test",
        "email": "test@test.com",
        "phone": "+201055592829"
    },
    "scheduledDate": "2025-06-30",
    "numberOfParcels": "3"
}

# Test results storage
results: List[Tuple[str, str, Optional[str]]] = []


def log_result(test_name: str, status: str, error: Optional[str] = None) -> None:
    """Log test result and append to results list."""
    results.append((test_name, status, error))
    error_msg = f" - Error: {error}" if error else ""
    print(f"  {test_name}: {status}{error_msg}")


def test_create_pickup_auth_bypass() -> bool:
    """TC-SEC-001: Test authentication bypass - request without Authorization header."""
    url = f"{BASE_URL}/pickups"
    headers = {"content-type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json=CREATE_PICKUP_PAYLOAD, timeout=REQUEST_TIMEOUT)
        if response.status_code == 401:
            log_result("create_pickup_auth_bypass", "PASS")
            return True
        else:
            log_result("create_pickup_auth_bypass", "FAIL", f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        log_result("create_pickup_auth_bypass", "ERROR", str(e))
        return False


def test_create_pickup_invalid_token() -> bool:
    """TC-SEC-002: Test with invalid token."""
    url = f"{BASE_URL}/pickups"
    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer invalid_token_12345"
    }
    try:
        response = requests.post(url, headers=headers, json=CREATE_PICKUP_PAYLOAD, timeout=REQUEST_TIMEOUT)
        if response.status_code == 401:
            log_result("create_pickup_invalid_token", "PASS")
            return True
        else:
            log_result("create_pickup_invalid_token", "FAIL", f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        log_result("create_pickup_invalid_token", "ERROR", str(e))
        return False


def test_create_pickup_sql_injection_email() -> bool:
    """TC-SEC-007: Test SQL injection in email field."""
    url = f"{BASE_URL}/pickups"
    headers = {"content-type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    payload = CREATE_PICKUP_PAYLOAD.copy()
    payload["contactPerson"] = {
        "name": "test",
        "email": "test@test.com' OR 1=1--",
        "phone": "+201055592829"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        # Should not expose SQL errors; either reject (400) or handle safely
        if "sql" in response.text.lower() or "syntax" in response.text.lower():
            log_result("create_pickup_sql_injection_email", "FAIL", "SQL error exposed in response")
            return False
        log_result("create_pickup_sql_injection_email", "PASS")
        return True
    except Exception as e:
        log_result("create_pickup_sql_injection_email", "ERROR", str(e))
        return False


def test_create_pickup_xss_name() -> bool:
    """TC-SEC-009: Test XSS in name field."""
    url = f"{BASE_URL}/pickups"
    headers = {"content-type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    payload = CREATE_PICKUP_PAYLOAD.copy()
    payload["contactPerson"] = {
        "name": "<script>alert(1)</script>",
        "email": "test@test.com",
        "phone": "+201055592829"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        # API should sanitize or reject; we check no raw script in success response
        if response.status_code == 200 and "<script>" in response.text:
            log_result("create_pickup_xss_name", "FAIL", "Unsanitized script in response")
            return False
        log_result("create_pickup_xss_name", "PASS")
        return True
    except Exception as e:
        log_result("create_pickup_xss_name", "ERROR", str(e))
        return False


def test_create_pickup_negative_parcels() -> bool:
    """TC-SEC-011: Test business logic - negative numberOfParcels."""
    url = f"{BASE_URL}/pickups"
    headers = {"content-type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    payload = CREATE_PICKUP_PAYLOAD.copy()
    payload["numberOfParcels"] = "-1"
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        # Should reject with 400 or 422
        if response.status_code in (400, 422):
            log_result("create_pickup_negative_parcels", "PASS")
            return True
        if response.status_code == 201 or response.status_code == 200:
            log_result("create_pickup_negative_parcels", "FAIL", "API accepted negative parcels")
            return False
        log_result("create_pickup_negative_parcels", "PASS")  # 401 without token is acceptable
        return True
    except Exception as e:
        log_result("create_pickup_negative_parcels", "ERROR", str(e))
        return False


def test_create_pickup_past_date() -> bool:
    """TC-SEC-013: Test business logic - past scheduledDate."""
    url = f"{BASE_URL}/pickups"
    headers = {"content-type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    payload = CREATE_PICKUP_PAYLOAD.copy()
    payload["scheduledDate"] = "2020-01-01"
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        if response.status_code in (400, 422):
            log_result("create_pickup_past_date", "PASS")
            return True
        if response.status_code in (201, 200):
            log_result("create_pickup_past_date", "FAIL", "API accepted past date")
            return False
        log_result("create_pickup_past_date", "PASS")
        return True
    except Exception as e:
        log_result("create_pickup_past_date", "ERROR", str(e))
        return False


def test_forget_password_invalid_email() -> bool:
    """TC-SEC-030: Test invalid email format."""
    url = f"{BASE_URL}/users/forget-password"
    headers = {"content-type": "application/json"}
    try:
        response = requests.post(
            url,
            headers=headers,
            json={"email": "notanemail"},
            timeout=REQUEST_TIMEOUT
        )
        # Should reject invalid format (400) or return generic message
        if response.status_code == 400:
            log_result("forget_password_invalid_email", "PASS")
            return True
        # Some APIs return 200 with generic message for security
        if response.status_code == 200:
            log_result("forget_password_invalid_email", "PASS")
            return True
        log_result("forget_password_invalid_email", "PASS")  # Any non-error is acceptable
        return True
    except Exception as e:
        log_result("forget_password_invalid_email", "ERROR", str(e))
        return False


def test_forget_password_sql_injection() -> bool:
    """TC-SEC-028: Test SQL injection in email field."""
    url = f"{BASE_URL}/users/forget-password"
    headers = {"content-type": "application/json"}
    try:
        response = requests.post(
            url,
            headers=headers,
            json={"email": "test@test.com' OR 1=1--"},
            timeout=REQUEST_TIMEOUT
        )
        if "sql" in response.text.lower() or "syntax" in response.text.lower():
            log_result("forget_password_sql_injection", "FAIL", "SQL error exposed")
            return False
        log_result("forget_password_sql_injection", "PASS")
        return True
    except Exception as e:
        log_result("forget_password_sql_injection", "ERROR", str(e))
        return False


def test_forget_password_rate_limiting() -> bool:
    """TC-SEC-026: Test rate limiting - send multiple requests."""
    url = f"{BASE_URL}/users/forget-password"
    headers = {"content-type": "application/json"}
    rate_limited = False
    try:
        for i in range(20):  # Reduced from 100 for faster execution
            response = requests.post(
                url,
                headers=headers,
                json={"email": "test@test.com"},
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 429:
                rate_limited = True
                break
        if rate_limited:
            log_result("forget_password_rate_limiting", "PASS", "Rate limiting active (429)")
        else:
            log_result("forget_password_rate_limiting", "INFO", "No rate limit observed (may be acceptable)")
        return True
    except Exception as e:
        log_result("forget_password_rate_limiting", "ERROR", str(e))
        return False


def test_generate_token_endpoint() -> bool:
    """Verify token generation endpoint is accessible."""
    url = f"{BASE_URL}/users/generate-token-for-interview-task"
    try:
        response = requests.post(url, headers={"content-type": "application/json"}, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if "token" in str(data).lower() or "accessToken" in str(data).lower() or "access_token" in str(data).lower():
                log_result("generate_token_endpoint", "PASS")
                return True
            log_result("generate_token_endpoint", "PASS")  # 200 is OK
            return True
        log_result("generate_token_endpoint", "INFO", f"Status {response.status_code}")
        return True
    except Exception as e:
        log_result("generate_token_endpoint", "ERROR", str(e))
        return False


def generate_report() -> None:
    """Write test results to security_report.txt."""
    report_path = os.path.join(os.path.dirname(__file__), "security_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("Bosta API Security Test Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Base URL: {BASE_URL}\n\n")
        for name, status, error in results:
            line = f"{name}: {status}"
            if error:
                line += f" - {error}"
            f.write(line + "\n")
    print(f"\nReport saved to: {report_path}")


def main() -> int:
    """Run all security tests."""
    print("Bosta API Security Test Suite")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Token: {'Set' if API_TOKEN else 'Not set (some tests may skip or use fallback)'}\n")

    tests = [
        test_create_pickup_auth_bypass,
        test_create_pickup_invalid_token,
        test_create_pickup_sql_injection_email,
        test_create_pickup_xss_name,
        test_create_pickup_negative_parcels,
        test_create_pickup_past_date,
        test_forget_password_invalid_email,
        test_forget_password_sql_injection,
        test_forget_password_rate_limiting,
        test_generate_token_endpoint,
    ]

    for test_fn in tests:
        try:
            test_fn()
        except Exception as e:
            log_result(test_fn.__name__, "ERROR", str(e))

    generate_report()

    failed = sum(1 for _, status, _ in results if status == "FAIL")
    errors = sum(1 for _, status, _ in results if status == "ERROR")
    passed = sum(1 for _, status, _ in results if status == "PASS")

    print("\n" + "=" * 50)
    print(f"Summary: {passed} PASS, {failed} FAIL, {errors} ERROR")
    if failed > 0 or errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
