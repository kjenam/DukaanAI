"""Gemini helpers. Every function has a no-AI fallback so the app never blocks billing."""
import json
import os
import re
import time

import requests

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Models: the "fast" chain answers billing commands (latency matters), the "smart" chain does insights.
# Each call walks the chain on 404 (retired model), 429/503 (quota or high demand) or a timeout.
FAST_CHAIN = [m.strip() for m in os.environ.get("GEMINI_FAST_MODEL", "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-flash-lite-latest").split(",") if m.strip()]
SMART_CHAIN = [m.strip() for m in os.environ.get("GEMINI_MODEL", "gemini-3.6-flash,gemini-3.5-flash-lite,gemini-flash-latest").split(",") if m.strip()]
FAST_TIMEOUT = float(os.environ.get("GEMINI_FAST_TIMEOUT", "12"))
SMART_TIMEOUT = float(os.environ.get("GEMINI_TIMEOUT", "40"))
LAST = {"model": None, "ms": None}   # for /healthz and the UI footer


def _key():
    return os.environ.get("GEMINI_API_KEY", "").strip()


def available():
    return bool(_key())


_session = requests.Session()   # keep-alive: saves a TLS handshake on every call


def _post(model, body, timeout):
    return _session.post(GEMINI_URL.format(model=model), params={"key": _key()}, json=body, timeout=timeout)


def gemini(prompt, json_mode=False, search=False, fast=False, max_tokens=None):
    """Call Gemini; returns text or None on any failure (caller falls back).

    fast=True uses the low-latency chain with minimal thinking (billing commands).
    """
    if not _key():
        return None
    chain = FAST_CHAIN if fast else SMART_CHAIN
    timeout = FAST_TIMEOUT if fast else SMART_TIMEOUT
    gen = {"temperature": 0.2, "maxOutputTokens": max_tokens or (768 if fast else 2048),
           "thinkingConfig": {"thinkingLevel": "minimal" if fast else "low"}}
    if json_mode:
        gen["responseMimeType"] = "application/json"
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": gen}
    if search:
        body["tools"] = [{"google_search": {}}]
    for model in chain:
        t0 = time.time()
        try:
            r = _post(model, body, timeout)
            if r.status_code == 400 and "thinkingConfig" in body["generationConfig"]:
                # model does not accept thinkingLevel: retry once without it
                body["generationConfig"] = {k: v for k, v in gen.items() if k != "thinkingConfig"}
                r = _post(model, body, timeout)
            if r.status_code in (400, 429) and "tools" in body:
                # grounding may be unsupported or over quota on this key: retry plain (no web search)
                body.pop("tools", None)
                r = _post(model, body, timeout)
            if r.status_code in (404, 429, 503):
                print(f"Gemini {model}: {r.status_code}, trying next model")
                continue
            if r.status_code != 200:
                print("Gemini error", model, r.status_code, r.text[:300])
                return None
            parts = r.json()["candidates"][0]["content"]["parts"]
            LAST.update(model=model, ms=int((time.time() - t0) * 1000))
            return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
        except requests.Timeout:
            print(f"Gemini {model}: timeout after {timeout}s, trying next model")
            continue
        except Exception as e:  # network, malformed response
            print("Gemini exception", model, e)
            return None
    return None


def _json(text):
    if not text:
        return None
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0) if m else text)
    except Exception:
        return None


# ---------------------------------------------------------------- command parsing

