import os
import sys
import time
import requests
from typing import Tuple, Optional, List

# --- Configuration ---
BASE_URL = os.getenv("BOSTA_API_URL", "https://stg-app.bosta.co/api/v2")
API_TOKEN = os.getenv("API_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6InVydmIxOWNKT0E4M044eHY2d0lzUCIsInJvbGVzIjpbIkJVU0lORVNTX0FETUlOIl0sImJ1c2luZXNzQWRtaW5JbmZvIjp7ImJ1c2luZXNzSWQiOiI2U2xuRmpodjVPRWFESWFBZWVjdGciLCJidXNpbmVzc05hbWUiOiJ0ZXN0IGNvbXBhbnkgbmFtZSJ9LCJlbWFpbCI6ImFtaXJhLm1vc2ErOTkxQGJvc3RhLmNvIiwicGhvbmUiOiIrMjAxMDU1NTkyODI5IiwiY291bnRyeSI6eyJfaWQiOiI2MGU0NDgyYzdjYjdkNGJjNDg0OWM0ZDUiLCJuYW1lIjoiRWd5cHQiLCJuYW1lQXIiOiLZhdi12LEiLCJjb2RlIjoiRUcifSwidG9rZW5UeXBlIjoiQUNDRVNTIiwidG9rZW5WZXJzaW9uIjoiVjIiLCJzZXNzaW9uSWQiOiIwMUtKM0dCNkQyNFY0WFc2UkdZRUFRUTFZWCIsImlhdCI6MTc3MTc5MzM3NiwiZXhwIjoxNzczMDAyOTc2fQ.EgVBrYV65HA9IgNydCH3XcgKSkuPJMzB4BZ28-7hpR0")
REQUEST_TIMEOUT = 10
results: List[Tuple[str, str, str, Optional[str]]] = []

def log_result(tc_id: str, category: str, status: str, error: Optional[str] = None) -> None:
    results.append((tc_id, category, status, error))
    color = "\033[92m" if status == "PASS" else "\033[91m"
    reset = "\033[0m"
    print(f"[{tc_id}] {category}: {color}{status}{reset} {f'({error})' if error else ''}")

# --- 1. Create Pickup Tests ---
def test_create_pickup_suite():
    url = f"{BASE_URL}/pickups"
    headers = {"Content-Type": "application/json", "Authorization": API_TOKEN}
    payload = {
        "businessLocationId": "MFqXsoFhxO",
        "contactPerson": {"name": "test", "email": "test@bosta.co", "phone": "+201055592829"},
        "scheduledDate": "2025-06-30", "numberOfParcels": "3"
    }

    # TC-SEC-001: No Auth
    resp = requests.post(url, json=payload)
    log_result("TC-SEC-001", "Pickup Auth", "PASS" if resp.status_code == 401 else "FAIL")

    # TC-SEC-007: SQL Injection in Email
    malicious_payload = payload.copy()
    malicious_payload["contactPerson"]["email"] = "test@test.com' OR 1=1--"
    resp = requests.post(url, json=malicious_payload, headers=headers)
    log_result("TC-SEC-007", "Pickup SQLi", "PASS" if "sql" not in resp.text.lower() else "FAIL")

    # TC-SEC-011: Negative Parcels
    bad_logic_payload = payload.copy()
    bad_logic_payload["numberOfParcels"] = -1
    resp = requests.post(url, json=bad_logic_payload, headers=headers)
    log_result("TC-SEC-011", "Pickup Logic", "PASS" if resp.status_code in [400, 422] else "FAIL", "Accepted negative value")

# --- 2. Update Bank Info Tests ---
def test_bank_info_suite():
    url = f"{BASE_URL}/businesses/add-bank-info"
    headers = {"Content-Type": "application/json", "Authorization": API_TOKEN}
    
    # TC-SEC-021: OTP Bypass (Null/Empty)
    payload = {
        "bankInfo": {"beneficiaryName": "Hacker", "bankName": "NBG", "ibanNumber": "EG123", "accountNumber": "123"},
        "paymentInfoOtp": None
    }
    resp = requests.post(url, json=payload, headers=headers)
    log_result("TC-SEC-021", "Bank OTP", "PASS" if resp.status_code != 200 else "FAIL", "Bypassed with null OTP")

    # TC-SEC-023: XSS in beneficiaryName
    payload["bankInfo"]["beneficiaryName"] = "<script>alert(1)</script>"
    payload["paymentInfoOtp"] = "123456"
    resp = requests.post(url, json=payload, headers=headers)
    log_result("TC-SEC-023", "Bank XSS", "PASS" if "<script>" not in resp.text else "FAIL")

# --- 3. Forget Password Tests ---
def test_forget_password_suite():
    url = f"{BASE_URL}/users/forget-password"
    
    # TC-SEC-026: Rate Limiting
    print("  Testing Rate Limiting (TC-SEC-026)... please wait.")
    limited = False
    for _ in range(15):
        resp = requests.post(url, json={"email": "test@bosta.co"})
        if resp.status_code == 429:
            limited = True
            break
    log_result("TC-SEC-026", "Forget Password Rate Limit", "PASS" if limited else "FAIL", "No rate limiting (429) detected")

    # TC-SEC-030: Invalid Email Format
    resp = requests.post(url, json={"email": "not_an_email"})
    log_result("TC-SEC-030", "Forget Password Format", "PASS" if resp.status_code == 400 else "FAIL")

# --- Report Generation ---
def generate_final_report():
    with open("security_assessment_report.txt", "w") as f:
        f.write("BOSTA API SECURITY ASSESSMENT REPORT\n")
        f.write("="*40 + "\n")
        for tc_id, cat, status, err in results:
            f.write(f"[{tc_id}] {cat}: {status} {f' - {err}' if err else ''}\n")
    print(f"\n[+] Report generated: security_assessment_report.txt")

def main():
    print("Starting Automated Security Assessment...")
    test_create_pickup_suite()
    test_bank_info_suite()
    test_forget_password_suite()
    generate_final_report()
    
    if any(r[2] == "FAIL" for r in results):
        sys.exit(1)

if __name__ == "__main__":
    main()
