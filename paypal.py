"""Thin PayPal REST client (sandbox by default): Invoicing v2 + Orders v2."""
import os
import time
import uuid
from datetime import date

import requests

TIMEOUT = 30
_token = {"value": None, "expires": 0}
_session = requests.Session()   # keep-alive across PayPal calls


class PayPalError(Exception):
    pass


def base_url():
    env = os.environ.get("PAYPAL_ENV", "sandbox").lower()
    return "https://api-m.paypal.com" if env == "live" else "https://api-m.sandbox.paypal.com"


def configured():
    return bool(os.environ.get("PAYPAL_CLIENT_ID") and os.environ.get("PAYPAL_CLIENT_SECRET"))


def inr_to_usd(inr):
    rate = float(os.environ.get("INR_PER_USD", "88"))
    return max(round(inr / rate, 2), 0.01)


def _access_token():
    if not configured():
        raise PayPalError("PayPal keys missing: set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in .env")
    if _token["value"] and _token["expires"] > time.time() + 60:
        return _token["value"]
    r = _session.post(base_url() + "/v1/oauth2/token",
                      auth=(os.environ["PAYPAL_CLIENT_ID"], os.environ["PAYPAL_CLIENT_SECRET"]),
                      data={"grant_type": "client_credentials"}, timeout=TIMEOUT)
    if r.status_code != 200:
        raise PayPalError(f"PayPal auth failed ({r.status_code}): {r.text[:200]}")
    data = r.json()
    _token.update(value=data["access_token"], expires=time.time() + int(data.get("expires_in", 3000)))
    return _token["value"]


def warm_up():
    """Fetch the OAuth token in a daemon thread at startup (no-op without keys)."""
    if not configured():
        return
    import threading

    def run():
        try:
            _access_token()
        except Exception as e:  # network down, bad keys: the first real call will report it
            print("PayPal warm-up failed:", e)
    threading.Thread(target=run, daemon=True).start()


def _call(method, path, body=None, ok=(200, 201, 202, 204)):
    headers = {"Authorization": "Bearer " + _access_token(), "Content-Type": "application/json",
               "Prefer": "return=representation", "PayPal-Request-Id": str(uuid.uuid4())}
    r = _session.request(method, base_url() + path, json=body, headers=headers, timeout=TIMEOUT)
    if r.status_code not in ok:
        detail = r.text[:400]
        try:
            j = r.json()
            detail = j.get("message", "") + " " + "; ".join(d.get("description", d.get("issue", ""))
                                                           for d in j.get("details", []))
        except Exception:
            pass
        raise PayPalError(f"PayPal {method} {path} failed ({r.status_code}): {detail.strip()}")
    return r.json() if r.text else {}


def _id_from(resp):
    if resp.get("id"):
        return resp["id"]
    href = resp.get("href") or next((l["href"] for l in resp.get("links", []) if l.get("rel") == "self"), "")
    return href.rstrip("/").split("/")[-1]


# ---------------------------------------------------------------- Invoicing v2

def create_and_send_invoice(customer_name, lines, amount_inr, recipient_email=None, shop_name="Dukaan Saathi", note=None):
    """lines: [{name}] summarised; amounts converted to USD at a fixed rate.

    `note` (e.g. the AI-written collection message) is shown to the payer on the invoice.
    If PayPal refuses to email the recipient (e.g. India-to-India restriction), the invoice is still
    issued as a shareable link (send_to_recipient=false) so the shopkeeper can WhatsApp it.
    """
    usd_total = inr_to_usd(amount_inr)
    first, _, last = customer_name.partition(" ")
    default_note = (f"Udhaar (credit) balance of ₹{amount_inr:,.2f} at {shop_name}. "
                    f"Converted at ₹{os.environ.get('INR_PER_USD', '88')} per USD.")
    body = {
        "detail": {
            "currency_code": "USD",
            "invoice_date": date.today().isoformat(),
            "note": (note.strip() + "\n\n" + default_note)[:4000] if note else default_note,
            "payment_term": {"term_type": "DUE_ON_RECEIPT"},
        },
        "invoicer": {"business_name": shop_name},
        "items": [{
            "name": "Khata balance (udhaar)",
            "description": "; ".join(f"{l['name']}" for l in lines)[:900] or "Groceries on credit",
            "quantity": "1",
            "unit_amount": {"currency_code": "USD", "value": f"{usd_total:.2f}"},
            "unit_of_measure": "AMOUNT",
        }],
    }
    if recipient_email:
        body["primary_recipients"] = [{"billing_info": {"name": {"given_name": first or customer_name,
                                                                 "surname": last or "-"},
                                                        "email_address": recipient_email}}]
    created = _call("POST", "/v2/invoicing/invoices", body)
    inv_id = _id_from(created)
    delivery = "email"
    try:
        _call("POST", f"/v2/invoicing/invoices/{inv_id}/send",
              {"send_to_invoicer": False, "send_to_recipient": bool(recipient_email)})
    except PayPalError as e:
        if recipient_email and ("406" in str(e) or "within India" in str(e) or "422" in str(e)):
            # PayPal will not email this recipient: issue the invoice as a link instead
            _call("POST", f"/v2/invoicing/invoices/{inv_id}/send", {"send_to_invoicer": False, "send_to_recipient": False})
            delivery = "link"
        else:
            raise
    info = get_invoice(inv_id)
    return {"paypal_id": inv_id, "amount_usd": usd_total, "delivery": delivery, **info}


def get_invoice(inv_id):
    inv = _call("GET", f"/v2/invoicing/invoices/{inv_id}")
    meta = inv.get("detail", {}).get("metadata", {})
    due = inv.get("due_amount", {}).get("value")
    return {"status": inv.get("status", "UNKNOWN"), "pay_url": meta.get("recipient_view_url"),
            "due_usd": float(due) if due is not None else None,
            "invoice_date": inv.get("detail", {}).get("invoice_date")}


def remind_invoice(inv_id):
    """Ask PayPal to email a reminder for an open invoice (204). Subject/note are system-defined."""
    _call("POST", f"/v2/invoicing/invoices/{inv_id}/remind", {"send_to_invoicer": False, "send_to_recipient": True})
    return get_invoice(inv_id)


def record_cash_payment(inv_id, amount_usd):
    _call("POST", f"/v2/invoicing/invoices/{inv_id}/payments", {
        "method": "CASH", "payment_date": date.today().isoformat(),
        "amount": {"currency_code": "USD", "value": f"{amount_usd:.2f}"},
        "note": "Paid in cash at the shop"})
    return get_invoice(inv_id)


PAID_STATES = {"PAID", "MARKED_AS_PAID"}

# ---------------------------------------------------------------- Orders v2 (supplier reorder)


def create_supplier_order(po_id, supplier_name, total_inr, payee_email=None):
    unit = {"reference_id": f"PO-{po_id}",
            "description": f"Stock reorder PO-{po_id} for {supplier_name}"[:127],
            "amount": {"currency_code": "USD", "value": f"{inr_to_usd(total_inr):.2f}"}}
    if payee_email:
        unit["payee"] = {"email_address": payee_email}
    order = _call("POST", "/v2/checkout/orders", {"intent": "CAPTURE", "purchase_units": [unit]})
    return order["id"]


def capture_order(order_id):
    res = _call("POST", f"/v2/checkout/orders/{order_id}/capture", {})
    return res.get("status", "UNKNOWN")
