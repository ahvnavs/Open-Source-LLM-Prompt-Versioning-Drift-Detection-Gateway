# Contributing to Prompt Drift Gateway

We welcome contributions to make this the industry standard for Open-Source LLM Gateways (on par with Kubernetes or Trivy).

## Development Flow

1. Fork the repository.
2. Create your feature branch (`git checkout -b feat/amazing-feature`).
3. Ensure the entire stack builds cleanly (`docker compose up -d --build`).
4. Commit your changes (`git commit -m 'feat: add amazing feature'`).
5. Push to the branch (`git push origin feat/amazing-feature`).
6. Open a Pull Request.

## Rules of the Master Node

- **No Host Dependencies:** Everything must run in Docker.
- **Strict Typing:** Python code must use Pydantic V2. TypeScript must be fully typed.
- **Statelessness:** The gateway must remain 100% stateless. State belongs in the database or Redis.
