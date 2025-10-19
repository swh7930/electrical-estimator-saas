document.addEventListener("DOMContentLoaded", () => {
  // Populate Estimator Defaults preview from Admin Settings
  fetch("/admin/settings.json")
    .then(r => r.ok ? r.json() : {})
    .then(data => {
      const s = (data && data.settings) || {};
      const p = s.pricing || {};

      const setText = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
      const setPct  = (id, v) => { if (Number.isFinite(v)) setText(id, `${v}%`); };

      if (Number.isFinite(p.labor_rate))       setText("previewLaborRate", `$${Number(p.labor_rate).toFixed(2)}/hr`);
      setPct("previewOverhead",        p.overhead_percent);
      setPct("previewMargin",          p.margin_percent);
      setPct("previewTax",             p.sales_tax_percent);
      setPct("previewMisc",            p.misc_percent);
      setPct("previewSmallTools",      p.small_tools_percent);
      setPct("previewLargeTools",      p.large_tools_percent);
      setPct("previewWaste",           p.waste_theft_percent);
    })
    .catch(() => {});

  // Populate Customer dropdown (active only)
  (async function loadCustomers() {
    const sel = document.getElementById("customerSelect");
    if (!sel) return;
    try {
      const res  = await fetch("/libraries/customers.json?active=true");
      const json = await res.json();
      const rows = (json && json.rows) || [];
      // keep first "Choose customer…" option
      sel.innerHTML = '<option value="">Choose customer…</option>';
      for (const c of rows) {
        const opt = document.createElement("option");
        opt.value = String(c.id);
        opt.textContent = c.company_name || "(unnamed)";
        sel.appendChild(opt);
      }
    } catch (_) { /* no-op */ }
  })();
});

// -- Create (Phase 3) --
(() => {
  const btn = document.getElementById("createEstimateBtn");
  if (!btn) return;

  const val = (id) => {
    const el = document.getElementById(id);
    return (el && (el.value || "").trim()) || "";
  };

  btn.addEventListener("click", async () => {
    const payload = {
      name: val("estimateName"),
      project_address: val("projectAddress"),
      project_ref: val("projectRef"),
      customer_id: (() => {
        const s = document.getElementById("customerSelect");
        if (!s) return null;
        const v = (s.value || "").trim();
        return /^\d+$/.test(v) ? Number(v) : null;
      })(),
    };

    if (!payload.name) {
      document.getElementById("estimateName")?.focus();
      return;
    }

    try {
      const res = await fetch("/estimates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Create failed.");
      const data = await res.json();
      const eid = data && data.id;
      if (eid) {
        window.location.assign(`/estimator?eid=${eid}&rt=estimates`);
      }
    } catch (e) {
      console.error(e);
    }
  });
})();
