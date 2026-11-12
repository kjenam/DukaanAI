/* Dukaan Saathi front end: plain JS, no build step. AG Grid + Chart.js are loaded lazily from CDNs. */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const rs = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });
const usd = (n) => "$" + Number(n || 0).toFixed(2);
const when = (iso) => (iso || "").slice(0, 16).replace("T", " ");

let LANG = localStorage.getItem("lang") || "en";
let MIC_LANG = localStorage.getItem("micLang") || "hi-IN";
let STATE = null;
let COLLECT = null;
const DESKTOP = window.matchMedia("(min-width: 1024px)");
const CDN = {
  agGrid: "https://cdn.jsdelivr.net/npm/ag-grid-community@33.3.2/dist/ag-grid-community.min.js",
  chart: "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js",
};

const T = {
  en: {
    todaySales: "Today's sales", udhaarTotal: "Udhaar outstanding", ppCollected: "Collected via PayPal", lowStock: "Low stock items",
    speakOrType: "Speak or type (Hindi / Hinglish / English)", go: "Go", recentBills: "Recent bills", khata: "Khata (udhaar)",
    lowStockAlerts: "Low stock alerts", deadstock: "Deadstock", aiTips: "✨ AI tips", allItems: "All items & prices",
    gridHint: "Double-click price, stock or alert level to edit", reorderTitle: "Smart reorder (AI agent)",
    reorderHelp: "The agent checks low stock and recent sales, drafts an order per supplier, and pays through PayPal only after you approve.",
    checkStock: "Check stock & draft orders", askShop: "Ask your shop", ask: "Ask", marketNews: "Market news", refresh: "Refresh",
    demo: "Demo tools", resetDemo: "Reset demo data", tabBill: "Bill", tabKhata: "Khata", tabCollect: "Collect", tabStock: "Stock",
    tabReorder: "Reorder", tabInsights: "Insights", micLang: "Mic: Hindi", micLangEn: "Mic: English", confirmBill: "Save bill",
    cash: "Cash", udhaar: "Udhaar", customer: "Customer", total: "Total", cancel: "Cancel", saved: "Saved", sendInvoice: "Send PayPal invoice",
    sync: "Sync status", recordCash: "Record cash payment", openLink: "Open pay link", balance: "Balance", addPayment: "Cash received",
    noBills: "No bills yet today. Try the mic!", approvePay: "Approve & pay with PayPal", listening: "Listening…",
    noLow: "All good, nothing is running low.", noDead: "No deadstock.", confirm: "Confirm", paid: "Paid",
    noMic: "Voice needs Chrome on Android or desktop. You can type instead.", payment: "Payment received",
    priceUpdate: "Update prices", stockAdd: "Add stock", aiAnswer: "Answer", noItems: "No items recognised.", save: "Save",
    trend: "Last 14 days", trendSub: "sales · udhaar given · collected", history: "Past runs",
    collectTitle: "AI collections agent · वसूली",
    collectHelp: "Reads every open khata, decides who to nudge today, writes a polite message, and uses PayPal invoices and reminders. Nothing is sent until you approve.",
    collectNote: "PayPal reminder emails use PayPal's standard text. The AI message appears on new invoices and in the WhatsApp link.",
    runAgent: "Run collections agent", runAgentShort: "Collections agent", approveAll: "Approve all & send", approve: "Approve & send",
    skip: "Skip", whatsapp: "WhatsApp", payLink: "Pay link", sent: "Sent", failed: "Failed", skipped: "Skipped", waiting: "Wait",
    proposed: "Awaiting approval", agentThinking: "Agent is reviewing the khata…", noCollect: "Nobody owes anything right now. Nice!",
    overdue: "days overdue", newInvoice: "New PayPal invoice", reminder: "PayPal reminder", understoodBy: "Understood by",
    editItem: "Edit item", price: "Price", stock: "Stock", alertAt: "Alert at", cashIn: "Cash received (₹)", resetQ: "Reset all demo data?",
    runFirst: "Run the agent to get today's to-do list.", retry: "Retry",
  },
  hi: {
    todaySales: "आज की बिक्री", udhaarTotal: "कुल उधार बाकी", ppCollected: "PayPal से वसूली", lowStock: "कम स्टॉक",
    speakOrType: "बोलिए या लिखिए (हिंदी / हिंग्लिश / English)", go: "चलो", recentBills: "हाल के बिल", khata: "खाता (उधार)",
    lowStockAlerts: "कम स्टॉक", deadstock: "न बिकने वाला माल", aiTips: "✨ AI सुझाव", allItems: "सारा सामान और भाव",
    gridHint: "भाव, स्टॉक या अलर्ट बदलने के लिए डबल-क्लिक करें", reorderTitle: "स्मार्ट ऑर्डर (AI एजेंट)",
    reorderHelp: "एजेंट कम स्टॉक और बिक्री देखकर हर सप्लायर का ऑर्डर बनाता है। आपकी मंज़ूरी के बाद ही PayPal से भुगतान होता है।",
    checkStock: "स्टॉक जांचें और ऑर्डर बनाएं", askShop: "दुकान से पूछें", ask: "पूछें", marketNews: "बाज़ार की खबर", refresh: "ताज़ा करें",
    demo: "डेमो", resetDemo: "डेमो डेटा रीसेट", tabBill: "बिल", tabKhata: "खाता", tabCollect: "वसूली", tabStock: "स्टॉक",
    tabReorder: "ऑर्डर", tabInsights: "जानकारी", micLang: "माइक: हिंदी", micLangEn: "माइक: English", confirmBill: "बिल सेव करें",
    cash: "नकद", udhaar: "उधार", customer: "ग्राहक", total: "कुल", cancel: "रद्द", saved: "सेव हो गया", sendInvoice: "PayPal इनवॉइस भेजें",
    sync: "स्टेटस जांचें", recordCash: "नकद भुगतान दर्ज करें", openLink: "भुगतान लिंक", balance: "बाकी", addPayment: "नकद मिला",
    noBills: "आज अभी कोई बिल नहीं। माइक दबाइए!", approvePay: "मंज़ूर करें, PayPal से भुगतान", listening: "सुन रहा हूँ…",
    noLow: "सब ठीक है, कुछ भी कम नहीं।", noDead: "कोई पड़ा हुआ माल नहीं।", confirm: "पक्का करें", paid: "भुगतान हो गया",
    noMic: "आवाज़ के लिए Android/कंप्यूटर पर Chrome चाहिए। आप लिख भी सकते हैं।", payment: "भुगतान मिला",
    priceUpdate: "भाव बदलें", stockAdd: "स्टॉक जोड़ें", aiAnswer: "जवाब", noItems: "कोई सामान नहीं पहचाना।", save: "सेव",
    trend: "पिछले 14 दिन", trendSub: "बिक्री · उधार दिया · वसूली", history: "पिछली बार",
    collectTitle: "AI वसूली एजेंट",
    collectHelp: "हर खुला खाता देखता है, तय करता है आज किसे याद दिलाना है, विनम्र संदेश लिखता है और PayPal इनवॉइस/रिमाइंडर भेजता है। आपकी मंज़ूरी के बिना कुछ नहीं जाता।",
    collectNote: "PayPal रिमाइंडर ईमेल PayPal के मानक शब्दों में जाता है। AI का संदेश नए इनवॉइस और WhatsApp लिंक में दिखता है।",
    runAgent: "वसूली एजेंट चलाएं", runAgentShort: "वसूली एजेंट", approveAll: "सब मंज़ूर करें और भेजें", approve: "मंज़ूर करें और भेजें",
    skip: "छोड़ें", whatsapp: "WhatsApp", payLink: "भुगतान लिंक", sent: "भेज दिया", failed: "असफल", skipped: "छोड़ा", waiting: "रुकें",
    proposed: "मंज़ूरी बाकी", agentThinking: "एजेंट खाता देख रहा है…", noCollect: "अभी किसी का उधार बाकी नहीं। बढ़िया!",
    overdue: "दिन से बाकी", newInvoice: "नया PayPal इनवॉइस", reminder: "PayPal रिमाइंडर", understoodBy: "समझा",
    editItem: "सामान बदलें", price: "भाव", stock: "स्टॉक", alertAt: "अलर्ट", cashIn: "नकद मिला (₹)", resetQ: "सारा डेमो डेटा रीसेट करें?",
    runFirst: "आज की सूची के लिए एजेंट चलाएं।", retry: "फिर से",
  },
};
const t = (k) => (T[LANG] && T[LANG][k]) || T.en[k] || k;
const itemName = (it) => (LANG === "hi" && it.name_hi ? `${it.name_hi} · ${it.name}` : it.name);

