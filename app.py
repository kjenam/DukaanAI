"""Dukaan Saathi: AI assistant for a village kirana shop (PayPal AI Hackathon 2026)."""
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request

load_dotenv()

import ai  # noqa: E402  (needs env loaded first)
import db  # noqa: E402
import paypal  # noqa: E402

app = Flask(__name__)
db.init_db()
paypal.warm_up()   # fetch the OAuth token in the background so the first PayPal call is not slow

SHOP_NAME = os.environ.get("SHOP_NAME", "Prajapat Kirana Store")
DEADSTOCK_DAYS = int(os.environ.get("DEADSTOCK_DAYS", "30"))


def conn():
    if "conn" not in g:
        g.conn = db.connect()
    return g.conn


@app.teardown_appcontext
def close_conn(_):
    c = g.pop("conn", None)
    if c:
        c.close()


def err(msg, code=400):
    return jsonify({"error": msg}), code


@app.errorhandler(paypal.PayPalError)
def paypal_error(e):
    return err(str(e), 502)


# ---------------------------------------------------------------- helpers

def items_all():
    return db.rows(conn(), "SELECT * FROM items ORDER BY category, name")


def customers_with_balance():
    """All customers with khata balance and last PayPal invoice, in 3 queries instead of 2 per customer."""
    c = conn()
    cs = db.rows(c, "SELECT * FROM customers ORDER BY name")
    bal = {r["customer_id"]: round(r["bal"], 2) for r in db.rows(c, """
        SELECT customer_id, COALESCE(SUM(CASE WHEN kind='credit' THEN amount ELSE -amount END),0) AS bal
        FROM khata_entries GROUP BY customer_id""")}
    last = {r["customer_id"]: r for r in db.rows(c, """
        SELECT i.* FROM invoices i JOIN (SELECT customer_id, MAX(id) AS mid FROM invoices GROUP BY customer_id) m
        ON m.mid = i.id""")}
    for x in cs:
        x["balance"] = bal.get(x["id"], 0.0)
        x["last_invoice"] = last.get(x["id"])
    cs.sort(key=lambda x: -x["balance"])
    return cs


def find_or_create_customer(name):
    name = (name or "").strip()
    if not name:
        return None
    c = db.one(conn(), "SELECT * FROM customers WHERE lower(name)=lower(?)", (name,))
    if c:
        return c
    first = name.split()[0].lower()
    c = db.one(conn(), "SELECT * FROM customers WHERE lower(name) LIKE ?", (first + "%",))
    if c:
        return c
    cid = conn().execute("INSERT INTO customers (name) VALUES (?)", (name.title(),)).lastrowid
    return db.one(conn(), "SELECT * FROM customers WHERE id=?", (cid,))


def low_stock():
    return db.rows(conn(), "SELECT * FROM items WHERE stock <= threshold ORDER BY stock*1.0/threshold")


def deadstock():
    cutoff = db.now() - timedelta(days=DEADSTOCK_DAYS)
    out = []
    for it in db.rows(conn(), """SELECT i.*, MAX(b.created_at) AS last_sale FROM items i
                                 LEFT JOIN bill_lines bl ON bl.item_id=i.id
                                 LEFT JOIN bills b ON b.id=bl.bill_id
                                 WHERE i.stock > 0 GROUP BY i.id"""):
        last = datetime.fromisoformat(it["last_sale"]) if it["last_sale"] else None
        if last is None or last < cutoff:
            it["days"] = (db.now() - last).days if last else 999
            it["value"] = round(it["stock"] * it["cost_price"], 2)
            out.append(it)
    out.sort(key=lambda x: -x["value"])
    return out


