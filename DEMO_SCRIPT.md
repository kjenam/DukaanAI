# Demo video script (3 minutes) — for the person recording

Record on the **live Render URL**. Two windows: a desktop browser at full width, and a phone (or Chrome device
mode at 390 px) for the voice bill. Log in to **sandbox.paypal.com** as the US sandbox buyer in a second tab
*before* recording so the pay steps are one click. Press **Insights → Reset demo data** first so low stock and
udhaar look realistic.

| Time | Screen | Say | Do |
|---|---|---|---|
| 0:00–0:15 | Title / phone | "Village kirana shops run on a paper khata. Udhaar is never collected on time, stock runs out, and the owner hates asking neighbours for money. Dukaan Saathi is an AI shop assistant with PayPal built in." | Show the phone home screen. |
| 0:15–0:45 | Phone · Bill | "The owner just talks to it, in Hindi." | Tap mic, say **"Sharma ji do kilo cheeni, ek Fortune tel, udhaar me likho"**. Preview appears in ~2 s (point at "Understood by Gemini AI · 1.8 s"). Tap **Save bill**. Udhaar stat goes up. |
| 0:45–1:10 | Desktop · Stock + Khata | "On a laptop it becomes the owner's dashboard: live stock in an AG Grid with low-stock and deadstock highlighted, inline edits, and the whole khata sorted by who owes most." | Open **Stock**, double-click a price and change it. Open **Khata**, click a customer. |
| 1:10–2:00 | Desktop · Collect | "This is the part owners dread, so we gave it to an agent. It reads every open khata, decides who to nudge today and who to leave alone, and writes a polite Hinglish message. Nothing is sent until the owner approves." | Click **Run collections agent**. Read one reason aloud ("paid 3 days ago, wait"). Edit one message. Click **Approve & send** → "PayPal invoice issued". Click **Pay link** → pay as the sandbox buyer → back in Khata click **Sync status** → PAID, balance 0. Show the **WhatsApp** button (opens the message with the pay link). |
| 2:00–2:35 | Desktop · Reorder | "Stock is the other half. The reorder agent looks at low stock and 14-day sales, drafts a purchase order per supplier and explains the quantities. The owner approves and pays the supplier with PayPal." | **Check stock & draft orders** → PayPal button → approve as sandbox buyer → capture → stock rises. |
| 2:35–2:55 | Desktop · Insights | "Everything ends up in one view: sales, udhaar given, collected via PayPal, and you can just ask the shop a question." | Show chart, click **Who owes me the most?**, toggle हिंदी. |
| 2:55–3:00 | Close | "Built for our own family shop in Rajasthan. Gemini for the thinking, PayPal Invoicing and Orders for the money, and the owner stays in control of every rupee." | End card: repo URL + live URL. |

## If something goes wrong while recording
- **Gemini slow or 429**: the offline parser still bills; say "even offline it understands the basics". Retry the agent once.
- **PayPal invoice says "issued as a link"**: that is the India restriction fallback; the pay link still works.
- **Reorder shows nothing low**: Insights → Reset demo data (Toor Dal and Mustard Oil are seeded low).
- **Render cold start**: open the URL 2 minutes before recording.
