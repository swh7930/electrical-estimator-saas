// ===== markup ↔ margin conversion =====
const marginToMarkup = {};
for (let i = 1; i <= 25; i++) marginToMarkup[i] = +(1 / (1 - i / 100)).toFixed(2);
[30, 40, 50].forEach(i => (marginToMarkup[i] = +(1 / (1 - i / 100)).toFixed(2)));
marginToMarkup[100] = 200.0;

// === App Settings (Summary) helpers ===
const EE_SETTINGS_VERSION_KEY = 'ee.settings.version.applied';
const EE_RESET_FLAG = 'ee.reset.applyFromSettings';

// ====== Per-estimate namespace (strict) ======
const { eid: EID, totalsKey: TOTALS_KEY, estimateDataKey: ESTIMATE_DATA_KEY } = nsKeys();
// ---- Step 2: Summary hydration order & safety ----
// If we're on an EID-backed page but its namespace is empty, and there is residual FAST data,
// migrate it forward exactly once so the page never paints blank or from the wrong store.
(function migrateFastToEidOnce() {
  if (!EID) return; // only meaningful for real estimates

  const FAST_TOTALS_KEY = 'ee.FAST.totals';
  const FAST_ED_KEY     = 'ee.FAST.estimateData';

  try {
    const eidTotals = localStorage.getItem(TOTALS_KEY);
    const eidED     = localStorage.getItem(ESTIMATE_DATA_KEY);
    const fastTotals = localStorage.getItem(FAST_TOTALS_KEY);
    const fastED     = localStorage.getItem(FAST_ED_KEY);

    // Migrate only when EID store is empty and FAST has data (no overwrite)
    if (!eidTotals && fastTotals) {
      localStorage.setItem(TOTALS_KEY, fastTotals);
      // dev-hint only; harmless in production
      try { console.info('[summary] migrated FAST.totals ->', TOTALS_KEY); } catch {}
    }
    if (!eidED && fastED) {
      localStorage.setItem(ESTIMATE_DATA_KEY, fastED);
      try { console.info('[summary] migrated FAST.estimateData ->', ESTIMATE_DATA_KEY); } catch {}
    }
  } catch (_) {
    // no-op
  }
})();

// Dev guardrail: if we're editing an EID but still have FAST blobs around,
// emit a console warning so regressions are obvious during testing.
(function devGuardrail() {
  if (!EID) return;
  if (localStorage.getItem('ee.FAST.totals') || localStorage.getItem('ee.FAST.estimateData')) {
    try {
      console.warn('[summary] FAST namespace still present while editing EID=', EID,
                   '— ensure all pages read/write via nsKeys() only.');
    } catch {}
  }
})();

function eeFetchAppSettings() {
  return fetch('/admin/settings.json').then(r => (r.ok ? r.json() : {}));
}

function eeApplySettingsToSummary(settings) {
  const s = settings || {};
  const p = s.pricing || {};
  const setSel = (sel, val) => { if (!sel) return; sel.value = String(parseInt(val) || 0); sel.dispatchEvent(new Event('change')); };
  const byName = (name) => document.querySelector(`select[name='${name}']`);

  // Five adders
  setSel(byName('misc_percent'),         p.misc_percent);
  setSel(byName('small_tools_percent'),  p.small_tools_percent);
  setSel(byName('large_tools_percent'),  p.large_tools_percent);
  setSel(byName('waste_theft_percent'),  p.waste_theft_percent);
  setSel(byName('sales_tax_percent'),    p.sales_tax_percent);

  // Profit (margin)
  setSel(document.querySelector(`select[name='margin_percent']`), p.margin_percent);

  // Overhead (dropdown by id)
  const over = document.getElementById('overheadPercentSelect');
  if (over && Number.isFinite(parseInt(p.overhead_percent))) {
    over.value = String(parseInt(p.overhead_percent));
    over.dispatchEvent(new Event('change'));
  }

  // Labor rate
  const labor = document.getElementById('laborRateInput');
  if (labor && Number.isFinite(parseFloat(p.labor_rate))) {
    const rate = parseFloat(p.labor_rate);
    const fmt = (typeof window.formatUSD === 'function') ? window.formatUSD : (n => `$${(Number(n)||0).toFixed(2)}`);
    labor.value = fmt(rate);
    window.estimateData = window.estimateData || {};
    estimateData.totals = estimateData.totals || {};
    estimateData.totals.laborRate = rate;
  }

  // Persist + recalc
  if (typeof window.saveEstimateData === 'function') saveEstimateData();
  if (typeof window.updateStepCMaterialSummary === 'function') updateStepCMaterialSummary();
  if (typeof window.updateSummaryTotals === 'function') updateSummaryTotals();
}

