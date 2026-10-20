"""CyberPlan rule engine.

Turns the confirmed questionnaire answers into regulatory outcomes (R1-R10).
Deterministic: same answers + same rules file + same evaluation date = same result.
No LLM is involved here. Every outcome carries the legal reference it comes from.

Only the Python standard library is used, so the engine can be tested on its own.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

RULES_DIR = Path(__file__).parent / "rules"
DEFAULT_RULES = RULES_DIR / "rules_2026-10-20.json"


class AnswerError(ValueError):
    """Raised when answers are missing or use an unknown option."""


def load_rules(path: Path | str = DEFAULT_RULES) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ validation
def _options(rules: dict, qid: str) -> list[str] | None:
    q = rules["questions"][qid]
    t = q["type"]
    if t == "yesno":
        return ["yes", "no"]
    if t == "practice":
        return rules["practice_answers"]
    if "options" in q:
        return q["options"]
    if q.get("options_from") == "cra_categories":
        return list(rules["cra_categories"]) + q.get("plus", [])
    if q.get("options_from") == "mr_annex_i":
        return list(rules["mr_annex_i"]) + q.get("plus", [])
    return None


def validate(answers: dict, rules: dict) -> dict:
    """Check option codes and return a cleaned copy. Unknown question ids are rejected."""
    clean = {}
    for qid, val in answers.items():
        if qid not in rules["questions"]:
            raise AnswerError(f"Unknown question: {qid}")
        q = rules["questions"][qid]
        if val is None or val == "":
            continue
        if q["type"] == "multi":
            if not isinstance(val, list):
                raise AnswerError(f"{qid}: expected a list")
            bad = [v for v in val if v not in q["options"]]
            if bad:
                raise AnswerError(f"{qid}: unknown option(s) {bad}")
            clean[qid] = sorted(set(val))
        elif q["type"] == "number":
            try:
                n = float(val)
            except (TypeError, ValueError):
                raise AnswerError(f"{qid}: expected a number")
            if not (q["min"] <= n <= q["max"]):
                raise AnswerError(f"{qid}: must be between {q['min']} and {q['max']}")
            clean[qid] = n
        else:
            opts = _options(rules, qid)
            if val not in opts:
                raise AnswerError(f"{qid}: unknown option '{val}'")
            clean[qid] = val
    for qid in ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1"]:
        if qid not in clean:
            raise AnswerError(f"{qid} is required")
    if clean["A1"] == "modifier" and "A1m" not in clean:
        raise AnswerError("A1m is required when A1 is 'modifier'")
    if clean.get("C6") == "yes":
        for q in ("C6a", "C6b", "C6c"):
            if q not in clean:
                raise AnswerError(f"{q} is required when C6 is 'yes'")
    return clean


def _d(s: str) -> date:
    return date.fromisoformat(s)


# ----------------------------------------------------------------------- rules
def r1_scope(a: dict, rules: dict) -> dict:
    R = rules["R1"]
    notes = []
    if a["A2"] == "no":
        out = {"status": "not_applies", "reason": "not_commercial", "cites": [R["cite_commercial"]]}
    elif a["B2"] == "no":
        out = {"status": "not_applies", "reason": "no_data_connection", "cites": [R["cite_scope"]]}
    elif a["B3"] != "none":
        out = {"status": "excluded", "reason": f"excluded_{a['B3']}", "cites": [R["exclusions"][a["B3"]]]}
    else:
        out = {"status": "applies", "reason": "in_scope", "cites": [R["cite_scope"]]}
        if a["B1"] == "no":
            notes.append("hardware_with_data_connection")
    role = a["A1"]
    if role == "modifier":
        role = "modifier_substantial" if a.get("A1m") == "yes" else "modifier_not_substantial"
    r = R["roles"][role]
    out["role"] = role
    out["obligations"] = r["obligations"] if out["status"] == "applies" else "none"
    if out["status"] == "applies":
        out["cites"].append(r["cite"])
    out["notes"] = notes
    return out


def r2_class(a: dict, rules: dict, r1: dict) -> dict:
    if r1["status"] != "applies":
        return {"status": "not_applicable"}
    R = rules["R2"]
    cat = a.get("B4")
    if cat is None:
        raise AnswerError("B4 is required when the CRA applies")
    if cat == "other":
        return {"status": "ok", "class": R["default_class"], "category": None, "cites": ["CRA Art. 6", "CRA Art. 7(1)"]}
    c = rules["cra_categories"][cat]
    annex = "CRA Annex IV" if cat.startswith("IV") else "CRA Annex III"
    return {"status": "ok", "class": c["class"], "category": cat, "category_label": c["label"],
            "cites": [annex, "CRA Art. 7(1)" if cat.startswith("III") else "CRA Art. 8",
                      "Implementing Regulation (EU) 2025/2392"]}


def r3_procedure(rules: dict, r2: dict) -> dict:
    if r2["status"] != "ok":
        return {"status": "not_applicable"}
    R = rules["R3"]
    spec = R["by_class"][r2["class"]]
    future = None
    if r2["class"] == "important_I":
        if R["harmonised_standards_cited"]:
            spec = {"options_with_standards": spec["if_standards_applied"], **spec["otherwise"]}
        else:
            future = "module_A_when_standards_cited"
            spec = spec["otherwise"]
    out = {"status": "ok", "procedures": spec["procedures"], "notified_body": spec["notified_body"],
           "cites": [spec["cite"]]}
    if future:
        out["future_note"] = future
    return out


def r4_reporting(a: dict, rules: dict, r1: dict, today: date) -> dict:
    R = rules["R4"]
    if r1["status"] != "applies":
        return {"status": "not_applicable"}
    if r1["obligations"] not in R["applies_to_obligations"]:
        return {"status": "not_direct", "reason": f"role_{r1['role']}", "cites": [R["cite"].split(",")[0]]}
    start = _d(rules["dates"]["CRA_REPORTING"]["date"])
    out = {"status": "applies", "since": start.isoformat(), "in_force": today >= start,
           "deadlines": R["deadlines"], "channel": R["channel"],
           "cites": ["CRA Art. 14", "CRA Art. 71(2)"]}
    if a["A4"] == "yes":
        out["already_on_market"] = True
        out["cites"].append("CRA Art. 69(3)")
    if a["A3"] in R["sme_fine_exemption"]["sizes"]:
        out["sme_fine_exemption"] = True
        out["cites"].append(R["sme_fine_exemption"]["cite"])
    return out


def r5_support(a: dict, rules: dict, r1: dict) -> dict:
    if r1["status"] != "applies" or r1["obligations"] != "manufacturer":
        return {"status": "not_applicable"}
    m = rules["R5"]["min_years"]
    use = a.get("B7")
    if use is None:
        return {"status": "ok", "min_years": m, "expected_use_years": None, "cites": [rules["R5"]["cite"]]}
    use_i = int(use) if float(use).is_integer() else use
    return {"status": "ok", "min_years": use_i if use < m else m, "expected_use_years": use_i,
            "reflect_expected_use": use > m, "cites": [rules["R5"]["cite"]]}


def r6_mr_scope(a: dict, rules: dict) -> dict:
    R = rules["R6"]
    if a["C1"] not in R["in_scope_products"]:
        out = {"status": "not_applies", "cites": [R["cite_scope"]]}
    else:
        out = {"status": "applies", "product_type": a["C1"], "cites": [R["cite_scope"]]}
        if a["C1"] == "partly_completed":
            out["cites"].append(R["cite_partly_completed"])
    if a.get("C6") == "yes":
        sub = a["C6a"] == "yes" and a["C6b"] == "yes" and a["C6c"] == "yes"
        out["modification"] = "substantial" if sub else "not_substantial"
        out["modifier_becomes_manufacturer"] = sub
        out.setdefault("cites", []).append(R["cite_modification"])
        if sub and out["status"] != "applies":
            out.update(status="applies", product_type="machinery")
    return out


def r7_mr_procedure(a: dict, rules: dict, r6: dict) -> dict:
    if r6["status"] != "applies":
        return {"status": "not_applicable"}
    R = rules["R7"]
    if r6["product_type"] == "partly_completed":
        spec, part = R["partly_completed"], None
    else:
        c2 = a.get("C2", "none")
        if a.get("C3") == "yes" or c2.startswith("A."):
            spec, part = R["part_A"], "A"
        elif c2.startswith("B."):
            part = "B"
            spec = R["part_B_with_standards"] if a.get("C2h") == "yes" else R["part_B_without_standards"]
        else:
            spec, part = R["other"], None
    out = {"status": "ok", "annex_i_part": part, "procedures": spec["procedures"],
           "notified_body": spec["notified_body"], "cites": [spec["cite"]]}
    if part == "A" and a.get("C3") == "yes" and not a.get("C2", "none").startswith("A."):
        out["reason"] = "ml_safety_function"
    return out


def r8_mr_cyber(a: dict, rules: dict, r6: dict) -> dict:
    if r6["status"] != "applies":
        return {"status": "not_applicable"}
    R = rules["R8"]
    t = R["exposure_triggers"]
    exposed = (a.get("C4") == t["C4"] or a.get("C5") == t["C5"]
               or any(i in t["B5_any_of"] for i in a.get("B5", [])))
    return {"status": "applies", "exposure": "high" if exposed else "standard",
            "requirements": R["requirements"], "certification_presumption": True,
            "from": rules["dates"]["MR_APPLICATION"]["date"], "watch": "W1",
            "cites": ["MR Annex III 1.1.9", "MR Annex III 1.2.1", "MR Art. 20(9)"]}


def r9_timeline(a: dict, rules: dict, r1: dict, r4: dict, r6: dict, today: date) -> dict:
    D = rules["dates"]
    items = []
    if r4.get("status") == "applies":
        items.append({"key": "CRA_REPORTING", "date": D["CRA_REPORTING"]["date"], "cite": D["CRA_REPORTING"]["cite"]})
    if r6["status"] == "applies":
        items.append({"key": "MR_APPLICATION", "date": D["MR_APPLICATION"]["date"], "cite": D["MR_APPLICATION"]["cite"]})
    if r1["status"] == "applies":
        items.append({"key": "CRA_FULL", "date": D["CRA_FULL"]["date"], "cite": D["CRA_FULL"]["cite"]})
    items.sort(key=lambda x: x["date"])
    for it in items:
        it["in_force"] = _d(it["date"]) <= today
    upcoming = [i for i in items if not i["in_force"]]
    out = {"status": "ok", "items": items, "next": upcoming[0] if upcoming else None,
           "cites": ["CRA Art. 71(2)", "MR Art. 54"]}
    if r6["status"] == "applies" and a.get("C7") == "before":
        out["mr_unit_note"] = True
        out["cites"].append("MR Art. 52")
    if r1["status"] == "applies" and a["A4"] == "yes":
        out["cra_legacy_note"] = True
        out["cites"].append("CRA Art. 69(2)")
    return out


def r10_gaps(a: dict, rules: dict, r1: dict, r4: dict, r6: dict, today: date) -> dict:
    R = rules["R10"]
    D = rules["dates"]
    window = timedelta(days=R["priority_rule"]["high_window_days"])
    cra_on = r1["status"] == "applies" and r1["obligations"] == "manufacturer"
    active = {"CRA": cra_on, "CRA_REPORTING": r4.get("status") == "applies", "MR": r6["status"] == "applies"}
    items = []
    for pid, p in R["practices"].items():
        links = [l for l in p["links"] if active[l["reg"]]]
        ans = a.get(pid, "unknown")
        if not links:
            items.append({"id": pid, "status": "not_applicable", "answer": ans})
            continue
        first = min(_d(D[l["date"]]["date"]) for l in links)
        state = {"yes": "in_place", "partial": "partial", "no": "missing", "unknown": "unknown"}[ans]
        prio = None
        if state != "in_place":
            prio = "high" if first <= today + window else "medium"
        items.append({"id": pid, "status": state, "answer": ans, "priority": prio,
                      "due": first.isoformat(), "cites": [l["cite"] for l in links]})
    gaps = [i for i in items if i["status"] in ("partial", "missing", "unknown")]
    order = {"high": 0, "medium": 1}
    gaps_sorted = sorted(gaps, key=lambda i: (order[i["priority"]], i["due"], i["id"]))
    out = {"status": "ok", "items": items,
           "high_count": sum(1 for g in gaps if g["priority"] == "high"),
           "medium_count": sum(1 for g in gaps if g["priority"] == "medium"),
           "top_actions": [g["id"] for g in gaps_sorted[:3]],
           "cites": [R["cite"]]}
    if cra_on and a.get("B6") in ("yes", "unknown") and a.get("D2", "unknown") != "yes":
        out["sbom_note"] = True
    return out


def lead_score(rules: dict, r2: dict, r1: dict, r6: dict, r7: dict, r10: dict) -> str:
    if r2.get("class") in ("important_II", "critical") or r7.get("annex_i_part") == "A" or r10["high_count"] >= rules["lead_score"]["hot_high_gaps"]:
        return "hot"
    if r1["status"] == "applies" or r6["status"] == "applies":
        return "warm"
    return "cold"


# ----------------------------------------------------------------------- entry
def evaluate(answers: dict, rules: dict | None = None, today: date | str | None = None) -> dict:
    rules = rules or load_rules()
    today = _d(today) if isinstance(today, str) else (today or date.today())
    a = validate(answers, rules)
    r1 = r1_scope(a, rules)
    r2 = r2_class(a, rules, r1)
    r3 = r3_procedure(rules, r2)
    r4 = r4_reporting(a, rules, r1, today)
    r5 = r5_support(a, rules, r1)
    r6 = r6_mr_scope(a, rules)
    r7 = r7_mr_procedure(a, rules, r6)
    r8 = r8_mr_cyber(a, rules, r6)
    r9 = r9_timeline(a, rules, r1, r4, r6, today)
    r10 = r10_gaps(a, rules, r1, r4, r6, today)
    summary = {
        "cra": r1["status"], "cra_class": r2.get("class"),
        "cra_notified_body": r3.get("notified_body"),
        "mr": r6["status"], "mr_annex_i_part": r7.get("annex_i_part"),
        "mr_notified_body": r7.get("notified_body"),
        "next_deadline": r9["next"], "top_actions": r10["top_actions"],
        "high_gaps": r10["high_count"],
        "lead_score": lead_score(rules, r2, r1, r6, r7, r10),
    }
    return {"rules_version": rules["meta"]["rules_version"], "evaluated_on": today.isoformat(),
            "summary": summary,
            "results": {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5, "R6": r6,
                        "R7": r7, "R8": r8, "R9": r9, "R10": r10},
            "answers": a}
