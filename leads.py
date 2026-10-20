"""Contacts: validation, consents, payload for the Google Apps Script webhook (sheet row + emails).

The same webhook serves every Pentaflowers mini app; `source` tells them apart. The content of the product
description never enters the contact record (spec: only fields, consents, rules version and main outcomes).
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")
FIELDS = {"first_name": 80, "last_name": 80, "email": 200, "company": 160, "role": 120, "country": 80}
_LAST = {"ok": None, "reason": "never tried"}
_HITS: dict[str, list[float]] = {}

MAIL = {
    "en": {
        "subject": "Your CyberPlan report{p}",
        "body": "Hello {first},\n\nattached is your CyberPlan report on the Cyber Resilience Act and the Machinery Regulation{p2}.\n\n"
                "It gives a first orientation based on your answers and is not legal advice.\n\n"
                "If you want to turn it into a plan, you can book a diagnosis with Pentaflowers: {diag}\n\n"
                "Pentaflowers Consulting SAS\nPrivacy notice: {privacy}\n",
    },
    "it": {
        "subject": "Il tuo report CyberPlan{p}",
        "body": "Buongiorno {first},\n\nin allegato trovi il tuo report CyberPlan sul Cyber Resilience Act e sul Regolamento Macchine{p2}.\n\n"
                "Dà un primo orientamento basato sulle tue risposte e non è una consulenza legale.\n\n"
                "Se vuoi trasformarlo in un piano, puoi prenotare una diagnosi con Pentaflowers: {diag}\n\n"
                "Pentaflowers Consulting SAS\nInformativa privacy: {privacy}\n",
    },
}
PRIVACY_URL = "https://www.pentaflowers.com/#privacy"


class LeadError(ValueError):
    pass


def clean(contact: dict) -> dict:
    out = {}
    for k, n in FIELDS.items():
        out[k] = re.sub(r"\s+", " ", str(contact.get(k) or "")).strip()[:n]
    out["email"] = out["email"].lower()
    missing = [k for k in FIELDS if not out[k]]
    if missing:
        raise LeadError("missing:" + ",".join(missing))
    if not EMAIL_RE.match(out["email"]):
        raise LeadError("invalid_email")
    if contact.get("consent_report") is not True:
        raise LeadError("consent_report_required")
    out["consent_report"] = True
    out["consent_contact"] = contact.get("consent_contact") is True
    out["consent_ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return out


def rate_ok(who: str, now: float | None = None) -> bool:
    per_day = int(os.environ.get("REPORT_PER_IP_DAY", "10"))
    t = now or time.time()
    hits = [x for x in _HITS.get(who, []) if t - x < 86400]
    if len(hits) >= per_day:
        _HITS[who] = hits
        return False
    _HITS[who] = hits + [t]
    return True


def payload(contact: dict, result: dict, product_name: str, lang: str, pdf: bytes, filename: str, diagnosis_url: str) -> dict:
    S = result["summary"]
    nxt = S.get("next_deadline") or {}
    m = MAIL.get(lang, MAIL["en"])
    p = f" — {product_name}" if product_name else ""
    p2 = f" ({product_name})" if product_name else ""
    return {
        "source": "CyberPlan",
        "name": f"{contact['first_name']} {contact['last_name']}",
        **contact,
        "updates": contact["consent_contact"],
        "lang": lang,
        "lead_score": S["lead_score"],
        "cra": S["cra"], "cra_class": S.get("cra_class") or "",
        "mr": S["mr"], "mr_annex_i_part": S.get("mr_annex_i_part") or "",
        "next_deadline": nxt.get("date", ""), "high_gaps": S["high_gaps"],
        "rules_version": result["rules_version"],
        "send_report": True,
        "report_filename": filename,
        "report_pdf_b64": base64.b64encode(pdf).decode(),
        "mail_subject": m["subject"].format(p=p),
        "mail_body": m["body"].format(first=contact["first_name"], p2=p2, diag=diagnosis_url, privacy=PRIVACY_URL),
    }


def forward(data: dict, url: str | None = None, secret: str | None = None, timeout: int = 40) -> bool:
    url = url or os.environ.get("LEAD_WEBHOOK_URL")
    if not url:
        _LAST.update(ok=False, reason="LEAD_WEBHOOK_URL not set")
        return False
    body = {**data, "secret": secret if secret is not None else os.environ.get("LEAD_SECRET", ""),
            "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + " UTC"}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"content-type": "text/plain;charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ans = r.read(300).decode("utf-8", "replace").strip()
    except Exception as e:
        _LAST.update(ok=False, reason=f"request failed: {type(e).__name__}")
        return False
    _LAST.update(ok=ans == "ok", reason=ans[:80] if "<" not in ans[:5] else "HTML page (deployment access must be 'Anyone')")
    return ans == "ok"


def status() -> dict:
    return {"webhook_configured": bool(os.environ.get("LEAD_WEBHOOK_URL")), "secret_configured": bool(os.environ.get("LEAD_SECRET")),
            "last_forward_ok": _LAST["ok"], "last_forward_reason": _LAST["reason"]}
