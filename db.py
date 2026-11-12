"""SQLite storage, schema and realistic kirana seed data for Dukaan Saathi."""
import os
import random
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.environ.get("SHOP_TZ", "Asia/Kolkata"))


def now():
    """Shop-local time (servers like Render run in UTC)."""
    return datetime.now(TZ).replace(tzinfo=None)

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "dukaan.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT, paypal_email TEXT
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_hi TEXT, aliases TEXT,
    unit TEXT NOT NULL, price REAL NOT NULL, cost_price REAL NOT NULL,
    stock REAL NOT NULL DEFAULT 0, threshold REAL NOT NULL DEFAULT 5,
    supplier_id INTEGER REFERENCES suppliers(id), category TEXT
);
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, price REAL NOT NULL,
    source TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, phone TEXT, email TEXT
);
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY, customer_id INTEGER, total REAL NOT NULL,
    mode TEXT NOT NULL, raw_text TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bill_lines (
    id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, item_id INTEGER NOT NULL,
    qty REAL NOT NULL, price REAL NOT NULL, amount REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS khata_entries (
    id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('credit','payment')),
    amount REAL NOT NULL, bill_id INTEGER, invoice_id INTEGER, note TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, paypal_id TEXT,
    amount_inr REAL NOT NULL, amount_usd REAL NOT NULL, status TEXT NOT NULL,
    pay_url TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY, supplier_id INTEGER NOT NULL, total_inr REAL NOT NULL,
    total_usd REAL NOT NULL, status TEXT NOT NULL, paypal_order_id TEXT,
    note TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS po_lines (
    id INTEGER PRIMARY KEY, po_id INTEGER NOT NULL, item_id INTEGER NOT NULL,
    qty REAL NOT NULL, cost_price REAL NOT NULL, amount REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS insights (
    key TEXT PRIMARY KEY, content TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, lang TEXT, source TEXT, summary TEXT
);
CREATE TABLE IF NOT EXISTS collection_actions (
    id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL, customer_id INTEGER NOT NULL,
    balance REAL NOT NULL, days_overdue INTEGER, priority INTEGER NOT NULL DEFAULT 2,
    action TEXT NOT NULL CHECK (action IN ('invoice','remind','wait')),
    reason TEXT, message TEXT,
    status TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed','sent','skipped','failed')),
    invoice_id INTEGER, pay_url TEXT, error TEXT, created_at TEXT NOT NULL, sent_at TEXT
);
"""

SUPPLIERS = [
    (1, "Gupta Traders (Kirana wholesale)", "9800000001"),
    (2, "Shree Ram Oil & Dal Depot", "9800000002"),
    (3, "Agarwal FMCG Distributors", "9800000003"),
]

# name, hindi, aliases, unit, price, cost, stock, threshold, supplier, category
ITEMS = [
    ("Sugar", "चीनी", "cheeni,chini,shakkar,शक्कर", "kg", 44, 40, 38, 15, 1, "Staples"),
    ("Wheat Atta (Aashirvaad 5kg)", "आटा", "atta,aata,gehu atta,aashirvaad", "pack", 265, 245, 12, 5, 3, "Staples"),
    ("Loose Wheat Flour", "खुला आटा", "khula atta,loose atta", "kg", 34, 30, 60, 20, 1, "Staples"),
    ("Basmati Rice", "बासमती चावल", "basmati,chawal basmati", "kg", 110, 95, 25, 10, 1, "Staples"),
    ("Rice (Regular)", "चावल", "chawal,chaval,rice", "kg", 48, 42, 45, 15, 1, "Staples"),
    ("Toor Dal", "तुअर दाल", "toor dal,arhar dal,arhar,tuar dal", "kg", 150, 135, 4, 8, 2, "Dal"),
    ("Moong Dal", "मूंग दाल", "moong dal,mung dal,moong", "kg", 120, 108, 14, 6, 2, "Dal"),
    ("Chana Dal", "चना दाल", "chana dal,chane ki dal", "kg", 95, 85, 16, 6, 2, "Dal"),
    ("Masoor Dal", "मसूर दाल", "masoor,masur dal", "kg", 100, 90, 10, 5, 2, "Dal"),
    ("Fortune Soyabean Oil 1L", "फॉर्च्यून तेल", "fortune,fortune tel,soyabean tel,soyabean oil,oil,tel", "pouch", 140, 128, 30, 12, 2, "Oil"),
    ("Mustard Oil 1L", "सरसों का तेल", "sarso tel,sarson tel,sarso ka tel,mustard oil,kachi ghani", "bottle", 175, 160, 6, 10, 2, "Oil"),
    ("Desi Ghee 1L", "घी", "ghee,desi ghee,amul ghee", "pack", 620, 575, 7, 3, 3, "Oil"),
    ("Tata Salt 1kg", "नमक", "namak,salt,tata namak", "pack", 28, 24, 40, 15, 3, "Spices"),
    ("Turmeric Powder 100g", "हल्दी", "haldi,turmeric", "pack", 32, 26, 25, 8, 3, "Spices"),
    ("Red Chilli Powder 100g", "लाल मिर्च", "mirch,lal mirch,chilli powder", "pack", 40, 33, 22, 8, 3, "Spices"),
    ("Coriander Powder 100g", "धनिया पाउडर", "dhaniya,dhania powder", "pack", 30, 24, 18, 6, 3, "Spices"),
    ("Jeera 100g", "जीरा", "jeera,zeera,cumin", "pack", 65, 55, 15, 5, 3, "Spices"),
    ("MDH Garam Masala 100g", "गरम मसाला", "garam masala,mdh", "pack", 92, 80, 10, 4, 3, "Spices"),
    ("Tea (Tata Tea Premium 250g)", "चाय पत्ती", "chai,chai patti,tea,tata tea", "pack", 135, 120, 20, 8, 3, "Beverages"),
    ("Parle-G Biscuit", "पारले जी", "parle,parle g,parle-g,biscuit", "pack", 10, 8.5, 120, 40, 3, "Snacks"),
    ("Good Day Biscuit", "गुड डे", "good day,gud day", "pack", 30, 26, 40, 15, 3, "Snacks"),
    ("Maggi Noodles", "मैगी", "maggi,maggie,noodles", "pack", 14, 12, 70, 25, 3, "Snacks"),
    ("Haldiram Bhujia 200g", "भुजिया", "bhujia,haldiram,namkeen", "pack", 55, 47, 25, 8, 3, "Snacks"),
    ("Amul Milk 500ml", "दूध", "doodh,dudh,milk,amul milk", "pouch", 34, 31, 30, 20, 3, "Dairy"),
    ("Amul Butter 100g", "मक्खन", "butter,makhan,makkhan", "pack", 58, 52, 12, 5, 3, "Dairy"),
    ("Paneer 200g", "पनीर", "paneer,panir", "pack", 90, 78, 8, 4, 3, "Dairy"),
    ("Eggs", "अंडे", "anda,ande,egg,eggs", "piece", 7, 6, 90, 30, 1, "Dairy"),
    ("Surf Excel 1kg", "सर्फ़", "surf,surf excel,washing powder", "pack", 140, 125, 15, 6, 3, "Household"),
    ("Wheel Detergent 1kg", "व्हील", "wheel,wheel powder", "pack", 70, 62, 20, 8, 3, "Household"),
    ("Lifebuoy Soap", "लाइफबॉय साबुन", "lifebuoy,sabun,soap", "piece", 38, 33, 40, 15, 3, "Household"),
    ("Vim Bar", "विम बार", "vim,vim bar,bartan sabun", "piece", 20, 17, 30, 10, 3, "Household"),
    ("Colgate 100g", "कोलगेट", "colgate,toothpaste,manjan", "piece", 55, 48, 18, 6, 3, "Personal care"),
    ("Clinic Plus Shampoo Sachet", "शैम्पू", "shampoo,clinic plus,sachet", "piece", 2, 1.6, 200, 50, 3, "Personal care"),
    ("Matchbox", "माचिस", "machis,matchbox,tilli", "piece", 2, 1.5, 150, 40, 1, "Household"),
    ("Agarbatti", "अगरबत्ती", "agarbatti,dhoop", "pack", 25, 20, 35, 10, 1, "Pooja"),
    ("Besan", "बेसन", "besan,gram flour", "kg", 90, 80, 12, 5, 1, "Staples"),
    ("Poha", "पोहा", "poha,chiwda", "kg", 60, 52, 14, 5, 1, "Staples"),
    # Slow movers that the seed leaves unsold, so the deadstock alert has something to show
    ("Kissan Mixed Fruit Jam 500g", "जैम", "jam,kissan jam", "jar", 160, 140, 9, 2, 3, "Spreads"),
    ("Saffola Oats 1kg", "ओट्स", "oats,saffola oats", "pack", 199, 175, 7, 2, 3, "Breakfast"),
    ("Horlicks 500g", "हॉर्लिक्स", "horlicks,horlicks powder", "jar", 285, 255, 6, 2, 3, "Beverages"),
    ("Dark Fantasy Biscuit", "डार्क फैंटेसी", "dark fantasy,choco fills", "pack", 40, 34, 18, 4, 3, "Snacks"),
]
DEADSTOCK_SEED = {"Kissan Mixed Fruit Jam 500g", "Saffola Oats 1kg", "Horlicks 500g", "Dark Fantasy Biscuit"}

CUSTOMERS = [
    ("Sharma ji", "9811111111"), ("Meena Devi", "9822222222"), ("Ramesh Choudhary", "9833333333"),
    ("Suresh Kumawat", "9844444444"), ("Lakshmi ben", "9855555555"), ("Vikram Singh", "9866666666"),
]


def now_iso(dt=None):
    return (dt or now()).isoformat(timespec="seconds")


def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def rows(conn, sql, params=()):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def one(conn, sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return dict(r) if r else None


def init_db(reset=False):
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = connect()
    conn.executescript(SCHEMA)
    if not one(conn, "SELECT id FROM items LIMIT 1"):
        seed(conn)
    conn.close()


def seed(conn):
    supplier_email = os.environ.get("SUPPLIER_PAYPAL_EMAIL", "")
    for sid, name, phone in SUPPLIERS:
        conn.execute("INSERT INTO suppliers (id, name, phone, paypal_email) VALUES (?,?,?,?)",
                     (sid, name, phone, supplier_email))
    start = now() - timedelta(days=45)
    for it in ITEMS:
        cur = conn.execute(
            "INSERT INTO items (name, name_hi, aliases, unit, price, cost_price, stock, threshold, supplier_id, category)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)", it)
        # a small price history so the price chart/history is not empty
        old = round(it[4] * random.Random(it[0]).uniform(0.9, 0.98))
        conn.execute("INSERT INTO price_history (item_id, price, source, created_at) VALUES (?,?,?,?)",
                     (cur.lastrowid, old, "seed", now_iso(start)))
        conn.execute("INSERT INTO price_history (item_id, price, source, created_at) VALUES (?,?,?,?)",
                     (cur.lastrowid, it[4], "seed", now_iso(start + timedelta(days=30))))
    for name, phone in CUSTOMERS:
        conn.execute("INSERT INTO customers (name, phone) VALUES (?,?)", (name, phone))

    rnd = random.Random(42)
    items = rows(conn, "SELECT * FROM items")
    sellable = [i for i in items if i["name"] not in DEADSTOCK_SEED]
    customers = rows(conn, "SELECT * FROM customers")
    for day in range(45):
        for _ in range(rnd.randint(4, 9)):
            when = start + timedelta(days=day, hours=rnd.randint(8, 20), minutes=rnd.randint(0, 59))
            picks = rnd.sample(sellable, rnd.randint(1, 4))
            lines = []
            for it in picks:
                qty = rnd.choice([1, 1, 2, 3]) if it["unit"] != "kg" else rnd.choice([0.5, 1, 2, 5])
                lines.append((it["id"], qty, it["price"], round(qty * it["price"], 2)))
            total = round(sum(l[3] for l in lines), 2)
            udhaar = rnd.random() < 0.3
            cust = rnd.choice(customers) if udhaar or rnd.random() < 0.3 else None
            mode = "udhaar" if udhaar else "cash"
            bid = conn.execute("INSERT INTO bills (customer_id, total, mode, raw_text, created_at) VALUES (?,?,?,?,?)",
                               (cust["id"] if cust else None, total, mode, "seed", now_iso(when))).lastrowid
            for item_id, qty, price, amount in lines:
                conn.execute("INSERT INTO bill_lines (bill_id, item_id, qty, price, amount) VALUES (?,?,?,?,?)",
                             (bid, item_id, qty, price, amount))
            if udhaar:
                conn.execute("INSERT INTO khata_entries (customer_id, kind, amount, bill_id, note, created_at)"
                             " VALUES (?,?,?,?,?,?)", (cust["id"], "credit", total, bid, "Bill #%d" % bid, now_iso(when)))
        # occasional repayments so balances look realistic
        if day % 6 == 5:
            cust = rnd.choice(customers)
            bal = balance(conn, cust["id"])
            if bal > 100:
                amt = round(bal * rnd.uniform(0.3, 0.7), -1)
                conn.execute("INSERT INTO khata_entries (customer_id, kind, amount, note, created_at) VALUES (?,?,?,?,?)",
                             (cust["id"], "payment", amt, "Cash jama", now_iso(start + timedelta(days=day, hours=19))))
    # deadstock items: one sale long ago so "days since last sale" is meaningful
    for it in items:
        if it["name"] in DEADSTOCK_SEED:
            when = start - timedelta(days=rnd.randint(10, 30))
            bid = conn.execute("INSERT INTO bills (customer_id, total, mode, raw_text, created_at) VALUES (NULL,?,?,?,?)",
                               (it["price"], "cash", "seed", now_iso(when))).lastrowid
            conn.execute("INSERT INTO bill_lines (bill_id, item_id, qty, price, amount) VALUES (?,?,?,?,?)",
                         (bid, it["id"], 1, it["price"], it["price"]))
    conn.commit()


def balance(conn, customer_id):
    r = one(conn, "SELECT COALESCE(SUM(CASE WHEN kind='credit' THEN amount ELSE -amount END),0) AS bal"
                  " FROM khata_entries WHERE customer_id=?", (customer_id,))
    return round(r["bal"], 2)
