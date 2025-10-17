(() => {
  const $ = (id) => document.getElementById(id);

  const categoryEl = $('djeCategory');
  const subcategoryEl = $('djeSubcategory');
  const descEl = $('djeDesc');
  const unitCostEl = $('unitCost');
  const costCodeEl = $('costCode');
  const isActiveEl = $('isActive');
  const errorsEl = $('addDjeErrors');

  const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

  function clamp2(v) {
    if (v === '' || v === null || v === undefined) return '';
    const n = Number(v);
    if (!Number.isFinite(n)) return '';
    return n.toFixed(2);
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

  async function createItem(redirectAfter = true) {
    clearErrors();
    if (unitCostEl) unitCostEl.value = clamp2(unitCostEl.value);

    const payload = {
      category: categoryEl?.value?.trim() || '',
      subcategory: subcategoryEl?.value?.trim() || '',
      description: descEl?.value?.trim() || '',
      default_unit_cost: unitCostEl?.value ? Number(unitCostEl.value) : null,
      cost_code: costCodeEl?.value?.trim() || '',
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
        // Keep category/subcategory; clear the rest
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

  $('djeAddBtn')?.addEventListener('click', (e) => {
    e.preventDefault();
    createItem(true);
  });
  $('djeAddContinueBtn')?.addEventListener('click', (e) => {
    e.preventDefault();
    createItem(false);
  });
  $('djeResetBtn')?.addEventListener('click', (e) => {
    e.preventDefault();
    if (categoryEl) categoryEl.value = '';
    if (subcategoryEl) subcategoryEl.value = '';
    if (descEl) descEl.value = '';
    if (unitCostEl) unitCostEl.value = '';
    if (costCodeEl) costCodeEl.value = '';
    if (isActiveEl) isActiveEl.checked = true;
    clearErrors();
    categoryEl?.focus();
  });

  unitCostEl?.addEventListener('blur', () => {
    unitCostEl.value = clamp2(unitCostEl.value);
  });
})();
