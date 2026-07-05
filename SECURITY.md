# Security Policy

## Enterprise API Boundaries

The Gateway enforces a strict **Zero-Trust** policy. All endpoints (excluding Prometheus metrics) require an `X-API-Key` header.

- Prompts are bound to the `OrganizationKey` that created them.
- Cross-tenant execution is mathematically blocked at the database level.
- The Next.js dashboard uses Server Actions to prevent API keys from exposing to the client's browser.

## Reporting Vulnerabilities

If you discover a security vulnerability within Prompt Drift Gateway, please open an issue in the repository. Do not post exploitable code publicly.
