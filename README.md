# दुकान साथी · Dukaan Saathi

**An AI shop assistant for village kirana stores, with PayPal doing the money.**
Built for the PayPal AI Hackathon 2026 by a team from a small village in Rajasthan, for our own family's grocery shop.

The shopkeeper talks in Hindi or Hinglish: *"Sharma ji do kilo cheeni, ek Fortune tel, udhaar me likho."*
Gemini turns it into a bill, updates stock and writes it in the khata (credit ledger). The interface itself is in English. An **AI collections agent**
decides who to nudge for udhaar, writes a polite message, and uses **PayPal Invoicing** to collect. When stock runs
low, a **reorder agent** drafts supplier orders that the owner pays with **PayPal Orders**. The owner approves every
rupee that moves.

> Demo video: `<youtube link>` · Devpost: `<link>` · **Run it locally in 5 minutes** (below). There is no hosted
> instance; the app runs on your machine against the free PayPal sandbox and a free Gemini key.
> **It also starts with no keys at all**: billing uses the built-in offline parser, the collections agent uses its
> rule planner, and PayPal buttons show a "add keys" note, so you can explore the whole UI immediately.

## What it does

| | Feature | AI | PayPal |
|---|---|---|---|
| 🧾 | **Voice/text billing** in Hindi, Hinglish, English (Web Speech API + text) | Gemini 3.5 Flash-Lite parses items, quantities, customer, udhaar in ~1–2 s; offline rule parser as fallback | |
| 📒 | **Khata** (udhaar ledger) per customer with history | | **Invoicing v2**: create + send invoice, sync status, record cash payment |
| 🤝 | **AI collections agent**: reads every open khata, FIFO-ages the debt, decides *invoice / remind / wait*, writes a polite message, owner approves one by one or all at once | Gemini plans + writes; rule planner fallback | **Invoicing v2** send (AI message goes on the invoice) and **remind**; WhatsApp link carries the message + PayPal pay link |
| 🚚 | **Agentic reorder**: low stock + 14-day sales → draft PO per supplier with reasons → owner edits, approves | Agent drafts quantities | **Orders v2** via PayPal JS SDK buttons (create → approve → capture) |
| 📦 | **Stock dashboard** (desktop): AG Grid with inline price/stock/alert edits, low-stock and deadstock highlighting, quick filter | Deadstock clearance tips, market price check | |
| 📊 | **Insights**: 14-day sales / udhaar / collected chart, "ask your shop" chat, market news | Gemini over live shop data (+ Google Search grounding when available) | |
| 🏠 | Landing page with today's attention items, phone-first bottom tabs, desktop sidebar dashboard | | |

## Architecture

```
Browser (phone or desktop)                Flask (app.py)                      External
┌──────────────────────────┐   JSON    ┌───────────────────────┐   REST   ┌──────────────────────┐
│ app.js: voice, tabs,     │ ───────▶ │ /api/parse, /api/bills │ ───────▶ │ Gemini generateContent│
│ previews, modals         │          │ /api/collections/*     │          │  (fast chain: 3.5     │
│ grid.js: AG Grid         │          │ /api/po/*, /api/state  │          │   flash-lite, minimal │
│ Chart.js, PayPal JS SDK  │ ◀─────── │ ai.py · vasooli.py     │ ◀─────── │   thinking)           │
└──────────────────────────┘          │ paypal.py · db.py      │          ├──────────────────────┤
          │ PayPal buttons / pay link  │ SQLite (dukaan.db)     │ ───────▶ │ PayPal sandbox:       │
          └───────────────────────────▶└───────────────────────┘          │ Invoicing v2, Orders v2│
                                                                          └──────────────────────┘
```

- `app.py` routes · `ai.py` Gemini client with model fallback chains and offline parsers · `vasooli.py` collections agent
  (FIFO overdue analysis, policy, message templates, AI plan validation) · `paypal.py` thin REST client (OAuth, Invoicing v2
  incl. remind, Orders v2) · `db.py` schema + realistic seed data (40 items, 6 customers, 45 days of bills and udhaar).
- No build step: vanilla JS, AG Grid Community and Chart.js from CDNs, loaded only when needed.

## Run it locally (5 minutes)

Requirements: Python 3.10+ (tested on 3.12 and 3.14), Chrome for voice input. Works on Windows, macOS and Linux.