PARSE_PROMPT = """You are the billing assistant of a small kirana (grocery) shop in a Rajasthan village.
The shopkeeper speaks Hindi, Hinglish or English; text may be in Devanagari or Roman script and may
come from speech-to-text with mistakes. Convert the command into JSON.

Item catalog (id|name|aliases|unit|price in rupees):
{catalog}

Known customers: {customers}

Return ONLY JSON with this shape:
{{
 "intent": "bill" | "payment" | "price_update" | "stock_add" | "query",
 "customer": string or null,      // match a known customer if it is clearly the same person, else the name as said
 "udhaar": true/false,             // true if the sale is on credit (udhaar / khata me likho / baad me dega)
 "items": [{{"item_id": int, "qty": number}}],      // for bill
 "amount": number or null,                        // for payment (customer paid money)
 "price_updates": [{{"item_id": int, "price": number}}],  // for price_update ("cheeni ab 46 rupaye kilo")
 "stock_updates": [{{"item_id": int, "qty": number}}],    // for stock_add ("50 kilo cheeni aayi")
 "question": string or null,        // for query: questions about the shop (dues, sales, stock)
 "notes": string                    // short note on anything unclear
}}
Rules: quantities are in the item's unit ("aadha kilo" = 0.5, "dhai" = 2.5, "pav" = 0.25 kg).
If the shopkeeper says an amount in rupees instead of quantity ("50 ka jeera"), set qty = amount / price.
Only use item_ids from the catalog. If an item cannot be matched, mention it in notes.

Command: "{text}"
"""


def catalog_text(items):
    return "\n".join(f"{i['id']} | {i['name']} | {i['name_hi']} | {i['aliases']} | {i['unit']} | {i['price']}"
                     for i in items)


def parse_command(text, items, customers):
    plan = None
    if available():
        out = gemini(PARSE_PROMPT.format(catalog=catalog_text(items),
                                         customers=", ".join(c["name"] for c in customers) or "none",
                                         text=text.replace('"', "'")), json_mode=True, fast=True)
        plan = _json(out)
        if plan:
            plan["source"] = "gemini"
    if not plan:
        plan = rule_parse(text, items, customers)
        plan["source"] = "rules"
    return clean_plan(plan, items)


def clean_plan(plan, items):
    ids = {i["id"] for i in items}
    plan.setdefault("intent", "bill")
    plan.setdefault("customer", None)
    plan["udhaar"] = bool(plan.get("udhaar"))
    for key in ("items", "price_updates", "stock_updates"):
        clean = []
        for x in plan.get(key) or []:
            try:
                iid = int(x.get("item_id"))
                val = float(x.get("qty", x.get("price", 0)) or 0)
            except (TypeError, ValueError):
                continue
            if iid in ids and val > 0:
                clean.append({"item_id": iid, ("price" if key == "price_updates" else "qty"): round(val, 3)})
        plan[key] = clean
    try:
        plan["amount"] = float(plan["amount"]) if plan.get("amount") else None
    except (TypeError, ValueError):
        plan["amount"] = None
    plan.setdefault("notes", "")
    return plan


# Simple offline parser used when there is no Gemini key or the API fails.
NUM_WORDS = {"aadha": 0.5, "आधा": 0.5, "pav": 0.25, "पाव": 0.25, "dhai": 2.5, "ढाई": 2.5, "dedh": 1.5, "डेढ़": 1.5,
             "ek": 1, "एक": 1, "do": 2, "दो": 2, "teen": 3, "तीन": 3, "char": 4, "चार": 4, "paanch": 5, "पांच": 5,
             "panch": 5, "das": 10, "दस": 10, "bees": 20, "बीस": 20, "pachas": 50, "पचास": 50}
UDHAAR_WORDS = ["udhaar", "udhar", "उधार", "khata", "खाता", "likh", "लिख", "baad me", "बाद में"]
PAY_WORDS = ["jama", "जमा", "diye", "दिए", "दिये", "paid", "chukaya", "चुकाया", "de gaye", "de gaya"]
PRICE_WORDS = ["rate", "price", "bhav", "भाव", "दाम", "daam", "ab ", "अब "]
STOCK_WORDS = ["aaya", "aayi", "aaye", "आया", "आई", "आए", "stock add", "maal aaya", "माल"]
QUERY_WORDS = ["?", "kaun", "कौन", "kitna", "कितना", "kitne", "कितने", "kya", "क्या", "who", "how", "which",
               "what", "sabse", "सबसे", "batao", "बताओ"]


