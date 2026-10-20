"""Report checks: the LLM text check, the standard fallback, the PDF and the contact rules (no network)."""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import leads  # noqa: E402
import report_pdf  # noqa: E402
import report_text as RT  # noqa: E402
from engine import evaluate  # noqa: E402

BASE = json.loads((ROOT / "tests" / "cases.json").read_text())["base"]
LIFT = {**BASE, "C1": "machinery", "C2": "A.3", "C4": "yes", "B5": ["wifi"]}


def res():
    return evaluate(LIFT, today="2026-10-20")


def test_check_accepts_engine_facts():
    fx = RT.facts(res(), "it")
    ok = "La segnalazione è in vigore dall'11 settembre 2026; il ponte è nell'Allegato I parte A e il 20 gennaio 2027 si applica il Regolamento."
    assert RT.check(ok, fx) == []


def test_check_rejects_invented_date_number_annex():
    fx = RT.facts(res(), "it")
    probs = RT.check("Entro il 30/06/2027 serve l'Allegato VIII, art. 99.", fx)
    assert any(p.startswith("date") for p in probs) and "annex VIII" in probs and "number 99" in probs


def test_fallback_after_two_bad_answers():
    calls = []

    def bad(system, user, tool):
        calls.append(1)
        return {k: "Scadenza il 1 marzo 2030, articolo 77." for k in RT.LLM_KEYS}
    texts, origin = RT.llm_texts(res(), "it", bad)
    assert len(calls) == 2 and set(origin.values()) == {"standard"}
    assert texts == RT.standard_texts(res(), "it")


def test_llm_failure_gives_standard_texts():
    def boom(system, user, tool):
        raise RuntimeError("down")
    texts, origin = RT.llm_texts(res(), "en", boom)
    assert set(origin.values()) == {"standard"} and texts["summary"]


def test_pdf_is_valid_both_languages():
    r = res()
    for lang in ("it", "en"):
        std = RT.standard_texts(r, lang)
        pdf = report_pdf.render(RT.build(r, {"name": "Lift"}, lang, std, {k: "standard" for k in std}, date(2026, 10, 20)))
        assert pdf.startswith(b"%PDF") and len(pdf) > 20000


def test_report_for_out_of_scope_product():
    r = evaluate({**BASE, "A2": "no"}, today="2026-10-20")
    std = RT.standard_texts(r, "it")
    pdf = report_pdf.render(RT.build(r, {}, "it", std, {k: "standard" for k in std}, date(2026, 10, 20)))
    assert pdf.startswith(b"%PDF")


def test_contact_rules():
    c = {"first_name": "A", "last_name": "B", "email": "a@b.it", "company": "C", "role": "D", "country": "IT"}
    for bad, code in [({**c, "consent_report": False}, "consent_report_required"),
                      ({**c, "email": "x", "consent_report": True}, "invalid_email"),
                      ({**c, "company": "", "consent_report": True}, "missing:company")]:
        try:
            leads.clean(bad)
            assert False
        except leads.LeadError as e:
            assert str(e) == code
    ok = leads.clean({**c, "consent_report": True})
    assert ok["consent_contact"] is False and ok["consent_ts"].endswith("UTC")


def test_payload_has_no_description():
    r = res()
    c = leads.clean({"first_name": "A", "last_name": "B", "email": "a@b.it", "company": "C", "role": "D", "country": "IT", "consent_report": True})
    p = leads.payload(c, r, "Lift", "it", b"%PDF-1.4", "f.pdf", "https://www.pentaflowers.com")
    assert p["source"] == "CyberPlan" and not any("description" in k for k in p) and p["lead_score"] == "hot"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