// Fetch estimate JSON and apply its settings snapshot to Summary
async function eeHydrateFromEstimateSnapshot(eid) {
  const res = await fetch(`/estimates/${encodeURIComponent(eid)}.json`, { headers: { 'Accept': 'application/json' } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const doc = await res.json();
  const snap = doc && doc.settings_snapshot ? doc.settings_snapshot : null;
  if (!snap) throw new Error('Missing settings_snapshot');
  eeApplySettingsToSummary(snap);
}


document.addEventListener("DOMContentLoaded", () => {
  // Pull Estimator header totals into Summary placeholders
  renderEstimatorTotalsFromLocalStorage();

  loadEstimateData(); // Load from localStorage

  renderDJEFromStorage();

  // Restore dropdowns for adders
  ["misc_percent", "small_tools_percent", "large_tools_percent", "waste_theft_percent", "sales_tax_percent"]
    .forEach((name) => {
      const select = document.querySelector(`select[name='${name}']`);
      if (select) {
        if (estimateData.materials[name] != null) {
          select.value = estimateData.materials[name];
        }
        select.addEventListener("change", () => {
          estimateData.materials[name] = parseInt(select.value) || 0;
          saveEstimateData();
          updateStepCMaterialSummary();
        });
      }
    });

  // Margin selector (UI only here)
  const marginSelect = document.querySelector("select[name='margin_percent']");
  if (marginSelect) {
    marginSelect.addEventListener("change", updateStepCMaterialSummary);
  }

  // ---------- Labor rate input ----------
  updateSummaryTotals();

  const laborRateInput = document.getElementById("laborRateInput");
  if (laborRateInput && estimateData?.totals?.laborRate) {
    laborRateInput.value = `$${estimateData.totals.laborRate.toFixed(2)}`;
  }
  const formatToCurrency = (value) => {
    const num = parseFloat(String(value).replace(/[^0-9.]/g, ""));
    if (isNaN(num)) return "$0.00";
    return `$${num.toFixed(2)}`;
  };
  if (laborRateInput) {
    laborRateInput.value = formatToCurrency(laborRateInput.value);
    laborRateInput.addEventListener("focus", () => {
      setTimeout(() => laborRateInput.select(), 0);
      laborRateInput.value = laborRateInput.value.replace(/[^0-9.]/g, "");
    });
    laborRateInput.addEventListener("blur", () => {
      laborRateInput.value = formatToCurrency(laborRateInput.value);
      // Guard: if still showing $0.00, hydrate from snapshot/admin now
      try {
        const isZero = /^\$?0+(\.0+)?$/.test(String(laborRateInput.value).trim());
        if (isZero) {
          if (EID) {
            eeHydrateFromEstimateSnapshot(EID)
              .catch(() => eeFetchAppSettings().then(doc => eeApplySettingsToSummary(doc.settings || {})));
          } else {
            eeFetchAppSettings().then(doc => eeApplySettingsToSummary(doc.settings || {}));
          }
        }
      } catch (_) {}
      const rate = parseFloat(laborRateInput.value.replace(/[^0-9.]/g, ""));
      estimateData.totals.laborRate = isNaN(rate) ? 0 : rate;
      saveEstimateData();
      updateSummaryTotals();
      updateStepCMaterialSummary();
    });
    laborRateInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        laborRateInput.value = formatToCurrency(laborRateInput.value);
        laborRateInput.blur();
      }
    });
  }

  // ---------- OVERHEAD (Step F): Standard dropdown; persisted under estimateData.materials.overhead_percent ----------
  if (!estimateData.materials) estimateData.materials = {};
  estimateData.materials.overhead_percent = normalizePercent(estimateData.materials.overhead_percent, 30);
  saveEstimateData();

  const overheadSelect = document.getElementById("overheadPercentSelect");
  if (overheadSelect) {
    // Initialize dropdown from storage (default to 30 if invalid)
    const allowed = ["10", "15", "20", "25", "30", "35", "40"];
    const stored = String(estimateData.materials.overhead_percent);
    overheadSelect.value = allowed.includes(stored) ? stored : "30";

    overheadSelect.addEventListener("change", () => {
      const pct = normalizePercent(overheadSelect.value, 30);
      estimateData.materials.overhead_percent = allowed.includes(String(pct)) ? pct : 30;
      saveEstimateData();
      updateStepCMaterialSummary();
    });
  }

  // Final initial calc
  updateStepCMaterialSummary();

  // === Apply defaults on load ===
  // If eid is present, use that estimate's snapshot (authoritative).
  // Otherwise, fall back to Admin Settings (versioned).
  (function hydrateDefaults() {
    if (EID) {
      eeHydrateFromEstimateSnapshot(EID)
        .then(() => {
          // Fallback: if labor rate is still not set (empty or non-numeric), apply Admin Settings.
          try {
            const labor = document.getElementById('laborRateInput');
            const hasRate = !!(labor && /\d/.test(String(labor.value || '')));
            if (!hasRate) {
              return eeFetchAppSettings()
                .then(doc => eeApplySettingsToSummary(doc.settings || {}))
                .catch(e => console.warn('[Summary] Admin settings hydrate failed (fallback):', e));
            }
          } catch (_) {}
        })
        .catch(err => {
          console.error('[Summary] Snapshot hydrate failed:', err);
          // Fallback to Admin Settings on error
          eeFetchAppSettings()
            .then(doc => eeApplySettingsToSummary(doc.settings || {}))
            .catch(e => console.warn('[Summary] Admin settings hydrate failed (fallback):', e));
        });
      return;
    }

    // Legacy path (no eid): use Admin Settings with version flag
    const applied = localStorage.getItem(EE_SETTINGS_VERSION_KEY);
    const forced =
      sessionStorage.getItem(EE_RESET_FLAG) === '1' ||
      (function needsDefaults() {
        try {
          const raw = localStorage.getItem(ESTIMATE_DATA_KEY);
          const ed = raw ? JSON.parse(raw) : null;
          const m = (ed && ed.materials) || {};
          const t = (ed && ed.totals) || {};
          const hasLabor = Number.isFinite(Number(t.laborRate)) && Number(t.laborRate) > 0;
          const keys = ['misc_percent','small_tools_percent','large_tools_percent','waste_theft_percent','sales_tax_percent'];
          const haveAdders = keys.every(k => Number.isFinite(Number(m[k])));
          return !hasLabor || !haveAdders;     // if missing, force applying Admin Settings
        } catch (_) { return true; }
      })();

    eeFetchAppSettings()
      .then(doc => {
        const version = String(doc.settings_version || (doc.settings && doc.settings.version) || 1);
        if (forced || applied !== version) {
          eeApplySettingsToSummary(doc.settings || {});
          localStorage.setItem(EE_SETTINGS_VERSION_KEY, version);
        }
        if (forced) sessionStorage.removeItem(EE_RESET_FLAG);
      })
      .catch(err => console.warn('[Summary] Admin settings hydrate failed:', err));
  })();



});

