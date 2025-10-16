// app/static/js/materials.index.js
(function () {
  function val(id) { const el = document.getElementById(id); return el ? el.value : ""; }
  function checked(id) { const el = document.getElementById(id); return !!(el && el.checked); }
  function setVal(id, v) { const el = document.getElementById(id); if (el) el.value = v; }
  function setSelect(id, v) { const el = document.getElementById(id); if (el) el.value = v; }

  function serializePayload() {
    return {
      material_type: val("materialType").trim(),
      item_description: val("mat_desc").trim(),
      sku: val("mat_sku").trim(),
      manufacturer: val("mat_mfr").trim(),
      vendor: val("mat_vendor").trim(),
      price: val("mat_price"),
      labor_unit: val("mat_labor"),
      unit_quantity_size: val("mat_uqs"),
      material_cost_code: val("mat_mcc").trim(),
      mat_cost_code_desc: val("mat_mccd").trim(),
      labor_cost_code: val("mat_lcc").trim(),
      labor_cost_code_desc: val("mat_lccd").trim(),
      is_active: checked("mat_active"),
    };
  }

  async function createMaterial(payload) {
    const res = await fetch("/libraries/materials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      // CSRF header is already attached globally in main.js
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err && err.errors ? JSON.stringify(err.errors) : "Failed to add material.";
      throw new Error(msg);
    }
    return res.json();
  }

  function resetForm(keepCategory) {
    const currentType = val("materialType");
    // clear all inputs
    setVal("mat_desc", "");
    setVal("mat_sku", "");
    setVal("mat_mfr", "");
    setVal("mat_vendor", "");
    setVal("mat_price", "");
    setVal("mat_labor", "");
    setSelect("mat_uqs", "");
    setVal("mat_mcc", "");
    setVal("mat_mccd", "");
    setVal("mat_lcc", "");
    setVal("mat_lccd", "");
    const active = document.getElementById("mat_active");
    if (active) active.checked = true;

    if (keepCategory) {
      setSelect("materialType", currentType);
    } else {
      setSelect("materialType", "");
    }
    // focus first field
    const cat = document.getElementById("materialType");
    if (cat) cat.focus();
  }

  async function onAdd(keepCategory) {
    // Required field quick checks (client-side guardrails)
    const cat = val("materialType");
    const desc = val("mat_desc");
    const price = val("mat_price");
    const labor = val("mat_labor");
    const uqs = val("mat_uqs");

    const errors = [];
    if (!cat) errors.push("Category");
    if (!desc) errors.push("Description");
    if (!price) errors.push("Price");
    if (!labor) errors.push("Labor Unit");
    if (!uqs) errors.push("Unit Qty Size");
    if (["1","100","1000"].indexOf(uqs) === -1) errors.push("Unit Qty Size must be 1, 100, or 1000");

    if (errors.length) {
      alert("Please complete: " + errors.join(", "));
      return;
    }

    const payload = serializePayload();
    try {
      const { ok, id } = await createMaterial(payload);
      if (!ok || !id) throw new Error("Unexpected response");

      // Optional: reset before redirect only if you actually stay on the page.
      // With a redirect, this isn't necessary, but keeping your existing intent:
      resetForm(!!keepCategory);

      // Redirect so server re-renders list and we can highlight the new row
      window.location.href = `/libraries/materials`;
    } catch (e) {
      alert(e.message || "Failed to add material.");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    const addBtn = document.getElementById("materialsAddBtn");
    const addContBtn = document.getElementById("materialsAddContinueBtn");
    if (addBtn) addBtn.addEventListener("click", () => onAdd(false), { passive: true });
    if (addContBtn) addContBtn.addEventListener("click", () => onAdd(true), { passive: true });
  });
})();

