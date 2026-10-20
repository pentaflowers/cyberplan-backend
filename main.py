"""CyberPlan API (FastAPI).

Endpoints
- GET  /health                 service is up
- GET  /api/v1/rules           rules version, questions and option lists for the interface
- POST /api/v1/evaluate        confirmed answers -> outcomes R1-R10 (deterministic, no LLM)
- GET  /api/v1/selftest        runs every test case on the live service
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engine import AnswerError, evaluate, load_rules

RULES = load_rules()
TZ = ZoneInfo("Europe/Paris")

app = FastAPI(title="CyberPlan API", version="0.1.0",
              description="CRA (EU) 2024/2847 and Machinery Regulation (EU) 2023/1230 rule engine.")

# Open during development; to be limited to cyberplan.pentaflowers.com and the Figma site at launch.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def today() -> date:
    return datetime.now(TZ).date()


@app.get("/")
def root():
    return {"service": "CyberPlan API by Pentaflowers", "rules_version": RULES["meta"]["rules_version"],
            "selftest": "/api/v1/selftest", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "rules_version": RULES["meta"]["rules_version"]}


@app.get("/api/v1/rules")
def rules_info():
    """Everything the interface needs to draw the questionnaire. Labels are English reference text;
    the interface shows its own translations, keyed by the same codes."""
    return {
        "rules_version": RULES["meta"]["rules_version"],
        "status": RULES["meta"]["status"],
        "questions": RULES["questions"],
        "practice_answers": RULES["practice_answers"],
        "cra_categories": RULES["cra_categories"],
        "mr_annex_i": RULES["mr_annex_i"],
        "dates": RULES["dates"],
        "watch": RULES["meta"]["watch"],
    }


class EvaluateRequest(BaseModel):
    answers: dict[str, Any] = Field(..., description="Question id -> answer code")
    evaluation_date: Optional[date] = Field(None, description="For tests only; defaults to today (Europe/Paris)")


@app.post("/api/v1/evaluate")
def evaluate_endpoint(req: EvaluateRequest):
    try:
        return evaluate(req.answers, RULES, req.evaluation_date or today())
    except AnswerError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/api/v1/selftest")
def selftest():
    from tests.run_cases import run
    import json
    from pathlib import Path
    n = len(json.loads((Path(__file__).parent / "tests" / "cases.json").read_text(encoding="utf-8"))["cases"])
    failures = run()
    failed = {f.split()[0].rstrip(":") for f in failures}
    return {"rules_version": RULES["meta"]["rules_version"], "cases": n, "passed": n - len(failed),
            "failures": failures}
