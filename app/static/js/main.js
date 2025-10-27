// CSRF: auto-inject header for same-origin write requests
(function () {
  var meta = document.querySelector('meta[name="csrf-token"]');
  var token = meta ? meta.getAttribute('content') : null;
  if (!token) return;

  var _fetch = window.fetch;
  window.fetch = function (input, init) {
    init = init || {};
    var url = (typeof input === 'string') ? input : (input && input.url) || '';
    var method = ((init.method || 'GET') + '').toUpperCase();
    var isWrite = /^(POST|PUT|PATCH|DELETE)$/.test(method);
    var sameOrigin = /^https?:\/\//i.test(url) ? url.indexOf(location.origin) === 0 : true;

    if (isWrite && sameOrigin) {
      var headers = init.headers || {};
      // Normalize to a plain object if Headers instance
      if (typeof Headers !== 'undefined' && headers instanceof Headers) {
        var obj = {};
        headers.forEach(function (v, k) { obj[k] = v; });
        headers = obj;
      }
      if (!('X-CSRFToken' in headers) && !('X-CSRF-Token' in headers)) {
        headers['X-CSRFToken'] = token;
      }
      init.headers = headers;
    }
    return _fetch(input, init);
  };
})();

// Keep estimator workflow links carrying ?eid=&rt= across pages
function eePropagateWorkflowParams() {
  const params = new URLSearchParams(window.location.search);
  const eid = params.get('eid');
  const rt  = params.get('rt');
  if (!eid && !rt) return; // nothing to do

  // Match only the workflow pages; leave other links untouched
  const selector = [
    'a[href^="/estimator"]',
    'a[href^="/adjustments"]',
    'a[href^="/dje"]',
    'a[href^="/summary"]'
  ].join(', ');

  document.querySelectorAll(selector).forEach(a => {
    const href = a.getAttribute('href');
    if (!href) return;
    try {
      const url = new URL(href, window.location.origin);
      const path = (url.pathname || '').replace(/\/+$/,'');
      if (path !== '/estimator') {          // don’t carry EID into a fresh Estimator page
        if (eid) url.searchParams.set('eid', eid);
        if (rt)  url.searchParams.set('rt', rt);
      }
      a.setAttribute('href', url.pathname + (url.search ? url.search : ''));
    } catch (_) {
      // Ignore malformed/anchor-only links
    }
  });
}

