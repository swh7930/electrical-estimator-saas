(function () {
  const $ = (id) => document.getElementById(id);
  const v = (id) => { const el = $(id); return el ? (el.value || '').trim() : ''; };
  const set = (id, val) => { const el = $(id); if (el) el.value = (val || ''); };

  function deriveCity(address) {
    if (!address) return null;
    const parts = address.split(',');
    return parts.length >= 2 ? parts[1].trim() || null : null;
  }

  async function addCustomer() {
    const name = v('cust-add-name');
    if (!name) { alert('Customer Name is required.'); return; }

    const payload = {
      name: name,
      primary_contact: v('cust-add-contact') || null,
      email: v('cust-add-email') || null,
      phone: v('cust-add-phone') || null,
      address: v('cust-add-address') || null,
      notes: v('cust-add-notes') || null
    };

    if (!payload.city) {
      const c = deriveCity(payload.address);
      if (c) payload.city = c;
    }

    const res = await fetch('/libraries/customers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      const msg = (data && data.errors && (data.errors.__all__ || data.errors.name)) || 'Failed to add customer.';
      alert(msg); return;
    }
    window.location.href = '/libraries/customers';
  }

  function resetAdd() {
    ['cust-add-name','cust-add-contact','cust-add-email','cust-add-phone','cust-add-address','cust-add-notes'].forEach(id => set(id, ''));
    $('cust-add-name')?.focus();
  }

  let editingId = null;

  document.addEventListener('click', function (evt) {
    const t = evt.target.closest('[data-action]');
    if (!t) return;
    const action = t.getAttribute('data-action');

    if (action === 'edit-customer') {
      editingId = Number(t.getAttribute('data-customer-id'));
      set('cust-modal-name', t.getAttribute('data-name') || '');
      set('cust-modal-contact', t.getAttribute('data-contact') || '');
      set('cust-modal-email', t.getAttribute('data-email') || '');
      set('cust-modal-phone', t.getAttribute('data-phone') || '');
      set('cust-modal-address', t.getAttribute('data-address') || '');
      set('cust-modal-notes', t.getAttribute('data-notes') || '');
    }

    if (action === 'delete-customer') {
      const id = Number(t.getAttribute('data-customer-id'));
      const name = t.getAttribute('data-name') || 'this customer';
      const delBtn = $('cust-delete-confirm');
      if (delBtn) delBtn.setAttribute('data-customer-id', String(id));
      const nameEl = $('cust-delete-name');
      if (nameEl) nameEl.textContent = name;
    }
  }, { passive: true });

  async function saveEdit() {
    const id = editingId;
    if (!id) return;
    const payload = {
      name: v('cust-modal-name'),
      primary_contact: v('cust-modal-contact') || null,
      email: v('cust-modal-email') || null,
      phone: v('cust-modal-phone') || null,
      address: v('cust-modal-address') || null,
      notes: v('cust-modal-notes') || null
    };
    if (!payload.name) { alert('Customer Name is required.'); return; }
    if (!payload.city && payload.address) {
      const c = deriveCity(payload.address);
      if (c) payload.city = c;
    }

    const res = await fetch(`/libraries/customers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      const msg = (data && data.errors && (data.errors.__all__ || data.errors.name)) || 'Failed to save.';
      alert(msg); return;
    }
    window.location.reload();
  }

  async function confirmDelete() {
    const btn = $('cust-delete-confirm');
    const id = btn && Number(btn.getAttribute('data-customer-id'));
    if (!id) return;
    const res = await fetch(`/libraries/customers/${id}`, { method: 'DELETE' });
    if (res.ok) window.location.reload();
    else alert('Failed to delete customer.');
  }

  document.addEventListener('DOMContentLoaded', function () {
    $('cust-add-submit')?.addEventListener('click', () => addCustomer(), { passive: true });
    $('cust-add-reset')?.addEventListener('click', () => resetAdd(), { passive: true });
    $('cust-modal-save')?.addEventListener('click', () => saveEdit(), { passive: true });
    $('cust-delete-confirm')?.addEventListener('click', () => confirmDelete(), { passive: true });
  });
})();
