# Devpost submission text — Dukaan Saathi (दुकान साथी)

**Tagline:** An AI shop assistant for village kirana stores: talk to it in Hindi, let the agent collect your udhaar with PayPal.

## Inspiration

Our family runs a kirana (grocery) shop in a village in Rajasthan. Everything lives in a paper khata: who bought what on
udhaar (credit), what came in, what ran out. Three things go wrong every single month. Udhaar is never collected on
time because asking a neighbour for money is awkward. Stock of the fast movers runs out because nobody notices until a
customer asks. And at the end of the day nobody knows if the shop actually made money. Dukaan Saathi is the assistant
we wished our parents had: it speaks their language, it does the awkward part, and PayPal does the money.

## What it does

- **Voice billing in Hindi/Hinglish.** *"Sharma ji do kilo cheeni, ek Fortune tel, udhaar me likho"* becomes a bill,
  stock update and khata entry in about two seconds. An offline rule parser keeps billing alive without the network.
- **AI collections agent (वसूली).** The agent reads every open khata, ages the debt FIFO, and decides per customer:
  send a new PayPal invoice, remind on an open one, or wait (paid recently, nudged recently, too small). It writes a
  polite Hinglish or Hindi message and a one-line reason for the owner. Nothing goes out until the owner approves,
  one by one or all at once. Approval creates a real **PayPal invoice** (the AI message becomes the invoice note) or
  calls PayPal's **remind** endpoint, and produces a WhatsApp link that carries the message and the PayPal pay link.
  Payments sync back and clear the khata; cash payments are recorded on the PayPal invoice too.
- **Agentic reorder.** Low stock plus 14-day sales → a draft purchase order per supplier with the agent's reasoning →
  the owner edits quantities and pays the supplier through **PayPal Orders** (JS SDK buttons, create → approve → capture).
- **Owner dashboard.** On a laptop the same app becomes a dashboard: AG Grid stock table with inline edits and
  low-stock/deadstock highlighting, khata grid sorted by who owes most, a 14-day chart of sales, udhaar given and
  collected via PayPal, deadstock clearance tips, market news, and "ask your shop" in Hindi or English.
- **Phone-first.** Bottom tabs, big mic button, English/हिंदी toggle, works in Chrome on Android.

## How we built it

Python/Flask + SQLite on Render, vanilla JS front end with no build step. **Gemini** (3.5 Flash-Lite with minimal
thinking for billing commands, 3.6 Flash for the agents and insights) through the REST API with fallback model chains;
**PayPal Invoicing v2** (create, send, remind, record payment, status) and **PayPal Orders v2** (create/capture) through
a thin REST client; the **PayPal JS SDK** for the approval buttons; **AG Grid Community** and **Chart.js** from CDNs,
loaded only on desktop; the **Web Speech API** for Hindi voice input. Seed data models 45 days of a real kirana shop.

## Challenges we ran into

- **Latency.** The first version waited 7–10 s per voice command. Switching the parser to Flash-Lite with thinking
  turned off, slimming the catalog prompt and keeping HTTP connections alive brought it to 1–2 s, with model fallbacks
  on 404/429/503 so a bad minute at the API never blocks billing.
- **PayPal in India.** PayPal does not allow India-to-India invoices or payments. We issue invoices as shareable links
  when email delivery is refused, keep the khata in rupees and invoice in USD at a fixed rate, and test with a US sandbox
  buyer. The honest pitch is customers and relatives abroad, and the identical flow for small shops in any PayPal market.
- **Keeping the human in charge.** Agents that send money messages to your neighbours need a brake. Every action is a
  proposal with a reason and an editable message; the policy (wait after a payment, no double nudges) lives both in the
  prompt and in a rule engine that validates whatever the model returns.

## Accomplishments we're proud of

A shopkeeper can run a day of billing by voice, see exactly who owes what, let an agent do the uncomfortable
collections conversation politely, and pay suppliers, all with real PayPal sandbox transactions end to end. And it
still works, more simply, when the AI is offline.

## What we learned

Model choice and thinking budget matter more than prompt cleverness for an interactive tool. PayPal's Invoicing API is
a surprisingly good fit for informal credit: invoices, reminders and recorded cash payments map one-to-one onto how a
khata already works.

## What's next

PayPal webhooks instead of manual sync, itemized invoice lines per bill, UPI as the domestic rail beside PayPal for
cross-border, supplier onboarding so purchase orders go to real distributors, and a weekly voice summary for the owner.

## Built with

Python, Flask, SQLite, Gemini API, PayPal Invoicing API v2, PayPal Orders API v2, PayPal JavaScript SDK, AG Grid
Community, Chart.js, Web Speech API, Render.

## Testing instructions for judges

Live URL: `<render url>` (free tier: first load may take 30–50 s). Sandbox buyer for paying invoices and approving
supplier orders: `sb-suh9453880126@personal.example.com` / `<password>`. Full 4-minute walkthrough is in the README
under "For judges".
