/**
 * Global storage key contract for Estimator.
 * Standard: use ee.<eid>. for saved estimates; ee.FAST. for fast/unsaved mode.
 * Always loaded BEFORE any page module so everyone can call nsKeys().
 */
(function () {
  if (window.nsKeys) return; // idempotent

  function nsKeys() {
    try {
      const p = new URLSearchParams(window.location.search);
      const eid = p.get('eid');
      const ns  = eid ? `ee.${eid}.` : 'ee.FAST.';
      return {
        eid,
        ns,
        gridKey:         ns + 'grid.v1',
        totalsKey:       ns + 'totals',
        estimateDataKey: ns + 'estimateData',
      };
    } catch (_) {
      // Safe, deterministic fallback (FAST namespace)
      const ns = 'ee.FAST.';
      return {
        eid: null,
        ns,
        gridKey:         ns + 'grid.v1',
        totalsKey:       ns + 'totals',
        estimateDataKey: ns + 'estimateData',
      };
    }
  }

  window.nsKeys = nsKeys;
  window.ee = window.ee || {};
  window.ee.nsKeys = nsKeys;

    /**
   * Hard reset: clear ALL estimator state for this browser session for:
   * - current EID namespace (ee.<eid>.*) when present
   * - FAST namespace (ee.FAST.*)
   * - legacy bare keys (e.g., "estimateData")
   * Emits: ee:reset:hard (via ee.fire if available)
   */
  function hardReset() {
    const { eid, gridKey, totalsKey, estimateDataKey } = nsKeys();

    // Explicit targets (exact keys we know about)
    const targets = new Set([
      gridKey, totalsKey, estimateDataKey,
      'ee.FAST.grid.v1', 'ee.FAST.totals', 'ee.FAST.estimateData',
      'estimateData', // legacy, should never exist now, but sanitize anyway
    ]);
    if (eid) {
      targets.add(`ee.${eid}.grid.v1`);
      targets.add(`ee.${eid}.totals`);
      targets.add(`ee.${eid}.estimateData`);
    }

    // Remove explicit keys
    for (const k of targets) {
      try { localStorage.removeItem(k); } catch {}
    }

    // Sweep any future keys we might add under these namespaces
    try {
      const prefixes = ['ee.FAST.'];
      if (eid) prefixes.push(`ee.${eid}.`);
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (!key) continue;
        if (prefixes.some(p => key.startsWith(p))) {
          localStorage.removeItem(key);
        }
      }
    } catch {}

    // Fire event for any listeners (best-effort / optional)
    try {
      if (window.ee && typeof window.ee.fire === 'function') {
        window.ee.fire('reset:hard', { eid });
      }
    } catch {}

    // Dev one-liner guardrail: warn if legacy global key somehow persists
    try {
      if (['127.0.0.1','localhost'].includes(location.hostname) &&
          localStorage.getItem('estimateData')) {
        console.warn('[dev] Legacy "estimateData" key still present after hardReset() — investigate writers.');
      }
    } catch {}
  }

  // Public API
  window.ee.hardReset = hardReset;

})();