function applyLang() {
  document.documentElement.lang = LANG;
  $$("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
  $("#micLangBtn").textContent = MIC_LANG === "hi-IN" ? t("micLang") : t("micLangEn");
  $("#micLang").textContent = MIC_LANG === "hi-IN" ? "हिं" : "EN";
  $("#topDate").textContent = new Date().toLocaleDateString(LANG === "hi" ? "hi-IN" : "en-IN", { weekday: "long", day: "numeric", month: "long" });
  if (STATE) renderAll();
  if (COLLECT) renderCollections();
}

function toast(msg, isErr = false) {
  const el = $("#toast");
  el.textContent = msg;
  el.className = "toast" + (isErr ? " err" : "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.add("hidden"), isErr ? 6000 : 3000);
}

async function api(path, body, method) {
  const opts = { method: method || (body ? "POST" : "GET"), headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `Request failed (${r.status})`);
  return data;
}

async function busy(btn, fn) {
  const old = btn ? btn.innerHTML : "";
  if (btn) { btn.disabled = true; btn.innerHTML = "…"; }
  try { return await fn(); } catch (e) { toast(e.message, true); } finally { if (btn) { btn.disabled = false; btn.innerHTML = old; } }
}

const _scripts = {};
function loadScript(src) {
  if (!_scripts[src]) _scripts[src] = new Promise((res, rej) => {
    const s = document.createElement("script"); s.src = src; s.onload = res; s.onerror = () => rej(new Error("Could not load " + src));
    document.head.appendChild(s);
  });
  return _scripts[src];
}

// ------------------------------------------------------------------ modal (replaces prompt/confirm)
function openModal({ title, body, ok = t("save"), danger = false, onOk }) {
  const m = $("#modal");
  m.innerHTML = `<div class="modal" role="dialog" aria-modal="true"><h3>${esc(title)}</h3><div class="mbody">${body}</div>
    <div class="row gap" style="margin-top:14px"><button class="btn ${danger ? "danger" : "primary"} grow" id="mOk">${esc(ok)}</button><button class="btn" id="mNo">${t("cancel")}</button></div></div>`;
  m.classList.remove("hidden");
  const close = () => m.classList.add("hidden");
  $("#mNo").onclick = close;
  m.onclick = (e) => { if (e.target === m) close(); };
  $("#mOk").onclick = () => busy($("#mOk"), async () => { await onOk(m); close(); });
  const first = $("input, textarea", m); if (first) { first.focus(); first.select && first.select(); }
  m.onkeydown = (e) => { if (e.key === "Enter" && e.target.tagName !== "TEXTAREA") $("#mOk").click(); if (e.key === "Escape") close(); };
}
const field = (id, label, value, type = "number") =>
  `<div class="field"><label class="lbl" for="${id}">${esc(label)}</label><input id="${id}" class="input" type="${type}" step="any" value="${esc(value)}"></div>`;

// ------------------------------------------------------------------ state + render
async function refresh() {
  STATE = await api("/api/state");
  renderAll();
}

function renderAll() {
  const s = STATE;
  $("#statSales").textContent = rs(s.today.sales);
  $("#statUdhaar").textContent = rs(s.udhaar_total);
  $("#statPP").textContent = rs(s.paypal_collected);
  $("#statLow").textContent = s.low_stock.length;
  $("#statLowWrap").classList.toggle("on", s.low_stock.length > 0);
  $("#collectPill").textContent = s.to_approve;
  $("#collectPill").classList.toggle("hidden", !s.to_approve);
  const warn = [];
  if (!s.ai) warn.push("AI off: add GEMINI_API_KEY (using the basic offline parser)");
  if (!s.paypal) warn.push("PayPal off: add PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET");
  $("#statusBar").textContent = warn.join(" · ");
  $("#statusBar").classList.toggle("hidden", !warn.length);
  const sys = `AI: ${s.ai ? "Gemini ✓" : "off"} · PayPal sandbox: ${s.paypal ? "✓" : "off"} · ₹${window.CONFIG.inrPerUsd} = $1`;
  $("#sysInfo").textContent = sys; $("#sysInfo2").textContent = sys;
  renderRecent(); renderCustomers(); renderStock(); renderPOs(s.pos);
}

function renderRecent() {
  const el = $("#recentBills");
  if (!STATE.recent_bills.length) { el.innerHTML = `<p class="muted">${t("noBills")}</p>`; return; }
  el.innerHTML = STATE.recent_bills.map((b) => `
    <div class="li"><div><div class="t">#${b.id} ${esc(b.customer || t("cash"))}</div>
      <div class="s">${esc(b.raw_text || "")} · ${when(b.created_at).slice(5)}</div></div>
      <div style="text-align:right"><div class="amt">${rs(b.total)}</div>
      <span class="badge ${b.mode === "udhaar" ? "amber" : "green"}">${t(b.mode)}</span></div></div>`).join("");
}

function useGrid() { return DESKTOP.matches && window.DukaanGrids; }

function renderCustomers() {
  const q = ($("#custSearch").value || "").toLowerCase();
  if (useGrid()) {
    DukaanGrids.ensure("customers", $("#custGrid"), { open: openCustomer });
    DukaanGrids.setRows("customers", STATE.customers);
    DukaanGrids.setFilter("customers", q);
  }
  const list = STATE.customers.filter((c) => c.name.toLowerCase().includes(q));
  $("#custList").innerHTML = list.map((c) => {
    const inv = c.last_invoice;
    const badge = inv ? `<span class="badge ${["PAID", "MARKED_AS_PAID"].includes(inv.status) ? "green" : "blue"}">PayPal ${esc(inv.status)}</span>` : "";
    return `<div class="li click" data-cid="${c.id}"><div><div class="t">${esc(c.name)}</div><div class="s">${esc(c.phone || "")} ${badge}</div></div>
      <div class="amt ${c.balance > 0 ? "due" : "ok"}">${rs(c.balance)}</div></div>`;
  }).join("");
  $$("#custList .li").forEach((li) => li.addEventListener("click", () => openCustomer(+li.dataset.cid)));
}

function renderStock() {
  const s = STATE;
  $("#lowList").innerHTML = s.low_stock.length ? s.low_stock.map((i) => `
    <div class="li"><div><div class="t">${esc(itemName(i))}</div><div class="s">${i.stock} ${esc(i.unit)} left · alert at ${i.threshold}</div></div>
    <span class="badge ${i.stock <= i.threshold / 2 ? "red" : "amber"}">${i.stock <= i.threshold / 2 ? "very low" : "low"}</span></div>`).join("")
    + `<button class="btn sm primary" style="margin-top:10px" onclick="goTab('reorder')">🚚 ${t("checkStock")}</button>`
    : `<p class="muted">${t("noLow")}</p>`;
  $("#deadList").innerHTML = s.deadstock.length ? s.deadstock.map((i) => `
    <div class="li"><div><div class="t">${esc(itemName(i))}</div><div class="s">${i.stock} ${esc(i.unit)} · ${i.days >= 999 ? "never sold" : i.days + " days since last sale"}</div></div>
    <div class="amt">${rs(i.value)}</div></div>`).join("") : `<p class="muted">${t("noDead")}</p>`;
  renderItems();
}

function renderItems() {
  const q = ($("#itemSearch").value || "").toLowerCase();
  if (useGrid()) {
    const dead = new Set(STATE.deadstock.map((d) => d.id));
    DukaanGrids.ensure("items", $("#itemGrid"), {
      isDead: (id) => dead.has(id), market: (id) => marketPriceModal(id),
      edit: async (id, patch) => { try { await api(`/api/items/${id}`, patch); toast(t("saved")); await refresh(); } catch (e) { toast(e.message, true); } },
    });
    DukaanGrids.setRows("items", STATE.items);
    DukaanGrids.setFilter("items", q);
  }
  const list = STATE.items.filter((i) => (i.name + " " + i.name_hi + " " + i.aliases).toLowerCase().includes(q));
  $("#itemList").innerHTML = list.map((i) => `
    <div class="li"><div class="grow"><div class="t">${esc(itemName(i))}</div>
      <div class="s">${i.stock} ${esc(i.unit)} in stock · cost ${rs(i.cost_price)}</div>
      <div class="s" id="mk-${i.id}"></div></div>
      <div style="text-align:right"><div class="amt">${rs(i.price)}/${esc(i.unit)}</div>
      <button class="chip small" data-edit="${i.id}">✏️</button> <button class="chip small" data-mk="${i.id}">📈</button></div></div>`).join("");
  $$("#itemList [data-edit]").forEach((b) => b.addEventListener("click", () => editItem(+b.dataset.edit)));
  $$("#itemList [data-mk]").forEach((b) => b.addEventListener("click", () => marketPrice(+b.dataset.mk, b)));
}

function editItem(id) {
  const it = STATE.items.find((x) => x.id === id);
  openModal({
    title: `${t("editItem")}: ${it.name}`,
    body: field("fPrice", `${t("price")} (₹ / ${it.unit})`, it.price) + field("fStock", `${t("stock")} (${it.unit})`, it.stock) + field("fTh", t("alertAt"), it.threshold),
    onOk: async () => { await api(`/api/items/${id}`, { price: +$("#fPrice").value, stock: +$("#fStock").value, threshold: +$("#fTh").value }); toast(t("saved")); await refresh(); },
  });
}

async function marketInfo(id) {
  const [m, h] = await Promise.all([api(`/api/items/${id}/market`), api(`/api/items/${id}/history`)]);
  const hist = h.slice(-4).map((x) => `${rs(x.price)} (${x.created_at.slice(5, 10)})`).join(" → ");
  return `<div class="ai-box">${esc(m.content)}<div class="src">Your price history: ${esc(hist)} · AI web estimate, verify before buying</div></div>`;
}
async function marketPrice(id, btn) {
  await busy(btn, async () => { $(`#mk-${id}`).innerHTML = await marketInfo(id); });
}
function marketPriceModal(id) {
  const it = STATE.items.find((x) => x.id === id);
  openModal({ title: `📈 ${it.name}`, body: `<div class="thinking"><div class="spinner"></div><span class="muted">Checking market price…</span></div>`, ok: "OK", onOk: async () => {} });
  marketInfo(id).then((html) => { const b = $("#modal .mbody"); if (b) b.innerHTML = html; }).catch((e) => toast(e.message, true));
}

// ------------------------------------------------------------------ voice
let recog = null;
function setupMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  $("#micBtn").addEventListener("click", () => {
    if (!SR) { toast(t("noMic"), true); return; }
    if (recog) { recog.stop(); return; }
    recog = new SR();
    recog.lang = MIC_LANG;
    recog.interimResults = true;
    recog.continuous = false;
    const btn = $("#micBtn");
    btn.classList.add("listening");
    $("#cmd").placeholder = t("listening");
    let finalText = "";
    recog.onresult = (e) => {
      let interim = "";
      for (const r of e.results) (r.isFinal ? (finalText = r[0].transcript) : (interim += r[0].transcript));
      $("#cmd").value = finalText || interim;
    };
    recog.onerror = (e) => toast("Mic: " + e.error, true);
    recog.onend = () => {
      btn.classList.remove("listening"); recog = null;
      if ($("#cmd").value.trim()) runCommand();
    };
    recog.start();
  });
  $("#micLangBtn").addEventListener("click", () => {
    MIC_LANG = MIC_LANG === "hi-IN" ? "en-IN" : "hi-IN";
    localStorage.setItem("micLang", MIC_LANG);
    applyLang();
  });
}

// ------------------------------------------------------------------ command → preview → confirm
async function runCommand() {
  const text = $("#cmd").value.trim();
  if (!text) return;
  const box = $("#preview");
  box.innerHTML = `<div class="card preview thinking"><div class="spinner"></div><div><div class="t">${LANG === "hi" ? "समझ रहा हूँ…" : "Understanding…"}</div><div class="s muted">${esc(text)}</div></div></div>`;
  const t0 = performance.now();
  await busy($("#goBtn"), async () => {
    try {
      const res = await api("/api/parse", { text, lang: LANG });
      res.ms = Math.round(performance.now() - t0);
      renderPreview(res);
    } catch (e) { box.innerHTML = ""; throw e; }
  });
}

function renderPreview(res) {
  const p = res.plan;
  const box = $("#preview");
  const src = `<div class="src">${t("understoodBy")} ${p.source === "gemini" ? "Gemini AI" : "offline parser"}${res.ms ? ` · ${(res.ms / 1000).toFixed(1)} s` : ""}${p.notes ? " · " + esc(p.notes) : ""}</div>`;
  if (res.answer) {
    box.innerHTML = `<div class="card preview"><h3>💬 ${t("aiAnswer")}</h3><div class="ai-box">${esc(res.answer)}</div>${src}</div>`;
    return;
  }
  if (p.intent === "payment") {
    box.innerHTML = `<div class="card preview"><h3>💰 ${t("payment")}</h3>
      <label class="lbl">${t("customer")}</label><input id="pvCust" class="input" value="${esc(p.customer || "")}">
      <label class="lbl" style="margin-top:8px">₹</label><input id="pvAmt" class="input" type="number" value="${p.amount || ""}">
      <div class="row gap" style="margin-top:12px"><button class="btn primary grow" id="pvOk">${t("confirm")}</button><button class="btn" id="pvNo">${t("cancel")}</button></div>${src}</div>`;
    $("#pvOk").onclick = () => busy($("#pvOk"), async () => {
      const r = await api("/api/payments", { customer: $("#pvCust").value, amount: +$("#pvAmt").value });
      toast(`${r.customer}: ${t("balance")} ${rs(r.balance)}`); doneCommand();
    });
  } else if (p.intent === "price_update" || p.intent === "stock_add") {
    const isPrice = p.intent === "price_update";
    const lines = isPrice ? p.price_updates : p.stock_updates;
    if (!lines.length) { box.innerHTML = `<div class="card preview"><p>${t("noItems")}</p>${src}</div>`; return; }
    box.innerHTML = `<div class="card preview"><h3>${isPrice ? "🏷️ " + t("priceUpdate") : "📦 " + t("stockAdd")}</h3><table>
      ${lines.map((l, i) => `<tr><td>${esc(itemName(l))}<div class="s muted">${isPrice ? "now " + rs(l.old_price) : "in stock " + l.stock + " " + esc(l.unit)}</div></td>
        <td class="num"><input class="qty" data-i="${i}" type="number" step="any" value="${isPrice ? l.price : l.qty}"> ${isPrice ? "₹" : esc(l.unit)}</td></tr>`).join("")}
      </table><div class="row gap"><button class="btn primary grow" id="pvOk">${t("confirm")}</button><button class="btn" id="pvNo">${t("cancel")}</button></div>${src}</div>`;
    $("#pvOk").onclick = () => busy($("#pvOk"), async () => {
      const updates = lines.map((l, i) => ({ item_id: l.item_id, [isPrice ? "price" : "qty"]: +$(`.qty[data-i="${i}"]`).value }));
      await api(isPrice ? "/api/prices" : "/api/stock", { updates });
      toast(t("saved")); doneCommand();
    });
  } else {
    if (!p.items.length) { box.innerHTML = `<div class="card preview"><p>${t("noItems")}</p>${src}</div>`; return; }
    let udhaar = !!p.udhaar;
    box.innerHTML = `<div class="card preview"><h3>🧾 ${t("tabBill")}</h3>
      <table>${p.items.map((l, i) => `<tr><td>${esc(itemName(l))}<div class="s muted">${rs(l.price)}/${esc(l.unit)}${l.qty > l.stock ? " · ⚠️ only " + l.stock + " in stock" : ""}</div></td>
        <td class="num"><input class="qty" data-i="${i}" type="number" step="any" value="${l.qty}"></td>
        <td class="num" id="amt-${i}">${rs(l.amount)}</td></tr>`).join("")}</table>
      <div class="total-row"><span>${t("total")}</span><span id="pvTotal">${rs(p.total)}</span></div>
      <div class="row gap between wrap">
        <div class="toggle"><button id="mCash">${t("cash")}</button><button id="mUdhaar">${t("udhaar")}</button></div>
        <input id="pvCust" class="input grow" style="min-width:150px" placeholder="${t("customer")}" value="${esc(p.customer || "")}">
      </div>
      ${p.customer && p.customer_exists ? `<div class="s muted" style="margin-top:6px">${esc(p.customer)} · ${t("balance")} ${rs(p.customer_balance)}</div>` : ""}
      <div class="row gap" style="margin-top:12px"><button class="btn primary grow" id="pvOk">${t("confirmBill")}</button><button class="btn" id="pvNo">${t("cancel")}</button></div>${src}</div>`;
    const setMode = () => { $("#mCash").classList.toggle("on", !udhaar); $("#mUdhaar").classList.toggle("on", udhaar); };
    $("#mCash").onclick = () => { udhaar = false; setMode(); };
    $("#mUdhaar").onclick = () => { udhaar = true; setMode(); };
    setMode();
    const recalc = () => {
      let tot = 0;
      p.items.forEach((l, i) => { const a = +$(`.qty[data-i="${i}"]`).value * l.price; tot += a; $(`#amt-${i}`).textContent = rs(a); });
      $("#pvTotal").textContent = rs(tot);
    };
    $$(".preview .qty").forEach((q) => q.addEventListener("input", recalc));
    $("#pvOk").onclick = () => busy($("#pvOk"), async () => {
      const lines = p.items.map((l, i) => ({ item_id: l.item_id, qty: +$(`.qty[data-i="${i}"]`).value }));
      const r = await api("/api/bills", { lines, udhaar, customer: $("#pvCust").value, raw_text: p.raw_text });
      let msg = `${t("saved")} · #${r.bill_id} · ${rs(r.total)}`;
      if (r.mode === "udhaar") msg += ` · ${r.customer} ${t("balance")} ${rs(r.balance)}`;
      if (r.low_stock.length) msg += ` · ⚠️ ${t("lowStock")}: ${r.low_stock.join(", ")}`;
      toast(msg); doneCommand();
    });
  }
  const no = $("#pvNo"); if (no) no.onclick = () => (box.innerHTML = "");
}

async function doneCommand() {
  $("#preview").innerHTML = "";
  $("#cmd").value = "";
  await refresh();
}

// ------------------------------------------------------------------ khata detail + PayPal invoice
async function openCustomer(cid) {
  goTab("khata");
  const c = await api(`/api/customers/${cid}`);
  const box = $("#custDetail");
  const open = c.invoices.find((i) => !["PAID", "MARKED_AS_PAID", "CANCELLED"].includes(i.status));
  box.innerHTML = `<div class="card preview">
    <div class="row between"><h3>${esc(c.name)} <span class="sub">${esc(c.phone || "")}</span></h3><div class="amt ${c.balance > 0 ? "due" : "ok"}" style="font-size:22px">${rs(c.balance)}</div></div>
    <label class="lbl">Email for PayPal invoice (optional; the demo buyer is used when empty)</label>
    <div class="row gap"><input id="cEmail" class="input grow" value="${esc(c.email || "")}" placeholder="buyer@personal.example.com"><button class="btn sm" id="cEmailSave">${t("save")}</button></div>
    <div class="pay-actions">
      ${c.balance > 0 && !open ? `<button class="btn paypal" id="cInvoice">${t("sendInvoice")} · ${usd(c.balance / window.CONFIG.inrPerUsd)}</button>` : ""}
      <button class="btn" id="cCash">💵 ${t("addPayment")}</button>
    </div>
    ${c.invoices.length ? `<h3 style="margin-top:14px">PayPal invoices</h3>` + c.invoices.map((i) => `
      <div class="li"><div><div class="t">${esc(i.paypal_id)}</div><div class="s">${rs(i.amount_inr)} = ${usd(i.amount_usd)} · ${when(i.created_at)}</div>
        <div class="pay-actions">
          ${i.pay_url ? `<a class="btn sm" href="${esc(i.pay_url)}" target="_blank" rel="noopener">${t("openLink")}</a>` : ""}
          ${!["PAID", "MARKED_AS_PAID", "CANCELLED"].includes(i.status) ? `<button class="btn sm" data-sync="${i.id}">🔄 ${t("sync")}</button><button class="btn sm warn" data-rec="${i.id}">💵 ${t("recordCash")}</button>` : ""}
        </div></div>
        <span class="badge ${["PAID", "MARKED_AS_PAID"].includes(i.status) ? "green" : "blue"}">${esc(i.status)}</span></div>`).join("") : ""}
    <h3 style="margin-top:14px">History</h3>
    ${c.entries.map((e) => `<div class="li"><div><div class="t">${esc(e.note || e.kind)}</div><div class="s">${when(e.created_at)}</div></div>
      <div class="amt ${e.kind === "credit" ? "due" : "ok"}">${e.kind === "credit" ? "+" : "−"}${rs(e.amount)}</div></div>`).join("")}
  </div>`;
  if (!DESKTOP.matches) box.scrollIntoView({ behavior: "smooth" });
  $("#cEmailSave").onclick = () => busy($("#cEmailSave"), async () => { await api(`/api/customers/${cid}`, { email: $("#cEmail").value }); toast(t("saved")); });
  const inv = $("#cInvoice");
  if (inv) inv.onclick = () => busy(inv, async () => {
    if ($("#cEmail").value !== (c.email || "")) await api(`/api/customers/${cid}`, { email: $("#cEmail").value });
    const r = await api(`/api/customers/${cid}/invoice`, {});
    toast(`PayPal invoice ${r.paypal_id} ${r.delivery === "link" ? "issued as a link" : "sent"} (${r.status})`);
    await refresh(); openCustomer(cid);
  });
  $("#cCash").onclick = () => openModal({
    title: `${c.name}: ${t("addPayment")}`, body: field("fCash", t("cashIn"), c.balance > 0 ? c.balance : ""), ok: t("confirm"),
    onOk: async () => { await api("/api/payments", { customer_id: cid, amount: +$("#fCash").value }); toast(t("saved")); await refresh(); openCustomer(cid); },
  });
  $$("[data-sync]", box).forEach((b) => (b.onclick = () => busy(b, async () => {
    const r = await api(`/api/invoices/${b.dataset.sync}/sync`, {});
    toast(`PayPal: ${r.status} · ${t("balance")} ${rs(r.balance)}`); await refresh(); openCustomer(cid);
  })));
  $$("[data-rec]", box).forEach((b) => (b.onclick = () => busy(b, async () => {
    const r = await api(`/api/invoices/${b.dataset.rec}/record-cash`, {});
    toast(`${t("paid")} · ${r.status} · ${t("balance")} ${rs(r.balance)}`); await refresh(); openCustomer(cid);
  })));
}

// ------------------------------------------------------------------ collections agent
async function loadCollections() {
  COLLECT = await api("/api/collections");
  renderCollections();
}

function actionCard(a) {
  const pr = { 1: "red", 2: "amber", 3: "blue" }[a.priority] || "blue";
  const kind = a.action === "invoice" ? t("newInvoice") : a.action === "remind" ? t("reminder") : t("waiting");
  const st = { proposed: `<span class="badge navy">${t("proposed")}</span>`, sent: `<span class="badge green">✓ ${t("sent")}</span>`,
    skipped: `<span class="badge">${t("skipped")}</span>`, failed: `<span class="badge red">${t("failed")}</span>` }[a.status];
  const canAct = a.status === "proposed" || a.status === "failed";
  return `<div class="act P${a.priority} ${a.status}" id="act-${a.id}">
    <div class="row between wrap gap">
      <div><b>${esc(a.customer)}</b> <span class="badge ${pr}">P${a.priority}</span> <span class="small muted">${a.days_overdue} ${t("overdue")}</span></div>
      <div class="row gap"><span class="amt due">${rs(a.balance)}</span>${st}</div>
    </div>
    <div class="reason">🤖 ${esc(a.reason || "")} <span class="badge blue" style="margin-left:4px">${kind}</span></div>
    ${a.error ? `<div class="reason" style="color:var(--red)">${esc(a.error)}</div>` : ""}
    ${a.action !== "wait" ? (canAct ? `<textarea class="msg input" data-msg="${a.id}">${esc(a.message)}</textarea>` : `<div class="ai-box" style="margin-top:8px;font-size:14px">${esc(a.message)}</div>`) : ""}
    <div class="acts">
      ${canAct && a.action !== "wait" ? `<button class="btn primary" data-approve="${a.id}">✅ ${a.status === "failed" ? t("retry") : t("approve")}</button><button class="btn ghost" data-skip="${a.id}">${t("skip")}</button>` : ""}
      ${a.status === "sent" && a.pay_url ? `<a class="btn sm" href="${esc(a.pay_url)}" target="_blank" rel="noopener">💳 ${t("payLink")}</a>` : ""}
      ${a.status === "sent" && a.wa_link ? `<a class="btn sm wa" href="${esc(a.wa_link)}" target="_blank" rel="noopener">💬 ${t("whatsapp")}</a>` : ""}
    </div></div>`;
}

function renderCollections() {
  const box = $("#collectBox"), run = COLLECT && COLLECT.run;
  const proposed = run ? run.actions.filter((a) => a.status === "proposed").length : 0;
  $("#collectAll").classList.toggle("hidden", proposed < 2);
  $("#collectSummary").textContent = run ? `${run.summary} · ${run.source === "gemini" ? "Gemini" : "rules"} · ${when(run.created_at)}` : "";
  if (!run) {
    box.innerHTML = `<div class="card"><p class="muted">${COLLECT && COLLECT.candidates === 0 ? t("noCollect") : t("runFirst")}</p></div>`;
  } else {
    const sent = run.actions.filter((a) => a.status === "sent");
    box.innerHTML = `<div class="card">
      <div class="kpi"><div><div class="k">${t("proposed")}</div><div class="v">${proposed}</div></div>
        <div><div class="k">${t("sent")}</div><div class="v">${sent.length}</div></div>
        <div><div class="k">${t("udhaarTotal")}</div><div class="v">${rs(run.actions.reduce((s, a) => s + a.balance, 0))}</div></div></div>
      ${run.actions.map(actionCard).join("")}</div>`;
    $$("[data-approve]", box).forEach((b) => (b.onclick = () => busy(b, async () => {
      const id = +b.dataset.approve, msg = ($(`[data-msg="${id}"]`) || {}).value;
      let r;
      try { r = await api(`/api/collections/${id}/approve`, msg !== undefined ? { message: msg } : {}); }
      catch (e) { await loadCollections(); throw e; }
      toast(r.action === "remind" ? "PayPal reminder sent ✓" : `PayPal invoice issued ✓`);
      await Promise.all([loadCollections(), refresh()]);
    })));
    $$("[data-skip]", box).forEach((b) => (b.onclick = () => busy(b, async () => { await api(`/api/collections/${b.dataset.skip}/skip`, {}); await loadCollections(); await refresh(); })));
  }
  $("#collectHistory").innerHTML = (COLLECT && COLLECT.history || []).map((h) => `
    <div class="li"><div><div class="t">${esc(h.summary || "")}</div><div class="s">${when(h.created_at)} · ${h.source === "gemini" ? "Gemini" : "rules"}</div></div>
      <span class="badge ${h.sent ? "green" : ""}">${h.sent || 0}/${h.total} ${t("sent").toLowerCase()}</span></div>`).join("") || `<p class="muted small">—</p>`;
}

async function runAgent() {
  const box = $("#collectBox");
  box.innerHTML = `<div class="card thinking"><div class="spinner"></div><div><div class="t">${t("agentThinking")}</div><div class="s muted">Gemini · khata · PayPal</div></div></div>`;
  await busy($("#collectRun"), async () => {
    const r = await api("/api/collections/plan", { lang: LANG });
    if (!r.run) { toast(r.message || t("noCollect")); }
    await Promise.all([loadCollections(), refresh()]);
  });
}

async function approveAll() {
  await busy($("#collectAll"), async () => {
    const r = await api("/api/collections/approve-all", {});
    toast(`${r.sent} sent${r.failed ? `, ${r.failed} failed` : ""}`, !!r.failed && !r.sent);
    await Promise.all([loadCollections(), refresh()]);
  });
}

// ------------------------------------------------------------------ agentic reorder
function renderPOs(pos) {
  const box = $("#poList");
  if (!pos || !pos.length) { box.innerHTML = ""; return; }
  Promise.all(pos.map((p) => api(`/api/po/${p.id}`))).then((full) => {
    box.innerHTML = full.map((po) => `
      <div class="card ${po.status === "draft" ? "preview" : ""}" id="po-${po.id}">
        <div class="row between"><h3>PO-${po.id} · ${esc(po.supplier)}</h3>
          <span class="badge ${po.status === "paid" ? "green" : "amber"}">${po.status === "paid" ? t("paid") : "awaiting approval"}</span></div>
        <div class="s muted">🤖 ${esc(po.note || "")}</div>
        <table style="width:100%;margin:8px 0">${po.lines.map((l) => `<tr><td>${esc(itemName(l))}</td>
          <td class="num">${po.status === "draft" ? `<input class="qty" data-line="${l.id}" type="number" value="${l.qty}">` : l.qty} ${esc(l.unit)}</td>
          <td class="num">${rs(l.amount)}</td></tr>`).join("")}</table>
        <div class="total-row"><span>${t("total")}</span><span>${rs(po.total_inr)} <span class="muted small">(${usd(po.total_usd)})</span></span></div>
        ${po.status === "draft" ? `<div class="row gap"><button class="btn sm" data-upd="${po.id}">Update qty</button><button class="btn sm ghost" data-cancel="${po.id}">${t("cancel")}</button></div>
          <div class="paypal-box" id="pp-${po.id}">${window.CONFIG.paypal ? "" : `<p class="muted small">Add PayPal keys to enable payment.</p>`}</div>`
        : `<div class="s muted">PayPal order ${esc(po.paypal_order_id || "")} · stock added</div>`}
      </div>`).join("");
    full.filter((po) => po.status === "draft").forEach(mountPayPal);
    $$("[data-upd]", box).forEach((b) => (b.onclick = () => busy(b, async () => {
      const card = $(`#po-${b.dataset.upd}`);
      const lines = $$("[data-line]", card).map((i) => ({ id: +i.dataset.line, qty: +i.value }));
      await api(`/api/po/${b.dataset.upd}/lines`, { lines }); await refresh();
    })));
    $$("[data-cancel]", box).forEach((b) => (b.onclick = () => busy(b, async () => { await api(`/api/po/${b.dataset.cancel}/cancel`, {}); await refresh(); })));
  });
}

function mountPayPal(po) {
  if (!window.paypal || !window.CONFIG.paypal) return;
  const el = $(`#pp-${po.id}`);
  if (!el) return;
  el.innerHTML = `<p class="small muted">✅ ${t("approvePay")}:</p>`;
  window.paypal.Buttons({
    style: { layout: "horizontal", tagline: false, height: 42 },
    createOrder: async () => (await api(`/api/po/${po.id}/paypal-order`, {})).id,
    onApprove: async (data) => {
      try {
        await api(`/api/po/${po.id}/capture`, { orderID: data.orderID });
        toast(`PO-${po.id}: ${t("paid")} ✓`);
        await refresh();
      } catch (e) { toast(e.message, true); }
    },
    onError: (e) => toast("PayPal: " + (e && e.message ? e.message : e), true),
  }).render(el);
}

// ------------------------------------------------------------------ insights
let CHART = null;
async function loadChart() {
  try {
    const [series] = await Promise.all([api("/api/insights/series?days=14"), loadScript(CDN.chart)]);
    const labels = series.map((d) => d.date.slice(5).replace("-", "/"));
    const ds = (label, key, color, fill) => ({ label, data: series.map((d) => d[key]), borderColor: color, backgroundColor: fill || color, tension: .35, borderWidth: 2.5, pointRadius: 2 });
    const cfg = { type: "line", data: { labels, datasets: [
      ds(LANG === "hi" ? "बिक्री" : "Sales", "sales", "#0070e0", "rgba(0,112,224,.12)"),
      ds(LANG === "hi" ? "उधार दिया" : "Udhaar given", "udhaar", "#b54708"),
      ds(LANG === "hi" ? "वसूली" : "Collected", "collected", "#118c4f") ] },
      options: { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
        plugins: { legend: { position: "bottom", labels: { boxWidth: 12, usePointStyle: true } }, tooltip: { callbacks: { label: (c) => ` ${c.dataset.label}: ${rs(c.parsed.y)}` } } },
        scales: { y: { beginAtZero: true, ticks: { callback: (v) => "₹" + (v >= 1000 ? (v / 1000) + "k" : v) }, grid: { color: "#eef2f7" } }, x: { grid: { display: false } } } } };
    cfg.data.datasets[0].fill = true;
    if (CHART) { CHART.data = cfg.data; CHART.update(); } else CHART = new Chart($("#salesChart"), cfg);
  } catch (e) { toast(e.message, true); }
}

async function loadNews(force) {
  $("#news").textContent = "…";
  try {
    const r = await api(`/api/insights/news?lang=${LANG}${force ? "&refresh=1" : ""}`);
    $("#news").innerHTML = esc(r.content) + (r.at ? `<div class="src">AI summary with web search · ${esc(when(r.at))} · verify before big purchases</div>` : "");
  } catch (e) { $("#news").textContent = e.message; }
}

async function askShop(q) {
  if (!q) return;
  $("#chatQ").value = q;
  await busy($("#chatBtn"), async () => {
    const r = await api("/api/chat", { q, lang: LANG });
    $("#chatA").textContent = r.answer;
    $("#chatA").classList.remove("hidden");
  });
}

function goTab(name) {
  $$(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  $$(".tab").forEach((s) => s.classList.toggle("active", s.id === "tab-" + name));
  if (!DESKTOP.matches) window.scrollTo(0, 0);
  if (name === "insights") { if ($("#news").textContent === "…") loadNews(false); loadChart(); }
  if (name === "collect" && !COLLECT) loadCollections().catch((e) => toast(e.message, true));
}
window.goTab = goTab;

// ------------------------------------------------------------------ wire up
document.addEventListener("DOMContentLoaded", async () => {
  $$(".tabs button").forEach((b) => b.addEventListener("click", () => goTab(b.dataset.tab)));
  const flip = () => { LANG = LANG === "en" ? "hi" : "en"; localStorage.setItem("lang", LANG); applyLang(); if (CHART) loadChart(); };
  $("#langBtn").onclick = flip; $("#langBtn2").onclick = flip;
  $("#goBtn").onclick = runCommand;
  $("#cmd").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); runCommand(); } });
  $$(".ex").forEach((x) => (x.onclick = () => { $("#cmd").value = x.textContent; runCommand(); }));
  $$(".exq").forEach((x) => (x.onclick = () => askShop(x.textContent)));
  $("#chatBtn").onclick = () => askShop($("#chatQ").value.trim());
  $("#chatQ").addEventListener("keydown", (e) => { if (e.key === "Enter") askShop($("#chatQ").value.trim()); });
  $("#custSearch").oninput = renderCustomers;
  $("#itemSearch").oninput = renderItems;
  $("#newsRefresh").onclick = () => loadNews(true);
  $("#collectRun").onclick = runAgent;
  $("#collectAll").onclick = approveAll;
  $("#deadRefresh").onclick = () => busy($("#deadRefresh"), async () => {
    const r = await api(`/api/insights/deadstock?lang=${LANG}&refresh=1`);
    $("#deadAdvice").textContent = r.advice || "Add GEMINI_API_KEY for AI suggestions.";
    $("#deadAdvice").classList.remove("hidden");
  });
  $("#suggestBtn").onclick = () => busy($("#suggestBtn"), async () => {
    const r = await api("/api/reorder/suggest", {});
    toast(r.pos.length ? `🤖 ${r.pos.length} draft order(s) ready for approval` : t("noLow"));
    await refresh();
  });
  $("#resetBtn").onclick = () => openModal({ title: t("resetDemo"), body: `<p>${t("resetQ")}</p>`, ok: t("confirm"), danger: true,
    onOk: async () => { await api("/api/reset", {}); location.reload(); } });
  setupMic();
  applyLang();
  // desktop: load AG Grid once, then render grids; phone: lists only
  const gridsReady = DESKTOP.matches ? loadScript(CDN.agGrid).then(() => loadScript("/static/grid.js")).catch((e) => console.warn(e)) : Promise.resolve();
  try { await Promise.all([refresh(), gridsReady]); if (DESKTOP.matches) renderAll(); } catch (e) { toast(e.message, true); }
  DESKTOP.addEventListener("change", () => location.reload());
});
