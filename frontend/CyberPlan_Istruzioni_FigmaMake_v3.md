# CyberPlan — instructions for the Figma Make bot (v3)

Two code files are attached to this message. They replace the earlier versions.

- `CyberPlan_App_v3.tsx` — the whole app (screens 1–4, with AI suggestions for the main function)
- `CyberPlan_i18n_v2.ts` — all texts in English and Italian

## What to do

1. Replace the **entire content** of `src/App.tsx` with the content of `CyberPlan_App_v3.tsx`, exactly as it is.
2. Replace the **entire content** of `src/i18n.ts` with the content of `CyberPlan_i18n_v2.ts`, exactly as it is.

## What not to do

- Do not change any logic, text, colour, spacing or the API address (`https://cyberplan-api.onrender.com`).
- Do not add libraries, mock data or example content.
- Leave the bracketed placeholder (`[Contact form and PDF report: next release step]`) as it is.

## Check after the change

- In block B, under "What is the main function of the product?", a grey box shows the button "Suggest categories from my description" (or the Italian version).
- If the product description in step 2 is shorter than 20 characters, the box asks to add a description instead.
