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
      if (eid) url.searchParams.set('eid', eid);
      if (rt)  url.searchParams.set('rt', rt);
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

  function nsKeys() {
    var params = new URLSearchParams(window.location.search);
    var eid = params.get('eid');
    var ns = eid ? ("ee." + eid + ".") : "ee.__global__.";
    return { eid: eid, gridKey: ns + "grid.v1", totalsKey: ns + "totals" };
  }

  function capturePayload() {
    var k = nsKeys();
    var payload = { v: 1, grid: null, totals: null, estimateData: null, cells: null, summary_export: null };

    try { payload.grid = JSON.parse(localStorage.getItem(k.gridKey) || "null"); } catch (_) {}
    try { payload.totals = JSON.parse(localStorage.getItem(k.totalsKey) || "null"); } catch (_) {}
    try { payload.estimateData = JSON.parse(localStorage.getItem("estimateData") || "null"); } catch (_) {}

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
    // Only on the Summary page (marker cell must exist)
    var marker = document.getElementById('labor-hours-pricing-sheet');
    if (!marker) return null;

    // Exact IDs taken from your current _summary_tables.html (no guesses)
    var ids = [
      'labor-hours-pricing-sheet',
      'summaryAdjustedHours',
      'summaryAdditionalHours',
      'summaryTotalHours',
      'summaryTotalLaborCost',
      'material-cost-price-sheet',
      'miscMaterialValue',
      'smallToolsValue',
      'largeToolsValue',
      'wasteTheftValue',
      'taxableMaterialValue',
      'salesTaxValue',
      'totalMaterialCostValue',
      'djeValue',
      'primeCostValue',
      'overheadValue',
      'breakEvenValue',
      'markupValue',
      'profitMarginValue',
      'estimatedSalesPriceValue',
      'oneManDays',
      'twoManDays',
      'fourManDays'
    ];

  var out = {};
  ids.forEach(function (id) {
    var el = document.getElementById(id);
    if (!el) return;
    var txt = (el.tagName === 'INPUT') ? el.value : el.textContent;
    out[id] = (txt == null ? '' : String(txt)).trim();
  });
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

  function enable(v) {
    if (v) {
      btn.removeAttribute('disabled');
      btn.classList.remove('disabled');
      btn.title = 'Download PDF';
    } else {
      btn.setAttribute('disabled', 'disabled');
      btn.classList.add('disabled');
      btn.title = 'Save your estimate first';
    }
  }

  enable(!!eid);

  btn.addEventListener('click', function (e) {
    e.preventDefault();
    if (!eid) return;
    window.open('/estimates/' + encodeURIComponent(eid) + '/export/summary.pdf', '_blank');
  }, { passive: false });
});

// --- Workflow header: Export CSV (Summary only) ---
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('exportSummaryCsvBtn');
  if (!btn) return;

  var params = new URLSearchParams(window.location.search);
  var eid = params.get('eid');

  function enable(v) {
    if (v) {
      btn.removeAttribute('disabled');
      btn.classList.remove('disabled');
      btn.title = 'Download CSV';
    } else {
      btn.setAttribute('disabled', 'disabled');
      btn.classList.add('disabled');
      btn.title = 'Save your estimate first';
    }
  }

  enable(!!eid);

  btn.addEventListener('click', function () {
    if (!eid) return;
    window.location.href = '/estimates/' + encodeURIComponent(eid) + '/export/summary.csv';
  }, { passive: true });
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