// --- Workflow header: Save button (shared across Estimator pages) ---
document.addEventListener('DOMContentLoaded', function () {
  var saveBtn = document.getElementById('workflowSaveBtn');
  if (!saveBtn) return;

  function getMode() {
    // If an eid is present in the URL, we are in standard mode.
    var params = new URLSearchParams(window.location.search);
    if (params.get('eid')) return 'standard';

    // Otherwise, fall back to meta (some pages may set this)
    try {
      var meta = (window.estimateData && window.estimateData.meta) || {};
      return meta.mode || 'fast';
    } catch (e) {
      return 'fast';
    }
  }

  function nsKeys() { return window.nsKeys(); }

  function capturePayload() {
    var k = nsKeys();
    var payload = { v: 1, grid: null, totals: null, estimateData: null, cells: null, summary_export: null };

    try { payload.grid = JSON.parse(localStorage.getItem(k.gridKey) || "null"); } catch (_) {}
    try { payload.totals = JSON.parse(localStorage.getItem(k.totalsKey) || "null"); } catch (_) {}
    try { payload.estimateData = JSON.parse(localStorage.getItem(k.estimateDataKey) || "null"); } catch (_) {}

    // Snapshot Summary visible values (cells)
    payload.cells = captureSummaryCells();

    // NEW: Snapshot controls (margin%, overhead%, adders, tax%, labor rate) in a clean place
    payload.summary_export = {
      cells: payload.cells || {},
      controls: captureSummaryControls()
    };

    // SANITIZE: margin/overhead do NOT belong under materials — remove if present
    try {
      if (payload.estimateData && payload.estimateData.materials) {
        if ('margin_percent' in payload.estimateData.materials) {
          delete payload.estimateData.materials.margin_percent;
        }
        if ('overhead_percent' in payload.estimateData.materials) {
          delete payload.estimateData.materials.overhead_percent;
        }
      }
    } catch (_) {}

    return { eid: k.eid, payload: payload };
  }

  function captureSummaryControls() {
    // Exact IDs in your Summary
    var marginSel   = document.getElementById('marginSelect');
    var overheadSel = document.getElementById('overheadPercentSelect');
    var laborRateEl = document.getElementById('laborRateInput');

    // Name-based selects in the Material section
    var miscSel  = document.querySelector('select[name="misc_percent"]');
    var smallSel = document.querySelector('select[name="small_tools_percent"]');
    var largeSel = document.querySelector('select[name="large_tools_percent"]');
    var wasteSel = document.querySelector('select[name="waste_theft_percent"]');
    var taxSel   = document.querySelector('select[name="sales_tax_percent"]');

    function val(sel) {
      if (!sel) return null;
      var v = sel.value;
      if (v === '' || v == null) return null;
      var n = Number(v);
      return Number.isFinite(n) ? n : v;
    }

    // Prefer authoritative persisted values when present
    var overheadFromData = (
      window.estimateData &&
      estimateData.materials &&
      Number.isFinite(Number(estimateData.materials.overhead_percent))
    ) ? Number(estimateData.materials.overhead_percent) : null;

    var laborFromData = (
      window.estimateData &&
      estimateData.totals &&
      typeof estimateData.totals.laborRate === 'number'
    ) ? estimateData.totals.laborRate : null;

    var laborFromInput = (function () {
      if (!laborRateEl) return null;
      var num = Number(String(laborRateEl.value).replace(/[^0-9.]/g, ''));
      return Number.isFinite(num) ? num : null;
    })();

    return {
      margin_percent: val(marginSel),
      overhead_percent: (overheadFromData != null ? overheadFromData : val(overheadSel)),
      misc_percent:  val(miscSel),
      small_tools_percent: val(smallSel),
      large_tools_percent: val(largeSel),
      waste_theft_percent: val(wasteSel),
      sales_tax_percent:  val(taxSel),
      // Prefer persisted numeric laborRate; else parse the input text
      labor_rate: (laborFromData != null ? laborFromData : laborFromInput)
    };
  }

  function captureSummaryCells() {
    // Try to harvest whatever is on the Summary DOM right now (no hard gate)
    var ids = [
      'labor-hours-pricing-sheet', 'summaryAdjustedHours', 'summaryAdditionalHours',
      'summaryTotalHours', 'summaryTotalLaborCost', 'material-cost-price-sheet',
      'miscMaterialValue', 'smallToolsValue', 'largeToolsValue', 'wasteTheftValue',
      'taxableMaterialValue', 'salesTaxValue', 'totalMaterialCostValue', 'djeValue',
      'primeCostValue', 'overheadValue', 'breakEvenValue', 'markupValue',
      'profitMarginValue', 'estimatedSalesPriceValue', 'oneManDays', 'twoManDays',
      'fourManDays', 'laborRateInput'
    ];

    var out = {};
    for (var i = 0; i < ids.length; i++) {
      var el = document.getElementById(ids[i]);
      if (!el) continue;
      var txt = (el.tagName === 'INPUT') ? el.value : el.textContent;
      out[ids[i]] = (txt == null ? '' : String(txt)).trim();
    }
    // If nothing was found at all, return an empty object (not null) so exporters still send controls
    return out;
  }

  function saveServer(eid, payload) {
    if (!eid) { window.location.href = "/estimates/new"; return; }
    try {
      fetch("/estimates/" + encodeURIComponent(eid) + "/payload", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      .then(function (res) {
        if (!res || !res.ok) throw new Error("save_failed");
        try { showToast("Estimate saved", "success"); } catch (_) {}
      })
      .catch(function () {
        try { showToast("Save failed", "danger"); } catch (_) {}
      });
    } catch (_) {
      try { showToast("Save failed", "danger"); } catch (__){ }
    }
  }

  saveBtn.addEventListener('click', function () {
    if (getMode() === 'standard') {
      try {
        // Persist grid/totals locally using your existing helper
        if (typeof window.saveEstimateData === 'function') window.saveEstimateData();
      } catch (e) {}

      var cap = capturePayload();
      saveServer(cap.eid, cap.payload);
    } else {
      // Fast flow → capture metadata first (no estimate id yet)
      window.location.href = '/estimates/new';
    }
  }, { passive: true });

  eePropagateWorkflowParams();
});

// --- Workflow header: Export PDF (Summary only) ---
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('exportSummaryPdfBtn');
  if (!btn) return;

  var params = new URLSearchParams(window.location.search);
  var eid = params.get('eid');

    // Always enabled; Fast path works without EID
    btn.removeAttribute('disabled');
    btn.classList.remove('disabled');
    btn.title = eid ? 'Download PDF' : 'Export current summary (Fast)';

    btn.addEventListener('click', function (e) {
      e.preventDefault();
      if (!eid) { return exportSummaryPdfSmart(e, null); }
      exportSummaryPdfSmart(e, eid);
    }, { passive: false });
});

