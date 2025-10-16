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
});