```powershell
git clone <repo-url> dukaan-saathi
cd dukaan-saathi
python -m venv .venv
.venv\Scripts\activate                                  # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                                  # macOS/Linux: cp .env.example .env   (then paste keys, optional)
python app.py
```
Open **http://localhost:5000**. The first start creates `dukaan.db` with ~40 kirana items, 6 customers and 45 days of
bills and udhaar. **Insights → Reset demo data** restores that seed any time. Voice input works in Chrome on `localhost`.

### Keys (all free; the app runs without them, with AI and PayPal features in offline mode)
1. **Gemini**: https://aistudio.google.com/apikey → `GEMINI_API_KEY` in `.env`. Enables the Hindi/Hinglish voice parser,
   the collections agent's reasoning and messages, deadstock tips, market news and "ask your shop".
2. **PayPal sandbox**: https://developer.paypal.com → Apps & Credentials → **Sandbox** → Create app → copy **Client ID**
   and **Secret** → `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`. Enables invoices, reminders, record-cash and supplier
   payments. All transactions are sandbox-only; no real money moves.
3. **Sandbox buyer** (to pay invoices and approve supplier orders): developer.paypal.com → Testing Tools → Sandbox
   Accounts → **Create account** → Personal, **Country = United States** → its email goes in `PAYPAL_DEMO_BUYER_EMAIL`,
   and you log in to sandbox.paypal.com with it when a pay page opens. PayPal does not allow India-to-India invoices or
   payments, so the buyer must be outside India; if email delivery is refused the app still issues a pay *link*.

Optional: `render.yaml` deploys the same app on Render's free tier (Blueprint) if you want a hosted copy.

## For judges: test it in 4 minutes

With the three keys above in `.env` (the Devpost testing instructions also include a ready-made US sandbox buyer login).

1. **Bill by voice or text** (Bill tab): click the chip *"Sharma ji 2 kilo cheeni, 1 Fortune tel, udhaar"* → preview in ~2 s
   (shows which model understood it and how fast) → **Save bill**. Udhaar outstanding goes up.
2. **Collections agent** (Collect tab): **Run collections agent** → one card per debtor with priority, reason and an
   editable message → **Approve & send** on one → a real PayPal invoice is issued (`INV2-…`) with the AI message as the
   invoice note. Click **Pay link**, log in as the sandbox buyer, pay. Back in **Khata → customer → Sync status** → PAID,
   balance clears. **WhatsApp** opens the message + pay link ready to send.
3. **Cash still works**: on another open invoice click **Record cash payment** → PayPal marks it paid, khata clears.
4. **Reorder** (Reorder tab): **Check stock & draft orders** → agent explains each quantity → PayPal button → approve as
   the buyer → captured, stock increases. (If nothing is low, Insights → Reset demo data.)
5. **Dashboard** (desktop width): Stock tab AG Grid: double-click a price to edit; red rows are low stock, amber are
   deadstock. Insights: 14-day chart, ask *"Who owes me the most?"*.

## Honest limitations

- PayPal does not process domestic payments between Indian accounts, so the khata stays in rupees while invoices and
  orders are issued in USD at a fixed rate (`INR_PER_USD`). The pitch: collecting from customers or relatives abroad, and
  the same flow works unchanged for small shops in any PayPal market.
- PayPal's `remind` endpoint sends PayPal's standard reminder email; the AI message is shown on new invoices and in the
  WhatsApp link, not inside the reminder email.
- Stock is marked received as soon as the supplier payment is captured (demo simplification).
- Market news and prices are AI summaries, labelled as estimates; web grounding is skipped when the key has no quota.

## Project layout

```
app.py          Flask routes: billing, khata, invoices, collections agent, reorder, insights
ai.py           Gemini client (fallback chains, minimal thinking) + prompts + offline parsers
vasooli.py      Collections agent: FIFO overdue analysis, policy, templates, AI-plan validation
paypal.py       PayPal REST: OAuth, Invoicing v2 (send/remind/payments), Orders v2 (create/capture)
db.py           SQLite schema + seed data
templates/      index.html (single page, phone + desktop layouts)
static/         app.js (UI), grid.js (AG Grid), style.css (PayPal-inspired theme)
DEMO_SCRIPT.md  3-minute video script · DEVPOST.md submission text · TEAM_PLAN.md
```
