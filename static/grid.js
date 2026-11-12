/* AG Grid Community wrappers for the desktop dashboard. Loaded lazily by app.js after ag-grid-community. */
(function () {
  const apis = {};
  const theme = () => agGrid.themeQuartz.withParams({
    accentColor: "#0070e0", browserColorScheme: "light", fontFamily: "Inter, system-ui, sans-serif",
    headerBackgroundColor: "#f3f6fb", headerFontWeight: 700, borderRadius: 10, wrapperBorderRadius: 12, rowHoverColor: "#e8f3fc",
  });
  const inr = (p) => (p.value == null ? "" : "₹" + Number(p.value).toLocaleString("en-IN", { maximumFractionDigits: 2 }));
  const num = (p) => Number(p.newValue);
  const btn = (label, cls, onClick) => {
    const b = document.createElement("button");
    b.className = "btn sm " + cls; b.textContent = label; b.style.margin = "2px 0";
    b.onclick = (e) => { e.stopPropagation(); onClick(); };
    return b;
  };

  function ensure(kind, el, h) {
    if (apis[kind]) return apis[kind];
    let cols, extra = {};
    if (kind === "items") {
      cols = [
        { field: "name", headerName: "Item", flex: 2, minWidth: 180, filter: true },
        { field: "category", headerName: "Category", width: 120, filter: true },
        { field: "stock", headerName: "Stock", width: 110, editable: true, valueParser: num, type: "rightAligned",
          valueFormatter: (p) => `${p.value} ${p.data.unit}` },
        { field: "threshold", headerName: "Alert at", width: 100, editable: true, valueParser: num, type: "rightAligned" },
        { field: "cost_price", headerName: "Cost", width: 100, valueFormatter: inr, type: "rightAligned" },
        { field: "price", headerName: "Price", width: 110, editable: true, valueParser: num, valueFormatter: inr, type: "rightAligned" },
        { headerName: "", width: 150, sortable: false, cellRenderer: (p) => btn("📈 Market", "", () => h.market(p.data.id)) },
      ];
      extra = {
        rowClassRules: { "ag-low": (p) => p.data.stock <= p.data.threshold, "ag-dead": (p) => h.isDead(p.data.id) },
        onCellValueChanged: (e) => h.edit(e.data.id, { [e.colDef.field]: Number(e.newValue) }),
      };
    } else if (kind === "customers") {
      cols = [
        { field: "name", headerName: "Customer", flex: 1, minWidth: 160, filter: true },
        { field: "phone", headerName: "Phone", width: 130 },
        { field: "balance", headerName: "Balance", width: 120, valueFormatter: inr, type: "rightAligned", sort: "desc",
          cellClass: (p) => (p.value > 0 ? "ag-due" : "") },
        { field: "days_overdue", headerName: "Overdue", width: 100, type: "rightAligned", valueFormatter: (p) => (p.value ? p.value + " d" : "") },
        { headerName: "PayPal invoice", width: 150, valueGetter: (p) => (p.data.last_invoice ? p.data.last_invoice.status : ""),
          cellRenderer: (p) => p.value ? `<span class="badge ${["PAID", "MARKED_AS_PAID"].includes(p.value) ? "green" : "blue"}">${p.value}</span>` : "" },
        { headerName: "", width: 110, sortable: false, cellRenderer: (p) => btn("Open", "primary", () => h.open(p.data.id)) },
      ];
      extra = { onRowClicked: (e) => h.open(e.data.id) };
    }
    apis[kind] = agGrid.createGrid(el, {
      theme: theme(), columnDefs: cols, rowData: [], rowHeight: 44, headerHeight: 40, animateRows: true,
      defaultColDef: { resizable: true, sortable: true, suppressMovable: true },
      getRowId: (p) => String(p.data.id), stopEditingWhenCellsLoseFocus: true, ...extra,
    });
    return apis[kind];
  }

  window.DukaanGrids = {
    ensure,
    setRows: (kind, rows) => apis[kind] && apis[kind].setGridOption("rowData", rows),
    setFilter: (kind, q) => apis[kind] && apis[kind].setGridOption("quickFilterText", q),
    has: (kind) => !!apis[kind],
  };
})();
