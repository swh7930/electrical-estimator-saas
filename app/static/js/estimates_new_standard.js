document.addEventListener("DOMContentLoaded", () => {
  const $ = (id) => document.getElementById(id);

  // --------- Mode & ID from URL (no inline data) ---------------------------
  const m = location.pathname.match(/^\/estimates\/(\d+)\/(edit|clone)$/);
  const MODE = m ? m[2] : "create";
  const ESTIMATE_ID = m ? Number(m[1]) : null;

  // --------- Elements ------------------------------------------------------
  const btnPrimary = $("createEstimateBtn");
  const customerSelect = $("customerSelect");

  // --------- Helpers -------------------------------------------------------
  const setText = (id, text) => { const el = $(id); if (el) el.textContent = text; };
  const setPct = (id, v) => { if (Number.isFinite(v)) setText(id, `${v}%`); };
  const val = (id) => (($(id)?.value) || "").trim();

  function applyDefaultsFrom(pricing) {
    if (!pricing || typeof pricing !== "object") return;
    if (Number.isFinite(pricing.labor_rate)) setText("previewLaborRate", `$${Number(pricing.labor_rate).toFixed(2)}/hr`);
    setPct("previewOverhead",     pricing.overhead_percent);
    setPct("previewMargin",       pricing.margin_percent);
    setPct("previewTax",          pricing.sales_tax_percent);
    setPct("previewMisc",         pricing.misc_percent);
    setPct("previewSmallTools",   pricing.small_tools_percent);
    setPct("previewLargeTools",   pricing.large_tools_percent);
    setPct("previewWaste",        pricing.waste_theft_percent);
  }

  async function fetchAdminSettingsAndApply() {
    try {
      const res = await fetch("/admin/settings.json");
      const data = await res.json();
      applyDefaultsFrom((data && data.settings && data.settings.pricing) || {});
    } catch (_) {}
  }

  async function loadCustomers(selectedId) {
    if (!customerSelect) return;
    try {
      const res = await fetch("/libraries/customers.json?active=true");
      const json = await res.json();
      const rows = (json && json.rows) || [];
      customerSelect.innerHTML = '<option value="">Choose customer…</option>';
      for (const c of rows) {
        const opt = document.createElement("option");
        opt.value = String(c.id);
        opt.textContent = c.company_name || "(unnamed)";
        customerSelect.appendChild(opt);
      }
      if (selectedId) customerSelect.value = String(selectedId);
    } catch (_) {}
  }

  function payloadFromForm() {
    const cid = (customerSelect && customerSelect.value) || "";
    return {
      name: val("estimateName"),
      project_address: val("projectAddress"),
      project_ref: val("projectRef"),
      customer_id: /^\d+$/.test(cid) ? Number(cid) : null,
    };
  }

  // --------- Create / Save handlers ---------------------------------------
  async function handleCreate() {
    const data = payloadFromForm();
    if (!data.name) { $("estimateName")?.focus(); return; }
    try {
      const res = await fetch("/estimates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Create failed");
      const json = await res.json();
      if (json && json.id) window.location.assign(`/estimator?eid=${json.id}&rt=estimates`);
    } catch (e) {
      console.error(e); alert("Create failed.");
    }
  }

  async function handleSave(estimateId) {
    const data = payloadFromForm();
    if (!data.name) { $("estimateName")?.focus(); return; }
    try {
      const res = await fetch(`/estimates/${estimateId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Save failed");
      // Stay on page; user can click "Back to Estimator" or navigate away
    } catch (e) {
      console.error(e); alert("Save failed.");
    }
  }

  // --------- Init per mode -------------------------------------------------
  if (MODE === "create") {
    // Start Standard Estimate
    fetchAdminSettingsAndApply();
    loadCustomers(null);
    btnPrimary?.addEventListener("click", handleCreate);
    return;
  }

  // EDIT / CLONE
  (async function initEditOrClone() {
    try {
      const res = await fetch(`/estimates/${ESTIMATE_ID}.json`);
      if (!res.ok) throw new Error("Load failed");
      const ctx = await res.json();

      // Defaults preview: prefer snapshot from the estimate
      const pricingFromSnap = ctx && ctx.settings_snapshot && ctx.settings_snapshot.pricing;
      if (pricingFromSnap) applyDefaultsFrom(pricingFromSnap);
      else await fetchAdminSettingsAndApply();

      // Prefill fields
      const setVal = (id, v) => { const el = $(id); if (el) el.value = v || ""; };
      setVal("estimateName", ctx.name || "");
      setVal("projectAddress", ctx.project_address || "");
      setVal("projectRef", ctx.project_ref || "");

      await loadCustomers(ctx.customer_id || null);

      if (MODE === "edit") {
        btnPrimary?.addEventListener("click", () => handleSave(ESTIMATE_ID));
      } else {
        // CLONE: require a NEW name
        const originalName = ctx.name || "";
        btnPrimary?.addEventListener("click", () => {
          const data = payloadFromForm();
          if (!data.name) { $("estimateName")?.focus(); return; }
          if (data.name === originalName) {
            $("estimateName")?.focus();
            $("estimateName")?.select?.();
            alert("Please choose a NEW name for the cloned estimate before creating.");
            return;
          }
          // create new from edited details
          handleCreate();
        });
      }
    } catch (e) {
      console.error(e);
      alert("Failed to load estimate.");
    }
  })();
});

