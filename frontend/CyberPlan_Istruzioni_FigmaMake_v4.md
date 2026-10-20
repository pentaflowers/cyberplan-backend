# CyberPlan — instructions for the Figma Make bot (v4)

Two code files are attached to this message. They replace the earlier versions.

- `CyberPlan_App_v4.tsx` — the whole app, screens 1–6 (start, product, questionnaire with AI suggestions, preview, contact form and PDF report, closing)
- `CyberPlan_i18n_v3.ts` — all texts in English and Italian

## What to do

1. Replace the **entire content** of `src/App.tsx` with the content of `CyberPlan_App_v4.tsx`, exactly as it is.
2. Replace the **entire content** of `src/i18n.ts` with the content of `CyberPlan_i18n_v3.ts`, exactly as it is.

## What not to do

- Do not change any logic, text, colour, spacing, link or the API address (`https://cyberplan-api.onrender.com`).
- Do not add libraries, mock data or example content.
- Do not pre-tick the consent checkboxes.

## Check after the change

- After the preview, "Continue" opens the form "Get your full report" with six fields and two unticked consents.
- Without the first consent the report cannot be requested.
- After a request, the PDF downloads and the closing page shows "Your report is ready", the "Book a diagnosis" button and the ElectroPlan card.