def cached_insight(key, producer, refresh=False, max_age_hours=20):
    row = db.one(conn(), "SELECT * FROM insights WHERE key=?", (key,))
    if row and not refresh and datetime.fromisoformat(row["created_at"]) > db.now() - timedelta(hours=max_age_hours):
        return row["content"], row["created_at"]
    content = producer()
    if content:
        conn().execute("INSERT OR REPLACE INTO insights (key, content, created_at) VALUES (?,?,?)",
                       (key, content, db.now_iso()))
        conn().commit()
        return content, db.now_iso()
    return (row["content"], row["created_at"]) if row else (None, None)


def shop_context():
    """Compact text summary of shop data for the Ask-your-shop chat."""
    c = conn()
    today = db.now().date().isoformat()
    week = (db.now() - timedelta(days=7)).isoformat()
    lines = [f"Shop: {SHOP_NAME}. Today: {today}."]
    lines.append("Customer udhaar balances (₹): " + ", ".join(
        f"{x['name']} {x['balance']:.0f}" for x in customers_with_balance() if abs(x["balance"]) > 0.5))
    t = db.one(c, "SELECT COALESCE(SUM(total),0) s, COUNT(*) n FROM bills WHERE created_at >= ?", (today,))
    w = db.one(c, "SELECT COALESCE(SUM(total),0) s, COUNT(*) n FROM bills WHERE created_at >= ?", (week,))
    lines.append(f"Sales today ₹{t['s']:.0f} in {t['n']} bills. Last 7 days ₹{w['s']:.0f} in {w['n']} bills.")
    top = db.rows(c, """SELECT i.name, SUM(bl.qty) q, SUM(bl.amount) a, i.unit FROM bill_lines bl
                        JOIN bills b ON b.id=bl.bill_id JOIN items i ON i.id=bl.item_id
                        WHERE b.created_at >= ? GROUP BY i.id ORDER BY a DESC LIMIT 10""", (week,))
    lines.append("Top sellers last 7 days: " + ", ".join(f"{x['name']} ({x['q']:g} {x['unit']}, ₹{x['a']:.0f})" for x in top))
    margin = db.rows(c, """SELECT i.name, SUM(bl.qty*(bl.price-i.cost_price)) p FROM bill_lines bl
                           JOIN bills b ON b.id=bl.bill_id JOIN items i ON i.id=bl.item_id
                           WHERE b.created_at >= ? GROUP BY i.id ORDER BY p DESC LIMIT 5""", (week,))
    lines.append("Most profit last 7 days: " + ", ".join(f"{x['name']} ₹{x['p']:.0f}" for x in margin))
    lines.append("Low stock: " + (", ".join(f"{x['name']} {x['stock']:g}/{x['threshold']:g} {x['unit']}"
                                           for x in low_stock()) or "none"))
    lines.append("Deadstock (no sale in %d days): " % DEADSTOCK_DAYS + (", ".join(
        f"{x['name']} {x['stock']:g} {x['unit']} worth ₹{x['value']:.0f}" for x in deadstock()) or "none"))
    lines.append("Stock list: " + "; ".join(f"{x['name']} {x['stock']:g} {x['unit']} @₹{x['price']:g}" for x in items_all()))
    return "\n".join(lines)


def fallback_answer(q):
    """Basic answers when Gemini is not configured."""
    ql = q.lower()
    if any(w in ql for w in ["owe", "udhaar", "udhar", "उधार", "baki", "बाकी", "due", "kitna dena"]):
        cs = [c for c in customers_with_balance() if c["balance"] > 0.5][:5]
        return "Highest udhaar: " + ", ".join(f"{c['name']} ₹{c['balance']:.0f}" for c in cs)
    if any(w in ql for w in ["low", "khatam", "खत्म", "kam", "कम", "stock"]):
        return "Low stock: " + (", ".join(f"{x['name']} ({x['stock']:g} {x['unit']})" for x in low_stock()) or "none")
    return "AI is not configured (add GEMINI_API_KEY). Here is a summary:\n" + "\n".join(shop_context().splitlines()[:5])


# ---------------------------------------------------------------- pages