def _numbers_before(text, pos, start=0):
    window = text[max(start, pos - 25):pos]
    nums = re.findall(r"(\d+(?:\.\d+)?)", window)
    if nums:
        return float(nums[-1])
    for w, v in NUM_WORDS.items():
        if re.search(r"(^|\s)" + re.escape(w) + r"(\s|$)", window):
            return v
    return None


def rule_parse(text, items, customers):
    t = " " + text.lower().strip() + " "
    plan = {"intent": "bill", "customer": None, "udhaar": any(w in t for w in UDHAAR_WORDS),
            "items": [], "amount": None, "price_updates": [], "stock_updates": [], "question": None, "notes": ""}
    for c in customers:
        first = c["name"].lower().split()[0]
        if c["name"].lower() in t or re.search(r"\b" + re.escape(first) + r"\b", t):
            plan["customer"] = c["name"]
            break
    found = []
    for it in items:
        names = [it["name"].lower(), (it["name_hi"] or "").lower()] + [a.strip().lower() for a in (it["aliases"] or "").split(",")]
        best = None
        for n in sorted(set(filter(None, names)), key=len, reverse=True):
            idx = t.find(n)
            if idx >= 0 and (best is None or len(n) > best[1]):
                best = (idx, len(n))
        if best:
            found.append((best[0], best[1], it))
    # keep longest non-overlapping matches ("fortune tel" beats "tel")
    found.sort(key=lambda f: -f[1])
    taken, matches = [], []
    for idx, ln, it in found:
        if all(idx + ln <= a or idx >= a + b for a, b in taken):
            taken.append((idx, ln))
            matches.append((idx, ln, it))
    matches.sort(key=lambda m: m[0])
    # each item's quantity is searched only between the previous item and this one
    prev_end, bounded = 0, []
    for idx, ln, it in matches:
        bounded.append((idx, prev_end, it))
        prev_end = idx + ln
    matches = [(idx, it) for idx, _, it in bounded]
    starts = {it["id"]: st for _, st, it in bounded}

    is_query = any(w in t for w in QUERY_WORDS) and not matches
    if is_query:
        plan["intent"] = "query"
        plan["question"] = text
        return plan
    if any(w in t for w in PAY_WORDS) and plan["customer"]:
        nums = re.findall(r"(\d+(?:\.\d+)?)", t)
        plan["intent"] = "payment"
        plan["amount"] = float(nums[-1]) if nums else None
        return plan
    if matches and any(w in t for w in STOCK_WORDS):
        plan["intent"] = "stock_add"
        plan["stock_updates"] = [{"item_id": it["id"], "qty": _numbers_before(t, idx, starts[it["id"]]) or 1} for idx, it in matches]
        return plan
    if matches and any(w in t for w in PRICE_WORDS):
        plan["intent"] = "price_update"
        for idx, it in matches:
            after = re.findall(r"(\d+(?:\.\d+)?)", t[idx:idx + 40])
            if after:
                plan["price_updates"].append({"item_id": it["id"], "price": float(after[0])})
        return plan
    for idx, it in matches:
        plan["items"].append({"item_id": it["id"], "qty": _numbers_before(t, idx, starts[it["id"]]) or 1})
    if not matches:
        plan["notes"] = "No items recognised. Try naming the item, e.g. '2 kilo cheeni'."
    return plan


# ---------------------------------------------------------------- insights

def answer_question(question, context, lang="en"):
    prompt = (f"You are Dukaan Saathi, assistant to a kirana shop owner. Answer the question using ONLY the shop "
              f"data below. Amounts are in rupees (₹). Be short and practical (max 6 lines). "
              f"Reply in {'simple Hindi (Devanagari)' if lang == 'hi' else 'simple English'}.\n\n"
              f"SHOP DATA:\n{context}\n\nQUESTION: {question}")
    return gemini(prompt)


