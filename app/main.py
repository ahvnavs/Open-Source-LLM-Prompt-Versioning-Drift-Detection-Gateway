import os
import time
import datetime
import hashlib
import httpx
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, ConfigDict
from typing import Dict, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# ==========================================
# 1. 12-FACTOR CONFIGURATION
# ==========================================
# In production, this will be passed via Kubernetes secrets (e.g., postgresql://user:pass@host/db)
# For the local sandbox, it defaults to a local SQLite file.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./prompt_state.db")
DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-4-turbo")

# ==========================================
# 2. DATABASE STATE MANAGEMENT
# ==========================================
# Connect args are required for SQLite to prevent thread sharing issues in FastAPI
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PromptRecord(Base):
    """SQLAlchemy model for storing versioned prompts immutably."""
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(String, unique=True, index=True, nullable=False)
    template_text = Column(Text, nullable=False)
    version_hash = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

# Dependency to safely yield and close database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 3. OPENAPI SCHEMAS (Pydantic)
# ==========================================
class ExecuteRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    prompt_id: str
    variables: Dict[str, str] = {}
    model_override: Optional[str] = None

class Telemetry(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    token_usage: int
    latency_ms: int
    model_used: str

class ExecuteResponse(BaseModel):
    success: bool
    executed_prompt: str
    llm_response: str
    telemetry: Telemetry

class CreatePromptRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    prompt_id: str
    template_text: str

class PromptResponse(BaseModel):
    prompt_id: str
    version_hash: str
    created_at: datetime.datetime

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1/chat/completions")

# ==========================================
# 4. MICROSERVICE INITIALIZATION
# ==========================================
app = FastAPI(
    title="Prompt Drift Gateway API",
    description="The centralized microservice for versioning, proxying, and testing LLM prompts.",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    """
    Automated infrastructure initialization.
    Creates tables if they don't exist and seeds the database for local testing.
    """
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    # Seed the test prompt if the database is empty
    if not db.query(PromptRecord).filter(PromptRecord.prompt_id == "auth-system-onboarding-v2").first():
        seed_prompt = PromptRecord(
            prompt_id="auth-system-onboarding-v2",
            template_text="You are a helpful assistant. Greet {user_name}, who is a {role}.",
            version_hash="sha256-mock-hash-123"
        )
        db.add(seed_prompt)
        db.commit()
    db.close()

# ==========================================
# 4.5. ENTERPRISE OBSERVABILITY (Prometheus)
# ==========================================
REQUEST_COUNT = Counter(
    'gateway_llm_requests_total',
    'Total LLM requests processed',
    ['model_used', 'status']
)
TOKEN_COUNT = Counter(
    'gateway_llm_token_usage_total',
    'Total tokens consumed for billing',
    ['model_used']
)
REQUEST_LATENCY = Histogram(
    'gateway_llm_request_latency_seconds',
    'LLM request latency',
    ['model_used']
)

@app.get("/metrics")
async def metrics():
    """Exposes real-time telemetry to the Prometheus scraper."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ==========================================
# 5. CORE ROUTING & EXECUTION
# ==========================================
@app.post("/v1/prompts/execute", response_model=ExecuteResponse)
async def execute_prompt(request: ExecuteRequest, db: Session = Depends(get_db)):
    """
    Executes a versioned prompt by fetching the template, injecting variables,
    and proxying the request asynchronously to the live LLM provider.
    """
    start_time = time.time()

    # Step A: State Lookup
    prompt_record = db.query(PromptRecord).filter(PromptRecord.prompt_id == request.prompt_id).first()
    if not prompt_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt ID '{request.prompt_id}' not found in the gateway database."
        )

    # Step B: Template Hydration
    try:
        hydrated_prompt = prompt_record.template_text.format(**request.variables)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_request,
            detail=f"Missing required variable for prompt template: {e}"
        )

    # Step C: Model Selection Routing
    active_model = request.model_override if request.model_override else DEFAULT_MODEL

    # Step D: Live Upstream LLM Proxy
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gateway misconfiguration: Missing LLM API Key."
        )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": active_model,
        "messages": [{"role": "user", "content": hydrated_prompt}],
        "temperature": 0.7
    }

    try:
        # Utilize httpx.AsyncClient for zero-blocking I/O
        async with httpx.AsyncClient() as client:
            response = await client.post(LLM_API_BASE_URL, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            llm_data = response.json()

            # Parse standard OpenAI response schema
            actual_response_text = llm_data["choices"][0]["message"]["content"]
            actual_tokens = llm_data.get("usage", {}).get("total_tokens", 0)

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream LLM Provider Error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Failed to connect to Upstream LLM: {str(e)}"
        )

    # Step E: Telemetry & Observability Calculation
    latency_seconds = time.time() - start_time
    latency_ms = int(latency_seconds * 1000)

    # Inject into Prometheus Time-Series Database
    REQUEST_COUNT.labels(model_used=active_model, status="success").inc()
    TOKEN_COUNT.labels(model_used=active_model).inc(actual_tokens)
    REQUEST_LATENCY.labels(model_used=active_model).observe(latency_seconds)

    return ExecuteResponse(
        success=True,
        executed_prompt=hydrated_prompt,
        llm_response=actual_response_text,
        telemetry=Telemetry(
            token_usage=actual_tokens,
            latency_ms=latency_ms,
            model_used=active_model
        )
    )

@app.post("/v1/prompts", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(request: CreatePromptRequest, db: Session = Depends(get_db)):
    """
    Ingests a new prompt, assigns a cryptographic hash, and stores it immutably.
    """
    # 1. Enforce Immutability: Check if the ID already exists
    existing = db.query(PromptRecord).filter(PromptRecord.prompt_id == request.prompt_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prompt ID already exists. Immutable gateway requires unique IDs for new versions (e.g., my-prompt-v2)."
        )

    # 2. Generate Cryptographic Hash (SHA-256)
    # This guarantees that the exact state of the text is mathematically verifiable
    encoded_text = request.template_text.encode('utf-8')
    version_hash = hashlib.sha256(encoded_text).hexdigest()

    # 3. Store State
    new_prompt = PromptRecord(
        prompt_id=request.prompt_id,
        template_text=request.template_text,
        version_hash=version_hash
    )

    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)

    return PromptResponse(
        prompt_id=new_prompt.prompt_id,
        version_hash=new_prompt.version_hash,
        created_at=new_prompt.updated_at
    )

@app.get("/healthz")
async def health_check():
    """Liveness probe for Kubernetes and Dapr sidecars."""
    return {"status": "healthy", "database": "connected"}
