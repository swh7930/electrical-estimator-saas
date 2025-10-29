(() => {
  "use strict";
  const meta = document.querySelector('meta[name="x-can-write"]');
  const CAN_WRITE = !!(meta && meta.content === '1');
  if (!CAN_WRITE) {
    const scope = document.getElementById('assemblies-grid') || document;
    scope.querySelectorAll('input, select, textarea, button').forEach((el) => {
      el.setAttribute('disabled', 'disabled');
      el.setAttribute('aria-disabled', 'true');
    });
    return; // skip binding bundle/component/create handlers
  }
  const $ = (id) => document.getElementById(id);

  // Inline Add controls
  const catSel = $('asmCategory');
  const subSel = $('asmSubcategory');
  const resetBtn = $('asmResetBtn');

  // Modal controls
  const modalEl = $('asmNewCatalogModal');
  const modalTitle = $('asmNewCatalogTitle');
  const modalLabel = $('asmNewCatalogLabel');
  const modalInput = $('asmNewCatalogInput');
  const modalHelp = $('asmNewCatalogHelp');
  const modalError = $('asmNewCatalogError');
  const modalConfirm = $('asmNewCatalogConfirmBtn');
  const modal = modalEl ? bootstrap.Modal.getOrCreateInstance(modalEl) : null;

  const NEW_SENTINEL = '__new__';
  let modalMode = null;        // 'category' | 'subcategory'
  let modalCatContext = null;  // category name for subcategory mode

  // Capture full subcategory option set from current DOM (data-cat carries parent category)
  const allSubOpts = Array.from(subSel.options)
    .map(o => ({ v: o.value || '', cat: (o.dataset.cat || '') }))
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
    for (const { v, cat } of allSubOpts) {
      if (cat.toLowerCase() === catLc) {
        subSel.add(new Option(v, v), subSel.options.length - 1); // before sentinel
      }
    }
  }

  function clearModalError() {
    modalError.classList.add('d-none');
    modalError.textContent = '';
  }
  function showModalError(msg) {
    modalError.textContent = msg || 'Invalid value.';
    modalError.classList.remove('d-none');
  }

  function setModal(mode, catName) {
    modalMode = mode;
    modalCatContext = catName || null;
    clearModalError();
    modalInput.value = '';
    if (mode === 'category') {
      modalTitle.textContent = 'Add New Category';
      modalLabel.textContent = 'Category name';
      modalInput.placeholder = 'e.g., Rough-In';
      modalHelp.textContent = 'This will create a new category in Assemblies.';
    } else {
      modalTitle.textContent = 'Add New Subcategory';
      modalLabel.textContent = 'Subcategory name';
      modalInput.placeholder = 'e.g., Boxes';
      modalHelp.textContent = `Under “${catName}”.`;
    }
  }

  // Category change → filter subs or open modal
  catSel?.addEventListener('change', () => {
    const v = catSel.value;
    if (!v) { resetSubSelect(true); return; }
    if (v === NEW_SENTINEL) { setModal('category'); modal?.show(); return; }
    populateSubOptions(v);
  });

  // Subcategory change → open modal for new
  subSel?.addEventListener('change', () => {
    if (subSel.value !== NEW_SENTINEL) return;
    const cat = catSel.value;
    if (!cat) { subSel.value = ''; return; }
    setModal('subcategory', cat);
    modal?.show();
  });

  // Confirm in modal
  modalConfirm?.addEventListener('click', () => {
    const name = (modalInput.value || '').trim();
    if (!name) { showModalError('Name is required.'); return; }

    if (modalMode === 'category') {
      // prevent dup (case-insensitive)
      const exists = Array.from(catSel.options)
        .some(o => o.value && o.value !== NEW_SENTINEL && o.value.toLowerCase() === name.toLowerCase());
      if (exists) { showModalError('That category already exists.'); return; }

      const idx = Array.from(catSel.options).findIndex(o => o.value === NEW_SENTINEL);
      catSel.add(new Option(name, name), idx > -1 ? idx : null);
      catSel.value = name;
      populateSubOptions(name);
      modal?.hide();
    }
    else if (modalMode === 'subcategory') {
      // prevent dup within selected category
      const cat = modalCatContext || '';
      const exists = allSubOpts.some(o => o.cat.toLowerCase() === cat.toLowerCase() && o.v.toLowerCase() === name.toLowerCase());
      if (exists) { showModalError('That subcategory already exists for this category.'); return; }

      allSubOpts.push({ v: name, cat });
      subSel.add(new Option(name, name), subSel.options.length - 1);
      subSel.value = name;
      modal?.hide();
    }
  });

  modalEl?.addEventListener('hidden.bs.modal', () => {
    // If user canceled mid-flow, revert sentinels
    if (modalMode === 'category' && catSel?.value === NEW_SENTINEL) {
      catSel.value = '';
      resetSubSelect(true);
    }
    if (modalMode === 'subcategory' && subSel?.value === NEW_SENTINEL) {
      subSel.value = '';
    }
    modalMode = null;
    modalCatContext = null;
  });

  // Reset button → also disable subcategory
  resetBtn?.addEventListener('click', (e) => {
    // type="reset" clears fields; we also disable the sub select
    setTimeout(() => resetSubSelect(true), 0);
  });

  // Init
  resetSubSelect(true);

  // --- Delete Assembly (modal + POST form submit) ---
  (() => {
    const $ = (id) => document.getElementById(id);
    const modalEl = $('deleteAsmModal');
    if (!modalEl) return;

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const nameEl = $('deleteAsmName');
    const formEl = $('asmDeleteForm');
    const errEl  = $('deleteAsmError');

    function clearErr() {
      if (!errEl) return;
      errEl.classList.add('d-none');
      errEl.textContent = '';
    }

    document.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-action="delete-asm"]');
      if (!btn) return;

      e.preventDefault();
      clearErr();
      if (nameEl) nameEl.textContent = btn.dataset.asmName || 'this assembly';
      if (formEl) formEl.action = btn.dataset.deleteUrl || '';
      modal.show();
    });

    formEl?.addEventListener('submit', () => {
      const submitBtn = $('confirmDeleteAsmBtn');
      submitBtn?.setAttribute('disabled', 'disabled');
    });
  })();

  // --- Edit Assembly (open modal, PUT on save) ---
  (() => {
    const $ = (id) => document.getElementById(id);

    const modalEl = $('editAsmModal');
    if (!modalEl) return;

    const compTbody = document.getElementById('compListBody');

    function renderList(list, asmId) {
      if (!compTbody) return;
      compTbody.innerHTML = '';
      if (!list || !list.length) {
        compTbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">No components.</td></tr>`;
        return;
      }
      for (const c of list) {
        const toggleLabel = c.is_active ? 'Deactivate' : 'Activate';
        const togglePath  = c.is_active ? 'deactivate' : 'activate';
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${c.material_name}</td>
          <td class="text-end">${c.qty_per_assembly}</td>
          <td class="text-end">${c.sort_order ?? ''}</td>
          <td class="text-center">${c.is_active ? '✓' : '—'}</td>
          <td class="text-end">
            <div class="btn-group">
              <button class="btn btn-sm btn-outline-secondary"
                      data-action="toggle-comp"
                      data-url="/admin/assemblies/${asmId}/components/${c.id}/${togglePath}">
                ${toggleLabel}
              </button>
            </div>
          </td>
        `;
        compTbody.appendChild(tr);
      }
    }

    async function loadComponents(asmId) {
      if (!compTbody) return;
      compTbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">Loading…</td></tr>`;
      try {
        const res = await fetch(`/admin/assemblies/${asmId}/components.json`, { credentials: 'same-origin' });
        const data = await res.json().catch(() => []);
        if (!res.ok) throw new Error();
        renderList(data, asmId);
      } catch {
        compTbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-3">Failed to load components.</td></tr>`;
      }
    }

    // Allow other code to tell us to refresh the list in this modal
    document.addEventListener('assemblies:reload-components', (e) => {
      const asmId = e?.detail?.asmId;
      if (asmId) loadComponents(asmId);
    });

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const errEl = $('editAsmErrors');
    const saveBtn = $('saveAsmEditBtn');

    const catEl = $('editAsmCategory');
    const subEl = $('editAsmSubcategory');
    const nameEl = $('editAsmName');
    const codeEl = $('editAsmCode');
    const notesEl = $('editAsmNotes');
    const featEl = $('editAsmFeatured');
    const actEl = $('editAsmActive');

    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

    const catPicker = document.getElementById('compMatCategory');
    const descPicker = document.getElementById('compMaterial');

    // Cache all material options with their type/category
    const allMatOpts = Array
      .from(document.querySelectorAll('#compMaterial option[data-type]'))
      .map(o => ({ id: o.value, label: o.textContent, type: o.dataset.type }));

    // Ensure Description is empty until a category is picked
    modalEl?.addEventListener('show.bs.modal', () => {
      if (catPicker) catPicker.value = '';
      if (descPicker) {
        descPicker.innerHTML = '';
        descPicker.add(new Option('Select…', ''));
      }
    });

    function rebuildDescForCategory(cat) {
      if (!descPicker) return;
      const sel = (cat || '').toLowerCase();
      descPicker.innerHTML = '';
      descPicker.add(new Option('Select…', ''));
      if (!sel) {
        // No category selected → keep only the placeholder
        return;
      }
      for (const o of allMatOpts) {
        if ((o.type || '').toLowerCase() === sel) {
          descPicker.add(new Option(o.label, o.id));
        }
      }
    }

    // wire category change
    catPicker?.addEventListener('change', () => {
      rebuildDescForCategory(catPicker.value);
      descPicker?.focus();
    });

    function clearErr() {
      if (!errEl) return;
      errEl.classList.add('d-none');
      errEl.textContent = '';
    }
    function showErr(msgs) {
      if (!errEl) return;
      const arr = Array.isArray(msgs) ? msgs : [String(msgs || 'Invalid')];
      errEl.innerHTML = arr.map(m => `<div>${m}</div>`).join('');
      errEl.classList.remove('d-none');
    }

    // Open modal from Actions button
    document.addEventListener('click', async (e) => {
      const btn = e.target.closest('button[data-action="edit-asm"]');
      if (!btn) return;

      e.preventDefault();
      clearErr();

      saveBtn.dataset.asmId = btn.dataset.asmId || '';
      catEl.value = btn.dataset.category || '';
      subEl.value = btn.dataset.subcategory || '';
      nameEl.value = btn.dataset.name || '';
      codeEl.value = btn.dataset.code || '';
      notesEl.value = btn.dataset.notes || '';
      featEl.checked = String(btn.dataset.featured) === '1';
      actEl.checked = String(btn.dataset.active) === '1';

      await loadComponents(saveBtn.dataset.asmId);
      modal.show();
    });

    // Enable Activate/Deactivate for existing components (uses your existing endpoints)
    document.addEventListener('click', async (e) => {
      const btn = e.target.closest('button[data-action="toggle-comp"]');
      if (!btn) return;
      e.preventDefault();

      const url = btn.dataset.url;           // e.g., /admin/assemblies/123/components/456/activate
      const asmId = saveBtn?.dataset?.asmId; // set when opening Edit modal
      if (!url || !asmId) return;

      btn.setAttribute('disabled', 'disabled');
      try {
        const res = await fetch(url, {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'X-CSRFToken': csrf }   // <-- this uses the csrf you already declared in this IIFE
        });
        if (!res.ok) throw new Error();
        await loadComponents(asmId);         // refresh the existing-components table
      } catch {
        // lightweight inline feedback
        btn.classList.remove('btn-outline-secondary');
        btn.classList.add('btn-outline-danger');
        btn.textContent = 'Retry';
      } finally {
        btn.removeAttribute('disabled');
      }
    });


  })();
})();

