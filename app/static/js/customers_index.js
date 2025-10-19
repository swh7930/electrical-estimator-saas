(function () {
  const $ = (id) => document.getElementById(id);
  const v = (id) => { const el = $(id); return el ? (el.value || '').trim() : ''; };
  const set = (id, val) => { const el = $(id); if (el) el.value = (val || ''); };

  function firstErr(errors) {
    if (!errors) return 'Request failed.';
    return errors.__all__ || errors.company_name || errors.email || errors.phone || errors.city || errors.state || errors.zip || 'Request failed.';
  }

  async function addCustomer() {
    const company = EM_VALID.collapseSpaces(v('cust-add-company'), 255);
    if (!company) { EM_NOTIFY.error('Company Name is required.'); return; }

    const email = EM_VALID.collapseSpaces(v('cust-add-email'), 255);
    if (email && !EM_VALID.validateEmail(email)) { EM_NOTIFY.error('Invalid email address.'); return; }

    let phone = EM_VALID.collapseSpaces(v('cust-add-phone'), 32);
    if (phone) {
      const normalized = EM_VALID.normalizePhone(phone);
      if (!normalized) { EM_NOTIFY.error('Invalid US phone number.'); return; }
      phone = normalized;
    }

    let state = EM_VALID.collapseSpaces(v('cust-add-state'), 2).toUpperCase();
    if (state && !(EM_VALID.validateState ? EM_VALID.validateState(state) : /^[A-Za-z]{2}$/.test(state))) {
      EM_NOTIFY.error('State must be 2 letters.'); return;
    }

    const zip = EM_VALID.collapseSpaces(v('cust-add-zip'), 10);
    if (zip && !(EM_VALID.validateZip ? EM_VALID.validateZip(zip) : /^\d{5}(-\d{4})?$/.test(zip))) {
      EM_NOTIFY.error('ZIP must be 12345 or 12345-1234.'); return;
    }

    const payload = {
      company_name: company,
      contact_name: EM_VALID.collapseSpaces(v('cust-add-contact'), 255) || null,
      email: email || null,
      phone: phone || null,
      address1: EM_VALID.collapseSpaces(v('cust-add-address1'), 255) || null,
      address2: EM_VALID.collapseSpaces(v('cust-add-address2'), 255) || null,
      city: EM_VALID.collapseSpaces(v('cust-add-city'), 100) || null,
      state: state || null,
      zip: zip || null,
      notes: EM_VALID.collapseSpaces(v('cust-add-notes'), 2000) || null,
      is_active: $('cust-add-active')?.checked ?? true
    };

    const res = await fetch('/libraries/customers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) { EM_NOTIFY.error(firstErr(data.errors)); return; }
    window.location.reload();
  }

  function resetAdd() {
    [
      'cust-add-company','cust-add-contact','cust-add-email','cust-add-phone',
      'cust-add-address1','cust-add-address2','cust-add-city','cust-add-state',
      'cust-add-zip','cust-add-notes'
    ].forEach(id => set(id, ''));
    const chk = $('cust-add-active'); if (chk) chk.checked = true;
    $('cust-add-company')?.focus();
  }

  let editingId = null;

  document.addEventListener('click', function (evt) {
    const t = evt.target.closest('[data-action]');
    if (!t) return;
    const action = t.getAttribute('data-action');

    if (action === 'edit-customer') {
      editingId = Number(t.getAttribute('data-customer-id'));
      set('cust-modal-company',  t.getAttribute('data-company')  || '');
      set('cust-modal-contact',  t.getAttribute('data-contact')  || '');
      set('cust-modal-email',    t.getAttribute('data-email')    || '');
      set('cust-modal-phone',    t.getAttribute('data-phone')    || '');
      set('cust-modal-address1', t.getAttribute('data-address1') || '');
      set('cust-modal-address2', t.getAttribute('data-address2') || '');
      set('cust-modal-city',     t.getAttribute('data-city')     || '');
      set('cust-modal-state',    t.getAttribute('data-state')    || '');
      set('cust-modal-zip',      t.getAttribute('data-zip')      || '');
      set('cust-modal-notes',    t.getAttribute('data-notes')    || '');
      const active = t.getAttribute('data-active') === 'true';
      const chk = $('cust-modal-active'); if (chk) chk.checked = active;
    }

    if (action === 'delete-customer') {
      const id = Number(t.getAttribute('data-customer-id'));
      const name = t.getAttribute('data-name') || 'this customer';
      $('cust-delete-confirm')?.setAttribute('data-customer-id', String(id));
      const nameEl = $('cust-delete-name'); if (nameEl) nameEl.textContent = name;
    }

    if (action === 'toggle-active') {
      const id = Number(t.getAttribute('data-customer-id'));
      toggleActive(id, t);
    }
  }, { passive: true });

  async function saveEdit() {
    const id = editingId;
    if (!id) return;

    const payload = {
      company_name: EM_VALID.collapseSpaces(v('cust-modal-company'), 255),
      contact_name: EM_VALID.collapseSpaces(v('cust-modal-contact'), 255) || null,
      email: EM_VALID.collapseSpaces(v('cust-modal-email'), 255) || null,
      phone: EM_VALID.collapseSpaces(v('cust-modal-phone'), 32) || null,
      address1: EM_VALID.collapseSpaces(v('cust-modal-address1'), 255) || null,
      address2: EM_VALID.collapseSpaces(v('cust-modal-address2'), 255) || null,
      city: EM_VALID.collapseSpaces(v('cust-modal-city'), 100) || null,
      state: (EM_VALID.collapseSpaces(v('cust-modal-state'), 2) || '').toUpperCase() || null,
      zip: EM_VALID.collapseSpaces(v('cust-modal-zip'), 10) || null,
      notes: EM_VALID.collapseSpaces(v('cust-modal-notes'), 2000) || null,
      is_active: $('cust-modal-active')?.checked ?? true
    };

    if (!payload.company_name) { EM_NOTIFY.error('Company Name is required.'); return; }
    if (payload.email && !EM_VALID.validateEmail(payload.email)) { EM_NOTIFY.error('Invalid email address.'); return; }
    if (payload.phone) {
      const normalized = EM_VALID.normalizePhone(payload.phone);
      if (!normalized) { EM_NOTIFY.error('Invalid US phone number.'); return; }
      payload.phone = normalized;
    }
    if (payload.state && !(EM_VALID.validateState ? EM_VALID.validateState(payload.state) : /^[A-Za-z]{2}$/.test(payload.state))) {
      EM_NOTIFY.error('State must be 2 letters.'); return;
    }
    if (payload.zip && !(EM_VALID.validateZip ? EM_VALID.validateZip(payload.zip) : /^\d{5}(-\d{4})?$/.test(payload.zip))) {
      EM_NOTIFY.error('ZIP must be 12345 or 12345-1234.'); return;
    }

    const res = await fetch(`/libraries/customers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) { EM_NOTIFY.error(firstErr(data.errors)); return; }
    window.location.reload();
  }

  async function confirmDelete() {
    const btn = $('cust-delete-confirm');
    const id = btn && Number(btn.getAttribute('data-customer-id'));
    if (!id) return;
    const res = await fetch(`/libraries/customers/${id}`, { method: 'DELETE' });
    if (res.ok) window.location.reload();
    else EM_NOTIFY.error('Failed to delete customer.');
  }

  async function toggleActive(id, switchEl) {
    const prev = switchEl.checked;
    const res = await fetch(`/libraries/customers/${id}/toggle_active`, { method: 'POST' });
    if (!res.ok) {
      switchEl.checked = !prev;
      EM_NOTIFY.error('Failed to toggle Active.');
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    $('cust-add-submit')?.addEventListener('click', addCustomer, { passive: true });
    $('cust-add-reset')?.addEventListener('click', resetAdd, { passive: true });
    $('cust-modal-save')?.addEventListener('click', saveEdit, { passive: true });
    $('cust-delete-confirm')?.addEventListener('click', confirmDelete, { passive: true });
  });
})();

