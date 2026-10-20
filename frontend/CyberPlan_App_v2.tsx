// CyberPlan — app (v2): screens 1–4 (start, product, questionnaire, preview).
// Design: Pentaflowers design guide v5 (light theme). All texts come from ./i18n (CyberPlan_i18n).
// The app never decides a regulatory outcome: it sends the answers to the CyberPlan API and shows what it returns.

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { copy, LANGS, type Lang, type Dict } from './i18n';

const API = 'https://cyberplan-api.onrender.com';
const PENTAFLOWERS_URL = 'https://www.pentaflowers.com';
const PRIVACY_URL = 'https://www.pentaflowers.com/#privacy';
const LEGAL_URL = ''; // separate legal notice page: add its address here if it exists

// ---------------------------------------------------------------- design tokens (guide v5)
const C = {
  bg: '#FFFFFF', mineral: '#F6F5F2', panel: '#E6E8EE', ink: '#0D0F22', body: '#2E3350', muted: '#4A4F6A',
  soft: '#C9CCD6', eyebrow: '#0A7C9C', tag: '#3B4A8C', accent: '#D63B30', accentHover: '#B8302A',
  green: '#22663D', greenBg: '#DEF0E4', inputBg: '#F4F5F8',
  dark: '#0D0F22', darkLink: '#B9BCCE', darkActive: '#1F2344', darkText: '#F4F2EC', darkBorder: '#3A3F66',
  dots: ['#E0443A', '#EDC948', '#4C72E6', '#4FB872'],
};
const SANS = "'Space Grotesk', system-ui, sans-serif";
const MONO = "'Space Mono', ui-monospace, monospace";
const gridCols = (min: number) => `repeat(auto-fit, minmax(min(100%, ${min}px), 1fr))`;

