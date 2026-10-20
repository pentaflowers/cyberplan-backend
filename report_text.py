"""CyberPlan report content.

Every fact in the report (outcomes, classes, procedures, dates, articles, tables) is written by this module from
the rule engine result. The LLM only adds short plain-language paragraphs, and only after a check: each date,
number, article and annex it mentions must come from the engine result. If the check fails twice, the standard
paragraph of this module is used instead.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
UI = json.loads((ROOT / "assets" / "ui_texts.json").read_text(encoding="utf-8"))
DIAGNOSIS_URL = "https://www.pentaflowers.com"
LLM_KEYS = ["summary", "cra", "mr", "overlap", "next_steps"]

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
}

T = {
    "en": {
        "title": "CyberPlan report",
        "subtitle": "Cyber Resilience Act and Machinery Regulation: first orientation",
        "product": "Product", "date": "Date", "rules": "Rules version", "company_size": "Company size",
        "disclaimer": "This report gives a first orientation based on the answers provided. It is not legal advice. Outcomes depend on the answers: if they change, the outcomes may change.",
        "footer": "CyberPlan by Pentaflowers · rules {v} · not legal advice · page {p}",
        "s_summary": "Summary", "s_cra": "Cyber Resilience Act", "s_mr": "Machinery Regulation",
        "s_overlap": "Where the two regulations overlap", "s_timeline": "Your timeline", "s_gaps": "Gap checklist",
        "s_data": "Answers provided", "s_sources": "Sources, limits and next step",
        "k_cra": "CRA", "k_class": "CRA class", "k_mr": "Machinery Regulation", "k_proc": "Notified body",
        "k_next": "Next deadline", "k_actions": "First actions", "none": "None", "applies": "Applies",
        "not_applies": "Does not apply", "excluded": "Does not apply (other legislation)",
        "nb_cra": "CRA: {v}", "nb_mr": "Machinery Regulation: {v}", "yes": "yes", "no": "no", "na": "not applicable",
        "scope": "Scope", "class": "Product class", "category": "Category", "procedure": "Conformity assessment",
        "reporting": "Reporting obligations", "support": "Support period", "annex_i": "Annex I", "cyber": "Cybersecurity requirements (Annex III)",
        "modification": "Modification of a machine in service", "basis": "Basis",
        "rep_since": "In force since {d} for products placed on the market, including those already sold.",
        "rep_since_future": "Applies from {d}, including to products already sold.",
        "rep_items": ["Early warning within 24 hours of becoming aware of an actively exploited vulnerability or a severe incident.",
                      "Notification within 72 hours.",
                      "Final report within 14 days after a corrective measure is available (vulnerability) or within one month (severe incident).",
                      "Reports go through the ENISA single reporting platform; users must be informed."],
        "rep_sme": "As a micro or small enterprise you cannot be fined for missing only the 24-hour early-warning deadlines (Art. 64(10)(a)); the obligation itself still applies.",
        "rep_not_direct": "Reporting is an obligation of the manufacturer.",
        "support_text": "Security updates must be provided for at least {n} years.",
        "support_reflect": "The support period must reflect the expected time of use you indicated ({u} years).",
        "support_unknown": "Security updates must be provided for at least 5 years, or for the expected time of use if shorter.",
        "cyber_intro": "From 20 January 2027 these points of Annex III apply to the machine:",
        "cyber_high": "The control system is connected, remotely accessible or updatable: these points need detailed treatment in the risk assessment and technical file.",
        "cyber_cert": "A certificate or statement of conformity under a European cybersecurity certification scheme gives a presumption of conformity for 1.1.9 and 1.2.1 as far as it covers them (Art. 20(9)).",
        "partly": "Partly completed machinery does not bear the CE marking: it comes with a declaration of incorporation and assembly instructions.",
        "both": "The product falls under both regulations. The technical file must show how it meets the CRA essential requirements (Annex I) and the Machinery Regulation requirements 1.1.9 and 1.2.1. A single risk assessment can cover both, if it addresses both sets of requirements.",
        "one_cra": "Only the CRA applies to this product: there is no overlap with the Machinery Regulation.",
        "one_mr": "Only the Machinery Regulation applies to this product: there is no overlap with the CRA.",
        "neither": "Neither regulation applies based on the answers provided.",
        "t_date": "Date", "t_event": "What applies", "t_status": "Status", "t_basis": "Basis",
        "in_force": "In force", "upcoming": "Upcoming",
        "unit_note": "Placing on the market is assessed unit by unit: units placed on the market from 20 January 2027 must comply with the Machinery Regulation even if the model was sold earlier.",
        "legacy_note": "Products placed on the market before 11 December 2027 must comply with the CRA essential requirements only if substantially modified after that date; reporting obligations apply to them anyway (Art. 69).",
        "g_practice": "Practice", "g_status": "Status", "g_priority": "Priority", "g_due": "Due", "g_basis": "Basis",
        "st_in_place": "In place", "st_partial": "Partly", "st_missing": "Missing", "st_unknown": "Unknown", "st_not_applicable": "Not applicable",
        "pr_high": "High", "pr_medium": "Medium",
        "gap_intro": "High priority: the requirement already applies or applies within about six months. Medium: it applies later.",
        "sbom_note": "The product contains third-party or open-source components: the software bill of materials (SBOM) is central to vulnerability handling.",
        "q": "Question", "a": "Answer", "years": "years",
        "sources": ["Regulation (EU) 2024/2847 (Cyber Resilience Act), OJ L 2024/2847, 20.11.2024",
                    "Commission Implementing Regulation (EU) 2025/2392 on the technical descriptions of important and critical products",
                    "Regulation (EU) 2023/1230 on machinery, consolidated text of 27.07.2026"],
        "limits": "Limits: CRA harmonised standards were not yet cited in the Official Journal on the rules date; the postponement of Machinery Regulation requirements 1.1.9 and 1.2.1 requested by industry had not been adopted. Rules are reviewed every month.",
        "next_title": "Next step",
        "next_text": "Pentaflowers can turn this orientation into a plan: scope confirmation, risk assessment, technical file and reporting procedure. Book a diagnosis at {url}.",
        "std_summary": "{cra} {mr} The next deadline that concerns this product is {next}.",
        "std_summary_none": "{cra} {mr}",
        "std_cra_applies": "The CRA applies to this product. The class follows from its main function and decides the conformity assessment route.",
        "std_cra_not": "Based on the answers provided, the CRA does not apply to this product.",
        "std_mr_applies": "The Machinery Regulation applies to this product. It replaces Directive 2006/42/EC and adds cybersecurity requirements for control systems.",
        "std_mr_not": "Based on the answers provided, the Machinery Regulation does not apply to this product.",
        "std_next": "Start from the actions marked high priority in the gap checklist, then plan the remaining ones before their deadlines.",
        "std_next_none": "No action is required under these two regulations based on the answers provided. Check again if the product or its market changes.",
        "llm_label": "Text written with AI from the outcomes above and checked automatically.",
    },
    "it": {
        "title": "Report CyberPlan",
        "subtitle": "Cyber Resilience Act e Regolamento Macchine: primo orientamento",
        "product": "Prodotto", "date": "Data", "rules": "Versione delle regole", "company_size": "Dimensione dell'azienda",
        "disclaimer": "Questo report dà un primo orientamento basato sulle risposte fornite. Non è una consulenza legale. Gli esiti dipendono dalle risposte: se cambiano, gli esiti possono cambiare.",
        "footer": "CyberPlan by Pentaflowers · regole {v} · non è consulenza legale · pagina {p}",
        "s_summary": "Sintesi", "s_cra": "Cyber Resilience Act", "s_mr": "Regolamento Macchine",
        "s_overlap": "Dove le due normative si sovrappongono", "s_timeline": "Il tuo calendario", "s_gaps": "Checklist dei gap",
        "s_data": "Risposte fornite", "s_sources": "Fonti, limiti e prossimo passo",
        "k_cra": "CRA", "k_class": "Classe CRA", "k_mr": "Regolamento Macchine", "k_proc": "Organismo notificato",
        "k_next": "Prossima scadenza", "k_actions": "Prime azioni", "none": "Nessuna", "applies": "Si applica",
        "not_applies": "Non si applica", "excluded": "Non si applica (altra normativa)",
        "nb_cra": "CRA: {v}", "nb_mr": "Regolamento Macchine: {v}", "yes": "sì", "no": "no", "na": "non applicabile",
        "scope": "Ambito", "class": "Classe del prodotto", "category": "Categoria", "procedure": "Valutazione della conformità",
        "reporting": "Obblighi di segnalazione", "support": "Periodo di supporto", "annex_i": "Allegato I", "cyber": "Requisiti di cybersicurezza (Allegato III)",
        "modification": "Modifica di una macchina in servizio", "basis": "Base",
        "rep_since": "In vigore dal {d} per i prodotti immessi sul mercato, compresi quelli già venduti.",
        "rep_since_future": "Si applica dal {d}, anche ai prodotti già venduti.",
        "rep_items": ["Allerta preliminare entro 24 ore da quando si viene a conoscenza di una vulnerabilità attivamente sfruttata o di un incidente grave.",
                      "Notifica entro 72 ore.",
                      "Rapporto finale entro 14 giorni da quando è disponibile una misura correttiva (vulnerabilità) o entro un mese (incidente grave).",
                      "Le segnalazioni passano dalla piattaforma unica di segnalazione dell'ENISA; gli utenti vanno informati."],
        "rep_sme": "Come micro o piccola impresa non puoi ricevere sanzioni pecuniarie per il solo mancato rispetto dei termini di 24 ore dell'allerta preliminare (art. 64(10)(a)); l'obbligo resta.",
        "rep_not_direct": "La segnalazione è un obbligo del fabbricante.",
        "support_text": "Gli aggiornamenti di sicurezza vanno forniti per almeno {n} anni.",
        "support_reflect": "Il periodo di supporto deve riflettere la durata d'uso prevista che hai indicato ({u} anni).",
        "support_unknown": "Gli aggiornamenti di sicurezza vanno forniti per almeno 5 anni, o per la durata d'uso prevista se inferiore.",
        "cyber_intro": "Dal 20 gennaio 2027 alla macchina si applicano questi punti dell'Allegato III:",
        "cyber_high": "Il sistema di comando è connesso, accessibile da remoto o aggiornabile: questi punti vanno trattati in dettaglio nella valutazione dei rischi e nel fascicolo tecnico.",
        "cyber_cert": "Un certificato o una dichiarazione di conformità secondo un sistema europeo di certificazione della cybersicurezza dà presunzione di conformità per 1.1.9 e 1.2.1 nei limiti di ciò che copre (art. 20(9)).",
        "partly": "La quasi-macchina non porta la marcatura CE: è accompagnata dalla dichiarazione di incorporazione e dalle istruzioni di assemblaggio.",
        "both": "Il prodotto ricade in entrambe le normative. Il fascicolo tecnico deve mostrare come rispetta i requisiti essenziali del CRA (Allegato I) e i requisiti 1.1.9 e 1.2.1 del Regolamento Macchine. Una sola valutazione dei rischi può coprirli entrambi, se tratta tutti e due gli insiemi di requisiti.",
        "one_cra": "A questo prodotto si applica solo il CRA: non c'è sovrapposizione con il Regolamento Macchine.",
        "one_mr": "A questo prodotto si applica solo il Regolamento Macchine: non c'è sovrapposizione con il CRA.",
        "neither": "In base alle risposte fornite non si applica nessuna delle due normative.",
        "t_date": "Data", "t_event": "Cosa si applica", "t_status": "Stato", "t_basis": "Base",
        "in_force": "In vigore", "upcoming": "In arrivo",
        "unit_note": "L'immissione sul mercato si valuta esemplare per esemplare: gli esemplari immessi dal 20 gennaio 2027 devono rispettare il Regolamento Macchine anche se il modello era già in vendita.",
        "legacy_note": "I prodotti immessi sul mercato prima dell'11 dicembre 2027 devono rispettare i requisiti essenziali del CRA solo se modificati in modo sostanziale dopo quella data; gli obblighi di segnalazione valgono comunque (art. 69).",
        "g_practice": "Pratica", "g_status": "Stato", "g_priority": "Priorità", "g_due": "Entro", "g_basis": "Base",
        "st_in_place": "In atto", "st_partial": "In parte", "st_missing": "Assente", "st_unknown": "Non noto", "st_not_applicable": "Non applicabile",
        "pr_high": "Alta", "pr_medium": "Media",
        "gap_intro": "Priorità alta: il requisito si applica già o si applica entro circa sei mesi. Media: si applica più avanti.",
        "sbom_note": "Il prodotto contiene componenti di terzi o open source: l'inventario dei componenti software (SBOM) è centrale per gestire le vulnerabilità.",
        "q": "Domanda", "a": "Risposta", "years": "anni",
        "sources": ["Regolamento (UE) 2024/2847 (Cyber Resilience Act), GU L 2024/2847, 20.11.2024",
                    "Regolamento di esecuzione (UE) 2025/2392 della Commissione sulle descrizioni tecniche dei prodotti importanti e critici",
                    "Regolamento (UE) 2023/1230 relativo alle macchine, testo consolidato del 27.07.2026"],
        "limits": "Limiti: alla data delle regole nessuna norma armonizzata del CRA era citata in Gazzetta Ufficiale; il rinvio dei requisiti 1.1.9 e 1.2.1 del Regolamento Macchine chiesto dall'industria non era stato adottato. Le regole vengono riviste ogni mese.",
        "next_title": "Prossimo passo",
        "next_text": "Pentaflowers può trasformare questo orientamento in un piano: conferma dell'ambito, valutazione dei rischi, fascicolo tecnico e procedura di segnalazione. Prenota una diagnosi su {url}.",
        "std_summary": "{cra} {mr} La prossima scadenza che riguarda il prodotto è il {next}.",
        "std_summary_none": "{cra} {mr}",
        "std_cra_applies": "Il CRA si applica a questo prodotto. La classe deriva dalla funzione principale e determina la procedura di valutazione della conformità.",
        "std_cra_not": "In base alle risposte fornite, il CRA non si applica a questo prodotto.",
        "std_mr_applies": "Il Regolamento Macchine si applica a questo prodotto. Sostituisce la direttiva 2006/42/CE e aggiunge requisiti di cybersicurezza per i sistemi di comando.",
        "std_mr_not": "In base alle risposte fornite, il Regolamento Macchine non si applica a questo prodotto.",
        "std_next": "Parti dalle azioni con priorità alta della checklist dei gap, poi pianifica le altre prima delle rispettive scadenze.",
        "std_next_none": "In base alle risposte fornite non servono azioni per queste due normative. Ripeti il check se il prodotto o il suo mercato cambiano.",
        "llm_label": "Testo scritto con l'AI a partire dagli esiti qui sopra e controllato automaticamente.",
    },
}

MR_REQ_IT = {
    "MR-1.1.9-1": "Il collegamento di un altro dispositivo, direttamente o tramite un dispositivo remoto, non deve creare situazioni pericolose",
    "MR-1.1.9-2": "I componenti hardware che trasmettono segnali o dati rilevanti per l'accesso al software critico per la conformità sono protetti dalla corruzione accidentale o intenzionale, con raccolta delle prove di intervento legittimo o illegittimo",
    "MR-1.1.9-3": "Software e dati critici per la conformità sono identificati e protetti dalla corruzione accidentale o intenzionale",
    "MR-1.1.9-4": "La macchina identifica il software necessario a funzionare in sicurezza e può fornire questa informazione in ogni momento",
    "MR-1.1.9-5": "La macchina raccoglie le prove di interventi legittimi o illegittimi sul software, sulle sue modifiche o sulla configurazione",
    "MR-1.2.1-a": "I sistemi di comando resistono alle influenze esterne previste e impreviste, compresi i tentativi dolosi ragionevolmente prevedibili di terzi",
    "MR-1.2.1-f": "Registro di tracciamento degli interventi e delle versioni del software di sicurezza caricate dopo l'immissione sul mercato, conservato per cinque anni",
}

CITE_IT = [("Implementing Regulation", "Regolamento di esecuzione"), ("Annex", "Allegato"), ("Part", "parte"), ("Art.", "art."), ("MR ", "Reg. Macchine ")]


def tr(lang: str) -> dict:
    return T.get(lang, T["en"])


def ui(lang: str) -> dict:
    return UI.get(lang, UI["en"])


def fmt_date(iso: str, lang: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS.get(lang, MONTHS['en'])[d.month - 1]} {d.year}"


def cite(s: str, lang: str) -> str:
    if lang == "it":
        for a, b in CITE_IT:
            s = s.replace(a, b)
    return s


def cites(lst, lang) -> str:
    return " · ".join(cite(c, lang) for c in (lst or []))


# ------------------------------------------------------------------ facts given to the LLM
def facts(result: dict, lang: str) -> dict:
    R = result["results"]
    U = ui(lang)
    f = {"language": lang, "rules_version": result["rules_version"], "evaluated_on": result["evaluated_on"]}
    r1 = R["R1"]
    f["cra"] = {"status": r1["status"], "reason": r1.get("reason"), "role": r1.get("role"), "basis": r1.get("cites")}
    if R["R2"].get("status") == "ok":
        f["cra"]["class"] = R["R2"]["class"]
        f["cra"]["category"] = U["cra"].get(R["R2"].get("category") or "other")
        f["cra"]["procedures"] = [U["procedure"].get(p, p) for p in R["R3"]["procedures"]]
        f["cra"]["notified_body_needed"] = R["R3"]["notified_body"] == "yes"
        f["cra"]["procedure_basis"] = R["R3"]["cites"]
    if R["R4"].get("status") == "applies":
        f["cra"]["reporting"] = {"since": R["R4"]["since"], "early_warning_hours": 24, "notification_hours": 72,
                                 "sme_fine_exemption": bool(R["R4"].get("sme_fine_exemption")), "basis": R["R4"]["cites"]}
    if R["R5"].get("status") == "ok":
        f["cra"]["support_period_min_years"] = R["R5"]["min_years"]
    r6 = R["R6"]
    f["machinery"] = {"status": r6["status"], "modification": r6.get("modification"), "basis": r6.get("cites")}
    if R["R7"].get("status") == "ok":
        f["machinery"]["annex_i_part"] = R["R7"]["annex_i_part"]
        f["machinery"]["procedures"] = [U["procedure"].get(p, p) for p in R["R7"]["procedures"]]
        f["machinery"]["notified_body_needed"] = R["R7"]["notified_body"] == "yes"
    if R["R8"].get("status") == "applies":
        f["machinery"]["cyber_requirements"] = {"from": R["R8"]["from"], "points": ["1.1.9", "1.2.1"],
                                                "detailed_treatment_needed": R["R8"]["exposure"] == "high"}
    if f["machinery"].get("annex_i_part"):
        f["machinery"]["annex"] = f"Annex I Part {f['machinery']['annex_i_part']}"
    refs = set()
    for r in R.values():
        refs.update(r.get("cites") or [])
    for g in R["R10"]["items"]:
        refs.update(g.get("cites") or [])
    f["references"] = sorted(refs)
    f["timeline"] = [{"date": i["date"], "what": U["deadline"][i["key"]], "in_force": i["in_force"]} for i in R["R9"]["items"]]
    gaps = [g for g in R["R10"]["items"] if g["status"] in ("partial", "missing", "unknown")]
    f["gaps"] = [{"practice": U["q"][g["id"]]["label"], "priority": g["priority"], "due": g["due"]} for g in gaps]
    return f


# ------------------------------------------------------------------ check of LLM text
DATE_NUM = re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b")
DATE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
ANNEX = re.compile(r"\b(?:annex|allegato|allegati)\s+([IVX]+)\b", re.I)


def _dates_in(text: str) -> set[str]:
    out = set()
    for d, m, y in DATE_NUM.findall(text):
        out.add(f"{int(y):04d}-{int(m):02d}-{int(d):02d}")
    for y, m, d in DATE_ISO.findall(text):
        out.add(f"{y}-{m}-{d}")
    for names in MONTHS.values():
        for i, name in enumerate(names):
            for d, y in re.findall(rf"\b(\d{{1,2}})\s+{name}\s+(\d{{4}})\b", text, re.I):
                out.add(f"{int(y):04d}-{i + 1:02d}-{int(d):02d}")
    return out


def check(text: str, fx: dict) -> list[str]:
    """Return the problems found; empty list = the paragraph only uses facts from the engine."""
    blob = json.dumps(fx, ensure_ascii=False)
    problems = []
    allowed_dates = set(DATE_ISO.findall(blob))
    allowed_dates = {f"{y}-{m}-{d}" for y, m, d in allowed_dates}
    for d in _dates_in(text):
        if d not in allowed_dates:
            problems.append(f"date {d}")
    allowed_nums = set(re.findall(r"\d+", blob)) | {str(int(n)) for n in re.findall(r"\d+", blob)}
    for n in re.findall(r"\d+", text):
        if n not in allowed_nums and str(int(n)) not in allowed_nums:
            problems.append(f"number {n}")
    allowed_annex = {a.upper() for a in ANNEX.findall(blob)}
    for a in ANNEX.findall(text):
        if a.upper() not in allowed_annex:
            problems.append(f"annex {a}")
    return problems


def standard_texts(result: dict, lang: str) -> dict:
    t = tr(lang)
    R = result["results"]
    cra_on = R["R1"]["status"] == "applies"
    mr_on = R["R6"]["status"] == "applies"
    nxt = result["summary"].get("next_deadline")
    cra_s = t["std_cra_applies"] if cra_on else t["std_cra_not"]
    mr_s = t["std_mr_applies"] if mr_on else t["std_mr_not"]
    summary = (t["std_summary"].format(cra=cra_s, mr=mr_s, next=fmt_date(nxt["date"], lang)) if nxt
               else t["std_summary_none"].format(cra=cra_s, mr=mr_s))
    overlap = t["both"] if cra_on and mr_on else t["one_cra"] if cra_on else t["one_mr"] if mr_on else t["neither"]
    has_gaps = any(g["status"] in ("partial", "missing", "unknown") for g in R["R10"]["items"])
    return {"summary": summary, "cra": cra_s, "mr": mr_s, "overlap": overlap,
            "next_steps": t["std_next"] if has_gaps else t["std_next_none"]}


LLM_SYSTEM = """You write short plain-language paragraphs for a compliance orientation report about the EU Cyber Resilience Act (CRA) and the EU Machinery Regulation.