def deadstock_advice(dead_items, lang="en"):
    if not dead_items:
        return None
    lines = "\n".join(f"- {d['name']}: {d['stock']} {d['unit']} in stock, MRP ₹{d['price']}, cost ₹{d['cost_price']}, "
                      f"{d['days']} days since last sale" for d in dead_items)
    prompt = ("These items are not selling in a small village kirana shop in Rajasthan. For each, suggest one "
              "practical action (small discount that stays above cost, combo with a fast-moving item, display "
              "change, or stop reordering). One line per item, max 18 words each. "
              f"Reply in {'Hindi' if lang == 'hi' else 'English'}.\n{lines}")
    return gemini(prompt)


def market_news(lang="en"):
    prompt = ("Give a short market update for a small grocery (kirana) shop owner in Rajasthan, India: 4-5 bullet "
              "points on recent price trends or news for sugar, wheat/atta, edible oil, pulses (dal), and anything "
              "affecting FMCG supply. Each bullet max 20 words, with the direction (up/down/stable) and the date "
              "or week if known. End with one line of buying advice. "
              f"Reply in {'Hindi' if lang == 'hi' else 'English'}.")
    return gemini(prompt, search=True)


COLLECTIONS_PROMPT = """You are the collections agent of {shop}, a small kirana (grocery) shop in a Rajasthan village.
Customers buy on udhaar (credit) and the owner finds it awkward to ask for money. You decide, for each customer
below, whether to nudge them today and write the message the owner will send. Be warm and respectful; these
are neighbours, not debtors.

Policy:
- action "wait": balance under ₹{min_balance}, OR paid something in the last {paid_days} days, OR nudged in the last {nudge_days} days.
- action "remind": a PayPal invoice is already open (open_invoice=true) -> PayPal re-sends it; write a short friendly follow-up.
- action "invoice": no open invoice -> a new PayPal invoice with a pay link will be created and your message goes on it.
- priority 1 = overdue 30+ days or balance ₹3000+, 2 = overdue 14+ days, 3 = otherwise.
- message: max 2 short lines, address them by first name + "ji", state the amount in ₹ and roughly how long it has
  been pending, say a PayPal link follows, thank them. {language}. Empty string for "wait".
- reason: one short line, in English, for the owner.

Customers (JSON): {rows}

Return ONLY a JSON array: [{{"customer_id": int, "action": "invoice"|"remind"|"wait", "priority": 1|2|3,
"reason": string, "message": string}}]
"""


def collections_plan(rows, lang="en", shop_name="Dukaan Saathi"):
    """Returns a list of actions, or None when the model is unavailable (caller uses the rule plan)."""
    if not rows or not available():
        return None
    slim = [{k: r[k] for k in ("customer_id", "name", "balance", "days_overdue", "days_since_payment",
                                "reminders_sent", "days_since_nudge", "invoice_age_days")} | {"open_invoice": bool(r["open_invoice"])}
            for r in rows]
    language = ("Write the message in simple Hindi (Devanagari script)" if lang == "hi"
                else "Write the message in Hinglish (Hindi words in Roman script, like a WhatsApp message)")
    out = gemini(COLLECTIONS_PROMPT.format(shop=shop_name, min_balance=100, paid_days=7, nudge_days=3,
                                           language=language, rows=json.dumps(slim, ensure_ascii=False)),
                 json_mode=True, max_tokens=4096)
    if not out:
        return None
    m = re.search(r"\[.*\]", out, re.S)
    try:
        plan = json.loads(m.group(0) if m else out)
        return plan if isinstance(plan, list) else None
    except Exception:
        return None


def market_price(item):
    prompt = (f"What is the current typical wholesale and retail price in India (preferably Rajasthan) for "
              f"'{item['name']}' per {item['unit']}? Reply in at most 2 short lines, with rupee ranges and the "
              f"source/date if known. Say clearly if you are unsure.")
    return gemini(prompt, search=True)
