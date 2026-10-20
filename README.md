# CyberPlan backend

Rule engine and API for **CyberPlan** (cyberplan.pentaflowers.com), the free Pentaflowers check on the
Cyber Resilience Act (Regulation (EU) 2024/2847) and the Machinery Regulation (Regulation (EU) 2023/1230).

Principle: **the LLM reads and writes, deterministic code decides.** No regulatory outcome comes from an LLM.

## Contents

| Path | What it is |
|---|---|
| `rules/rules_2026-10-20.json` | Rules file: dates, product categories, procedures, practice-to-requirement links, legal references, watch list. Versioned and dated. |
| `engine.py` | Applies rules R1–R10 to the confirmed answers. Python standard library only. |
| `tests/cases.json` | Test cases: answers → expected outcome → legal reference. |
| `tests/run_cases.py` | Runs every test case. |

## Updating the rules

1. Copy the rules file with the new date (`rules_YYYY-MM-DD.json`) and change `meta.rules_version`.
2. Point `DEFAULT_RULES` in `engine.py` to the new file.
3. Run `python tests/run_cases.py`; all cases must pass (update the expected values only when the law changed).
4. Note the change and its source in the commit message.

Sources are reviewed monthly, and right after known events: CRA harmonised standards cited in the OJ,
decisions on postponing Machinery Regulation Annex III 1.1.9 and 1.2.1, new delegated or implementing acts.

## Status

Step 1 of the first release: rules and tests. The API (Render) comes in step 2.