// --- Workflow header: Export CSV (Summary only) ---
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('exportSummaryCsvBtn');
  if (!btn) return;

  var params = new URLSearchParams(window.location.search);
  var eid = params.get('eid');

  // Always enabled; Fast path works without EID
  btn.removeAttribute('disabled');
  btn.classList.remove('disabled');
  btn.title = eid ? 'Download CSV' : 'Export current summary (Fast)';

  btn.addEventListener('click', function (e) {
    e.preventDefault();
    if (!eid) { return exportSummaryCsvSmart(e, null); }
    exportSummaryCsvSmart(e, eid);
  }, { passive: false });
});

// --- Estimates Index: Export CSV (preserve current query string) ---
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('exportEstimatesCsvBtn');
  if (!btn) return;

  btn.addEventListener('click', function (e) {
    // Always allow direct download; append current query string if present
    var url = '/estimates/export/index.csv';
    var qs = window.location.search;
    btn.setAttribute('href', url + (qs ? qs : ''));
  }, { passive: true });
});

// --- Auto-hydrate from server if local cache is empty (standard flow only) ---
document.addEventListener('DOMContentLoaded', function () {
  try {
    var params = new URLSearchParams(window.location.search);
    var eid = params.get('eid');
    if (!eid) return; // only standard mode pages have / need eid

    var ns = "ee." + eid + ".";
    var gridKey = ns + "grid.v1";
    var totalsKey = ns + "totals";
    var estKey = "estimateData";

    var hasGrid = !!localStorage.getItem(gridKey);
    var hasTotals = !!localStorage.getItem(totalsKey);
    var hasEst = !!localStorage.getItem(estKey);

    // If we already have cache, do nothing.
    if (hasGrid && hasTotals) return;

    // Prevent reload loop if we just hydrated
    var hydratedFlag = "ee.hydrated." + eid;
    if (sessionStorage.getItem(hydratedFlag)) return;

    fetch("/estimates/" + encodeURIComponent(eid) + "/payload.json")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j || !j.payload) return;
        var p = j.payload || {};
        var wrote = false;

        if (!hasGrid && p.grid != null) {
          localStorage.setItem(gridKey, JSON.stringify(p.grid));
          wrote = true;
        }
        if (!hasTotals && p.totals != null) {
          localStorage.setItem(totalsKey, JSON.stringify(p.totals));
          wrote = true;
        }
        if (!hasEst && p.estimateData != null) {
          localStorage.setItem(estKey, JSON.stringify(p.estimateData));
          wrote = true;
        }

        // Let existing page scripts render the freshly cached data
        if (wrote) {
          try { window.dispatchEvent(new CustomEvent('ee:payload:applied', { detail: { eid: eid } })); } catch (_) {}
          sessionStorage.setItem(hydratedFlag, "1");
          location.reload();
        }
      })
      .catch(function () { /* silent */ });
  } catch (_) { /* silent */ }
});


