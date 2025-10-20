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
    var payload = { v: 1, grid: null, totals: null, estimateData: null };
    try { payload.grid = JSON.parse(localStorage.getItem(k.gridKey) || "null"); } catch (_) {}
    try { payload.totals = JSON.parse(localStorage.getItem(k.totalsKey) || "null"); } catch (_) {}
    try { payload.estimateData = JSON.parse(localStorage.getItem("estimateData") || "null"); } catch (_) {}
    return { eid: k.eid, payload: payload };
  }

  function saveServer(eid, payload) {
    if (!eid) { window.location.href = "/estimates/new"; return; }
    try {
      fetch("/estimates/" + encodeURIComponent(eid) + "/payload", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }).then(function () {
        // keep console quiet; UI toast can be added later if desired
      });
    } catch (_) {}
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