// --- Create flow: open modal from inline Add, stage components, save via /assemblies/bundle ---
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);

  // Inline Add form
  const inlineForm = document.querySelector('#asm-inline-add form');
  if (!inlineForm) return;

  const catSel = $('asmCategory');
  const subSel = $('asmSubcategory');
  const nameEl = $('asmName');
  const codeEl = $('asmCode');
  const notesEl = $('asmNotes');
  const activeEl = $('asmActive');
  const featuredEl = $('asmFeatured'); // if present; ok if null

  // Edit modal handles both edit & create
  const modalEl = $('editAsmModal');
  const modal = modalEl ? bootstrap.Modal.getOrCreateInstance(modalEl) : null;

  const errEl = $('editAsmErrors');
  const saveBtn = $('saveAsmEditBtn');

  const editCatEl = $('editAsmCategory');
  const editSubEl = $('editAsmSubcategory');
  const editNameEl = $('editAsmName');
  const editCodeEl = $('editAsmCode');
  const editNotesEl = $('editAsmNotes');
  const editFeaturedEl = $('editAsmFeatured');
  const editActiveEl = $('editAsmActive');

  const compMatSel = $('compMaterial');
  const compQtyEl = $('compQty');
  const compSortEl = $('compSort');
  const addCompBtn = $('addCompBtn');
  const compTbody = $('compListBody');

  const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

  let mode = 'edit';          // 'edit' | 'create'
  let staged = [];            // [{material_id, material_name, qty_per_assembly, sort_order?}, ...]
  let createCat = '';
  let createSub = '';

  function clearErr() {
    if (!errEl) return;
    errEl.classList.add('d-none');
    errEl.textContent = '';
  }
  function showErr(msgs) {
    if (!errEl) return;
    const arr = Array.isArray(msgs) ? msgs : [String(msgs || 'Invalid')];
    errEl.innerHTML = arr.map(m => `<div>${m}</div>`).join('');
    errEl.classList.remove('d-none');
  }

  function renderStaged() {
    if (!compTbody) return;
    compTbody.innerHTML = '';
    if (!staged.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 4;
      td.className = 'text-center text-muted py-3';
      td.textContent = 'No components staged.';
      tr.appendChild(td);
      compTbody.appendChild(tr);
      return;
    }
    staged.forEach((c, idx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${c.material_name}</td>
        <td class="text-end">${c.qty_per_assembly}</td>
        <td class="text-end">${c.sort_order ?? ''}</td>
        <td class="text-end">
          <button type="button" class="btn btn-sm btn-outline-danger" data-action="remove-staged" data-idx="${idx}">Remove</button>
        </td>
      `;
      compTbody.appendChild(tr);
    });
  }

  function resetCompInputs() {
    if (compMatSel) compMatSel.value = '';
    if (compQtyEl) compQtyEl.value = '';
    if (compSortEl) compSortEl.value = '';
  }

  // Intercept inline Add submit → open modal in CREATE mode
  inlineForm.addEventListener('submit', (e) => {

    e.preventDefault();

    // Basic required checks (same as inline UI)
    const errs = [];
    if (!catSel?.value) errs.push('Category is required.');
    if (!subSel?.value) errs.push('Subcategory is required.');
    if (!nameEl?.value?.trim()) errs.push('Assembly Name is required.');
    if (errs.length) { alert(errs.join('\n')); return; } // minimal feedback here; modal will handle main errors

    mode = 'create';
    staged = [];
    createCat = catSel.value;
    createSub = subSel.value;

    // Prefill modal
    if (editCatEl) editCatEl.value = createCat;
    if (editSubEl) editSubEl.value = createSub;
    if (editNameEl) editNameEl.value = nameEl.value || '';
    if (editCodeEl) editCodeEl.value = codeEl?.value || '';
    if (editNotesEl) editNotesEl.value = notesEl?.value || '';
    if (editFeaturedEl) editFeaturedEl.checked = !!(featuredEl?.checked);
    if (editActiveEl) editActiveEl.checked = !!(activeEl?.checked);

    clearErr();
    renderStaged();
    // Show a clean empty state for “existing components” in create mode
    const existingTbody = document.getElementById('compListBody');
    if (existingTbody) {
      existingTbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">No components.</td></tr>';
    }

    // switch to Components tab so user starts adding immediately
    document.querySelector('#asm-components-tab')?.click();

    modal?.show();
  });

  // Add component: in EDIT mode → POST to server; in CREATE mode → stage locally
  addCompBtn?.addEventListener('click', async () => {
    clearErr();

    const asmId = saveBtn?.dataset?.asmId || '';     // present in edit mode
    const mid = compMatSel?.value;
    const mname = compMatSel?.selectedOptions?.[0]?.text || '';
    const qtyStr = compQtyEl?.value || '';
    const sortStr = compSortEl?.value || '';

    const errs = [];
    if (!mid) errs.push('Select a material.');
    const qty = Number(qtyStr);
    if (!Number.isInteger(qty) || qty < 1) errs.push('Qty must be a whole number ≥ 1.');
    if (errs.length) { showErr(errs); return; }

    const sort_order = sortStr ? Number(sortStr) : null;

    // EDIT mode: call existing POST /admin/assemblies/<id>/components, then reload modal list
    if (asmId) {
      try {
        // quick progress row
        if (compTbody) {
          compTbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">Saving…</td></tr>`;
        }
        const body = new URLSearchParams();
        body.set('material_id', String(mid));
        body.set('qty_per_assembly', String(qty));
        if (sortStr) body.set('sort_order', String(sort_order));

        const res = await fetch(`/admin/assemblies/${asmId}/components`, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf
          },
          body: body.toString()
        });

        if (!res.ok) throw new Error('Bad response');

        // server added it; refresh list in-place, then clear inputs
        document.dispatchEvent(new CustomEvent('assemblies:reload-components', { detail: { asmId } }));
        resetCompInputs();
        compMatSel?.focus();
        return;
      } catch (e) {
        showErr('Failed to add component. Please try again.');
        return;
      }
    }

    // CREATE mode (no asmId yet): stage locally
    staged.push({ material_id: Number(mid), material_name: mname, qty_per_assembly: qty, sort_order });
    renderStaged();
    resetCompInputs();
    compMatSel?.focus();
  });

  // Remove from staged
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-action="remove-staged"]');
    if (!btn) return;
    const idx = Number(btn.dataset.idx);
    if (Number.isInteger(idx)) {
      staged.splice(idx, 1);
      renderStaged();
    }
  });

  // SAVE button: create bundle OR update existing via PUT (existing behavior)
  saveBtn?.addEventListener('click', async () => {
    clearErr();

    const name = (editNameEl?.value || '').trim();
    if (!name) { showErr('Assembly Name is required.'); return; }

    if (mode === 'create') {
      // Must have at least one component before we create
      if (!staged.length) { showErr('At least one component is required.'); document.querySelector('#asm-components-tab')?.click(); return; }

      const payload = {
        name,
        category: editCatEl?.value || createCat,
        subcategory: editSubEl?.value || createSub,
        assembly_code: (editCodeEl?.value || '').trim(),
        notes: (editNotesEl?.value || '').trim(),
        is_featured: !!(editFeaturedEl?.checked),
        is_active: !!(editActiveEl?.checked),
        components: staged.map(c => ({
          material_id: c.material_id,
          qty_per_assembly: c.qty_per_assembly,
          sort_order: c.sort_order
        }))
      };

      try {
        const res = await fetch('/admin/assemblies/bundle', {
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
          showErr(data?.errors || data?.message || 'Create failed.');
          return;
        }
        window.location.assign('/admin/assemblies' + window.location.search);
      } catch {
        showErr('Network error. Please try again.');
      }
      return;
    }

    // EDIT mode (existing functionality)
    const id = saveBtn?.dataset?.asmId;
    if (!id) { showErr('Missing assembly id.'); return; }

    const payload = {
      name,
      assembly_code: (editCodeEl?.value || '').trim(),
      notes: (editNotesEl?.value || '').trim(),
      is_featured: !!(editFeaturedEl?.checked),
      is_active: !!(editActiveEl?.checked)
    };

    try {
      const res = await fetch(`/admin/assemblies/${id}/edit`, {
        method: 'PUT',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { showErr(data?.errors || data?.message || 'Update failed.'); return; }
      window.location.assign('/admin/assemblies' + window.location.search);
    } catch {
      showErr('Network error.');
    }
  });
})();

// -- Back link (query-param handshake) --
(() => {
  const backEl = document.getElementById('asmBackLink');
  if (!backEl) return;

  backEl.addEventListener('click', (e) => {
    e.preventDefault();
    const rt = backEl.dataset.rt || '';
    const href = backEl.dataset.href || '';

    // If user arrived from Estimator, try to go back in history first to preserve state.
    if (rt.startsWith('estimator')) {
      // Only use history if we really have a referring page.
      if (document.referrer && (document.referrer.includes('/estimator') || document.referrer.includes('/estimates'))) {
        history.back();
        return;
      }
      // Fallback: if a href is provided, use it; otherwise do nothing.
      if (href) {
        window.location.assign(href);
      }
      return;
    }

    // Home path (or anything with a direct href)
    if (href) {
      window.location.assign(href);
    }
  });
})();