// Global: Treat Enter like Tab inside forms (but not on buttons or textareas)
document.addEventListener("keydown", (e) => {
  if (e.key !== "Enter") return;

  const t = e.target;
  if (!t || !(t instanceof HTMLElement)) return;
  const tag = t.tagName;

  // Allow normal behavior on buttons and textareas
  if (tag === "BUTTON" || tag === "TEXTAREA") return;

  // If inside a form (or a container that opts in via data-enter-as-tab), move focus
  const scope = t.closest("[data-enter-as-tab]") || t.closest("form");
  if (!scope) return;

  // Don't submit the form on Enter; advance focus instead
  e.preventDefault();

  // Focusable controls, excluding disabled/readonly/hidden
  const focusables = Array.from(scope.querySelectorAll(
    'input:not([type="hidden"]):not([disabled]):not([readonly]),' +
    'select:not([disabled]), textarea:not([disabled]):not([readonly]),' +
    '[tabindex]:not([tabindex="-1"])'
  ));

  const idx = focusables.indexOf(t);
  const next = focusables[(idx + 1) % focusables.length];
  if (next) {
    next.focus();
    if (typeof next.select === "function") next.select();
  }
});

// Uses existing #toastStack container in base.html
function showToast(message, type, delay) {
  var stack = document.getElementById('toastStack');
  if (!stack) { try { alert(message); } catch (_) {} return; }

  var theme = (type === 'danger' || type === 'error') ? 'text-bg-danger'
            : (type === 'warning') ? 'text-bg-warning'
            : 'text-bg-success';

  var el = document.createElement('div');
  el.className = 'toast ' + theme + ' border-0';
  el.setAttribute('role', 'status');
  el.setAttribute('aria-live', 'polite');
  el.setAttribute('aria-atomic', 'true');
  el.innerHTML =
    '<div class="d-flex">' +
      '<div class="toast-body">' + message + '</div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>' +
    '</div>';

  stack.appendChild(el);

  // Prefer Bootstrap if present; fallback to simple show/hide
  try {
    var Toast = window.bootstrap && window.bootstrap.Toast;
    if (Toast) {
      var t = new Toast(el, { delay: delay || 2200, autohide: true });
      el.addEventListener('hidden.bs.toast', function () { el.remove(); });
      t.show();
    } else {
      el.classList.add('show');
      setTimeout(function () { el.remove(); }, (delay || 2200) + 400);
    }
  } catch (_) {
    el.classList.add('show');
    setTimeout(function () { el.remove(); }, (delay || 2200) + 400);
  }
}

// Smart export: if eid present -> Saved GET; else -> Fast POST with summary_export
function exportSummaryPdfSmart(e, eid) {
  try { if (e && typeof e.preventDefault === 'function') e.preventDefault(); } catch(_) {}
  try { if (document.activeElement && typeof document.activeElement.blur === 'function') document.activeElement.blur(); } catch(_) {}

  // Saved path = simple GET
  if (eid) {
    window.open('/estimates/' + encodeURIComponent(eid) + '/export/summary.pdf', '_blank');
    return;
  }

  // Fast path = build from DOM right now (no payload dependency)
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  var cells = (typeof captureSummaryCells === 'function')
    ? (captureSummaryCells() || {})
    : harvestCellsFallback();

  var controls = (typeof captureSummaryControls === 'function')
    ? (captureSummaryControls() || {})
    : harvestControlsFallback();

  fetch('/estimates/exports/summary.pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: JSON.stringify({ summary_export: { cells: cells, controls: controls } })
  })
  .then(function (r) { if (!r.ok) throw new Error('export_failed'); return r.blob(); })
  .then(function (b) { var u = URL.createObjectURL(b); window.open(u, '_blank'); })
  .catch(function () { try { showToast('Export PDF failed', 'danger'); } catch(_) {} });
}


