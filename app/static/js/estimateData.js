// DEV: start each new browser tab with a blank estimate (wipe once per tab session)
(function () {
    const FLAG = "ee.session.booted";
    if (!sessionStorage.getItem(FLAG)) {
        ["ee.grid.v1", "ee.totals", "estimateData"].forEach(k => localStorage.removeItem(k));
        sessionStorage.setItem(FLAG, "1");
    }
})();

let estimateData = {
    adjustments: [],            // From Labor-Unit Adjustments table
    additionalLabor: [],        // From Additional Labor table
    totals: {
        estimated: 0.0,           // Base estimated labor hours
        adjustments: 0.0,         // From % or manual hrs
        additional: 0.0,          // Manually entered
        final: 0.0                // Sum of all
    },
    created: new Date().toISOString()
};

estimateData.materials = {
    misc_percent: 0,
    small_tools_percent: 0,
    large_tools_percent: 0,
    waste_theft_percent: 0,
    sales_tax_percent: 0,
    margin_percent: 0
};

// Load from localStorage if it exists
const loadEstimateData = () => {
    const saved = localStorage.getItem("estimateData");
    if (saved) {
        estimateData = JSON.parse(saved);
    }
};

// Save current state to localStorage
const saveEstimateData = () => {
    localStorage.setItem("estimateData", JSON.stringify(estimateData));
};

// --- Shared currency helpers (global, idempotent) ---
window.usd = window.usd || new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
window.formatUSD = window.formatUSD || (v => window.usd.format(Number(v) || 0));
window.parseUSD = window.parseUSD || (s => {
    const n = Number(String(s ?? '').replace(/[^0-9.-]/g, ''));
    return Number.isFinite(n) ? n : 0;
});

// --- S3-02a: global event helpers (idempotent; safe to load last) ---
window.ee = window.ee || {};
if (typeof window.ee.fire !== 'function') {
    window.ee.fire = function (name, detail = {}) {
        try { window.dispatchEvent(new CustomEvent(name, { detail })); }
        catch (e) { console.warn('ee.fire failed:', name, e); }
    };
}
if (typeof window.ee.on !== 'function') {
    window.ee.on = function (name, handler, opts) {
        try { window.addEventListener(name, handler, opts); }
        catch (e) { console.warn('ee.on failed:', name, e); }
    };
}
