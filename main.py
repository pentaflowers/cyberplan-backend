"""CyberPlan API (FastAPI).

Endpoints
- GET  /health                 service is up
- GET  /api/v1/rules           rules version, questions and option lists for the interface
- POST /api/v1/evaluate        confirmed answers -> outcomes R1-R10 (deterministic, no LLM)
- GET  /api/v1/selftest        runs every test case on the live service
- POST /api/v1/suggest-function   LLM proposes up to 3 CRA categories for question B4 (user chooses)
- GET  /api/v1/suggest-selftest   runs 5 reference products through the LLM; results in the service log
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engine import AnswerError, evaluate, load_rules
import llm

RULES = load_rules()
TZ = ZoneInfo("Europe/Paris")
log = logging.getLogger("uvicorn.error")

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


class SuggestRequest(BaseModel):
    name: str = Field("", max_length=120)
    description: str = Field(..., min_length=20, max_length=3000)
    lang: str = Field("en", max_length=5)


@app.post("/api/v1/suggest-function")
def suggest_function(req: SuggestRequest, request: Request):
    who = request.client.host if request.client else "?"
    if not llm.rate_ok(who):
        raise HTTPException(status_code=429, detail="daily_limit")
    try:
        return llm.suggest(RULES, req.name, req.description, req.lang)
    except llm.LLMError as e:
        log.warning("suggest-function failed: %s", e)
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/v1/suggest-selftest")
def suggest_selftest(request: Request):
    who = request.client.host if request.client else "?"
    out = []
    for name, desc, expected in llm.SELFTEST:
        if not llm.rate_ok(who):
            raise HTTPException(status_code=429, detail="daily_limit")
        try:
            r = llm.suggest(RULES, name, desc, "it")
            codes = [c["code"] for c in r["candidates"]]
            ok = bool(codes) and codes[0] in expected
            out.append({"product": name, "codes": codes, "expected_first": sorted(expected), "ok": ok,
                        "reasons": [c["reason"] for c in r["candidates"]]})
            log.info("SUGGEST_SELFTEST %s | %s | first ok=%s | %s", name, ",".join(codes), ok,
                     " / ".join(c["reason"] for c in r["candidates"]))
        except llm.LLMError as e:
            out.append({"product": name, "error": str(e)})
            log.warning("SUGGEST_SELFTEST %s | error %s", name, e)
    return {"passed": sum(1 for x in out if x.get("ok")), "total": len(out), "results": out}