// ===== helpers =====
function normalizePercent(value, fallback) {
  const n = parseInt(value, 10);
  return Number.isFinite(n) && n >= 0 ? n : fallback;
}

// S1-06f3 — Read 'ee.totals' and render Summary placeholders
function renderEstimatorTotalsFromLocalStorage() {
  const currencyFmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

  let mat = 0;
  let hrs = 0;

  try {
    const raw = localStorage.getItem(TOTALS_KEY);
    if (raw) {
      const data = JSON.parse(raw);
      if (typeof data?.material_cost_price_sheet === "number") mat = data.material_cost_price_sheet;
      if (typeof data?.labor_hours_pricing_sheet === "number") hrs = data.labor_hours_pricing_sheet;
    }
  } catch {
    // ignore parse errors; keep neutral defaults
  }

  const matEl = document.getElementById("material-cost-price-sheet");
  const hrsEl = document.getElementById("labor-hours-pricing-sheet");

  if (matEl) matEl.textContent = currencyFmt.format(mat);
  if (hrsEl) hrsEl.textContent = hrs.toFixed(2);
}

function formatDays(value) {
  const rounded = value.toFixed(1);
  const clean = rounded.endsWith(".0") ? parseInt(rounded) : rounded;
  return `${clean} day${clean == 1 ? "" : "s"}`;
}