@app.get("/")
def index():
    return render_template("index.html", shop_name=SHOP_NAME,
                           paypal_client_id=os.environ.get("PAYPAL_CLIENT_ID", ""),
                           inr_per_usd=os.environ.get("INR_PER_USD", "88"))


@app.get("/healthz")
def health():
    return {"ok": True, "ai": ai.available(), "paypal": paypal.configured(), "ai_last": ai.LAST}


# ---------------------------------------------------------------- state

@app.get("/api/state")
def state():
    c = conn()
    today = db.now().date().isoformat()
    t = db.one(c, "SELECT COALESCE(SUM(total),0) s, COUNT(*) n FROM bills WHERE created_at >= ?", (today,))
    recent = db.rows(c, """SELECT b.*, cu.name AS customer FROM bills b LEFT JOIN customers cu ON cu.id=b.customer_id
                           WHERE b.raw_text != 'seed' ORDER BY b.id DESC LIMIT 8""")
    customers = customers_with_balance()
    return jsonify({
        "shop": SHOP_NAME, "ai": ai.available(), "paypal": paypal.configured(),
        "items": items_all(), "customers": customers,
        "low_stock": low_stock(), "deadstock": deadstock(),
        "today": {"sales": t["s"], "bills": t["n"]},
        "udhaar_total": round(sum(x["balance"] for x in customers if x["balance"] > 0), 2),
        "recent_bills": recent,
        "pos": db.rows(c, """SELECT p.*, s.name AS supplier FROM purchase_orders p JOIN suppliers s ON s.id=p.supplier_id
                             WHERE p.status IN ('draft','paid') ORDER BY p.id DESC LIMIT 10"""),
    })


# ---------------------------------------------------------------- command → plan → confirm

@app.post("/api/parse")
def parse():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    lang = data.get("lang", "en")
    if not text:
        return err("Say or type something first")
    items = items_all()
    plan = ai.parse_command(text, items, db.rows(conn(), "SELECT * FROM customers"))
    by_id = {i["id"]: i for i in items}
    if plan["intent"] == "query":
        q = plan.get("question") or text
        answer = ai.answer_question(q, shop_context(), lang) or fallback_answer(q)
        return jsonify({"plan": plan, "answer": answer})
    for line in plan["items"]:
        it = by_id[line["item_id"]]
        line.update(name=it["name"], name_hi=it["name_hi"], unit=it["unit"], price=it["price"],
                    amount=round(line["qty"] * it["price"], 2), stock=it["stock"])
    for key in ("price_updates", "stock_updates"):
        for line in plan[key]:
            it = by_id[line["item_id"]]
            line.update(name=it["name"], name_hi=it["name_hi"], unit=it["unit"], old_price=it["price"], stock=it["stock"])
    plan["total"] = round(sum(l["amount"] for l in plan["items"]), 2)
    if plan.get("customer"):
        existing = db.one(conn(), "SELECT * FROM customers WHERE lower(name)=lower(?)", (plan["customer"],))
        plan["customer_exists"] = bool(existing)
        if existing:
            plan["customer_balance"] = db.balance(conn(), existing["id"])
    plan["raw_text"] = text
    return jsonify({"plan": plan})