function exportSummaryCsvSmart(e, eid) {
  try { if (e && typeof e.preventDefault === 'function') e.preventDefault(); } catch(_) {}
  try { if (document.activeElement && typeof document.activeElement.blur === 'function') document.activeElement.blur(); } catch(_) {}

  // Saved path = simple GET
  if (eid) {
    window.location.href = '/estimates/' + encodeURIComponent(eid) + '/export/summary.csv';
    return;
  }

  // Fast path = build from DOM right now
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  var cells = (typeof captureSummaryCells === 'function')
    ? (captureSummaryCells() || {})
    : harvestCellsFallback();

  var controls = (typeof captureSummaryControls === 'function')
    ? (captureSummaryControls() || {})
    : harvestControlsFallback();

  fetch('/estimates/exports/summary.csv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: JSON.stringify({ summary_export: { cells: cells, controls: controls } })
  })
  .then(function (r) {
    if (!r.ok) throw new Error('export_failed');
    var disp = r.headers.get('Content-Disposition') || '';
    var m = /filename\*?=(?:UTF-8''|")?([^";]+)/i.exec(disp);
    var filename = (m && m[1]) ? decodeURIComponent(m[1]) : 'estimate_summary.csv';
    return r.blob().then(function (b) { return { b: b, filename: filename }; });
  })
  .then(function (o) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(o.b);
    a.download = o.filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(function () {
      URL.revokeObjectURL(a.href); a.remove();
    }, 500);
  })
  .catch(function () { try { showToast('Export CSV failed', 'danger'); } catch(_) {} });
}

// --- Fallback harvesters (used when captureSummary* are not defined) ---
function harvestCellsFallback() {
  // Use your exact Summary IDs; input uses .value, others .textContent
  var ids = [
    'labor-hours-pricing-sheet','summaryAdjustedHours','summaryAdditionalHours',
    'summaryTotalHours','summaryTotalLaborCost','material-cost-price-sheet',
    'miscMaterialValue','smallToolsValue','largeToolsValue','wasteTheftValue',
    'taxableMaterialValue','salesTaxValue','totalMaterialCostValue','djeValue',
    'primeCostValue','overheadValue','breakEvenValue','markupValue',
    'profitMarginValue','estimatedSalesPriceValue','oneManDays','twoManDays',
    'fourManDays','laborRateInput'
  ];
  var out = {};
  for (var i=0;i<ids.length;i++){
    var el = document.getElementById(ids[i]);
    if (!el) continue;
    var val = (el.tagName === 'INPUT') ? el.value : el.textContent;
    if (val == null) continue;
    val = String(val).trim();
    // keep zeros like "0" / "$0.00"
    out[ids[i]] = val;
  }
  return out;
}

function harvestControlsFallback() {
  // Your exact controls in Summary
  var marginSel   = document.getElementById('marginSelect');
  var overheadSel = document.getElementById('overheadPercentSelect');
  var laborRateEl = document.getElementById('laborRateInput');
  var miscSel     = document.querySelector('select[name="misc_percent"]');
  var smallSel    = document.querySelector('select[name="small_tools_percent"]');
  var largeSel    = document.querySelector('select[name="large_tools_percent"]');
  var wasteSel    = document.querySelector('select[name="waste_theft_percent"]');
  var taxSel      = document.querySelector('select[name="sales_tax_percent"]');

  function numOrNull(x){
    if (x == null || x === '') return null;
    var n = Number(x);
    return Number.isFinite(n) ? n : x;
  }
  function pick(sel){ return sel ? numOrNull(sel.value) : null; }

  // Prefer numeric labor rate if typed; leave as number
  var lr = null;
  if (laborRateEl) {
    var raw = String(laborRateEl.value || '').replace(/[^0-9.]/g,'');
    lr = raw ? Number(raw) : null;
    if (!Number.isFinite(lr)) lr = null;
  }

  return {
    margin_percent:        pick(marginSel),
    overhead_percent:      pick(overheadSel),
    misc_percent:          pick(miscSel),
    small_tools_percent:   pick(smallSel),
    large_tools_percent:   pick(largeSel),
    waste_theft_percent:   pick(wasteSel),
    sales_tax_percent:     pick(taxSel),
    labor_rate:            lr
  };
}

