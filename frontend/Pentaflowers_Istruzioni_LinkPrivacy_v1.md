# Pentaflowers site — give the legal pages their own address (v1)

The CyberPlan and ElectroPlan mini apps must link directly to the Pentaflowers privacy notice and legal notice. Today these pages open from the footer, but the browser address stays `www.pentaflowers.com`, so there is no link to them.

## What to do

1. Give each legal page a hash address:
   - privacy notice (the "Informazioni legali" page, titled "Accordo di riservatezza e dati" in Italian) → `#privacy`
   - legal notice / imprint, if it is a separate page → `#legal`
2. When the site is opened with one of these addresses (for example `https://www.pentaflowers.com/#privacy`), show that page directly, scrolled to the top.
3. When a visitor opens the page from the footer, update the browser address to the same hash, so the link can be copied and shared.
4. The browser Back button must return to the previous page of the site.
5. A language can be passed too: `#privacy?lang=it` opens the page in Italian (same for en, fr, es, de). Without it, keep the current behaviour.

## What not to do

- Do not change the content, design, texts or translations of any page.
- Do not change other navigation, forms, login or API calls.
- Use hash addresses (`/#privacy`), not paths (`/privacy`): paths can return "page not found" on the hosting.

## Check after the change

- Opening `https://www.pentaflowers.com/#privacy` in a new tab shows the privacy page directly.
- Opening `https://www.pentaflowers.com/#legal` shows the legal notice (if it is a separate page).
- Clicking the footer links updates the address, and Back works.