function updateSummaryTotals() {
  // Always use the Estimator hours painted in the Summary header
  const hrsEl = document.getElementById("labor-hours-pricing-sheet");
  const domBase = hrsEl ? parseFloat(String(hrsEl.innerText).replace(/[^0-9.]/g, "")) || 0 : 0;

  // Adjustments & Additional come from storage (independent of Estimator reset)
  const adjusted = Number(estimateData?.totals?.adjustments) || 0;
  const additional = Number(estimateData?.totals?.additional) || 0;

  // Final hours = Estimator (DOM) + Adjustments + Additional
  const finalTotal = domBase + adjusted + additional;

  // Paint the three hour fields
  const adjustedElement = document.getElementById("summaryAdjustedHours");
  const additionalElement = document.getElementById("summaryAdditionalHours");
  const totalElement = document.getElementById("summaryTotalHours");
  if (adjustedElement) adjustedElement.innerText = adjusted.toFixed(2);
  if (additionalElement) additionalElement.innerText = additional.toFixed(2);
  if (totalElement) totalElement.innerText = finalTotal.toFixed(2);

  // Labor $ = final hours × laborRate
  const laborRate = Number(estimateData?.totals?.laborRate) || 0;
  const laborCost = finalTotal * laborRate;
  const laborCostElement = document.getElementById("summaryTotalLaborCost");
  if (laborCostElement) laborCostElement.innerText = formatUSD(laborCost);

  // Mirror the authoritative Estimator hours back into storage so nothing stale survives
  if (!estimateData.totals) estimateData.totals = {};
  estimateData.totals.estimated = domBase;
  if (typeof saveEstimateData === "function") saveEstimateData();
}

// S3-01 — strip $ and commas from currency text → number
function __eeParseCurrency(text) {
  if (!text) return 0;
  const n = Number(String(text).replace(/[^0-9.-]/g, ""));
  return Number.isFinite(n) ? n : 0;
}

function renderDJEFromStorage() {
  try { loadEstimateData?.(); } catch { }
  const n = Number(estimateData?.costs?.dje) || 0;
  const el = document.getElementById("djeValue");
  if (el) el.innerText = formatUSD(n);
}

