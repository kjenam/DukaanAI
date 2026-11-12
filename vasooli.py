"""AI collections agent (vasooli = recovery of dues): decides who to nudge for udhaar and how, the owner approves.

Pure helpers over a sqlite connection; Flask routes live in app.py.
"""
import re
from datetime import datetime
from urllib.parse import quote

import db

OPEN_INVOICE_STATES_EXCLUDED = ("PAID", "MARKED_AS_PAID", "CANCELLED")
MIN_BALANCE = 100          # smaller balances are not worth a nudge
PAID_RECENTLY_DAYS = 7     # leave people alone for a week after they pay something
REMINDED_RECENTLY_DAYS = 3


def _days(iso, now):
    if not iso:
        return None
    return max((now - datetime.fromisoformat(iso)).days, 0)


def customer_rows(conn, now=None):
    """One row per customer with an outstanding balance, with the signals the agent reasons over."""
    now = now or db.now()
    out = []
    for c in db.rows(conn, "SELECT * FROM customers ORDER BY name"):
        entries = db.rows(conn, "SELECT kind, amount, created_at FROM khata_entries WHERE customer_id=? ORDER BY created_at, id", (c["id"],))
        # FIFO: payments settle the oldest credits first; the oldest credit left open sets "days overdue"
        open_credits = []
        last_payment = None
        for e in entries:
            if e["kind"] == "credit":
                open_credits.append([e["amount"], e["created_at"]])
            else:
                last_payment = e["created_at"]
                left = e["amount"]
                while left > 0 and open_credits:
                    take = min(left, open_credits[0][0])
                    open_credits[0][0] -= take
                    left -= take
                    if open_credits[0][0] <= 0.005:
                        open_credits.pop(0)
        balance = round(sum(a for a, _ in open_credits), 2)
        if balance <= 0.5:
            continue
        inv = db.one(conn, "SELECT * FROM invoices WHERE customer_id=? AND status NOT IN (?,?,?) ORDER BY id DESC LIMIT 1",
                     (c["id"], *OPEN_INVOICE_STATES_EXCLUDED))
        last_nudge = db.one(conn, """SELECT MAX(sent_at) AS at, SUM(action='remind') AS reminders FROM collection_actions
                                     WHERE customer_id=? AND status='sent'""", (c["id"],))
        out.append({
            "customer_id": c["id"], "name": c["name"], "phone": c["phone"] or "", "email": c["email"] or "",
            "balance": balance,
            "days_overdue": _days(open_credits[0][1], now) if open_credits else 0,
            "days_since_payment": _days(last_payment, now),
            "open_invoice": inv,
            "invoice_age_days": _days(inv["created_at"], now) if inv else None,
            "reminders_sent": int(last_nudge["reminders"] or 0) if last_nudge else 0,
            "days_since_nudge": _days(last_nudge["at"], now) if last_nudge and last_nudge["at"] else None,
        })
    out.sort(key=lambda r: (-r["days_overdue"], -r["balance"]))
    return out


def rule_plan(rows, lang="en", shop_name="the shop"):
    """Offline planner with the same policy the AI prompt describes, so the feature works without a key."""
    plan = []
    for r in rows:
        action, reason = "invoice", ""
        if r["balance"] < MIN_BALANCE:
            action, reason = "wait", f"Balance ₹{r['balance']:.0f} is small; not worth a nudge yet."
        elif r["days_since_payment"] is not None and r["days_since_payment"] < PAID_RECENTLY_DAYS:
            action, reason = "wait", f"Paid something {r['days_since_payment']} days ago; give them a week."
        elif r["days_since_nudge"] is not None and r["days_since_nudge"] < REMINDED_RECENTLY_DAYS:
            action, reason = "wait", f"Already nudged {r['days_since_nudge']} days ago."
        elif r["open_invoice"]:
            action, reason = "remind", f"PayPal invoice open for {r['invoice_age_days']} days; send a reminder."
        else:
            reason = f"₹{r['balance']:.0f} outstanding for {r['days_overdue']} days; no invoice yet."
        priority = 1 if r["days_overdue"] >= 30 or r["balance"] >= 3000 else (2 if r["days_overdue"] >= 14 else 3)
        plan.append({"customer_id": r["customer_id"], "action": action, "priority": priority, "reason": reason,
                     "message": template_message(r, lang, shop_name) if action != "wait" else ""})
    return plan


def template_message(r, lang, shop_name):
    first = r["name"].split()[0]
    amt = f"₹{r['balance']:,.0f}"
    if lang == "hi":
        return (f"Namaste {first} ji, {shop_name} se. Aapka khata balance {amt} hai ({r['days_overdue']} din se). "
                f"Neeche diye PayPal link se jab suvidha ho bhugtaan kar dijiye. Dhanyavaad 🙏")
    return (f"Hello {first} ji, this is {shop_name}. Your khata balance is {amt}, pending for {r['days_overdue']} days. "
            f"You can pay whenever convenient using the PayPal link below. Thank you 🙏")


def wa_link(phone, message, pay_url=None):
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        digits = "91" + digits
    text = message + (("\n" + pay_url) if pay_url else "")
    return f"https://wa.me/{digits}?text={quote(text)}" if digits else f"https://wa.me/?text={quote(text)}"


def merge_ai_plan(rows, ai_plan, lang, shop_name):
    """Validate the AI's JSON against known customers; fall back per customer to the rule plan."""
    rules = {p["customer_id"]: p for p in rule_plan(rows, lang, shop_name)}
    by_id = {r["customer_id"]: r for r in rows}
    seen, merged = set(), []
    for p in ai_plan or []:
        try:
            cid = int(p.get("customer_id"))
        except (TypeError, ValueError):
            continue
        if cid not in by_id or cid in seen:
            continue
        seen.add(cid)
        r, base = by_id[cid], rules[cid]
        action = p.get("action") if p.get("action") in ("invoice", "remind", "wait") else base["action"]
        # the AI may not "remind" without an open invoice, nor "invoice" when one is already open
        if action == "remind" and not r["open_invoice"]:
            action = "invoice"
        if action == "invoice" and r["open_invoice"]:
            action = "remind"
        try:
            priority = min(max(int(p.get("priority", base["priority"])), 1), 3)
        except (TypeError, ValueError):
            priority = base["priority"]
        message = "" if action == "wait" else ((p.get("message") or "").strip() or template_message(r, lang, shop_name))
        merged.append({"customer_id": cid, "action": action, "priority": priority,
                       "reason": (p.get("reason") or base["reason"]).strip()[:300], "message": message[:600]})
    for cid, base in rules.items():
        if cid not in seen:
            merged.append(base)
    merged.sort(key=lambda p: (p["priority"], -by_id[p["customer_id"]]["balance"]))
    return merged