// Disable all workflow Reset buttons when an estimate is SAVED (?eid=... in URL).
// Works on Estimator, Adjustments, DJE, and Summary pages.
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    try {
      var eid = new URLSearchParams(location.search).get('eid');
      if (!eid) return; // Fast mode: keep reset buttons active

      var ids = ['estimatorResetBtn', 'resetAdjustmentsPageBtn', 'djeResetBtn', 'resetAllBtn'];

      function hardDisable(el) {
        if (!el) return;
        el.setAttribute('disabled', 'disabled');
        el.classList.add('disabled');
        el.setAttribute('aria-disabled', 'true');
        el.style.pointerEvents = 'none';
      }

      ids.forEach(function (id) { hardDisable(document.getElementById(id)); });

      // Capture-phase guard: block any click that lands on these buttons even if a script re-enables them later.
      document.addEventListener('click', function (e) {
        var t = e.target && e.target.closest && e.target.closest('#estimatorResetBtn, #resetAdjustmentsPageBtn, #djeResetBtn, #resetAllBtn');
        if (t) { e.preventDefault(); e.stopImmediatePropagation(); }
      }, true);
    } catch (_) { /* silent */ }
  });
})();

// Global hard reset click delegate.
// Triggers when a control has any of these hooks:
// - [data-ee-hard-reset]  (preferred)
// - [data-action="reset-estimate"]  (compat)
// - #btnResetEstimate      (compat)
(function attachHardResetDelegate() {
  try {
    document.addEventListener('click', function (e) {
      const el = e.target.closest('[data-ee-hard-reset],[data-action="reset-estimate"],#btnResetEstimate');
      if (!el) return;
      if (el.matches('.disabled, [disabled]')) return;

      // Optional confirm to prevent accidental nukes.
      const ok = window.confirm('Reset this estimate? This will clear both draft (FAST) and this estimate\u2019s local data in this browser.');
      if (!ok) return;

      try { window.ee.hardReset(); } catch {}
      // Reload so every page re-hydrates from authoritative sources.
      try { location.reload(); } catch {}
      e.preventDefault();
    }, { passive: false });
  } catch {}
})();

// --- Billing: Customer Portal (mirror Checkout JSON pattern) ---
(function () {
  function $all(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }
  function setDisabled(form, disabled) {
    $all("button, input[type=submit]", form).forEach(function (el) { el.disabled = !!disabled; });
  }

  async function onPortalSubmit(ev) {
    ev.preventDefault(); // avoid CSP form-action; use JSON + JS navigation instead
    const form = ev.currentTarget;
    setDisabled(form, true);
    try {
      const resp = await fetch("/billing/portal.json", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Accept": "application/json", "Content-Type": "application/json" },
        body: "{}"
      });
      if (!resp.ok) {
        // Try to surface Stripe's user_message if any
        let msg = "Failed to create portal session";
        try { const j = await resp.json(); if (j && j.error) msg = j.error; } catch(_) {}
        throw new Error(msg);
      }
      const data = await resp.json();
      if (!data || !data.url) throw new Error("Missing portal URL");
      window.location.assign(data.url);
    } catch (err) {
      console.error("Manage Billing failed:", err);
      alert("Unable to open Customer Portal: " + err.message);
      // Optional fallback (non-blocking): try a GET navigation
      // window.location.assign("/billing/portal");
    } finally {
      setDisabled(form, false);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    const forms = $all('form[action$="/billing/portal"]');
    if (!forms.length) return;
    forms.forEach(function (form) {
      form.addEventListener("submit", onPortalSubmit, { passive: false });
    });
  });
})();
