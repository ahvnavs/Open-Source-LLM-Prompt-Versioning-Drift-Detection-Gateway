# Prompt Drift Gateway 🚀

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Docker Pulls](https://img.shields.io/docker/pulls/yourdockerhub/prompt-gateway.svg)](#)

The **Prompt Drift Gateway** is an open-source, ultra-fast microservice designed to version, proxy, and test LLM prompts. 

Stop hardcoding AI prompts into your application logic. Decouple your stateless business logic from your AI execution, prevent silent "prompt drift," and swap underlying LLM models without redeploying your core infrastructure.

## 🧠 Why We Built This
When underlying AI models (like GPT-4, Claude, or Google Gemma) are updated, previously working prompts begin to output malformed data. We built this gateway to act as a centralized, 12-Factor compliant proxy that versions every prompt, tracks token usage, and provides immediate rollback capabilities. 

## ⚖️ Open Source Core vs. Enterprise Cloud

We operate an **Open-Core** model. The core proxy engine is 100% open-source and free to run on your own infrastructure forever. For teams requiring zero-maintenance scaling, we offer a managed SaaS.

### **Community Edition (Open Source)**
* 🟢 Self-hosted Docker container deployment.
* 🟢 Cryptographic prompt versioning.
* 🟢 FastAPI-driven asynchronous proxy routing.
* 🟢 Local PostgreSQL/Redis state management.

### **Enterprise Cloud SaaS (Managed)**
* ☁️ **Zero-Ops Infrastructure:** Fully hosted on globally distributed AWS architecture.
* 👥 **Role-Based Access Control (RBAC):** Allow non-technical Product Managers to A/B test prompts safely.
* 📊 **Advanced Analytics:** Real-time dashboard for token cost tracking and rate-limiting per API key.
* 🔒 **Enterprise SLAs:** 99.99% uptime guarantee and priority support.

👉 **[Start your 14-day trial of Enterprise Cloud SaaS here](https://yourdomain.com/signup)**

---

## ⚡ Quickstart (Local Sandbox)

To spin up the core engine locally for testing:

1. **Clone the repository:**
   git clone [https://github.com/yourusername/prompt-drift-gateway.git](https://github.com/yourusername/prompt-drift-gateway.git)
   cd prompt-drift-gateway
2. **Deploy via Docker Compose:**
   docker-compose up --build
