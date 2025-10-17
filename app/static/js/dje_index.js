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
        // insert before "+ New…" sentinel (last option)
        subSel.add(new Option(o.v, o.v), subSel.options.length - 1);
      }
    }
  }

  function onCategoryChanged() {
    const v = catSel.value;
    if (!v) {
      resetSubSelect(true);
      return;
    }
    if (v === NEW_SENTINEL) {
      const name = (window.prompt('Enter new category name:') || '').trim();
      if (!name) { catSel.value = ''; resetSubSelect(true); return; }
      if (!window.confirm(`You're creating a new Category "${name}". Continue?`)) {
        catSel.value = ''; resetSubSelect(true); return;
      }
      // Append new category option just before the sentinel if present
      const idx = Array.from(catSel.options).findIndex(o => o.value === NEW_SENTINEL);
      catSel.add(new Option(name, name), idx > -1 ? idx : null);
      catSel.value = name;
    }
    populateSubOptions(catSel.value);
  }

  function onSubcategoryChanged() {
    if (subSel.value !== NEW_SENTINEL) return;

    const cat = catSel.value;
    if (!cat) { subSel.value = ''; return; }

    const name = (window.prompt(`Enter new subcategory for "${cat}":`) || '').trim();
    if (!name) { subSel.value = ''; return; }
    if (!window.confirm(`You're creating a new Subcategory "${name}" under "${cat}". Continue?`)) {
      subSel.value = ''; return;
    }

    // Update in-memory list so future category changes include it
    allSubOpts.push({ v: name, cat });

    // Insert into visible select (before sentinel) and select it
    subSel.add(new Option(name, name), subSel.options.length - 1);
    subSel.value = name;
  }

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

  // Init: disable and show only sentinels (options read above already)
  resetSubSelect(true);
})();
