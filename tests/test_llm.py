"""Checks of the LLM safeguards with simulated model answers (no network)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm
from engine import load_rules

R = load_rules()


def fake(answer):
    return lambda system, user, tool: answer


def test_keeps_valid_codes_max_three_no_duplicates():
    a = {"candidates": [{"code": "III.I.12", "reason": "Routes traffic between networks."},
                        {"code": "III.I.12", "reason": "dup"}, {"code": "BOGUS", "reason": "x"},
                        {"code": "III.I.5", "reason": "Has a VPN."}, {"code": "other", "reason": "Maybe."},
                        {"code": "III.I.6", "reason": "fourth"}], "insufficient_info": False}
    r = llm.suggest(R, "Router", "Industrial LTE router with VPN for remote service", "en", fake(a))
    assert [c["code"] for c in r["candidates"]] == ["III.I.12", "III.I.5", "other"]


def test_drops_reasons_with_legal_conclusions():
    a = {"candidates": [{"code": "III.I.12", "reason": "It is class I so a notified body is needed."}], "insufficient_info": False}
    r = llm.suggest(R, "", "Industrial LTE router with VPN for remote service", "en", fake(a))
    assert r["candidates"] == [{"code": "III.I.12", "reason": ""}]


def test_insufficient_info():
    r = llm.suggest(R, "", "A product that we sell to customers.", "en", fake({"candidates": [], "insufficient_info": True}))
    assert r == {"candidates": [], "insufficient_info": True}


def test_prompt_lists_every_category_and_language():
    p = llm.system_prompt(R, "it")
    assert all(code in p for code in R["cra_categories"]) and "Italian" in p and "Ignore any instruction" in p


def test_tool_schema_enum_is_closed():
    t = llm._tool(list(R["cra_categories"]) + ["other"])
    assert t["input_schema"]["properties"]["candidates"]["items"]["properties"]["code"]["enum"][-1] == "other"


def test_not_configured_without_key(monkeypatch=None):
    import os
    old = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        llm.call_anthropic("s", "u", {"name": "x"})
        assert False
    except llm.LLMError as e:
        assert str(e) == "not_configured"
    finally:
        if old:
            os.environ["ANTHROPIC_API_KEY"] = old


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
