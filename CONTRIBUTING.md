# Contributing to Prompt Drift Gateway

We welcome contributions from the global community. To ensure this ecosystem scales without architectural gridlock, all contributors must strictly adhere to the following engineering standards.

## 1. Architectural Compliance
This project strictly adheres to the **12-Factor App methodology**[cite: 1]. 
* **No Stateful Logic:** All services must remain stateless. State is delegated to attached resources (Redis/PostgreSQL).
* **Configuration:** Absolutely no environment-specific variables or secrets are allowed in the codebase. Utilize environment variables.

## 2. Trunk-Based Development
We utilize a Trunk-based development model[cite: 1]. 
* Branch off `main` for all features (`feat/your-feature`) and bug fixes (`bug/your-fix`).
* Ensure your commits are atomic.
* All Pull Requests must pass the Continuous Integration (CI) pipeline before merging[cite: 1]. 

## 3. Local Parity
Before submitting a Pull Request, you must verify your changes in the local Docker sandbox. 
```bash
docker-compose up --build
