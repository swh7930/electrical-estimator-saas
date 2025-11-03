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
      window.location.href = `/libraries/materials` + window.location.search;
    } catch (e) {
      alert(e.message || "Failed to add material.");
    }
  }

  // --- “+ New Category” support (Materials) ---
  const NEW_SENTINEL = '__new__';

  // Modal refs
  const matNewCatModalEl = document.getElementById('matNewCategoryModal');
  const matNewCatModal = matNewCatModalEl ? bootstrap.Modal.getOrCreateInstance(matNewCatModalEl) : null;
  const matNewCatInput = document.getElementById('matNewCategoryInput');
  const matNewCatError = document.getElementById('matNewCategoryError');

  function showInlineError(el, msgs) {
    if (!el) return;
    const arr = Array.isArray(msgs) ? msgs : [String(msgs || 'Unknown error')];
    el.classList.remove('d-none');
    el.innerHTML = arr.map(m => `<div>${m}</div>`).join('');
  }
  function clearInlineError(el) {
    if (!el) return;
    el.classList.add('d-none');
    el.innerHTML = '';
  }
  function addNewMaterialCategory(sel, name) {
    const exists = Array.from(sel.options)
      .some(o => o.value && o.value !== NEW_SENTINEL && o.value.toLowerCase() === name.toLowerCase());
    if (exists) { showInlineError(matNewCatError, 'That category already exists.'); return false; }
    const sentinelIdx = Array.from(sel.options).findIndex(o => o.value === NEW_SENTINEL);
    sel.add(new Option(name, name), sentinelIdx > -1 ? sentinelIdx : null);
    sel.value = name;
    return true;
  }

  document.addEventListener("DOMContentLoaded", function () {
        var meta = document.querySelector('meta[name="x-can-write"]');
    var CAN_WRITE = !!(meta && meta.content === '1');
    if (!CAN_WRITE) {
      var scope = document.getElementById('materials-grid') || document;
      scope.querySelectorAll('input, select, textarea, button').forEach(function (el) {
        el.setAttribute('disabled', 'disabled');
        el.setAttribute('aria-disabled', 'true');
      });
      return; // skip binding Add/Edit/Delete handlers
    }

    const addBtn = document.getElementById("materialsAddBtn");
    const addContBtn = document.getElementById("materialsAddContinueBtn");
    const resetBtn = document.getElementById("materialsResetBtn");
    if (addBtn) addBtn.addEventListener("click", () => onAdd(false), { passive: true });
    if (addContBtn) addContBtn.addEventListener("click", () => onAdd(true), { passive: true });
    if (resetBtn) resetBtn.addEventListener("click", () => resetForm(false), { passive: true });
    // Wire “+ New category…” sentinel
    const catSel = document.getElementById('materialType');
    const matNewCatConfirm = document.getElementById('matNewCategoryConfirmBtn');

    catSel?.addEventListener('change', () => {
      if (catSel.value === NEW_SENTINEL) {
        clearInlineError(matNewCatError);
        if (matNewCatInput) matNewCatInput.value = '';
        matNewCatModal?.show();
      }
    });

    matNewCatConfirm?.addEventListener('click', () => {
      const name = (matNewCatInput?.value || '').trim();
      if (!name) { showInlineError(matNewCatError, 'Name is required.'); return; }
      const ok = addNewMaterialCategory(catSel, name);
      if (ok) matNewCatModal?.hide();
    });

    matNewCatModalEl?.addEventListener('hidden.bs.modal', () => {
      // If user cancels, reset sentinel selection
      if (catSel?.value === NEW_SENTINEL) catSel.value = '';
    });
  });

  // --- Delete flow (open modal, confirm, DELETE, remove row) ---
  document.addEventListener("click", (e) => {
    const btn = e.target.closest('[data-action="delete-material"]');
    if (!btn) return;

    const id = btn.getAttribute("data-material-id");
    const modalEl = document.getElementById("confirmDeleteModal");
    const confirmBtn = modalEl.querySelector("#confirmDeleteBtn");
    confirmBtn.dataset.materialId = id;

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  });

  document.addEventListener("click", async (e) => {
    const confirmBtn = e.target.closest("#confirmDeleteBtn");
    if (!confirmBtn) return;

    const id = confirmBtn.dataset.materialId;
    if (!id) return;

    confirmBtn.disabled = true;
    try {
      const res = await fetch(`/libraries/materials/${id}`, { method: "DELETE" });
      if (res.status !== 204) {
        let msg = "Failed to delete material.";
        try {
          const j = await res.json();
          msg = (j && (j.message || j.error)) || (j && j.errors && (j.errors.__all__ || Object.values(j.errors)[0])) || msg;
        } catch (_) {}
        throw new Error(msg);
      }

      // Remove the row
      const row = document.getElementById(`mat-${id}`);
      if (row) row.remove();

      // Hide modal
      const modalEl = document.getElementById("confirmDeleteModal");
      bootstrap.Modal.getInstance(modalEl)?.hide();
    } catch (err) {
      alert(err.message || "Failed to delete material.");
    } finally {
      confirmBtn.disabled = false;
    }
  });

  // --- Edit flow (open modal, prefill, save via PUT) ---
  document.addEventListener("click", (e) => {
    const btn = e.target.closest('[data-action="edit-material"]');
    if (!btn) return;

    const id = btn.getAttribute("data-material-id");
    const modalEl = document.getElementById("materialEditModal");
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

    // Prefill — use modal IDs (edit_*)
    setVal("edit_materialType", btn.dataset.type || "");
    setVal("edit_desc", btn.dataset.desc || "");
    setVal("edit_sku", btn.dataset.sku || "");
    setVal("edit_mfr", btn.dataset.mfr || "");
    setVal("edit_vendor", btn.dataset.vendor || "");
    const _price = btn.dataset.price || "";
    const _labor = btn.dataset.labor || "";
    setVal("edit_price", _price === "" ? "" : toTwoDecimals(_price));
    setVal("edit_labor", _labor === "" ? "" : toTwoDecimals(_labor));
    setSelect("edit_uqs", btn.dataset.uqs || "");
    setVal("edit_mcc", btn.dataset.mcc || "");
    setVal("edit_mccd", btn.dataset.mccd || "");
    setVal("edit_lcc", btn.dataset.lcc || "");
    setVal("edit_lccd", btn.dataset.lccd || "");
    const active = document.getElementById("edit_active");
    if (active) active.checked = btn.dataset.active === "1";

    // Stash id on Save button
    const saveBtn = document.getElementById("materialEditSaveBtn");
    saveBtn.dataset.materialId = id;

    modal.show();
  });

  document.addEventListener("click", async (e) => {
    const saveBtn = e.target.closest("#materialEditSaveBtn");
    if (!saveBtn) return;

    const id = saveBtn.dataset.materialId;
    if (!id) return;

    // Build payload using backend keys
    const payload = {
      item_description: val("edit_desc").trim(),
      sku: val("edit_sku").trim(),
      manufacturer: val("edit_mfr").trim(),
      vendor: val("edit_vendor").trim(),
      price: parseFloat(val("edit_price")),
      labor_unit: parseFloat(val("edit_labor")),
      unit_quantity_size: parseInt(val("edit_uqs"), 10),
      material_cost_code: val("edit_mcc").trim(),
      mat_cost_code_desc: val("edit_mccd").trim(),
      labor_cost_code: val("edit_lcc").trim(),
      labor_cost_code_desc: val("edit_lccd").trim(),
      is_active: checked("edit_active"),
    };

    // Minimal client-side sanity (optional)
    if (!payload.item_description) return alert("Description is required.");
    if (![1,100,1000].includes(payload.unit_quantity_size)) return alert("Unit Qty Size must be 1, 100, or 1000.");

    saveBtn.disabled = true;
    try {
      const res = await fetch(`/libraries/materials/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const msg = (err && (err.message || err.error)) || (err && err.errors && (err.errors.__all__ || Object.values(err.errors)[0])) || "Failed to update material.";
        throw new Error(msg);
      }
      // Close modal and do a clean reload (keeps list rendering consistent)
      bootstrap.Modal.getInstance(document.getElementById("materialEditModal"))?.hide();
      window.location.href = `/libraries/materials` + window.location.search;
    } catch (err) {
      alert(err.message || "Failed to update material.");
    } finally {
      saveBtn.disabled = false;
    }
  });

  // --- Numeric formatting helpers (local to this page) ---
    function toTwoDecimals(n) {
      const x = parseFloat(n);
      return Number.isFinite(x) ? x.toFixed(2) : "";
    }
    function clampTwoDecimalsInput(el) {
      // keep at most 2 decimals while typing
      const m = String(el.value).match(/^(\d+)(?:\.(\d{0,2}))?/);
      if (m) el.value = m[2] !== undefined ? `${m[1]}.${m[2]}` : m[1];
    }

    // Inline Add: format on blur
    document.getElementById("mat_price")?.addEventListener("blur", (e) => {
      e.target.value = toTwoDecimals(e.target.value);
    });
    document.getElementById("mat_labor")?.addEventListener("input", (e) => {
      clampTwoDecimalsInput(e.target);
    });
    document.getElementById("mat_labor")?.addEventListener("blur", (e) => {
      e.target.value = toTwoDecimals(e.target.value);
    });

    // Edit modal: format on blur / restrict decimals
    document.getElementById("edit_price")?.addEventListener("blur", (e) => {
      e.target.value = toTwoDecimals(e.target.value);
    });
    document.getElementById("edit_labor")?.addEventListener("input", (e) => {
      clampTwoDecimalsInput(e.target);
    });
    document.getElementById("edit_labor")?.addEventListener("blur", (e) => {
      e.target.value = toTwoDecimals(e.target.value);
    });
})();

// -- Back link (query-param handshake) --
(() => {
  const el = document.getElementById('materialsBackLink');
  if (!el) return;
  el.addEventListener('click', (e) => {
    e.preventDefault();
    const rt = el.dataset.rt || '';
    const href = el.dataset.href || '';
    if (rt.startsWith('estimator')) {
      if (document.referrer && (document.referrer.includes('/estimator') || document.referrer.includes('/estimates'))) {
        history.back(); return;
      }
      if (href) window.location.assign(href);
      return;
    }
    if (href) window.location.assign(href);
  });
})();
