# Devpost "Additional info" answers — Dukaan Saathi

**Upload a file:** skip (optional).
**Submitter type:** Team · **Country:** India · **Canada province:** N/A · **Organization:** N/A
**New or existed before Oct 1, 2026:** New · **If existed before:** N/A

## Explain how your project meets the main technology requirement

PayPal (sandbox):
- PayPal Invoicing API v2: the AI collections agent turns each approved udhaar (credit) entry into a real invoice (POST /v2/invoicing/invoices + /send); the agent's Hinglish message becomes the invoice note. We also call /remind for open invoices, /payments to record cash paid at the counter, and GET status to sync payments back so the khata (ledger) clears automatically.
- PayPal Orders API v2 + PayPal JavaScript SDK: the reorder agent drafts a purchase order per supplier; the owner approves and pays with PayPal Buttons (create order → buyer approval → capture). Stock updates on capture.

AI:
- Google Gemini (gemini-3.5-flash-lite with minimal thinking for ~1–2 s Hindi/Hinglish voice-command parsing into items, quantities, customer and udhaar; gemini-3.6-flash for the collections agent, reorder reasoning, deadstock tips, market news and "ask your shop" Q&A over live shop data, with Google Search grounding when available). Model fallback chains keep the app working on 404/429/503, and an offline rule-based parser and planner take over when no key is set.
- Web Speech API (hi-IN / en-IN) for voice input on the phone.

## Additional sponsor tools
Select: AG Grid (desktop stock and khata tables, inline edits, low-stock/deadstock row highlighting). Also Render if it appears in the list (render.yaml blueprint for the free-tier deploy).

## Repository URL
https://github.com/kjenam/DukaanAI

## Working demo URL
Leave blank (the app runs locally in 5 minutes; no hosted copy). If you deploy with render.yaml before submitting, paste the onrender.com URL here instead.

## Testing instructions
Runs locally in 5 minutes (Python 3.10+, Chrome for voice): git clone https://github.com/kjenam/DukaanAI → python -m venv .venv → activate → pip install -r requirements.txt → copy .env.example .env → python app.py → open http://localhost:5000. It starts with no keys in offline mode (rule parser, rule collections planner, PayPal disabled) so the UI and data can be explored immediately.

For the full flow add to .env: GEMINI_API_KEY (free at aistudio.google.com/apikey) and your PayPal SANDBOX app's PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET (developer.paypal.com → Apps & Credentials → Sandbox). Sandbox buyer for paying invoices and approving supplier orders: sb-suh9453880126@personal.example.com / [PASSWORD] (US personal sandbox account; PayPal blocks India-to-India payments, so the buyer must be outside India). Set PAYPAL_DEMO_BUYER_EMAIL to that email.

4-minute walkthrough (also in README "For judges"): 1) Bill tab → click the chip "Sharma ji 2 kilo cheeni, 1 Fortune tel, udhaar" → Save bill. 2) Collect tab → Run collections agent → Approve & send on one card → a real PayPal invoice (INV2-…) is created → Pay link → log in as the buyer and pay → Khata → customer → Sync status → PAID. 3) Record cash payment on another open invoice. 4) Reorder tab → Check stock & draft orders → PayPal button → approve as the buyer → captured, stock increases (if nothing is low: Insights → Reset demo data). 5) On a laptop: Stock tab AG Grid inline edits, Insights chart, "Who owes me the most?", हिंदी toggle. All transactions are sandbox-only.

## PayPal experience rating
[Your call; we suggest 7.]

## Why / feedback
The Invoicing v2 API maps almost one-to-one onto how an informal khata works: create and send an invoice, remind, record a cash payment, read status. That made the collections agent straightforward, and the Orders v2 + JS SDK flow for supplier payments worked on the first try in sandbox. What cost us time: PayPal does not allow India-to-India invoices or payments, so as an Indian team we had to invoice in USD at a fixed rate and create a US sandbox buyer; invoice email delivery was sometimes refused in sandbox, so we fall back to the shareable pay link; and the remind endpoint only sends PayPal's standard email, so our AI-written message cannot ride on reminders. Clearer sandbox error messages for the country restriction and INR support would have saved us hours.

## Open to contact
[Your call; Yes recommended.]

## APIMatic Context Plugin
N/A, not used.

## AG Grid experience
We used AG Grid Community from the CDN for the desktop stock and khata tables: quick filter, sorting, inline editing of price/stock/alert level that writes straight to the API, and row classes for low-stock (red) and deadstock (amber). It took under an hour to set up with no build step, and it made the phone app feel like a real owner dashboard on a laptop. We'd like better documentation examples for plain-JS (non-framework) setups.

## Checkboxes
Tick all three eligibility boxes.

## AI tools leveraged while working on this project
Google Gemini API (in the product and for testing prompts), Claude Code (pair-programming, debugging, docs), ChatGPT/other if you used them [edit to match reality].

## Level of learning: Significant · AI value for career: Yes