@app.post("/api/bills")
def create_bill():
    data = request.get_json(force=True)
    lines = [l for l in data.get("lines", []) if float(l.get("qty", 0)) > 0]
    if not lines:
        return err("Bill has no items")
    mode = "udhaar" if data.get("udhaar") else "cash"
    cust = find_or_create_customer(data.get("customer"))
    if mode == "udhaar" and not cust:
        return err("Udhaar needs a customer name")
    c = conn()
    total = 0
    priced = []
    for l in lines:
        it = db.one(c, "SELECT * FROM items WHERE id=?", (int(l["item_id"]),))
        if not it:
            return err(f"Unknown item {l['item_id']}")
        qty = float(l["qty"])
        amount = round(qty * it["price"], 2)
        total += amount
        priced.append((it, qty, amount))
    total = round(total, 2)
    bid = c.execute("INSERT INTO bills (customer_id, total, mode, raw_text, created_at) VALUES (?,?,?,?,?)",
                    (cust["id"] if cust else None, total, mode, data.get("raw_text", ""), db.now_iso())).lastrowid
    for it, qty, amount in priced:
        c.execute("INSERT INTO bill_lines (bill_id, item_id, qty, price, amount) VALUES (?,?,?,?,?)",
                  (bid, it["id"], qty, it["price"], amount))
        c.execute("UPDATE items SET stock = MAX(stock - ?, 0) WHERE id=?", (qty, it["id"]))
    if mode == "udhaar":
        c.execute("INSERT INTO khata_entries (customer_id, kind, amount, bill_id, note, created_at) VALUES (?,?,?,?,?,?)",
                  (cust["id"], "credit", total, bid, f"Bill #{bid}", db.now_iso()))
    c.commit()
    low = [it["name"] for it, _, _ in priced
           if db.one(c, "SELECT stock<=threshold AS low FROM items WHERE id=?", (it["id"],))["low"]]
    return jsonify({"bill_id": bid, "total": total, "mode": mode, "customer": cust["name"] if cust else None,
                    "balance": db.balance(c, cust["id"]) if cust else None, "low_stock": low})


@app.post("/api/payments")
def add_payment():
    data = request.get_json(force=True)
    cust = (db.one(conn(), "SELECT * FROM customers WHERE id=?", (data["customer_id"],)) if data.get("customer_id")
            else find_or_create_customer(data.get("customer")))
    amount = float(data.get("amount") or 0)
    if not cust or amount <= 0:
        return err("Need a customer and an amount")
    conn().execute("INSERT INTO khata_entries (customer_id, kind, amount, note, created_at) VALUES (?,?,?,?,?)",
                   (cust["id"], "payment", amount, data.get("note") or "Cash jama", db.now_iso()))
    conn().commit()
    return jsonify({"customer": cust["name"], "balance": db.balance(conn(), cust["id"])})


@app.post("/api/prices")
def update_prices():
    for u in request.get_json(force=True).get("updates", []):
        price = float(u["price"])
        if price <= 0:
            continue
        conn().execute("UPDATE items SET price=? WHERE id=?", (price, int(u["item_id"])))
        conn().execute("INSERT INTO price_history (item_id, price, source, created_at) VALUES (?,?,?,?)",
                       (int(u["item_id"]), price, u.get("source", "shopkeeper"), db.now_iso()))
    conn().commit()
    return jsonify({"ok": True})


@app.post("/api/stock")
def add_stock():
    for u in request.get_json(force=True).get("updates", []):
        conn().execute("UPDATE items SET stock = stock + ? WHERE id=?", (float(u["qty"]), int(u["item_id"])))
    conn().commit()
    return jsonify({"ok": True})


@app.post("/api/items/<int:item_id>")
def edit_item(item_id):
    data = request.get_json(force=True)
    for field in ("stock", "threshold"):
        if field in data:
            conn().execute(f"UPDATE items SET {field}=? WHERE id=?", (float(data[field]), item_id))
    if "price" in data:
        conn().execute("UPDATE items SET price=? WHERE id=?", (float(data["price"]), item_id))
        conn().execute("INSERT INTO price_history (item_id, price, source, created_at) VALUES (?,?,?,?)",
                       (item_id, float(data["price"]), "shopkeeper", db.now_iso()))
    conn().commit()
    return jsonify({"ok": True})


@app.get("/api/items/<int:item_id>/history")
def item_history(item_id):
    return jsonify(db.rows(conn(), "SELECT * FROM price_history WHERE item_id=? ORDER BY created_at", (item_id,)))


