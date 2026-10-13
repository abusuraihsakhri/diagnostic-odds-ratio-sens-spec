"""
FastAPI REST API Server for Diagnostic Odds Ratio Sens Spec.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import Field
from dor_youden import calculate_diagnostic_metrics
from .base import SecurityException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Diagnostic Odds Ratio Sens Spec API",
    description="Diagnostic table calculations and a separate example rules-based task API",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    query: str


class DiagnosticTableRequest(BaseModel):
    tp: int = Field(..., ge=0)
    fp: int = Field(..., ge=0)
    fn: int = Field(..., ge=0)
    tn: int = Field(..., ge=0)
    alpha: float = Field(default=0.05, gt=0, lt=1, allow_inf_nan=False)


@app.post("/api/diagnostic-metrics")
def api_diagnostic_metrics(table: DiagnosticTableRequest):
    try:
        return calculate_diagnostic_metrics(**table.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "diagnostic-odds-ratio-sens-spec", "version": "1.0.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "RUNNING"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
        return dossier.to_dict()
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Input contains a potentially identifying value.") from exc


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Register the browser files last, after the existing API routes.
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "web", html=True),
          name="browser")