const GLOBAL_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
html, body { margin: 0; background: ${C.bg}; }
.cp-root { font-family: ${SANS}; color: ${C.body}; background: ${C.bg}; min-height: 100vh; display: flex; flex-direction: column; overflow-x: hidden; }
.cp-root *, .cp-root *::before, .cp-root *::after { box-sizing: border-box; }
.cp-wrap { width: 100%; max-width: 1280px; margin: 0 auto; padding-left: 20px; padding-right: 20px; }
@media (min-width: 640px) { .cp-wrap { padding-left: 32px; padding-right: 32px; } }
.cp-input { width: 100%; font: inherit; font-size: 16px; color: ${C.ink}; background: ${C.inputBg}; border: 1px solid ${C.soft}; border-radius: 0; padding: 12px 14px; min-height: 48px; }
.cp-input:focus { outline: none; border-color: ${C.ink}; }
.cp-btn-primary { background: ${C.accent}; color: #fff; }
.cp-btn-primary:hover { background: ${C.accentHover}; }
.cp-btn-outline:hover { background: ${C.mineral}; }
.cp-choice:focus-within { outline: 2px solid ${C.ink}; outline-offset: 2px; }
.cp-link { color: ${C.darkLink}; text-decoration: none; }
.cp-link:hover { color: ${C.darkText}; text-decoration: underline; }
.cp-by { white-space: nowrap; }
@media (max-width: 420px) { .cp-by { display: none; } }
.cp-sr { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }
`;

// ---------------------------------------------------------------- questionnaire model
type Answers = Record<string, any>;
type QType = 'single' | 'multi' | 'number' | 'cra' | 'mr' | 'practice';
interface QDef { id: string; type: QType; options?: string[]; show?: (a: Answers) => boolean; optional?: boolean }

const YN = ['yes', 'no'];
const craPossible = (a: Answers) => a.A2 !== 'no' && a.B2 !== 'no' && (a.B3 ?? 'none') === 'none';
const isMachine = (a: Answers) => !!a.C1 && a.C1 !== 'none';

const BLOCKS: { key: 'A' | 'B' | 'C' | 'D'; questions: QDef[] }[] = [
  { key: 'A', questions: [
    { id: 'A1', type: 'single', options: ['manufacturer', 'importer', 'distributor', 'modifier'] },
    { id: 'A1m', type: 'single', options: YN, show: (a) => a.A1 === 'modifier' },
    { id: 'A2', type: 'single', options: YN },
    { id: 'A3', type: 'single', options: ['micro', 'small', 'medium', 'large'] },
    { id: 'A4', type: 'single', options: YN },
  ] },
  { key: 'B', questions: [
    { id: 'B1', type: 'single', options: YN },
    { id: 'B2', type: 'single', options: YN },
    { id: 'B3', type: 'single', options: ['medical', 'vehicles', 'aviation', 'marine', 'defence', 'none'] },
    { id: 'B4', type: 'cra', show: craPossible },
    { id: 'B5', type: 'multi', options: ['ethernet', 'wifi', 'cellular', 'fieldbus', 'usb', 'remote_cloud'], optional: true },
    { id: 'B6', type: 'single', options: ['yes', 'no', 'unknown'], show: craPossible },
    { id: 'B7', type: 'number', show: craPossible },
  ] },
  { key: 'C', questions: [
    { id: 'C1', type: 'single', options: ['machinery', 'interchangeable_equipment', 'safety_component', 'lifting_accessory', 'chains_ropes_webbing', 'removable_transmission', 'partly_completed', 'none'] },
    { id: 'C2', type: 'mr', show: isMachine },
    { id: 'C2h', type: 'single', options: ['yes', 'no', 'unknown'], show: (a) => isMachine(a) && String(a.C2 ?? '').startsWith('B.') },
    { id: 'C3', type: 'single', options: YN, show: isMachine },
    { id: 'C4', type: 'single', options: YN, show: isMachine },
    { id: 'C5', type: 'single', options: YN, show: isMachine },
    { id: 'C6', type: 'single', options: YN, show: isMachine },
    { id: 'C6a', type: 'single', options: YN, show: (a) => isMachine(a) && a.C6 === 'yes' },
    { id: 'C6b', type: 'single', options: YN, show: (a) => isMachine(a) && a.C6 === 'yes' },
    { id: 'C6c', type: 'single', options: YN, show: (a) => isMachine(a) && a.C6 === 'yes' },
    { id: 'C7', type: 'single', options: ['before', 'after'], show: isMachine },
  ] },
  { key: 'D', questions: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9'].map((id) => ({ id, type: 'practice' as QType })) },
];

const CRA_GROUPS: { group: string; codes: string[] }[] = [
  { group: 'craI', codes: Array.from({ length: 19 }, (_, i) => `III.I.${i + 1}`) },
  { group: 'craII', codes: ['III.II.1', 'III.II.2', 'III.II.3', 'III.II.4'] },
  { group: 'craIV', codes: ['IV.1', 'IV.2', 'IV.3'] },
  { group: 'other', codes: ['other'] },
];
const MR_GROUPS: { group: string; codes: string[] }[] = [
  { group: 'mrA', codes: ['A.1', 'A.2', 'A.3', 'A.4', 'A.5', 'A.6'] },
  { group: 'mrB', codes: Array.from({ length: 19 }, (_, i) => `B.${i + 1}`) },
  { group: 'other', codes: ['none'] },
];

const visible = (q: QDef, a: Answers) => !q.show || q.show(a);
const answered = (q: QDef, a: Answers) => {
  const v = a[q.id];
  if (q.type === 'multi') return true;
  if (q.type === 'number') return v !== undefined && v !== '' && !Number.isNaN(Number(v));
  return v !== undefined && v !== '';
};

/** Only visible questions travel to the API; hidden answers are dropped. */
function payload(a: Answers): Answers {
  const out: Answers = {};
  for (const b of BLOCKS) for (const q of b.questions) {
    if (!visible(q, a)) continue;
    const v = a[q.id];
    if (q.type === 'multi') out[q.id] = Array.isArray(v) ? v : [];
    else if (q.type === 'number') { if (v !== undefined && v !== '') out[q.id] = Number(v); }
    else if (v !== undefined && v !== '') out[q.id] = v;
  }
  return out;
}

// ---------------------------------------------------------------- small helpers
function fill(s: string, vars: Record<string, string | number>) {
  return s.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ''));
}
function fmtDate(iso: string, lang: Lang) {
  const d = new Date(iso + 'T12:00:00');
  return new Intl.DateTimeFormat(lang === 'it' ? 'it-IT' : 'en-GB', { day: 'numeric', month: 'long', year: 'numeric' }).format(d);
}
function cite(s: string, t: Dict) {
  return t.citeMap.reduce((acc, [from, to]) => acc.split(from).join(to), s);
}
function initialLang(): Lang {
  try {
    const n = (navigator.language || 'en').slice(0, 2).toLowerCase();
    return (LANGS as string[]).includes(n) ? (n as Lang) : 'en';
  } catch { return 'en'; }
}

// ---------------------------------------------------------------- icons (inline stroke SVG)
const Arrow = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
);
const ArrowLeft = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6" /></svg>
);
const Check = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 12.5l5 5L20 6.5" /></svg>
);
const Dots = () => (
  <span aria-hidden="true" style={{ display: 'inline-grid', gridTemplateColumns: '8px 8px', gap: 3 }}>
    {C.dots.map((c) => <span key={c} style={{ width: 8, height: 8, borderRadius: 999, background: c, display: 'block' }} />)}
  </span>
);

// ---------------------------------------------------------------- building blocks
function Eyebrow({ children }: { children: React.ReactNode }) {
  return <p style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.eyebrow, margin: 0 }}>{children}</p>;
}
function H1({ children }: { children: React.ReactNode }) {
  return <h1 style={{ fontFamily: SANS, fontWeight: 500, fontSize: 'clamp(38px, 6vw, 80px)', lineHeight: 0.96, letterSpacing: '-0.045em', color: C.ink, margin: 0 }}>{children}</h1>;
}
function H2({ children }: { children: React.ReactNode }) {
  return <h2 style={{ fontFamily: SANS, fontWeight: 500, fontSize: 'clamp(28px, 3vw, 42px)', lineHeight: 1.05, letterSpacing: '-0.035em', color: C.ink, margin: 0 }}>{children}</h2>;
}
function H3({ children }: { children: React.ReactNode }) {
  return <h3 style={{ fontFamily: SANS, fontWeight: 600, fontSize: 22, letterSpacing: '-0.015em', color: C.ink, margin: 0 }}>{children}</h3>;
}
function P({ children, muted }: { children: React.ReactNode; muted?: boolean }) {
  return <p style={{ fontSize: 17, lineHeight: 1.6, color: muted ? C.muted : C.body, margin: 0 }}>{children}</p>;
}
const btnBase: React.CSSProperties = {
  fontFamily: SANS, fontWeight: 600, fontSize: 16, borderRadius: 999, minHeight: 48, padding: '12px 22px',
  display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 10, cursor: 'pointer', border: 'none',
};
function PrimaryButton({ children, onClick, disabled }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean }) {
  return <button type="button" className="cp-btn-primary" onClick={onClick} disabled={disabled} style={{ ...btnBase, opacity: disabled ? 0.6 : 1 }}>{children}<Arrow /></button>;
}
function OutlineButton({ children, onClick, back }: { children: React.ReactNode; onClick?: () => void; back?: boolean }) {
  return (
    <button type="button" className="cp-btn-outline" onClick={onClick} style={{ ...btnBase, background: 'transparent', color: C.ink, border: `1px solid ${C.ink}` }}>
      {back && <ArrowLeft />}{children}{!back && <Arrow />}
    </button>
  );
}
type BadgeKind = 'green' | 'blue' | 'ink' | 'tag';
function Badge({ kind, children }: { kind: BadgeKind; children: React.ReactNode }) {
  const s: Record<BadgeKind, React.CSSProperties> = {
    green: { background: C.greenBg, color: C.green },
    blue: { background: C.tag, color: '#fff' },
    ink: { background: C.ink, color: '#fff' },
    tag: { background: 'transparent', color: C.tag, border: `1px solid ${C.tag}` },
  };
  return <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, padding: '4px 10px', borderRadius: 999, display: 'inline-block', ...s[kind] }}>{children}</span>;
}
function Cite({ children }: { children: React.ReactNode }) {
  return <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.muted }}>{children}</span>;
}
function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return <div style={{ background: C.bg, border: `1px solid ${C.ink}`, padding: 24, display: 'flex', flexDirection: 'column', gap: 14, ...style }}>{children}</div>;
}

// ---------------------------------------------------------------- header, footer, progress
function Header({ lang, setLang, t }: { lang: Lang; setLang: (l: Lang) => void; t: Dict }) {
  return (
    <header style={{ background: C.dark }}>
      <div className="cp-wrap" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, minHeight: 68 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Dots />
          <span style={{ color: C.darkText, fontWeight: 600, fontSize: 20, letterSpacing: '-0.02em' }}>{t.ui.brand}</span>
          <span className="cp-by" style={{ color: C.darkLink, fontFamily: MONO, fontWeight: 700, fontSize: 13 }}>{t.ui.by}</span>
        </div>
        <div role="group" aria-label={t.ui.language} style={{ display: 'flex', gap: 4, border: `1px solid ${C.darkBorder}`, borderRadius: 999, padding: 3 }}>
          {LANGS.map((l) => (
            <button key={l} type="button" onClick={() => setLang(l)} aria-pressed={lang === l}
              style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, minWidth: 44, minHeight: 36, borderRadius: 999, border: 'none', cursor: 'pointer',
                background: lang === l ? C.darkActive : 'transparent', color: lang === l ? C.darkText : C.darkLink }}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
}

function Footer({ t }: { t: Dict }) {
  const link = (url: string, label: string) => url
    ? <a className="cp-link" href={url} target="_blank" rel="noopener noreferrer">{label}</a>
    : null;
  return (
    <footer style={{ background: C.dark, marginTop: 'auto' }}>
      <div className="cp-wrap" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 16, paddingTop: 28, paddingBottom: 28, fontSize: 15 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: C.darkText }}>
          <Dots /><span>{t.ui.footerTool}</span>
          <a className="cp-link" href={PENTAFLOWERS_URL} target="_blank" rel="noopener noreferrer">{t.ui.footerLink}</a>
        </div>
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          {link(PRIVACY_URL, t.ui.privacy)}
          {link(LEGAL_URL, t.ui.legal)}
        </div>
      </div>
    </footer>
  );
}

function Progress({ current, t }: { current: number; t: Dict }) {
  return (
    <nav aria-label={t.ui.stepsLabel} style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
      {[1, 2, 3, 4, 5, 6].map((n) => (
        <span key={n} aria-current={n === current ? 'step' : undefined}
          style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, minWidth: 36, padding: '4px 0', textAlign: 'center',
            borderBottom: `3px solid ${n <= current ? C.ink : C.soft}`, color: n <= current ? C.ink : C.muted }}>
          {String(n).padStart(2, '0')}
        </span>
      ))}
    </nav>
  );
}

// ---------------------------------------------------------------- question widgets
function ChoiceCards({ name, options, value, onChange, labels, multi }: {
  name: string; options: string[]; value: any; onChange: (v: any) => void; labels: Record<string, string>; multi?: boolean;
}) {
  const sel: string[] = multi ? (Array.isArray(value) ? value : []) : value ? [value] : [];
  const min = options.length <= 2 ? 140 : 210;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: gridCols(min), gap: 10 }}>
      {options.map((o) => {
        const on = sel.includes(o);
        return (
          <label key={o} className="cp-choice" style={{ display: 'flex', alignItems: 'center', gap: 12, minHeight: 52, padding: '12px 14px', cursor: 'pointer',
            border: `1px solid ${C.ink}`, background: on ? C.panel : C.bg, color: C.ink, fontSize: 16, lineHeight: 1.35 }}>
            <input className="cp-sr" type={multi ? 'checkbox' : 'radio'} name={name} value={o} checked={on}
              onChange={() => onChange(multi ? (on ? sel.filter((x) => x !== o) : [...sel, o]) : o)} />
            <span aria-hidden="true" style={{ width: 22, height: 22, flex: '0 0 22px', border: `1px solid ${C.ink}`, borderRadius: multi ? 0 : 999,
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: on ? C.ink : C.bg, color: '#fff' }}>
              {on && <Check size={14} />}
            </span>
            <span>{labels[o] ?? o}</span>
          </label>
        );
      })}
    </div>
  );
}

function GroupedSelect({ id, value, onChange, groups, labels, t }: {
  id: string; value: any; onChange: (v: string) => void; groups: { group: string; codes: string[] }[]; labels: Record<string, string>; t: Dict;
}) {
  return (
    <select id={id} className="cp-input" value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
      <option value="" disabled>{t.ui.selectPlaceholder}</option>
      {groups.map((g) => (
        <optgroup key={g.group} label={t.groups[g.group]}>
          {g.codes.map((c) => <option key={c} value={c}>{labels[c] ?? c}</option>)}
        </optgroup>
      ))}
    </select>
  );
}

function QuestionField({ q, a, set, t, missing }: { q: QDef; a: Answers; set: (id: string, v: any) => void; t: Dict; missing: boolean }) {
  const def = t.q[q.id];
  const labelId = `lbl-${q.id}`;
  const label = (
    <span id={labelId} style={{ fontSize: 18, fontWeight: 600, color: C.ink, lineHeight: 1.35, letterSpacing: '-0.01em' }}>{def.label}</span>
  );
  const help = def.help ? <span style={{ fontSize: 15, color: C.muted, lineHeight: 1.5 }}>{def.help}</span> : null;
  const err = missing ? <span role="alert" style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.accent }}>{t.ui.chooseOne}</span> : null;
  const wrap: React.CSSProperties = { display: 'flex', flexDirection: 'column', gap: 10, padding: '22px 0', borderTop: `1px solid ${C.soft}` };

  if (q.type === 'cra' || q.type === 'mr') {
    return (
      <div style={wrap}>
        <label htmlFor={`f-${q.id}`} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>{label}{help}</label>
        <GroupedSelect id={`f-${q.id}`} value={a[q.id]} onChange={(v) => set(q.id, v)} t={t}
          groups={q.type === 'cra' ? CRA_GROUPS : MR_GROUPS} labels={q.type === 'cra' ? t.cra : t.mr} />
        {err}
      </div>
    );
  }
  if (q.type === 'number') {
    return (
      <div style={wrap}>
        <label htmlFor={`f-${q.id}`}>{label}</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, maxWidth: 220 }}>
          <input id={`f-${q.id}`} className="cp-input" type="number" inputMode="numeric" min={0} max={50}
            value={a[q.id] ?? ''} onChange={(e) => set(q.id, e.target.value)} />
          <span style={{ color: C.muted }}>{t.ui.years}</span>
        </div>
        {err}
      </div>
    );
  }
  const opts = q.type === 'practice' ? ['yes', 'partial', 'no', 'unknown'] : q.options!;
  const labels = q.type === 'practice' ? t.practice : (def.options ?? {});
  return (
    <fieldset style={{ ...wrap, border: 'none', margin: 0, padding: '22px 0', borderTop: `1px solid ${C.soft}` }} aria-labelledby={labelId}>
      <legend className="cp-sr">{def.label}</legend>
      {label}{help}
      {q.type === 'multi' && <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.muted }}>{t.ui.chooseMany}</span>}
      <ChoiceCards name={q.id} options={opts} value={a[q.id]} onChange={(v) => set(q.id, v)} labels={labels} multi={q.type === 'multi'} />
      {err}
    </fieldset>
  );
}

// ---------------------------------------------------------------- screens
function StartScreen({ t, onStart }: { t: Dict; onStart: () => void }) {
  return (
    <section className="cp-wrap" style={{ paddingTop: 'clamp(48px, 8vw, 104px)', paddingBottom: 'clamp(64px, 8vw, 96px)', display: 'flex', flexDirection: 'column', gap: 40 }}>
      <Progress current={1} t={t} />
      <div style={{ display: 'grid', gridTemplateColumns: gridCols(420), gap: 40, alignItems: 'end' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <Eyebrow>{t.start.eyebrow}</Eyebrow>
          <H1>{t.start.title}</H1>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <P>{t.start.intro}</P>
          <P>{t.start.intro2}</P>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {t.start.chips.map((c) => (
              <span key={c} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.ink, border: `1px solid ${C.soft}`, borderRadius: 999, padding: '6px 12px' }}>
                <Check size={14} />{c}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div style={{ background: C.panel, padding: 'clamp(20px, 3vw, 32px)' }}>
        <Card>
          <H3>{t.start.getTitle}</H3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gridTemplateColumns: gridCols(260), gap: 12 }}>
            {t.start.get.map((g) => (
              <li key={g} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', fontSize: 16, lineHeight: 1.5 }}>
                <span style={{ color: C.green, marginTop: 3 }}><Check /></span>{g}
              </li>
            ))}
          </ul>
        </Card>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 20, justifyContent: 'space-between', border: `1px solid ${C.ink}`, padding: 24 }}>
        <p style={{ margin: 0, fontSize: 15, color: C.muted, maxWidth: 640, lineHeight: 1.5 }}>{t.ui.notLegalAdvice}</p>
        <PrimaryButton onClick={onStart}>{t.start.cta}</PrimaryButton>
      </div>
    </section>
  );
}

function DescribeScreen({ t, product, setProduct, onBack, onNext }: {
  t: Dict; product: { name: string; description: string }; setProduct: (p: { name: string; description: string }) => void; onBack: () => void; onNext: () => void;
}) {
  return (
    <section className="cp-wrap" style={{ paddingTop: 'clamp(40px, 6vw, 80px)', paddingBottom: 'clamp(64px, 8vw, 96px)', display: 'flex', flexDirection: 'column', gap: 32, maxWidth: 1280 }}>
      <Progress current={2} t={t} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 820 }}>
        <Eyebrow>{fill(t.ui.step, { n: '02', total: '06' })} · {t.describe.eyebrow}</Eyebrow>
        <H1>{t.describe.title}</H1>
        <P>{t.describe.intro}</P>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 22, maxWidth: 820 }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <span style={{ fontSize: 18, fontWeight: 600, color: C.ink }}>{t.describe.nameLabel}</span>
          <input className="cp-input" value={product.name} maxLength={120} onChange={(e) => setProduct({ ...product, name: e.target.value })} />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <span style={{ fontSize: 18, fontWeight: 600, color: C.ink }}>{t.describe.descLabel}</span>
          <span style={{ fontSize: 15, color: C.muted }}>{t.describe.descHelp}</span>
          <textarea className="cp-input" rows={6} maxLength={3000} value={product.description}
            onChange={(e) => setProduct({ ...product, description: e.target.value })} style={{ resize: 'vertical', lineHeight: 1.5 }} />
        </label>
        <p style={{ margin: 0, fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.tag }}>{t.describe.uploadLater}</p>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between' }}>
        <OutlineButton back onClick={onBack}>{t.ui.back}</OutlineButton>
        <PrimaryButton onClick={onNext}>{t.ui.continue}</PrimaryButton>
      </div>
    </section>
  );
}

function QuestionsScreen({ t, answers, setAnswer, block, setBlock, onBack, onDone }: {
  t: Dict; answers: Answers; setAnswer: (id: string, v: any) => void; block: number; setBlock: (n: number) => void; onBack: () => void; onDone: () => void;
}) {
  const [showMissing, setShowMissing] = useState(false);
  const top = useRef<HTMLDivElement>(null);
  const b = BLOCKS[block];
  const qs = b.questions.filter((q) => visible(q, answers));
  const missing = qs.filter((q) => !q.optional && !answered(q, answers)).map((q) => q.id);

  useEffect(() => { setShowMissing(false); top.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, [block]);

  const next = () => {
    if (missing.length) { setShowMissing(true); document.getElementById(`lbl-${missing[0]}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }); return; }
    if (block < BLOCKS.length - 1) setBlock(block + 1); else onDone();
  };
  const back = () => (block > 0 ? setBlock(block - 1) : onBack());

  return (
    <section ref={top} className="cp-wrap" style={{ paddingTop: 'clamp(40px, 6vw, 80px)', paddingBottom: 'clamp(64px, 8vw, 96px)', display: 'flex', flexDirection: 'column', gap: 28 }}>
      <Progress current={3} t={t} />
      <div style={{ display: 'grid', gridTemplateColumns: gridCols(380), gap: 24, alignItems: 'end' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Eyebrow>{fill(t.ui.step, { n: '03', total: '06' })} · {b.key} / D</Eyebrow>
          <H1>{t.blocks[b.key].title}</H1>
        </div>
        <P>{t.blocks[b.key].intro}</P>
      </div>
      <div style={{ display: 'flex', gap: 6 }} aria-hidden="true">
        {BLOCKS.map((x, i) => <span key={x.key} style={{ flex: 1, height: 4, background: i <= block ? C.ink : C.soft }} />)}
      </div>
      <div style={{ maxWidth: 920, display: 'flex', flexDirection: 'column' }}>
        {qs.map((q) => <QuestionField key={q.id} q={q} a={answers} set={setAnswer} t={t} missing={showMissing && missing.includes(q.id)} />)}
      </div>
      {showMissing && missing.length > 0 && (
        <p role="alert" style={{ margin: 0, fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.accent }}>{t.ui.missing}</p>
      )}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between' }}>
        <OutlineButton back onClick={back}>{t.ui.back}</OutlineButton>
        <PrimaryButton onClick={next}>{t.ui.continue}</PrimaryButton>
      </div>
    </section>
  );
}

function PreviewScreen({ t, lang, result, loading, slow, error, product, onRetry, onEdit, onNext }: {
  t: Dict; lang: Lang; result: any; loading: boolean; slow: boolean; error: boolean; product: { name: string };
  onRetry: () => void; onEdit: () => void; onNext: () => void;
}) {
  const head = (
    <div style={{ display: 'grid', gridTemplateColumns: gridCols(380), gap: 24, alignItems: 'end' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <Eyebrow>{fill(t.ui.step, { n: '04', total: '06' })} · {t.preview.eyebrow}</Eyebrow>
        <H1>{t.preview.title}</H1>
      </div>
      <P>{t.preview.intro}</P>
    </div>
  );
  const shell = (body: React.ReactNode) => (
    <section className="cp-wrap" style={{ paddingTop: 'clamp(40px, 6vw, 80px)', paddingBottom: 'clamp(64px, 8vw, 96px)', display: 'flex', flexDirection: 'column', gap: 32 }}>
      <Progress current={4} t={t} />{head}{body}
    </section>
  );

  if (loading || (!result && !error)) {
    return shell(
      <Card>
        <p role="status" style={{ margin: 0, fontSize: 18, fontWeight: 600, color: C.ink }}>{t.ui.loading}</p>
        {slow && <P muted>{t.ui.coldStart}</P>}
      </Card>,
    );
  }
  if (error) {
    return shell(
      <Card>
        <p role="alert" style={{ margin: 0, fontSize: 18, fontWeight: 600, color: C.ink }}>{t.ui.apiError}</p>
        <div><OutlineButton onClick={onRetry}>{t.ui.retry}</OutlineButton></div>
      </Card>,
    );
  }

  const R = result.results;
  const o = t.outcome;
  const cites = (arr?: string[]) => (arr && arr.length ? <Cite>{t.preview.basis}: {arr.map((c) => cite(c, t)).join(' · ')}</Cite> : null);
  const procs = (arr?: string[]) => (
    <ul style={{ margin: 0, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 4 }}>
      {(arr ?? []).map((p) => <li key={p} style={{ fontSize: 16, lineHeight: 1.5 }}>{t.procedure[p] ?? p}</li>)}
    </ul>
  );
  const row = (label: string, content: React.ReactNode) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingTop: 14, borderTop: `1px solid ${C.soft}` }}>
      <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.muted }}>{label}</span>
      <div style={{ color: C.ink, fontSize: 16, lineHeight: 1.5 }}>{content}</div>
    </div>
  );

  // CRA card
  const r1 = R.R1;
  const craOn = r1.status === 'applies';
  const craCard = (
    <Card>
      <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.eyebrow }}>{t.preview.craTitle}</span>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10 }}>
        <H3>{o[`cra_${r1.status}`]}</H3>
        {!craOn && <Badge kind="green">{o[`cra_${r1.status}`]}</Badge>}
      </div>
      {!craOn && r1.reason && <P>{o[`reason_${r1.reason}`]}</P>}
      {craOn && r1.role !== 'manufacturer' && o[`role_${r1.role}`] && <P>{o[`role_${r1.role}`]}</P>}
      {craOn && (r1.notes ?? []).includes('hardware_with_data_connection') && <P muted>{o.hardware_note}</P>}
      {cites(r1.cites)}
      {craOn && R.R2.status === 'ok' && row(t.preview.classLabel, (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div><Badge kind={R.R2.class === 'default' ? 'tag' : 'ink'}>{o[`class_${R.R2.class}`]}</Badge></div>
          {R.R2.category && <span>{t.cra[R.R2.category]}</span>}
          {cites(R.R2.cites)}
        </div>
      ))}
      {craOn && R.R3.status === 'ok' && row(t.preview.procedureLabel, (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div><Badge kind={R.R3.notified_body === 'yes' ? 'ink' : 'green'}>{R.R3.notified_body === 'yes' ? t.preview.nbYes : t.preview.nbNo}</Badge></div>
          {procs(R.R3.procedures)}
          {R.R3.future_note && <P muted>{o.future_module_A}</P>}
          {cites(R.R3.cites)}
        </div>
      ))}
    </Card>
  );

  // Machinery Regulation card
  const r6 = R.R6; const r7 = R.R7; const r8 = R.R8;
  const mrOn = r6.status === 'applies';
  const mrCard = (
    <Card>
      <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, color: C.eyebrow }}>{t.preview.mrTitle}</span>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10 }}>
        <H3>{o[`mr_${r6.status}`]}</H3>
        {!mrOn && <Badge kind="green">{o.mr_not_applies}</Badge>}
      </div>
      {r6.modification && <P>{r6.modification === 'substantial' ? o.mr_substantial : o.mr_not_substantial}</P>}
      {cites(r6.cites)}
      {mrOn && r7.status === 'ok' && row(t.preview.annexLabel, (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <span>{r7.annex_i_part === 'A' ? o.mr_part_A : r7.annex_i_part === 'B' ? o.mr_part_B : t.preview.mrNotInAnnex}</span>
        </div>
      ))}
      {mrOn && r7.status === 'ok' && row(t.preview.procedureLabel, (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div><Badge kind={r7.notified_body === 'yes' ? 'ink' : 'green'}>{r7.notified_body === 'yes' ? t.preview.nbYes : t.preview.nbNo}</Badge></div>
          {procs(r7.procedures)}
          {cites(r7.cites)}
        </div>
      ))}
      {mrOn && r8.status === 'applies' && row('1.1.9 · 1.2.1', (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <span>{o.mr_cyber}</span>
          {r8.exposure === 'high' && <span>{o.mr_cyber_high}</span>}
          {cites(r8.cites)}
        </div>
      ))}
      {R.R9.mr_unit_note && <P muted>{o.mr_before_note}</P>}
    </Card>
  );

  // Deadlines
  const items: any[] = R.R9.items ?? [];
  const shown = [...items.filter((i) => i.in_force), ...items.filter((i) => !i.in_force)].slice(0, 3);
  const deadlines = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <H2>{t.preview.deadlinesTitle}</H2>
      {shown.length === 0 ? <P>{t.preview.noDeadlines}</P> : (
        <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column' }}>
          {shown.map((d) => (
            <li key={d.key} style={{ display: 'grid', gridTemplateColumns: gridCols(220), gap: 12, padding: '18px 0', borderTop: `1px solid ${C.ink}`, alignItems: 'start' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <span style={{ fontSize: 22, fontWeight: 600, color: C.ink, letterSpacing: '-0.015em' }}>{fmtDate(d.date, lang)}</span>
                <div><Badge kind={d.in_force ? 'ink' : 'blue'}>{d.in_force ? t.preview.inForce : t.preview.upcoming}</Badge></div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <span style={{ fontSize: 17, color: C.ink, lineHeight: 1.45 }}>{t.deadline[d.key]}</span>
                <Cite>{cite(d.cite, t)}</Cite>
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );

  return shell(
    <>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
        {product.name && <Badge kind="tag">{t.preview.product}: {product.name}</Badge>}
        <Cite>{fill(t.preview.rulesVersion, { date: fmtDate(result.rules_version, lang) })}</Cite>
      </div>
      <div style={{ background: C.panel, padding: 'clamp(16px, 3vw, 32px)', display: 'grid', gridTemplateColumns: gridCols(420), gap: 20 }}>
        {craCard}{mrCard}
      </div>
      {deadlines}
      <div style={{ display: 'grid', gridTemplateColumns: gridCols(360), gap: 24, border: `1px solid ${C.ink}`, padding: 24, alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <H3>{t.report.title}</H3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {t.report.items.map((i) => (
              <li key={i} style={{ display: 'flex', gap: 10, fontSize: 16, lineHeight: 1.45 }}><span style={{ color: C.green, marginTop: 2 }}><Check /></span>{i}</li>
            ))}
          </ul>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'flex-start' }}>
          <PrimaryButton onClick={onNext}>{t.ui.continue}</PrimaryButton>
          <OutlineButton back onClick={onEdit}>{t.ui.editAnswers}</OutlineButton>
        </div>
      </div>
      <p style={{ margin: 0, fontSize: 15, color: C.muted, lineHeight: 1.5 }}>{t.ui.notLegalAdvice}</p>
    </>,
  );
}

function ReportPlaceholder({ t, onBack }: { t: Dict; onBack: () => void }) {
  return (
    <section className="cp-wrap" style={{ paddingTop: 'clamp(40px, 6vw, 80px)', paddingBottom: 'clamp(64px, 8vw, 96px)', display: 'flex', flexDirection: 'column', gap: 28 }}>
      <Progress current={5} t={t} />
      <Card><P>{t.report.placeholder}</P></Card>
      <div><OutlineButton back onClick={onBack}>{t.ui.back}</OutlineButton></div>
    </section>
  );
}

// ---------------------------------------------------------------- app
type Screen = 'start' | 'describe' | 'questions' | 'preview' | 'report';

export default function App() {
  const [lang, setLang] = useState<Lang>(initialLang);
  const t = copy[lang];
  const [screen, setScreen] = useState<Screen>('start');
  const [block, setBlock] = useState(0);
  const [product, setProduct] = useState({ name: '', description: '' });
  const [answers, setAnswers] = useState<Answers>({ B5: [] });
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [slow, setSlow] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  // Wake the free-plan server while the user reads the first screens.
  useEffect(() => { fetch(`${API}/health`).catch(() => undefined); }, []);
  useEffect(() => { window.scrollTo({ top: 0 }); }, [screen]);

  const setAnswer = (id: string, v: any) => setAnswers((a) => ({ ...a, [id]: v }));

  const evaluate = async () => {
    setLoading(true); setError(false); setSlow(false); setResult(null);
    const slowTimer = window.setTimeout(() => setSlow(true), 4000);
    const ctrl = new AbortController();
    const killTimer = window.setTimeout(() => ctrl.abort(), 90000);
    try {
      const res = await fetch(`${API}/api/v1/evaluate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: payload(answers) }), signal: ctrl.signal,
      });
      if (!res.ok) throw new Error(String(res.status));
      setResult(await res.json());
    } catch {
      setError(true);
    } finally {
      window.clearTimeout(slowTimer); window.clearTimeout(killTimer); setLoading(false);
    }
  };

  const view = useMemo(() => {
    switch (screen) {
      case 'start':
        return <StartScreen t={t} onStart={() => setScreen('describe')} />;
      case 'describe':
        return <DescribeScreen t={t} product={product} setProduct={setProduct} onBack={() => setScreen('start')} onNext={() => { setBlock(0); setScreen('questions'); }} />;
      case 'questions':
        return <QuestionsScreen t={t} answers={answers} setAnswer={setAnswer} block={block} setBlock={setBlock}
          onBack={() => setScreen('describe')} onDone={() => { setScreen('preview'); evaluate(); }} />;
      case 'preview':
        return <PreviewScreen t={t} lang={lang} result={result} loading={loading} slow={slow} error={error} product={product}
          onRetry={evaluate} onEdit={() => { setBlock(0); setScreen('questions'); }} onNext={() => setScreen('report')} />;
      default:
        return <ReportPlaceholder t={t} onBack={() => setScreen('preview')} />;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screen, t, lang, product, answers, block, result, loading, slow, error]);

  return (
    <div className="cp-root">
      <style>{GLOBAL_CSS}</style>
      <Header lang={lang} setLang={setLang} t={t} />
      <main style={{ flex: 1 }}>{view}</main>
      <Footer t={t} />
    </div>
  );
}