@app.get("/api/items/<int:item_id>/market")
def item_market(item_id):
    it = db.one(conn(), "SELECT * FROM items WHERE id=?", (item_id,))
    if not it:
        return err("Unknown item", 404)
    if not ai.available():
        return jsonify({"content": "Add GEMINI_API_KEY to look up market prices.", "at": None})
    content, at = cached_insight(f"market:{item_id}", lambda: ai.market_price(it),
                                 refresh=request.args.get("refresh") == "1", max_age_hours=12)
    return jsonify({"content": content or "Could not fetch a market price right now.", "at": at})


# ---------------------------------------------------------------- khata + PayPal invoices

@app.get("/api/customers/<int:cid>")
def customer_detail(cid):
    cust = db.one(conn(), "SELECT * FROM customers WHERE id=?", (cid,))
    if not cust:
        return err("Unknown customer", 404)
    cust["balance"] = db.balance(conn(), cid)
    cust["entries"] = db.rows(conn(), "SELECT * FROM khata_entries WHERE customer_id=? ORDER BY created_at DESC LIMIT 40", (cid,))
    cust["invoices"] = db.rows(conn(), "SELECT * FROM invoices WHERE customer_id=? ORDER BY id DESC", (cid,))
    return jsonify(cust)


@app.post("/api/customers/<int:cid>")
def customer_update(cid):
    data = request.get_json(force=True)
    conn().execute("UPDATE customers SET email=COALESCE(?, email), phone=COALESCE(?, phone) WHERE id=?",
                   (data.get("email") or None, data.get("phone") or None, cid))
    conn().commit()
    return jsonify({"ok": True})


@app.post("/api/customers/<int:cid>/invoice")
def send_invoice(cid):
    cust = db.one(conn(), "SELECT * FROM customers WHERE id=?", (cid,))
    if not cust:
        return err("Unknown customer", 404)
    bal = db.balance(conn(), cid)
    if bal <= 0:
        return err("No udhaar balance to invoice")
    open_inv = db.one(conn(), "SELECT * FROM invoices WHERE customer_id=? AND status NOT IN ('PAID','MARKED_AS_PAID','CANCELLED')", (cid,))
    if open_inv:
        return err("This customer already has an open invoice. Sync it or record a payment first.")
    lines = db.rows(conn(), """SELECT i.name || ' x' || bl.qty AS name FROM khata_entries k
                               JOIN bill_lines bl ON bl.bill_id=k.bill_id JOIN items i ON i.id=bl.item_id
                               WHERE k.customer_id=? AND k.kind='credit' ORDER BY k.created_at DESC LIMIT 15""", (cid,))
    email = cust.get("email") or os.environ.get("PAYPAL_DEMO_BUYER_EMAIL") or None
    res = paypal.create_and_send_invoice(cust["name"], lines, bal, email, SHOP_NAME)
    now = db.now_iso()
    iid = conn().execute("""INSERT INTO invoices (customer_id, paypal_id, amount_inr, amount_usd, status, pay_url, created_at, updated_at)
                            VALUES (?,?,?,?,?,?,?,?)""",
                         (cid, res["paypal_id"], bal, res["amount_usd"], res["status"], res.get("pay_url"), now, now)).lastrowid
    conn().commit()
    return jsonify(db.one(conn(), "SELECT * FROM invoices WHERE id=?", (iid,)))


def _apply_invoice_status(inv, info):
    conn().execute("UPDATE invoices SET status=?, pay_url=COALESCE(?, pay_url), updated_at=? WHERE id=?",
                   (info["status"], info.get("pay_url"), db.now_iso(), inv["id"]))
    already = db.one(conn(), "SELECT id FROM khata_entries WHERE invoice_id=?", (inv["id"],))
    if info["status"] in paypal.PAID_STATES and not already:
        how = "PayPal" if info["status"] == "PAID" else "cash (recorded on PayPal invoice)"
        conn().execute("""INSERT INTO khata_entries (customer_id, kind, amount, invoice_id, note, created_at)
                          VALUES (?,?,?,?,?,?)""",
                       (inv["customer_id"], "payment", inv["amount_inr"], inv["id"],
                        f"Invoice {inv['paypal_id']} paid via {how}", db.now_iso()))
    conn().commit()
    out = db.one(conn(), "SELECT * FROM invoices WHERE id=?", (inv["id"],))
    out["balance"] = db.balance(conn(), inv["customer_id"])
    return out


