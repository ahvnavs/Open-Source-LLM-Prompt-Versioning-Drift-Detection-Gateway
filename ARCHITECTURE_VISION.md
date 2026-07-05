# OMNI & CNEB Architecture Blueprint

This repository is the physical manifestation of the **Cloud-Native Enterprise Blueprint (CNEB)** and the **OMNI Meta-Compiler Ecosystem** drafted by the Noida engineering team.

## The Problem

Modern AI integration is fragmented. Prompts live in codebases, token burn rates are invisible to finance teams, and developers are locked into expensive public APIs.

## The Solution

We decouple the "what" (the prompt) from the "how" (the execution).

1. **The Gateway (Python/FastAPI):** Acts as the immutable source of truth. Prompts are hashed via SHA-256 to prevent drift.
2. **The Execution Engine (Docker/Ollama):** AI inference is brought in-house. Llama 3.1 runs securely inside the cluster, ensuring data privacy and zero cost.
3. **The Control Plane (Next.js):** Provides a visual playground for non-technical stakeholders to test bounded contexts.
4. **The Telemetry Pipeline (Prometheus):** Every token generated is tracked and tagged by Organization, setting the foundation for future FinOps billing.
