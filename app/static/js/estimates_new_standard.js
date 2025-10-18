// app/static/js/estimates_new_standard.js
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