@app.post("/api/invoices/<int:iid>/sync")
def sync_invoice(iid):
    inv = db.one(conn(), "SELECT * FROM invoices WHERE id=?", (iid,))
    if not inv:
        return err("Unknown invoice", 404)
    return jsonify(_apply_invoice_status(inv, paypal.get_invoice(inv["paypal_id"])))


@app.post("/api/invoices/<int:iid>/record-cash")
def record_cash(iid):
    inv = db.one(conn(), "SELECT * FROM invoices WHERE id=?", (iid,))
    if not inv:
        return err("Unknown invoice", 404)
    return jsonify(_apply_invoice_status(inv, paypal.record_cash_payment(inv["paypal_id"], inv["amount_usd"])))


# ---------------------------------------------------------------- agentic supplier reorder

@app.post("/api/reorder/suggest")
def reorder_suggest():
    c = conn()
    c.execute("DELETE FROM po_lines WHERE po_id IN (SELECT id FROM purchase_orders WHERE status='draft')")
    c.execute("DELETE FROM purchase_orders WHERE status='draft'")
    week = (db.now() - timedelta(days=14)).isoformat()
    by_supplier = {}
    for it in low_stock():
        sold = db.one(c, """SELECT COALESCE(SUM(bl.qty),0) q FROM bill_lines bl JOIN bills b ON b.id=bl.bill_id
                            WHERE bl.item_id=? AND b.created_at >= ?""", (it["id"], week))["q"]
        # cover ~2 weeks of demand, at least 3x threshold
        target = max(sold, it["threshold"] * 3)
        qty = max(round(target - it["stock"]), 1)
        by_supplier.setdefault(it["supplier_id"], []).append((it, qty, sold))
    created = []
    for sid, lines in by_supplier.items():
        sup = db.one(c, "SELECT * FROM suppliers WHERE id=?", (sid,))
        total = round(sum(it["cost_price"] * q for it, q, _ in lines), 2)
        note = "; ".join(f"{it['name']}: {it['stock']:g} left, sold {s:g} in 14 days" for it, _, s in lines)
        pid = c.execute("""INSERT INTO purchase_orders (supplier_id, total_inr, total_usd, status, note, created_at)
                           VALUES (?,?,?,?,?,?)""", (sid, total, paypal.inr_to_usd(total), "draft", note, db.now_iso())).lastrowid
        for it, q, _ in lines:
            c.execute("INSERT INTO po_lines (po_id, item_id, qty, cost_price, amount) VALUES (?,?,?,?,?)",
                      (pid, it["id"], q, it["cost_price"], round(q * it["cost_price"], 2)))
        created.append(pid)
    c.commit()
    return jsonify({"pos": [po_detail(p) for p in created]})


def po_detail(pid):
    po = db.one(conn(), "SELECT p.*, s.name AS supplier, s.paypal_email FROM purchase_orders p JOIN suppliers s ON s.id=p.supplier_id WHERE p.id=?", (pid,))
    if po:
        po["lines"] = db.rows(conn(), """SELECT pl.*, i.name, i.name_hi, i.unit FROM po_lines pl JOIN items i ON i.id=pl.item_id
                                        WHERE pl.po_id=?""", (pid,))
    return po


@app.get("/api/po/<int:pid>")
def get_po(pid):
    po = po_detail(pid)
    return jsonify(po) if po else err("Unknown order", 404)


