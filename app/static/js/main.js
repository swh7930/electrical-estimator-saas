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
    try {
      var meta = (window.estimateData && window.estimateData.meta) || {};
      return meta.mode || 'fast';
    } catch (e) {
      return 'fast';
    }
  }

  saveBtn.addEventListener('click', function () {
    if (getMode() === 'standard') {
      try {
        // Use your existing helper; estimator grid is already persisted by its own script
        if (typeof window.saveEstimateData === 'function') window.saveEstimateData();
      } catch (e) {
        // keep console clean
      }
    } else {
      // Fast flow → capture metadata first
      window.location.href = '/estimates/new';
    }
  }, { passive: true });

  eePropagateWorkflowParams();
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