function updateStepCMaterialSummary() {
  // base = numeric value from "#material-cost-price-sheet"
  const base = __eeParseCurrency(document.getElementById("material-cost-price-sheet")?.innerText || "");

  const miscPercent = parseInt(document.querySelector("select[name='misc_percent']").value) || 0;
  const smallToolsPercent = parseInt(document.querySelector("select[name='small_tools_percent']").value) || 0;
  const largeToolsPercent = parseInt(document.querySelector("select[name='large_tools_percent']").value) || 0;
  const wasteTheftPercent = parseInt(document.querySelector("select[name='waste_theft_percent']").value) || 0;
  const salesTaxPercent = parseInt(document.querySelector("select[name='sales_tax_percent']").value) || 0;

  const misc = (miscPercent / 100) * base;
  const smallTools = (smallToolsPercent / 100) * base;
  const largeTools = (largeToolsPercent / 100) * base;
  const wasteTheft = (wasteTheftPercent / 100) * base;

  const taxable = base + misc + smallTools + largeTools + wasteTheft;
  const salesTax = (salesTaxPercent / 100) * taxable;
  const totalMaterial = taxable + salesTax;

  document.getElementById("miscMaterialValue").innerText = formatUSD(misc);
  document.getElementById("smallToolsValue").innerText = formatUSD(smallTools);
  document.getElementById("largeToolsValue").innerText = formatUSD(largeTools);
  document.getElementById("wasteTheftValue").innerText = formatUSD(wasteTheft);
  document.getElementById("taxableMaterialValue").innerText = formatUSD(taxable);
  document.getElementById("salesTaxValue").innerText = formatUSD(salesTax);
  document.getElementById("totalMaterialCostValue").innerText = formatUSD(totalMaterial);

  // Prime cost
  const laborCost = parseFloat(document.getElementById("summaryTotalLaborCost").innerText.replace(/[^0-9.]/g, "")) || 0;
  const djeText = document.getElementById("djeValue")?.innerText || "$0.00";
  const dje = __eeParseCurrency(djeText);
  const primeCost = laborCost + totalMaterial + dje;
  document.getElementById("primeCostValue").innerText = formatUSD(primeCost);

  // Overhead percent: persisted value (authoritative), fallback to dropdown
  const overheadSelect = document.getElementById("overheadPercentSelect");
  const overheadPercent =
    typeof estimateData?.materials?.overhead_percent === "number"
      ? estimateData.materials.overhead_percent
      : (parseInt(overheadSelect?.value, 10) || 30);

  const overheadCost = (overheadPercent / 100) * primeCost;
  document.getElementById("overheadValue").innerText = formatUSD(overheadCost);

  // Break-even
  const breakEven = primeCost + overheadCost;
  document.getElementById("breakEvenValue").innerText = formatUSD(breakEven);

  // Margin / markup
  const marginPercent = parseInt(document.querySelector("select[name='margin_percent']").value) || 0;
  const markupMultiplier = marginToMarkup[marginPercent] ?? 1;
  document.getElementById("markupValue").innerText = `${(markupMultiplier * 100 - 100).toFixed(2)}%`;

  const profitValue = breakEven * (markupMultiplier - 1);
  document.getElementById("profitMarginValue").innerText = formatUSD(profitValue);

  const estimatedSalesPrice = breakEven + profitValue;
  document.getElementById("estimatedSalesPriceValue").innerText = formatUSD(estimatedSalesPrice);

  // Labor-day views
  const estimated = estimateData?.totals?.estimated ?? 0;
  const adjusted = estimateData?.totals?.adjustments ?? 0;
  const additional = estimateData?.totals?.additional ?? 0;
  const finalTotal = estimated + adjusted + additional;

  const oneMan = finalTotal / 8;
  const twoMan = oneMan / 2;
  const fourMan = twoMan / 2;

  document.getElementById("oneManDays").innerText = formatDays(oneMan);
  document.getElementById("twoManDays").innerText = formatDays(twoMan);
  document.getElementById("fourManDays").innerText = formatDays(fourMan);
}

// ---- S2-05: Summary live sync (paint + recalc) ----
function syncSummaryFromStorage() {
  // 1) Paint Estimator's totals (hours/material) into the two display spans
  if (typeof renderEstimatorTotalsFromLocalStorage === "function") {
    try { renderEstimatorTotalsFromLocalStorage(); } catch (_) { }
  }
  // 2) Recompute Summary's totals/costs using your existing logic
  if (typeof updateSummaryTotals === "function") {
    try { updateSummaryTotals(); } catch (_) { }
  }
  // 3) If you have any step C material summary routine, trigger it too
  if (typeof updateStepCMaterialSummary === "function") {
    try { updateStepCMaterialSummary(); } catch (_) { }
  }
}

// On page load, tab focus, and cross-tab storage updates
document.addEventListener("DOMContentLoaded", syncSummaryFromStorage);
document.addEventListener("visibilitychange", () => { if (!document.hidden) syncSummaryFromStorage(); });
window.addEventListener("storage", (e) => {
  const k = e.key || '';
  if (k === TOTALS_KEY || k === __ED_KEY) syncSummaryFromStorage();
});


/*
function resetAllFromSummary() {
  // canonical zero payloads
  const zeroTotals = {
    material_cost_price_sheet: 0,
    labor_hours_pricing_sheet: 0
  };
  const zeroEstimate = {
    adjustments: [],
    additionalLabor: [],
    costs: { dje: 0 },
    totals: { estimated: 0, adjustments: 0, additional: 0, final: 0, laborRate: 0 },
    materials: {
      misc_percent: 10, small_tools_percent: 5, large_tools_percent: 3,
      waste_theft_percent: 10, sales_tax_percent: 8, overhead_percent: 30,
      margin_percent: 0
    }
  };

  // write zeros (don’t remove; just overwrite)
  localStorage.setItem('ee.totals', JSON.stringify(zeroTotals));
  localStorage.setItem('estimateData', JSON.stringify(zeroEstimate));

  // make next loads start fresh in this tab too
  try { sessionStorage.removeItem('ee.session.booted'); } catch { }

  // hard reload this page so UI paints from clean storage (no bfcache surprises)
  location.replace(location.pathname + '?reset=' + Date.now());
}
*/

