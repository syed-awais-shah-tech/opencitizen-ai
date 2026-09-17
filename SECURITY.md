# Security Policy

OpenCitizen AI takes the security and integrity of user data, public datasets, and system infrastructure very seriously. This document outlines our security policies and procedures for reporting vulnerabilities.

## Supported Versions

As OpenCitizen AI is currently in early active development, only the latest release on the default branch (`main`) receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| `main`  | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

If you discover a potential security vulnerability in OpenCitizen AI, please report it responsibly:

1. **Do not create a public GitHub issue.**
2. Send an email to [shahsyedawais78@gmail.com](mailto:shahsyedawais78@gmail.com) with the subject line:
   `[SECURITY] Vulnerability Report - OpenCitizen AI`.
3. Include detailed information to help us reproduce and resolve the issue:
   - Type of issue (e.g., SQL injection, credential exposure, SSRF, arbitrary code execution)
   - Steps to reproduce the vulnerability
   - Proof-of-concept code, payloads, or screenshots
   - Potential impact of the vulnerability
   - Any suggested mitigations or patches

### Response Timeline

- **Initial Acknowledgement:** Within 48 hours of receipt.
- **Triage & Status Update:** Within 7 calendar days.
- **Resolution & Coordinated Disclosure:** We will work with the reporter to validate the fix before publicly disclosing details.

## Security Practices for Contributors

To keep OpenCitizen AI secure:
- **Never commit secrets:** Never commit API keys (e.g., Gemini API keys), database passwords, tokens, or credentials to the repository.
- **Use `.env` files:** Always load sensitive configuration from environment variables.
- **Dependencies:** Keep dependencies up to date and audit packages regularly.
- **Least Privilege:** Services running inside Docker or standalone processes should adhere to least privilege principles.
