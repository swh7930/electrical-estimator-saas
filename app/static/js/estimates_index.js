(function () {
  const $ = (id) => document.getElementById(id);

  const tbody = $('estimatesTableBody');
  const qInput = $('estFilterQ');
  const custSelect = $('estFilterCustomer');
  const statusSelect = $('estFilterStatus');
  const updatedFrom = $('estFilterFrom');
  const clearBtn = $('estFilterClear');

  function badge(status) {
    const s = (status || '').toLowerCase();
    const map = {
      draft:    'badge bg-secondary',
      submitted:'badge bg-info text-dark',
      awarded:  'badge bg-success',
      lost:     'badge bg-danger'
    };
    const cls = map[s] || 'badge bg-secondary';
    return `<span class="${cls}">${s ? (s[0].toUpperCase()+s.slice(1)) : 'Draft'}</span>`;
  }

  function fmtDate(iso) {
    try {
      if (!iso) return '';
      const d = new Date(iso);
      return d.toLocaleString();
    } catch (_) { return ''; }
  }

  async function loadCustomers() {
    if (!custSelect) return;
    try {
      const res = await fetch('/libraries/customers.json?active=true');
      const data = await res.json();
      const rows = (data && data.rows) || [];
      // Reset options
      custSelect.innerHTML = '<option value="">All customers</option>';
      for (const c of rows) {
        const opt = document.createElement('option');
        opt.value = String(c.id);
        opt.textContent = c.company_name || '(unnamed)';
        custSelect.appendChild(opt);
      }
    } catch (e) {
      // non-fatal
      console.warn('customers.json failed', e);
    }
  }

  function rowHtml(item) {
    const id = item.id;
    const name = item.name || '(untitled)';
    const cust = item.customer_name || '';
    const st = item.status || 'draft';
    const updated = fmtDate(item.updated_at);
    return `<tr data-id="${id}" data-name="${name}">
      <td>${name}</td>
      <td>${cust || ''}</td>
      <td>${badge(st)}</td>
      <td>${updated}</td>
      <td class="text-end">
        <div class="btn-group">
          <a class="btn btn-sm btn-outline-primary" data-action="open-estimate">Open</a>
          <button class="btn btn-sm btn-outline-secondary" data-action="clone-estimate">Clone</button>
          <button class="btn btn-sm btn-outline-danger" data-action="delete-estimate">Delete</button>
        </div>
      </td>
    </tr>`;
  }

  async function loadEstimates() {
    if (!tbody) return;
    const params = new URLSearchParams();
    const q = (qInput && qInput.value.trim()) || '';
    const custId = (custSelect && custSelect.value) || '';
    const st = (statusSelect && statusSelect.value) || '';
    const from = (updatedFrom && updatedFrom.value) || '';

    if (q) params.set('q', q);
    if (custId) params.set('customer_id', custId);
    if (st) params.set('status', st);
    if (from) params.set('updated_from', from);

    try {
      const res = await fetch('/estimates/list.json?' + params.toString());
      const data = await res.json();
      const rows = (data && data.rows) || [];
      tbody.innerHTML = rows.map(rowHtml).join('') || '<tr><td colspan="5" class="text-center text-muted py-4">No estimates yet.</td></tr>';
    } catch (e) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger py-4">Failed to load estimates.</td></tr>';
    }
  }

  function onTableClick(e) {
    const t = e.target.closest('[data-action]');
    if (!t) return;
    const tr = e.target.closest('tr[data-id]');
    const id = tr ? tr.getAttribute('data-id') : null;
    const name = tr ? tr.getAttribute('data-name') : '';
    const action = t.getAttribute('data-action');
    if (!id) return;

    if (action === 'open-estimate') {
      window.location.assign(`/estimator?eid=${id}&rt=estimates`);
      return;
    }
    if (action === 'clone-estimate') {
      (async () => {
        try {
          const res = await fetch(`/estimates/${id}/clone`, { method: 'POST' });
          if (!res.ok) throw new Error('Clone failed');
          await loadEstimates();
        } catch (err) {
          console.error(err);
          alert('Clone failed.');
        }
      })();
      return;
    }
    if (action === 'delete-estimate') {
      if (!confirm(`Delete “${name}”? This cannot be undone.`)) return;
      (async () => {
        try {
          const res = await fetch(`/estimates/${id}`, { method: 'DELETE' });
          if (!res.ok) throw new Error('Delete failed');
          await loadEstimates();
        } catch (err) {
          console.error(err);
          alert('Delete failed.');
        }
      })();
      return;
    }
  }

  function wireFilters() {
    if (qInput) qInput.addEventListener('input', debounce(loadEstimates, 250));
    if (custSelect) custSelect.addEventListener('change', loadEstimates);
    if (statusSelect) statusSelect.addEventListener('change', loadEstimates);
    if (updatedFrom) updatedFrom.addEventListener('change', loadEstimates);
    if (clearBtn) clearBtn.addEventListener('click', () => {
      if (qInput) qInput.value = '';
      if (custSelect) custSelect.value = '';
      if (statusSelect) statusSelect.value = '';
      if (updatedFrom) updatedFrom.value = '';
      loadEstimates();
    });
  }

  function debounce(fn, ms) {
    let t; return function () { clearTimeout(t); t = setTimeout(fn, ms); };
  }

  document.addEventListener('DOMContentLoaded', async () => {
    await loadCustomers();
    wireFilters();
    $('estimatesTable')?.addEventListener('click', onTableClick);
    loadEstimates();
  });
})();