@app.post("/api/po/<int:pid>/lines")
def edit_po_lines(pid):
    """Owner can change quantities before approving."""
    po = po_detail(pid)
    if not po or po["status"] != "draft":
        return err("Only draft orders can be edited")
    for l in request.get_json(force=True).get("lines", []):
        qty = max(float(l["qty"]), 0)
        conn().execute("UPDATE po_lines SET qty=?, amount=ROUND(?*cost_price,2) WHERE id=? AND po_id=?",
                       (qty, qty, int(l["id"]), pid))
    total = db.one(conn(), "SELECT COALESCE(SUM(amount),0) t FROM po_lines WHERE po_id=?", (pid,))["t"]
    conn().execute("UPDATE purchase_orders SET total_inr=?, total_usd=? WHERE id=?", (total, paypal.inr_to_usd(total), pid))
    conn().commit()
    return jsonify(po_detail(pid))


@app.post("/api/po/<int:pid>/paypal-order")
def po_paypal_order(pid):
    po = po_detail(pid)
    if not po or po["status"] != "draft":
        return err("Order is not awaiting approval")
    if po["total_inr"] <= 0:
        return err("Order total is zero")
    order_id = paypal.create_supplier_order(pid, po["supplier"], po["total_inr"], po.get("paypal_email") or None)
    conn().execute("UPDATE purchase_orders SET paypal_order_id=? WHERE id=?", (order_id, pid))
    conn().commit()
    return jsonify({"id": order_id})


@app.post("/api/po/<int:pid>/capture")
def po_capture(pid):
    po = po_detail(pid)
    order_id = (request.get_json(silent=True) or {}).get("orderID") or (po or {}).get("paypal_order_id")
    if not po or not order_id:
        return err("Unknown order")
    if po["status"] == "paid":
        return jsonify(po)
    status = paypal.capture_order(order_id)
    if status != "COMPLETED":
        return err(f"PayPal capture status: {status}")
    conn().execute("UPDATE purchase_orders SET status='paid', paypal_order_id=? WHERE id=?", (order_id, pid))
    for l in po["lines"]:  # demo simplification: stock marked received on payment
        conn().execute("UPDATE items SET stock = stock + ? WHERE id=?", (l["qty"], l["item_id"]))
    conn().commit()
    return jsonify(po_detail(pid))


@app.post("/api/po/<int:pid>/cancel")
def po_cancel(pid):
    conn().execute("UPDATE purchase_orders SET status='cancelled' WHERE id=? AND status='draft'", (pid,))
    conn().commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------- insights

@app.post("/api/chat")
def chat():
    data = request.get_json(force=True)
    q = (data.get("q") or "").strip()
    if not q:
        return err("Ask a question")
    return jsonify({"answer": ai.answer_question(q, shop_context(), data.get("lang", "en")) or fallback_answer(q)})


@app.get("/api/insights/deadstock")
def deadstock_insight():
    lang = request.args.get("lang", "en")
    dead = deadstock()
    content, at = (None, None)
    if dead and ai.available():
        content, at = cached_insight(f"deadstock:{lang}", lambda: ai.deadstock_advice(dead, lang),
                                     refresh=request.args.get("refresh") == "1")
    return jsonify({"items": dead, "advice": content, "at": at, "days": DEADSTOCK_DAYS})


@app.get("/api/insights/news")
def news_insight():
    lang = request.args.get("lang", "en")
    if not ai.available():
        return jsonify({"content": "Add GEMINI_API_KEY to get a daily market summary.", "at": None})
    content, at = cached_insight(f"news:{lang}", lambda: ai.market_news(lang), refresh=request.args.get("refresh") == "1")
    return jsonify({"content": content or "Could not fetch market news right now.", "at": at})


@app.post("/api/reset")
def reset():
    if os.environ.get("ALLOW_RESET", "1") != "1":
        return err("Reset disabled", 403)
    g.pop("conn").close() if "conn" in g else None
    db.init_db(reset=True)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
