# Phase 5: Security Testing Automation and CI/CD Setup Guide

## Overview

This guide covers the complete Phase 5 deliverables for Bosta API security testing automation and CI/CD integration.

---

## Deliverables Summary

| Deliverable | File | Description |
|-------------|------|-------------|
| Phase 5.1 | `Phase_5.1_Security_Test_Cases.csv` | 36 security test cases for Create Pickup, Update Bank Info, Forget Password APIs |
| Phase 5.2 | `Phase_5.2_Security_Test_Execution_Report.md` | Test execution report template with curl commands |
| Phase 5.3 | `security_tests.py` | Python automation script for security tests |
| Phase 5.3 | `.github/workflows/security-tests.yml` | GitHub Actions workflow |
| Phase 5.3 | `.gitlab-ci.yml` | GitLab CI configuration |
| Phase 5.3 | `requirements.txt` | Python dependencies |

---

## Running Security Tests Locally

### Prerequisites

- Python 3.9 or higher
- `requests` library

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or directly
pip install requests
```

### Execute Tests

```bash
# Run without token (auth bypass and unauthenticated tests)
python security_tests.py

# Run with token (full coverage including authenticated tests)
set API_TOKEN=your_token_here
python security_tests.py

# On Linux/Mac:
export API_TOKEN=your_token_here
python security_tests.py
```

### Obtain API Token

```bash
curl --location --request POST 'https://stg-app.bosta.co/api/v2/users/generate-token-for-interview-task'
```

Copy the token from the response and set it as `API_TOKEN`.

### Output

- Console: Real-time test results (PASS/FAIL/ERROR)
- `security_report.txt`: Detailed report saved in project root

---

## CI/CD Integration

### GitHub Actions

1. **Add repository secrets** (Settings → Secrets and variables → Actions):
   - `API_TOKEN`: Optional. Add if you want authenticated tests to run in CI.

2. **Add variables** (optional):
   - `BOSTA_API_URL`: Override base URL (default: `https://stg-app.bosta.co/api/v2`)

3. **Triggers**:
   - Push to `main` or `develop`
   - Pull requests to `main`
   - Daily at midnight UTC (schedule)
   - Manual via "Run workflow"

4. **Artifacts**:
   - `security-test-results`: Contains `security_report.txt`
   - `newman-api-results`: Postman/Newman results (if collection exists)

### GitLab CI

1. **Add CI/CD variables** (Settings → CI/CD → Variables):
   - `API_TOKEN`: Optional, masked
   - `BOSTA_API_URL`: Optional

2. **Pipelines** run on push to `main` or `develop`.

3. **Artifacts**:
   - `security_report.txt`
   - `newman_results.json`

---

## Running Postman Tests with Newman

Newman runs the Bosta Tracking API collection in CI. To run locally:

```bash
# Install Newman
npm install -g newman

# Run collection with environment
newman run Bosta_Tracking_API_Collection.json \
  -e Bosta_Tracking_API_Environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

---

## Security Test Cases Overview

### API #1: Create Pickup (`POST /api/v2/pickups`)

| Category | Tests |
|----------|-------|
| Authentication | No auth, invalid token, expired token |
| Input Validation | SQL injection, NoSQL injection, XSS, command injection |
| Business Logic | Negative parcels, past date, invalid format |
| Data Exposure | Response inspection |

### API #2: Update Bank Info

| Category | Tests |
|----------|-------|
| Token Security | Expired, tampered, wrong user |
| Sensitive Data | OTP bypass, SQL injection in IBAN |
| Input Validation | XSS in beneficiaryName |

### API #3: Forget Password (`POST /api/v2/users/forget-password`)

| Category | Tests |
|----------|-------|
| Rate Limiting | Rapid requests |
| Email Enumeration | Registered vs unregistered response comparison |
| Input Validation | SQL injection, XSS, invalid format |
| Token Security | Predictability, expiration, reuse |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'requests'` | Run `pip install requests` |
| Tests fail with connection error | Check network; verify `stg-app.bosta.co` is accessible |
| 401 on all authenticated tests | Set valid `API_TOKEN` from generate-token endpoint |
| Newman not found | Install: `npm install -g newman` |

---

## Notes

- Replace `[TOKEN]` placeholders in manual curl commands with actual tokens.
- Security tests are designed to verify *secure* behavior (e.g., 401 on auth bypass = PASS).
- Some tests (e.g., rate limiting) may return INFO if behavior is acceptable but not strictly enforced.
