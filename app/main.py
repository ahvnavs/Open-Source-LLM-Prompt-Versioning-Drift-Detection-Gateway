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
from fastapi.security import APIKeyHeader

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./prompt_state.db")
DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL", "llama3.1")

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PromptRecord(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    organization_name = Column(String, index=True, nullable=False)
    prompt_id = Column(String, unique=True, index=True, nullable=False)
    template_text = Column(Text, nullable=False)
    version_hash = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class OrganizationKey(Base):
    __tablename__ = "organization_keys"
    id = Column(Integer, primary_key=True, index=True)
    organization_name = Column(String, unique=True, index=True, nullable=False)
    api_key_hash = Column(String, unique=True, index=True, nullable=False)
    tier = Column(String, default="standard")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_current_organization(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)):
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing 'X-API-Key' header. Enterprise Gateway access denied.")

    incoming_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    org_record = db.query(OrganizationKey).filter(OrganizationKey.api_key_hash == incoming_hash).first()

    if not org_record:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key.")
    return org_record

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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-local-ollama-dummy-key")
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "http://ollama:11434/v1/chat/completions")

app = FastAPI(title="Prompt Drift Gateway API", version="1.0.0")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    mock_key_hash = hashlib.sha256("sk-test-enterprise-key".encode('utf-8')).hexdigest()
    if not db.query(OrganizationKey).filter(OrganizationKey.organization_name == "Acme Corp").first():
        db.add(OrganizationKey(organization_name="Acme Corp", api_key_hash=mock_key_hash, tier="enterprise"))

    if not db.query(PromptRecord).filter(PromptRecord.prompt_id == "auth-system-onboarding-v2").first():
        db.add(PromptRecord(
            organization_name="Acme Corp",
            prompt_id="auth-system-onboarding-v2",
            template_text="You are a helpful assistant. Greet {user_name}, who is a {role}.",
            version_hash="sha256-mock-hash-123"
        ))
    db.commit()
    db.close()

REQUEST_COUNT = Counter('gateway_llm_requests_total', 'Total LLM requests processed', ['model_used', 'status', 'org_name'])
TOKEN_COUNT = Counter('gateway_llm_token_usage_total', 'Total tokens consumed for billing', ['model_used', 'org_name'])
REQUEST_LATENCY = Histogram('gateway_llm_request_latency_seconds', 'LLM request latency', ['model_used'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/v1/prompts/execute", response_model=ExecuteResponse)
async def execute_prompt(request: ExecuteRequest, db: Session = Depends(get_db), organization: OrganizationKey = Depends(get_current_organization)):
    start_time = time.time()

    prompt_record = db.query(PromptRecord).filter(PromptRecord.prompt_id == request.prompt_id).first()
    if not prompt_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prompt ID '{request.prompt_id}' not found.")

    if prompt_record.organization_name != organization.organization_name:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access violation.")

    try:
        hydrated_prompt = prompt_record.template_text.format(**request.variables)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing variable: {e}")

    active_model = request.model_override if request.model_override else DEFAULT_MODEL

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": active_model, "messages": [{"role": "user", "content": hydrated_prompt}], "temperature": 0.7, "stream": False}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(LLM_API_BASE_URL, json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()
            llm_data = response.json()
            actual_response_text = llm_data["choices"][0]["message"]["content"]
            actual_tokens = llm_data.get("usage", {}).get("total_tokens", 0)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Upstream LLM Error: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Connection Failed: {str(e)}")

    latency_seconds = time.time() - start_time
    REQUEST_COUNT.labels(model_used=active_model, status="success", org_name=organization.organization_name).inc()
    TOKEN_COUNT.labels(model_used=active_model, org_name=organization.organization_name).inc(actual_tokens)
    REQUEST_LATENCY.labels(model_used=active_model).observe(latency_seconds)

    return ExecuteResponse(success=True, executed_prompt=hydrated_prompt, llm_response=actual_response_text, telemetry=Telemetry(token_usage=actual_tokens, latency_ms=int(latency_seconds * 1000), model_used=active_model))

@app.post("/v1/prompts", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(request: CreatePromptRequest, db: Session = Depends(get_db), organization: OrganizationKey = Depends(get_current_organization)):
    if db.query(PromptRecord).filter(PromptRecord.prompt_id == request.prompt_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prompt ID already exists.")

    version_hash = hashlib.sha256(request.template_text.encode('utf-8')).hexdigest()
    new_prompt = PromptRecord(organization_name=organization.organization_name, prompt_id=request.prompt_id, template_text=request.template_text, version_hash=version_hash)

    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)

    return PromptResponse(prompt_id=new_prompt.prompt_id, version_hash=new_prompt.version_hash, created_at=new_prompt.updated_at)

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "database": "connected"}
