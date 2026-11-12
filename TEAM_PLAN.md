# Team plan: 2 people, deadline 13 Nov 1:30 AM IST (12 Nov 12:00 PM PT)

**Aim to submit by 11:00 PM IST on 12 Nov.** Devpost gets slow near the deadline.

## Who owns what

| | Person A: AI + data | Person B: PayPal + UI + deploy |
|---|---|---|
| Files | `ai.py`, `db.py`, `app.py` (billing, khata, insights routes) | `paypal.py`, `static/app.js`, `templates/index.html`, `render.yaml`, `app.py` (invoice/PO routes) |
| Keys | Gemini key | PayPal sandbox app + 2–3 sandbox accounts |
| Tasks | Test 20+ real voice commands in Hindi/Hinglish, fix the prompt in `PARSE_PROMPT` for misses · replace seed items/prices with your real shop's · check deadstock/news output · write the Devpost text | Invoice: send → pay as sandbox buyer → Sync → khata clears · Record cash · Reorder: approve → capture → stock up · GitHub + Render deploy · test the mic on a phone · record the demo video |

The API contract between you is already fixed in `app.py` (`/api/...` routes return JSON). Avoid editing the same file at the same time.
If you must, tell each other first, or use separate Git branches.

## Timeline (IST)

| When | Person A | Person B |
|---|---|---|
| **Tonight, till ~1:00 AM** | Run locally, add Gemini key, try the 6 example chips + 10 own commands | Run locally, add PayPal keys, send 1 invoice and pay it in sandbox, approve 1 reorder |
| 12 Nov 9:00–12:00 | Fix parse misses · real item list & prices | Push to GitHub · deploy on Render · open on phone, test mic over HTTPS |
| 12:00–16:00 | Polish Hindi UI text, deadstock/news prompts | Fix any PayPal edge cases · make the demo flow smooth (pre-login sandbox buyer) |
| 16:00–19:00 | Write Devpost: Inspiration, What it does, How we built it, Challenges, What's next | Record the 2–3 min video (script in README), upload to YouTube (unlisted is fine) |
| 19:00–21:00 | Both: fresh **Reset demo data** on the live URL, full run-through as a judge would | |
| **By 23:00** | **Submit on Devpost**: live URL, GitHub repo, video link, test instructions (sandbox buyer login for judges) | |

## Submission checklist

- [ ] Live Render URL works on a phone (first load may be slow, so warm it up before judging)
- [ ] GitHub repo public, README up to date, **no `.env` committed**
- [ ] Demo video ≤ 3 min shows: voice bill → PayPal invoice paid → agent reorder paid with PayPal
- [ ] Devpost "Built with": Python, Flask, SQLite, Gemini API, PayPal Invoicing API, PayPal Orders API, PayPal JS SDK, Web Speech API, Render
- [ ] Testing instructions for judges include a sandbox buyer email/password to approve payments
- [ ] Check the rules page for anything else required (video length, team members added on Devpost)
