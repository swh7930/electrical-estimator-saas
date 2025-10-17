(() => {
  const $ = (id) => document.getElementById(id);

  const catSel = $('djeCategory');
  const subSel = $('djeSubcategory');

  const descEl = $('djeDesc');
  const unitCostEl = $('unitCost');
  const costCodeEl = $('costCode');
  const isActiveEl = $('isActive');
  const addErrorsEl = $('addDjeErrors');

  const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
  const NEW_SENTINEL = '__new__';

  // New Category/Subcategory modal refs (from previous step)
  const newCatModalEl = $('djeNewCatalogModal');
  const newCatModal = newCatModalEl ? new bootstrap.Modal(newCatModalEl) : null;
  const newTitle = $('djeNewCatalogTitle');
  const newLabel = $('djeNewCatalogLabel');
  const newInput = $('djeNewCatalogInput');
  const newHelp = $('djeNewCatalogHelp');
  const newError = $('djeNewCatalogError');
  const newConfirm = $('djeNewCatalogConfirmBtn');
  let newMode = null;      // 'category' | 'subcategory'
  let newCatCtx = null;    // when adding subcategory

  // Edit modal refs
  const editModalEl = $('editDjeModal');
  const editModal = editModalEl ? new bootstrap.Modal(editModalEl) : null;
  const editErrorsEl = $('editDjeErrors');
  const editCatEl = $('editDjeCategory');
  const editSubEl = $('editDjeSubcategory');
  const editDescEl = $('editDjeDesc');
  const editCostEl = $('editDjeUnitCost');
  const editCodeEl = $('editDjeCostCode');
  const editActiveEl = $('editDjeIsActive');
  const saveEditBtn = $('saveDjeEditBtn');

  // Delete modal refs
  const delModalEl = $('deleteDjeModal');
  const delModal = delModalEl ? new bootstrap.Modal(delModalEl) : null;
  const delNameEl = $('deleteDjeName');
  const delErrorEl = $('deleteDjeError');
  const confirmDelBtn = $('confirmDeleteDjeBtn');

  function clamp2(v) {
    if (v === '' || v === null || v === undefined) return '';
    const n = Number(v);
    if (!Number.isFinite(n)) return '';
    return n.toFixed(2);
  }

  function showErrors(el, msgs) {
    if (!el) return;
    const arr = Array.isArray(msgs) ? msgs : [String(msgs || 'Unknown error')];
    el.classList.remove('d-none');
    el.innerHTML = arr.map(m => `<div>${m}</div>`).join('');
  }
  function clearErrors(el) {
    if (!el) return;
    el.classList.add('d-none');
    el.innerHTML = '';
  }

  // ---- Subcategory filtering (single select source) ----
  const allSubOpts = Array.from(subSel.options)
    .map(o => ({ v: o.value || '', cat: (o.dataset.cat || ''), el: o }))
    .filter(o => o.v && o.v !== NEW_SENTINEL && o.cat);

  function resetSubSelect(disable = true) {
    subSel.innerHTML = '';
    subSel.add(new Option('Select…', ''));
    subSel.add(new Option('+ New subcategory…', NEW_SENTINEL));
    subSel.disabled = !!disable;
  }
  function populateSubOptions(catVal) {
    resetSubSelect(false);
    const catLc = (catVal || '').toLowerCase();
    for (const o of allSubOpts) {
      if (o.cat.toLowerCase() === catLc) {
        subSel.add(new Option(o.v, o.v), subSel.options.length - 1);
      }
    }
  }

  // ---- “+ New …” modal behavior (no prompts) ----
  function setNewModal(mode, catName) {
    newMode = mode;
    newCatCtx = catName || null;
    newInput.value = '';
    clearErrors(newError);
    if (mode === 'category') {
      newTitle.textContent = 'Add New Category';
      newLabel.textContent = 'Category name';
      newInput.placeholder = 'e.g., Permits';
      newHelp.textContent = 'This will create a new category in the DJE library.';
    } else {
      newTitle.textContent = 'Add New Subcategory';
      newLabel.textContent = 'Subcategory name';
      newInput.placeholder = 'e.g., City permit';
      newHelp.textContent = `Under “${catName}”.`;
    }
  }
  newCatModalEl?.addEventListener('hidden.bs.modal', () => {
    // Reset selects if user cancelled mid-flow
    if (newMode === 'category' && catSel?.value === NEW_SENTINEL) {
      catSel.value = '';
      resetSubSelect(true);
    }
    if (newMode === 'subcategory' && subSel?.value === NEW_SENTINEL) {
      subSel.value = '';
    }
    newMode = null; newCatCtx = null;
  });

  function addNewCategory(name) {
    const exists = Array.from(catSel.options)
      .some(o => o.value && o.value !== NEW_SENTINEL && o.value.toLowerCase() === name.toLowerCase());
    if (exists) { showErrors(newError, 'That category already exists.'); return false; }

    const sentinelIdx = Array.from(catSel.options).findIndex(o => o.value === NEW_SENTINEL);
    catSel.add(new Option(name, name), sentinelIdx > -1 ? sentinelIdx : null);
    catSel.value = name;
    populateSubOptions(name);
    return true;
    // (We’re not persisting catalogs separately; the real record gets saved on Add/PUT)
  }
  function addNewSubcategory(cat, name) {
    const exists = allSubOpts.some(o => o.cat.toLowerCase() === cat.toLowerCase() && o.v.toLowerCase() === name.toLowerCase());
    if (exists) { showErrors(newError, 'That subcategory already exists for this category.'); return false; }
    allSubOpts.push({ v: name, cat });
    subSel.add(new Option(name, name), subSel.options.length - 1);
    subSel.value = name;
    return true;
  }

  newConfirm?.addEventListener('click', () => {
    const name = (newInput?.value || '').trim();
    if (!name) { showErrors(newError, 'Name is required.'); return; }
    let ok = false;
    if (newMode === 'category') ok = addNewCategory(name);
    else if (newMode === 'subcategory') ok = addNewSubcategory(newCatCtx, name);
    if (ok) newCatModal?.hide();
  });

  function onCategoryChanged() {
    const v = catSel.value;
    if (!v) { resetSubSelect(true); return; }
    if (v === NEW_SENTINEL) { setNewModal('category'); newCatModal?.show(); return; }
    populateSubOptions(v);
  }
  function onSubcategoryChanged() {
    const v = subSel.value;
    if (v !== NEW_SENTINEL) return;
    const cat = catSel.value;
    if (!cat) { subSel.value = ''; return; }
    setNewModal('subcategory', cat);
    newCatModal?.show();
  }

  // ---- Inline Add (POST) ----
  async function createItem(redirectAfter = true) {
    clearErrors(addErrorsEl);

    const category = catSel?.value || '';
    const subcategory = subSel?.value || '';
    const description = (descEl?.value || '').trim();
    const costStr = (unitCostEl?.value || '').trim();

    const errs = [];
    if (!category) errs.push('Category is required.');
    if (!subcategory) errs.push('Subcategory is required.');
    if (!description) errs.push('Description is required.');
    if (costStr === '' || !Number.isFinite(Number(costStr))) errs.push('Unit Cost must be a valid number.');
    if (errs.length) { showErrors(addErrorsEl, errs); return; }

    if (unitCostEl) unitCostEl.value = clamp2(unitCostEl.value);

    const payload = {
      category, subcategory, description,
      default_unit_cost: unitCostEl?.value ? Number(unitCostEl.value) : null,
      cost_code: (costCodeEl?.value || '').trim(),
      is_active: isActiveEl?.checked ?? true
    };

    try {
      const res = await fetch('/libraries/dje', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { showErrors(addErrorsEl, data?.errors || data?.message || 'Failed to add DJE item.'); return; }

      if (redirectAfter) window.location.assign('/libraries/dje');
      else {
        if (descEl) descEl.value = '';
        if (unitCostEl) unitCostEl.value = '';
        if (costCodeEl) costCodeEl.value = '';
        if (isActiveEl) isActiveEl.checked = true;
        descEl?.focus();
      }
    } catch { showErrors(addErrorsEl, 'Network error. Please try again.'); }
  }

  // ---- Edit (PUT) ----
  function openEdit(btn) {
    clearErrors(editErrorsEl);
    const id = btn.dataset.djeId;
    editCatEl.value = btn.dataset.category || '';
    editSubEl.value = btn.dataset.subcategory || '';
    editDescEl.value = btn.dataset.desc || '';
    editCostEl.value = clamp2(btn.dataset.cost || '');
    editCodeEl.value = btn.dataset.cost_code || '';
    editActiveEl.checked = String(btn.dataset.active) === '1';
    saveEditBtn.dataset.djeId = id || '';
    editModal?.show();
  }

  async function saveEdit() {
    clearErrors(editErrorsEl);
    const id = saveEditBtn?.dataset?.djeId;
    if (!id) return;

    const description = (editDescEl?.value || '').trim();
    const costStr = (editCostEl?.value || '').trim();
    const errs = [];
    if (!description) errs.push('Description is required.');
    if (costStr === '' || !Number.isFinite(Number(costStr))) errs.push('Unit Cost must be a valid number.');
    if (errs.length) { showErrors(editErrorsEl, errs); return; }

    if (editCostEl) editCostEl.value = clamp2(editCostEl.value);

    const payload = {
      description,
      default_unit_cost: Number(editCostEl.value),
      cost_code: (editCodeEl?.value || '').trim(),
      is_active: !!(editActiveEl?.checked)
    };

    try {
      const res = await fetch(`/libraries/dje/${id}`, {
        method: 'PUT',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { showErrors(editErrorsEl, data?.errors || data?.message || 'Update failed.'); return; }
      window.location.assign('/libraries/dje');
    } catch { showErrors(editErrorsEl, 'Network error.'); }
  }

  // ---- Delete (DELETE) ----
  function openDelete(btn) {
    clearErrors(delErrorEl);
    const id = btn.dataset.djeId;
    const desc = (btn.dataset.desc || '').trim();
    const cat = (btn.dataset.category || '').trim();
    const sub = (btn.dataset.subcategory || '').trim();

    let name = desc;
    if (!name) {
    name = [cat, sub].filter(Boolean).join(' / ');
    }
    if (!name) {
    name = 'this item';
    }
    delNameEl.textContent = name;
    confirmDelBtn.dataset.djeId = id || '';
    delModal?.show();
  }

  async function confirmDelete() {
    clearErrors(delErrorEl);
    const id = confirmDelBtn?.dataset?.djeId;
    if (!id) return;
    try {
      const res = await fetch(`/libraries/dje/${id}`, {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrf }
      });
      if (res.status === 204) {
        // remove row and close
        const row = document.querySelector(`#dje-${id}`);
        if (row) row.remove();
        delModal?.hide();
        return;
      }
      const data = await res.json().catch(() => ({}));
      showErrors(delErrorEl, data?.errors || data?.message || 'Delete failed.');
    } catch { showErrors(delErrorEl, 'Network error.'); }
  }

  // ---- Wire events ----
  catSel?.addEventListener('change', onCategoryChanged);
  subSel?.addEventListener('change', onSubcategoryChanged);

  $('djeAddBtn')?.addEventListener('click', (e) => { e.preventDefault(); createItem(true); });
  $('djeAddContinueBtn')?.addEventListener('click', (e) => { e.preventDefault(); createItem(false); });
  $('djeResetBtn')?.addEventListener('click', (e) => {
    e.preventDefault();
    if (catSel) catSel.value = '';
    resetSubSelect(true);
    if (descEl) descEl.value = '';
    if (unitCostEl) unitCostEl.value = '';
    if (costCodeEl) costCodeEl.value = '';
    if (isActiveEl) isActiveEl.checked = true;
    clearErrors(addErrorsEl);
    catSel?.focus();
  });

  unitCostEl?.addEventListener('blur', () => { unitCostEl.value = clamp2(unitCostEl.value); });
  editCostEl?.addEventListener('blur', () => { editCostEl.value = clamp2(editCostEl.value); });

  // Event delegation for Edit/Delete buttons in table
  document.addEventListener('click', (e) => {
    const editBtn = e.target.closest('button[data-action="edit-dje"]');
    if (editBtn) { e.preventDefault(); openEdit(editBtn); return; }
    const delBtn = e.target.closest('button[data-action="delete-dje"]');
    if (delBtn) { e.preventDefault(); openDelete(delBtn); return; }
  });
  saveEditBtn?.addEventListener('click', saveEdit);
  confirmDelBtn?.addEventListener('click', confirmDelete);

  // Init
  resetSubSelect(true);
})();

