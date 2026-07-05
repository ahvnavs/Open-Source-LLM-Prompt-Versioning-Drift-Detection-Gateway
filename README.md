# Prompt Drift Gateway & Enterprise Dashboard

An Open-Source, zero-cost, fully containerized Enterprise SaaS platform for versioning, proxying, and testing LLM prompts.

Built strictly on the **Cloud-Native Enterprise Blueprint (CNEB)** and the **OMNI Architecture Framework**.

## Features

- **Strict Multi-Tenancy:** Cryptographically isolated prompts per organization via `X-API-Key`.
- **Zero-Cost Local AI:** 100% free Llama 3.1 inference embedded directly in the Docker cluster via Ollama. No host dependencies. No OpenAI bills.
- **12-Factor App Compliance:** Stateless architecture, decoupled infrastructure, and configuration via environment variables.
- **Enterprise Observability:** Built-in Prometheus telemetry tracking token burn rates, latency, and LLM provider health.
- **Next.js Dashboard:** Secure, server-action-driven UI for Product Managers to test prompts without touching code.

## Quickstart (The Singular Command)

Because the entire ecosystem is containerized in a monorepo, booting the SaaS takes one command:

```bash
docker compose up -d --build
