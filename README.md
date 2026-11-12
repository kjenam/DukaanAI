# दुकान साथी · Dukaan Saathi

**An AI assistant for village kirana shops, with PayPal for getting paid and paying suppliers.**
Built for the PayPal AI Hackathon 2026 by a team from a small village in Rajasthan, for our own family's grocery shop.

The shopkeeper speaks in Hindi or Hinglish ("Sharma ji 2 kilo cheeni, 1 Fortune tel, udhaar me likho").
The AI turns it into a bill, updates stock, and writes it in the khata (credit ledger). Udhaar is collected with
**PayPal invoices**. When stock runs low, an **AI agent drafts supplier orders and pays them with PayPal (Orders v2)
after the owner approves**.

## Features

| | Feature | AI | PayPal |
|---|---|---|---|
| 🧾 | Voice/text billing in Hindi, Hinglish, English (`hi-IN` / `en-IN` mic + text fallback) | Gemini parses the command into items, qty, customer, udhaar | |
| 📒 | Khata (udhaar) per customer, with full history | | **Invoicing v2**: send invoice, sync status, record cash payment |
| 📦 | Stock tracking, low-stock alerts | | |
| 🚚 | Agentic reorder: low stock + 14-day sales → draft order per supplier → owner approves | Agent drafts quantities | **Orders v2** + PayPal JS SDK buttons (create → approve → capture) |
| 🏷️ | Price updates by voice ("cheeni ab 46 rupaye kilo") with price history, plus market price check | Gemini + Google Search grounding | |
| 💤 | Deadstock: items unsold for 30+ days, with AI clearance ideas | Gemini | |
| 📰 | Daily market news summary (sugar, atta, oil, dal) | Gemini + Google Search grounding | |
| 💬 | Ask your shop: "Who owes the most?", "Top items by profit this week?" | Gemini over live shop data | |
| 🌐 | English / हिंदी UI toggle | | |

If no Gemini key is set, a built-in offline parser still handles common commands, so billing never stops.

## Run it locally (Windows)

```powershell
cd dukaan-saathi
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then open .env and paste your keys
python app.py
```
Open http://localhost:5000. Voice input works on `localhost` and HTTPS only, in Chrome (desktop or Android).
To test on your phone over Wi-Fi, use the deployed Render URL, since the mic needs HTTPS.

The app creates `dukaan.db` (SQLite) with ~40 realistic kirana items, 6 customers, 45 days of sales and udhaar.
**Insights → Reset demo data** restores it any time.

## Keys you need

1. **Gemini**: free key from https://aistudio.google.com/apikey → `GEMINI_API_KEY`.
2. **PayPal sandbox**: https://developer.paypal.com → Apps & Credentials → *Sandbox* → your app → copy
   Client ID and Secret → `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`.
3. **Sandbox accounts** (developer.paypal.com → Testing tools → Sandbox accounts):
   - a **Personal** account → put its email in `PAYPAL_DEMO_BUYER_EMAIL`. Invoices go to it, and you log in with it to approve supplier payments.
   - optional: a second **Business** account as the supplier → `SUPPLIER_PAYPAL_EMAIL`.

## Deploy on Render (free)

1. Push this folder to a GitHub repo (`.env` and `*.db` are git-ignored).
2. Render → New → **Blueprint** → pick the repo (it reads `render.yaml`), or New → Web Service with
   build `pip install -r requirements.txt` and start `gunicorn app:app --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT`.
3. Add the keys as environment variables. Open the `https://…onrender.com` URL on your phone.

Notes: the free tier sleeps after inactivity (first load takes ~30–50 s), and the SQLite file resets on every
redeploy. That's fine for the demo, since the seed data reloads automatically.

## Demo script (2–3 min)

1. **Problem (15 s)**: village shops run on paper khata, udhaar is never collected on time, and stock runs out.
2. **Voice bill (30 s)**: tap the mic and say *"Sharma ji do kilo cheeni, ek Fortune tel, udhaar me likho"*. Show the preview, then Save. The udhaar total goes up.
3. **Collect udhaar with PayPal (40 s)**: Khata → Sharma ji → **Send PayPal invoice**, open the pay link (sandbox buyer), pay, then **Sync status**. The balance clears. Also show **Record cash payment** for customers who pay cash.
4. **Agentic reorder (40 s)**: Stock shows Toor Dal very low → Reorder → **Check stock & draft orders**. The agent explains why it chose each quantity → **PayPal button** → approve as the shop → stock goes up.
5. **Insights (20 s)**: deadstock AI tips, market news, ask "sabse zyada udhaar kiska hai?", toggle Hindi UI.
6. **Close (10 s)**: built for our own shop, works in Hindi, and the owner approves every payment.

## Project layout

```
app.py          Flask routes (billing, khata, invoices, reorder, insights)
ai.py           Gemini calls (parse, chat, deadstock, news, market price) + offline parser
paypal.py       PayPal REST client: OAuth, Invoicing v2, Orders v2
db.py           SQLite schema + seed data
templates/      index.html (single page)
static/         app.js (UI, voice, PayPal buttons), style.css
TEAM_PLAN.md    who builds what, timeline to the deadline
```

## Honest limitations

- PayPal doesn't handle domestic payments between Indian users, so the khata stays in rupees and invoices/orders
  are in USD at a fixed rate (`INR_PER_USD`). The pitch: small shops collecting from customers or family abroad,
  and the same flow works for small shops in any PayPal market.
- In this demo, stock is marked as received as soon as the supplier payment is captured.
- Market prices and news are AI summaries with web search. They're labelled as estimates in the app.
