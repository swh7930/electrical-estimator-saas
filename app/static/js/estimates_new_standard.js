document.addEventListener("DOMContentLoaded", () => {
  fetch("/admin/settings.json")
    .then(r => r.ok ? r.json() : {})
    .then(data => {
      const s = data.settings || {};
      const p = s.pricing || {};
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = `${v}%`; };

      if (Number.isFinite(p.overhead_percent)) set("previewOverhead", p.overhead_percent);
      if (Number.isFinite(p.margin_percent))   set("previewMargin",  p.margin_percent);
      if (Number.isFinite(p.sales_tax_percent))set("previewTax",     p.sales_tax_percent);
      if (Number.isFinite(p.misc_percent))        set("previewMisc",      p.misc_percent);
      if (Number.isFinite(p.small_tools_percent)) set("previewSmallTools",p.small_tools_percent);
      if (Number.isFinite(p.large_tools_percent)) set("previewLargeTools",p.large_tools_percent);
    })
    .catch(() => {});
});

// -- Create & Open Estimator (Phase 3) --
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
      customer_id: (function () {
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
      // Soft-fail: keep console clean; UI is minimal at this step
      console.error(e);
    }
  });
})();
