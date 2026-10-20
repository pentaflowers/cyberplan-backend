# CyberPlan — instructions for the Figma Make bot (v2)

Two code files are attached to this message:

- `CyberPlan_App_v2.tsx` — the whole app (screens 1–4); it replaces any earlier CyberPlan_App version
- `CyberPlan_i18n_v1.ts` — all texts in English and Italian

## What to do

1. Replace the **entire content** of `src/App.tsx` with the content of `CyberPlan_App_v2.tsx`, exactly as it is.
2. Create the file `src/i18n.ts` with the content of `CyberPlan_i18n_v1.ts`, exactly as it is. The app imports it as `./i18n`.
3. Make sure `App` is the only thing rendered on the page: no other template component, header or footer around it.
4. If the template's `index.css` sets a dark page background, a font other than Space Grotesk, or global colours on `body`, remove those rules. Keep the Tailwind import if there is one. The app loads its own fonts (Space Grotesk and Space Mono from Google Fonts).

## What not to do

- Do not change any logic, text, colour, spacing or the API address (`https://cyberplan-api.onrender.com`).
- Do not add libraries, mock data or example content.
- Do not translate or rewrite texts: they all live in `src/i18n.ts`.
- Leave the bracketed placeholder (`[Contact form and PDF report: next release step]`) as it is.

## Check after the change

- The page opens on "Which cybersecurity rules apply to your product?" (or the Italian version, depending on the browser language), with a dark header and footer and a white page.
- The EN / IT switch in the header changes all texts.
- At 390 px width there is no horizontal scroll.
- Going through the questionnaire, the preview shows results. The first time it can take up to a minute, because the server wakes up from sleep.
