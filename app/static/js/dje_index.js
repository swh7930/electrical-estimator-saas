(() => {
  const $ = (id) => document.getElementById(id);

  const catSel = $('djeCategory');
  const subSel = $('djeSubcategory');

  const descEl = $('djeDesc');
  const unitCostEl = $('unitCost');
  const costCodeEl = $('costCode');
  const isActiveEl = $('isActive');
  const errorsEl = $('addDjeErrors');

  const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
  const NEW_SENTINEL = '__new__';

  // Modal elements
  const modalEl = $('djeNewCatalogModal');
  const modalTitle = $('djeNewCatalogTitle');
  const modalLabel = $('djeNewCatalogLabel');
  const modalInput = $('djeNewCatalogInput');
  const modalHelp = $('djeNewCatalogHelp');
  const modalError = $('djeNewCatalogError');
  const modalConfirmBtn = $('djeNewCatalogConfirmBtn');

  let modalMode = null;          // 'category' | 'subcategory'
  let modalCatContext = null;    // category name when adding subcategory
  let modalInstance = null;

  if (window.bootstrap && modalEl) {
    modalInstance = new bootstrap.Modal(modalEl);
    modalEl.addEventListener('shown.bs.modal', () => { modalInput?.focus(); });
    modalEl.addEventListener('hidden.bs.modal', () => {
      // If user canceled mid-flow, reset selects appropriately
      if (modalMode === 'category' && catSel?.value === NEW_SENTINEL) {
        catSel.value = '';
        resetSubSelect(true);
      }
      if (modalMode === 'subcategory' && subSel?.value === NEW_SENTINEL) {
        subSel.value = '';
      }
      modalMode = null;
      modalCatContext = null;
      clearModal();
    });
  }

  function setModal(mode, catName) {
    modalMode = mode;
    modalCatContext = catName || null;
    clearModal();

    if (mode === 'category') {
      modalTitle.textContent = 'Add New Category';
      modalLabel.textContent = 'Category name';
      modalInput.placeholder = 'e.g., Permits';
      modalHelp.textContent = 'This will create a new category in the DJE library.';
    } else {
      modalTitle.textContent = 'Add New Subcategory';
      modalLabel.textContent = 'Subcategory name';
      modalInput.placeholder = 'e.g., City permit';
      modalHelp.textContent = `Under “${catName}”.`;
    }
  }

  function clearModal() {
    modalInput.value = '';
    modalError.classList.add('d-none');
    modalError.textContent = '';
  }

  function showModalError(msg) {
    modalError.textContent = msg || 'Invalid value.';
    modalError.classList.remove('d-none');
  }

  function showErrors(msgs) {
    if (!errorsEl) return;
    const arr = Array.isArray(msgs) ? msgs : [String(msgs || 'Unknown error')];
    errorsEl.classList.remove('d-none');
    errorsEl.innerHTML = arr.map(m => `<div>${m}</div>`).join('');
  }
  function clearErrors() {
    if (!errorsEl) return;
    errorsEl.classList.add('d-none');
    errorsEl.innerHTML = '';
  }
  function clamp2(v) {
    if (v === '' || v === null || v === undefined) return '';
    const n = Number(v);
    if (!Number.isFinite(n)) return '';
    return n.toFixed(2);
  }

  // Capture all subcategory options from the DOM once (skip sentinels)
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
        subSel.add(new Option(o.v, o.v), subSel.options.length - 1); // before sentinel
      }
    }
  }

  function onCategoryChanged() {
    const v = catSel.value;
    if (!v) { resetSubSelect(true); return; }

    if (v === NEW_SENTINEL) {
      setModal('category');
      modalInstance?.show();
      return;
    }
    populateSubOptions(catSel.value);
  }

  function onSubcategoryChanged() {
    const v = subSel.value;
    if (v !== NEW_SENTINEL) return;

    const cat = catSel.value;
    if (!cat) { subSel.value = ''; return; }

    setModal('subcategory', cat);
    modalInstance?.show();
  }

  function addNewCategory(name) {
    // Duplicate check (case-insensitive)
    const exists = Array.from(catSel.options)
      .some(o => o.value && o.value !== NEW_SENTINEL && o.value.toLowerCase() === name.toLowerCase());
    if (exists) { showModalError('That category already exists.'); return false; }

    const idx = Array.from(catSel.options).findIndex(o => o.value === NEW_SENTINEL);
    catSel.add(new Option(name, name), idx > -1 ? idx : null);
    catSel.value = name;
    populateSubOptions(name);
    return true;
  }

  function addNewSubcategory(cat, name) {
    // Duplicate check limited to selected category (case-insensitive)
    const exists = allSubOpts.some(o => o.cat.toLowerCase() === cat.toLowerCase() && o.v.toLowerCase() === name.toLowerCase());
    if (exists) { showModalError('That subcategory already exists for this category.'); return false; }

    // Update in-memory list so future filters include it
    allSubOpts.push({ v: name, cat });

    // Insert into visible select (before sentinel) and select it
    subSel.add(new Option(name, name), subSel.options.length - 1);
    subSel.value = name;
    return true;
  }

  modalConfirmBtn?.addEventListener('click', () => {
    const name = (modalInput?.value || '').trim();
    if (!name) { showModalError('Name is required.'); return; }

    let ok = false;
    if (modalMode === 'category') ok = addNewCategory(name);
    else if (modalMode === 'subcategory') ok = addNewSubcategory(modalCatContext, name);

    if (ok) modalInstance?.hide();
  });

  modalInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      modalConfirmBtn?.click();
    }
  });

  async function createItem(redirectAfter = true) {
    clearErrors();

    const category = catSel?.value || '';
    const subcategory = subSel?.value || '';
    const description = (descEl?.value || '').trim();
    const costStr = (unitCostEl?.value || '').trim();

    const errs = [];
    if (!category) errs.push('Category is required.');
    if (!subcategory) errs.push('Subcategory is required.');
    if (!description) errs.push('Description is required.');
    if (costStr === '' || !Number.isFinite(Number(costStr))) errs.push('Unit Cost must be a valid number.');
    if (errs.length) { showErrors(errs); return; }

    if (unitCostEl) unitCostEl.value = clamp2(unitCostEl.value);

    const payload = {
      category,
      subcategory,
      description,
      default_unit_cost: unitCostEl?.value ? Number(unitCostEl.value) : null,
      cost_code: (costCodeEl?.value || '').trim(),
      is_active: isActiveEl?.checked ?? true
    };

    try {
      const res = await fetch('/libraries/dje', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        showErrors(data?.errors || data?.message || 'Failed to add DJE item.');
        return;
      }

      if (redirectAfter) {
        window.location.assign('/libraries/dje');
      } else {
        // Keep Category/Subcategory; clear the rest
        if (descEl) descEl.value = '';
        if (unitCostEl) unitCostEl.value = '';
        if (costCodeEl) costCodeEl.value = '';
        if (isActiveEl) isActiveEl.checked = true;
        descEl?.focus();
      }
    } catch {
      showErrors('Network error. Please try again.');
    }
  }

  // Wire events
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
    clearErrors();
    catSel?.focus();
  });

  unitCostEl?.addEventListener('blur', () => {
    unitCostEl.value = clamp2(unitCostEl.value);
  });

  // Init
  resetSubSelect(true);
})();

