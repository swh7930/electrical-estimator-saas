// ===== markup ↔ margin conversion =====
const marginToMarkup = {};
for (let i = 1; i <= 25; i++) marginToMarkup[i] = +(1 / (1 - i / 100)).toFixed(2);
[30, 40, 50].forEach(i => (marginToMarkup[i] = +(1 / (1 - i / 100)).toFixed(2)));
marginToMarkup[100] = 200.0;

document.addEventListener("DOMContentLoaded", () => {
  // Pull Estimator header totals into Summary placeholders
  renderEstimatorTotalsFromLocalStorage();

  loadEstimateData(); // Load from localStorage

  renderDJEFromStorage();


  // ---------- DEFAULTS (materials adders only; no margin/overhead here) ----------
  const defaultMaterials = {
    misc_percent: 10,
    small_tools_percent: 5,
    large_tools_percent: 3,
    waste_theft_percent: 10,
    sales_tax_percent: 8
  };

  const materials = estimateData.materials || {};
  const allZero =
    Object.keys(materials).length > 0 &&
    Object.values(materials).every((val) => val === 0);

  if (!estimateData.materials || allZero) {
    estimateData.materials = { ...defaultMaterials };
    saveEstimateData();
  }

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
    const raw = localStorage.getItem("ee.totals");
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
  if (e.key === "ee.totals" || e.key === "estimateData") syncSummaryFromStorage();
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
// === wire Reset button + do a hard reset (tiny, self-contained) ===
(function () {
  function eeResetAll() {
    // canonical zero payloads
    localStorage.setItem('ee.totals', JSON.stringify({
      material_cost_price_sheet: 0,
      labor_hours_pricing_sheet: 0
    }));
    localStorage.setItem('estimateData', JSON.stringify({
      adjustments: [],
      additionalLabor: [],
      costs: { dje: 0 },
      totals: { estimated: 0, adjustments: 0, additional: 0, final: 0, laborRate: 0 },
      materials: {
        misc_percent: 10, small_tools_percent: 5, large_tools_percent: 3,
        waste_theft_percent: 10, sales_tax_percent: 8, overhead_percent: 30,
        margin_percent: 0
      }
    }));

    // ensure this tab starts fresh next load
    try { sessionStorage.removeItem('ee.session.booted'); } catch { }

    // S3-02a — notify listeners that a global reset is happening (pre-reload)
    if (window.ee && typeof window.ee.fire === 'function') {
      window.ee.fire('ee:resetAll', { source: 'summary' });
    }

    // repaint immediately (same tab never gets a 'storage' event)
    location.reload();
  }

  // expose globally for safety (works even if markup adds onclick="")
  window.eeResetAll = eeResetAll;

  window.App = window.App || {};
  if (typeof window.App.resetAll !== 'function') {
    window.App.resetAll = window.eeResetAll;
  }

  // bind safely whether the script loads before or after the button
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
    const raw = localStorage.getItem('ee.totals');
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



