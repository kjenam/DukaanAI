# Team plan: deadline 13 Nov 1:30 AM IST (12 Nov 3:00 PM EST)

**Target: submit on Devpost by 11:00 PM IST on 12 Nov.** Code freeze 10:00 PM IST.

## Status (12 Nov evening)

Done and tested in sandbox: fast Gemini parse (1–2 s), invoice send → pay → sync (PAID), record cash (MARKED_AS_PAID),
reorder create → approve → capture (stock up), AI collections agent (plan → approve → PayPal invoice/remind → WhatsApp
link), new responsive UI (phone tabs + desktop AG Grid dashboard + chart), README, DEVPOST.md, DEMO_SCRIPT.md.

## Who does what tonight

| Person A (owner of the repo) | Person B |
|---|---|
| Push `DukaanAi` to a public GitHub repo, deploy on Render via Blueprint, add env vars (Gemini key, PayPal client id/secret, `PAYPAL_DEMO_BUYER_EMAIL` = the US sandbox buyer) | Read `DEMO_SCRIPT.md`; log in to sandbox.paypal.com as the US buyer in a second tab; warm up the Render URL |
| On the live URL: Insights → Reset demo data, run the 5 judge steps from the README once | Record the 3-minute video on the live URL (desktop + phone/device mode), upload to YouTube (unlisted is fine) |
| Fill the Devpost form from `DEVPOST.md`: description, tools, repo link, live URL, video link, testing instructions with the sandbox buyer email + password | Send the video link to A by 10:30 PM |
| Final check: repo public, no `.env` committed, README links filled in | Watch the submission confirmation arrive |

## Submission checklist

- [ ] Live Render URL works on a phone and a laptop (warm it up before judging)
- [ ] GitHub repo public, README up to date, **no `.env` committed** (`git ls-files | grep .env` shows only `.env.example`)
- [ ] Video ≤ 3 min shows: voice bill → collections agent → PayPal invoice paid → reorder paid with PayPal → dashboard
- [ ] Devpost "Built with": Python, Flask, SQLite, Gemini API, PayPal Invoicing API, PayPal Orders API, PayPal JS SDK, AG Grid, Chart.js, Web Speech API, Render
- [ ] Testing instructions include the sandbox buyer email/password
- [ ] Both team members added on Devpost