// === wire Reset button + do a hard reset (use App Settings, not factory defaults) ===
(function () {
  function eeResetAll() {
    // Saved estimates: do nothing (button will be disabled anyway)
    var eid = new URLSearchParams(window.location.search).get('eid');
    if (eid) return;

    // FAST (unsaved) reset: clear only fast working state and signal other pages
    try { localStorage.removeItem('ee.FAST.grid.v1'); } catch (_) {}
    try { localStorage.removeItem('ee.FAST.totals'); } catch (_) {}
    try { localStorage.removeItem('ee.FAST.estimateData'); } catch (_) {}
    try { localStorage.setItem('ee.reset', String(Date.now())); } catch (_) {}

    // Reload Summary — other pages will hydrate clean on next visit
    try { sessionStorage.setItem(EE_RESET_FLAG, '1'); } catch (_) {}
    location.reload();
  }

  // Expose + bind
  window.eeResetAll = eeResetAll;
  window.App = window.App || {};
  if (typeof window.App.resetAll !== 'function') window.App.resetAll = window.eeResetAll;

  function bindResetButton() {
    const btn = document.getElementById('resetAllBtn');
    if (btn) btn.onclick = eeResetAll;
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindResetButton);
  } else {
    bindResetButton();
  }
})();


// S3-02c — Summary listeners (refresh header cells from storage)

// helper: refresh just the two header cells
function __ee_refreshSummaryHeaderFromStorage() {
  try {
    // Estimator writes the header payload to 'ee.totals'
    const raw = localStorage.getItem(TOTALS_KEY);
    const t = raw ? JSON.parse(raw) : null;

    // Labor Hours header
    const hrsEl = document.getElementById('labor-hours-pricing-sheet');
    if (hrsEl) {
      const hrs = t && typeof t.labor_hours_pricing_sheet === 'number'
        ? t.labor_hours_pricing_sheet
        : 0;
      // keep your formatting consistent; fall back to .toFixed(2)
      hrsEl.textContent =
        (typeof window.roundHours === 'function')
          ? Number(window.roundHours(hrs)).toFixed(2)
          : Number(hrs).toFixed(2);
    }

    // Material Cost header
    const matEl = document.getElementById('material-cost-price-sheet');
    if (matEl) {
      const amt = t && typeof t.material_cost_price_sheet === 'number'
        ? t.material_cost_price_sheet
        : 0;
      const fmt = (typeof window.formatUSD === 'function')
        ? window.formatUSD
        : (n => `$${(Number(n) || 0).toFixed(2)}`);
      matEl.textContent = fmt(amt);
    }
  } catch (e) {
    console.warn('S3-02c: summary header refresh failed', e);
  }
}

// listen for estimator + dje changes (safe no-ops if bus not present)
window.ee && window.ee.on && window.ee.on('ee:totalsChanged', () => {
  __ee_refreshSummaryHeaderFromStorage();
});

window.ee && window.ee.on && window.ee.on('ee:djeChanged', () => {
  __ee_refreshSummaryHeaderFromStorage();
});

// Disable Summary "Reset All" when estimate is saved (eid present)
(function () {
  try {
    var eid = new URLSearchParams(window.location.search).get('eid');
    if (!eid) return; // Fast mode: keep clickable

    function disable(el) {
      if (!el) return;
      el.setAttribute('disabled', 'disabled');
      el.classList.add('disabled');
      el.setAttribute('aria-disabled', 'true');
      el.style.pointerEvents = 'none';
      var href = el.getAttribute('href');
      if (href) { el.setAttribute('data-href-disabled', href); el.removeAttribute('href'); }
    }

    // Likely candidates: element wired to eeResetAll, or common ids/attrs you use
    var nodes = document.querySelectorAll(
      '[onclick*="eeResetAll"], #resetAllBtn, [data-reset="all"], [data-action="reset-all"]'
    );
    nodes.forEach(disable);
  } catch (_) {}
})();