You receive only the outcomes computed by a rule engine. Rules:
- Write in {language}. Each paragraph at most 80 words, for a technical director. No headings, no lists, no markdown.
- Use only the facts given. Do not add obligations, deadlines, dates, numbers, articles, annexes or legal conclusions that are not in the facts. Never contradict them.
- When a regulation does not apply, say so in one sentence and do not describe its obligations.
- Do not repeat the full tables: explain what the outcomes mean and why they matter.
- summary: the overall picture. cra: CRA outcomes. mr: Machinery Regulation outcomes. overlap: how the two relate for this product. next_steps: what to do first, based on the gaps.
Always answer by calling the write_report_texts tool."""


def _tool() -> dict:
    return {"name": "write_report_texts", "description": "Plain-language paragraphs for the report.",
            "input_schema": {"type": "object", "properties": {k: {"type": "string"} for k in LLM_KEYS},
                             "required": LLM_KEYS}}


def llm_texts(result: dict, lang: str, caller) -> tuple[dict, dict]:
    """Return (texts, origin). origin[key] is 'llm' or 'standard'. Two attempts, then standard text per paragraph."""
    std = standard_texts(result, lang)
    fx = facts(result, lang)
    lang_name = {"it": "Italian", "en": "English"}.get(lang, "English")
    texts, origin = dict(std), {k: "standard" for k in LLM_KEYS}
    pending = list(LLM_KEYS)
    for _ in range(2):
        if not pending:
            break
        try:
            raw = caller(LLM_SYSTEM.format(language=lang_name), json.dumps(fx, ensure_ascii=False), _tool())
        except Exception:
            continue
        for k in list(pending):
            v = re.sub(r"\s+", " ", str(raw.get(k) or "")).strip()
            if 20 <= len(v) <= 900 and not check(v, fx):
                texts[k], origin[k] = v, "llm"
                pending.remove(k)
    return texts, origin


# ------------------------------------------------------------------ report structure
def answer_label(qid: str, val, lang: str) -> str:
    U = ui(lang)
    q = U["q"].get(qid, {})
    if qid == "B4":
        return U["cra"].get(val, val)
    if qid == "C2":
        return U["mr"].get(val, val)
    if qid == "B5":
        return ", ".join(q.get("options", {}).get(v, v) for v in val) or tr(lang)["none"]
    if qid == "B7":
        n = int(val) if float(val).is_integer() else val
        return f"{n} {tr(lang)['years']}"
    if qid.startswith("D"):
        return U["practice"].get(val, val)
    return q.get("options", {}).get(val, str(val))


def build(result: dict, product: dict, lang: str, texts: dict, origin: dict, today: date) -> dict:
    t, U, R, S = tr(lang), ui(lang), result["results"], result["summary"]
    o = U["outcome"]
    yesno = lambda b: t["yes"] if b else t["no"]
    sec = []

    def p(text, llm=False):
        return {"type": "p", "text": text, "llm": llm}

    # 1. Summary
    status_word = {"applies": t["applies"], "not_applies": t["not_applies"], "excluded": t["excluded"]}
    nb = []
    if S["cra_notified_body"]:
        nb.append(t["nb_cra"].format(v=yesno(S["cra_notified_body"] == "yes")))
    if S["mr_notified_body"]:
        nb.append(t["nb_mr"].format(v=yesno(S["mr_notified_body"] == "yes")))
    nxt = S.get("next_deadline")
    kv = [(t["k_cra"], status_word[S["cra"]]),
          (t["k_class"], o[f"class_{S['cra_class']}"] if S["cra_class"] else t["na"]),
          (t["k_mr"], status_word[S["mr"]] + (f" · {o['mr_part_' + S['mr_annex_i_part']]}" if S.get("mr_annex_i_part") else "")),
          (t["k_proc"], "; ".join(nb) if nb else t["na"]),
          (t["k_next"], f"{fmt_date(nxt['date'], lang)} · {U['deadline'][nxt['key']]}" if nxt else t["none"])]
    actions = [U["q"][a]["label"] for a in S["top_actions"]]
    sec.append({"id": "summary", "title": t["s_summary"], "blocks": [
        {"type": "kv", "rows": kv},
        p(texts["summary"], origin["summary"] == "llm"),
        {"type": "h", "text": t["k_actions"]},
        {"type": "bullets", "items": actions or [t["none"]]},
    ]})

    # 2. CRA
    r1 = R["R1"]
    b = [{"type": "h", "text": t["scope"]},
         p(o[f"cra_{r1['status']}"] + ("" if r1["status"] == "applies" else " " + o.get(f"reason_{r1.get('reason')}", ""))),
         {"type": "cite", "text": f"{t['basis']}: {cites(r1.get('cites'), lang)}"}]
    if r1["status"] == "applies":
        if r1.get("role") != "manufacturer" and o.get(f"role_{r1['role']}"):
            b.append(p(o[f"role_{r1['role']}"]))
        if "hardware_with_data_connection" in (r1.get("notes") or []):
            b.append(p(o["hardware_note"]))
        r2, r3 = R["R2"], R["R3"]
        b += [{"type": "h", "text": t["class"]},
              {"type": "kv", "rows": [(t["class"], o[f"class_{r2['class']}"]), (t["category"], U["cra"][r2.get("category") or "other"])]},
              {"type": "cite", "text": f"{t['basis']}: {cites(r2.get('cites'), lang)}"},
              {"type": "h", "text": t["procedure"]},
              p(U["outcome"]["future_module_A"] if r3.get("future_note") else ""),
              {"type": "bullets", "items": [U["procedure"].get(x, x) for x in r3["procedures"]]},
              p(f"{t['k_proc']}: {yesno(r3['notified_body'] == 'yes')}"),
              {"type": "cite", "text": f"{t['basis']}: {cites(r3.get('cites'), lang)}"}]
        r4 = R["R4"]
        b.append({"type": "h", "text": t["reporting"]})
        if r4["status"] == "applies":
            since = fmt_date(r4["since"], lang)
            b += [p((t["rep_since"] if r4["in_force"] else t["rep_since_future"]).format(d=since)),
                  {"type": "bullets", "items": t["rep_items"]}]
            if r4.get("sme_fine_exemption"):
                b.append(p(t["rep_sme"]))
            b.append({"type": "cite", "text": f"{t['basis']}: {cites(r4.get('cites'), lang)}"})
        else:
            b.append(p(t["rep_not_direct"]))
        r5 = R["R5"]
        if r5.get("status") == "ok":
            b.append({"type": "h", "text": t["support"]})
            if r5.get("expected_use_years") is None:
                b.append(p(t["support_unknown"]))
            else:
                b.append(p(t["support_text"].format(n=r5["min_years"])))
                if r5.get("reflect_expected_use"):
                    b.append(p(t["support_reflect"].format(u=r5["expected_use_years"])))
            b.append({"type": "cite", "text": f"{t['basis']}: {cites(r5.get('cites'), lang)}"})
    b.append(p(texts["cra"], origin["cra"] == "llm"))
    sec.append({"id": "cra", "title": t["s_cra"], "blocks": [x for x in b if not (x["type"] == "p" and not x["text"])]})

    # 3. Machinery Regulation
    r6, r7, r8 = R["R6"], R["R7"], R["R8"]
    b = [{"type": "h", "text": t["scope"]}, p(o[f"mr_{r6['status']}"]),
         {"type": "cite", "text": f"{t['basis']}: {cites(r6.get('cites'), lang)}"}]
    if r6.get("modification"):
        b += [{"type": "h", "text": t["modification"]},
              p(o["mr_substantial"] if r6["modification"] == "substantial" else o["mr_not_substantial"])]
    if r7.get("status") == "ok":
        part = r7.get("annex_i_part")
        b += [{"type": "h", "text": t["annex_i"]},
              p(o[f"mr_part_{part}"] if part else U["outcome"].get("mr_not_in_annex", "") or ("Non rientra nell'Allegato I" if lang == "it" else "Not in Annex I")),
              {"type": "h", "text": t["procedure"]},
              {"type": "bullets", "items": [U["procedure"].get(x, x) for x in r7["procedures"]]},
              p(f"{t['k_proc']}: {yesno(r7['notified_body'] == 'yes')}"),
              {"type": "cite", "text": f"{t['basis']}: {cites(r7.get('cites'), lang)}"}]
        if r6.get("product_type") == "partly_completed":
            b.append(p(t["partly"]))
    if r8.get("status") == "applies":
        reqs = [(MR_REQ_IT.get(q["id"], q["text"]) if lang == "it" else q["text"]) + f" ({cite(q['cite'], lang)})" for q in r8["requirements"]]
        b += [{"type": "h", "text": t["cyber"]}, p(t["cyber_intro"]), {"type": "bullets", "items": reqs}]
        if r8["exposure"] == "high":
            b.append(p(t["cyber_high"]))
        b.append(p(t["cyber_cert"]))
    if R["R9"].get("mr_unit_note"):
        b.append(p(t["unit_note"]))
    b.append(p(texts["mr"], origin["mr"] == "llm"))
    sec.append({"id": "mr", "title": t["s_mr"], "blocks": b})

    # 4. Overlap
    sec.append({"id": "overlap", "title": t["s_overlap"], "blocks": [p(texts["overlap"], origin["overlap"] == "llm")]})

    # 5. Timeline
    items = R["R9"]["items"]
    tb = [{"type": "table", "head": [t["t_date"], t["t_event"], t["t_status"], t["t_basis"]],
           "rows": [[fmt_date(i["date"], lang), U["deadline"][i["key"]], t["in_force"] if i["in_force"] else t["upcoming"], cite(i["cite"], lang)] for i in items],
           "widths": [0.18, 0.47, 0.13, 0.22]}] if items else [p(t["none"])]
    if R["R9"].get("cra_legacy_note"):
        tb.append(p(t["legacy_note"]))
    sec.append({"id": "timeline", "title": t["s_timeline"], "blocks": tb})

    # 6. Gaps
    rows = []
    for g in R["R10"]["items"]:
        if g["status"] == "not_applicable":
            continue
        rows.append([U["q"][g["id"]]["label"], t[f"st_{g['status']}"], t[f"pr_{g['priority']}"] if g.get("priority") else "—",
                     fmt_date(g["due"], lang), cites(g.get("cites"), lang)])
    order = {t["pr_high"]: 0, t["pr_medium"]: 1, "—": 2}
    rows.sort(key=lambda r: order.get(r[2], 3))
    gb = [p(t["gap_intro"])]
    gb.append({"type": "table", "head": [t["g_practice"], t["g_status"], t["g_priority"], t["g_due"], t["g_basis"]], "rows": rows,
               "widths": [0.34, 0.12, 0.1, 0.16, 0.28], "status_col": 1, "priority_col": 2} if rows else p(t["none"]))
    if R["R10"].get("sbom_note"):
        gb.append(p(t["sbom_note"]))
    gb.append(p(texts["next_steps"], origin["next_steps"] == "llm"))
    sec.append({"id": "gaps", "title": t["s_gaps"], "blocks": gb})

    # 7. Data
    order_q = [q for blk in ["A", "B", "C", "D"] for q in U["q"] if q.startswith(blk)]
    arows = [[U["q"][q]["label"], answer_label(q, result["answers"][q], lang)] for q in order_q if q in result["answers"]]
    sec.append({"id": "data", "title": t["s_data"], "blocks": [{"type": "table", "head": [t["q"], t["a"]], "rows": arows, "widths": [0.62, 0.38]}]})

    # 8. Sources, limits, next step
    sec.append({"id": "sources", "title": t["s_sources"], "blocks": [
        {"type": "bullets", "items": t["sources"] + [f"{t['rules']}: {result['rules_version']}"]},
        p(t["limits"]),
        {"type": "h", "text": t["next_title"]},
        p(t["next_text"].format(url=DIAGNOSIS_URL.replace("https://", ""))),
    ]})

    return {"lang": lang, "meta": {
        "title": t["title"], "subtitle": t["subtitle"], "product": (product.get("name") or "").strip()[:120],
        "date": fmt_date(today.isoformat(), lang), "rules_version": result["rules_version"], "disclaimer": t["disclaimer"],
        "footer": t["footer"], "llm_label": t["llm_label"],
        "labels": {"product": t["product"], "date": t["date"], "rules": t["rules"]}}, "sections": sec}
