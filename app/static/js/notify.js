(function (global) {
  function escapeHtml(str) {
    return (str || '').replace(/[&<>"']/g, (m) => (
      { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[m]
    ));
  }

  function showToast({ title = '', body = '', variant = 'primary', delay = 4000 } = {}) {
    const stack = document.getElementById('toastStack');
    if (!stack || !global.bootstrap || !global.bootstrap.Toast) {
      // Safe fallback if Bootstrap/stack not available
      alert([title, body].filter(Boolean).join(' — '));
      return;
    }

    const el = document.createElement('div');
    el.className = `toast align-items-center text-bg-${variant} border-0`;
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');
    el.setAttribute('aria-atomic', 'true');

    el.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          ${title ? `<strong class="me-2">${escapeHtml(title)}</strong>` : ''}${escapeHtml(body)}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    stack.appendChild(el);
    const t = new bootstrap.Toast(el, { delay, autohide: true });
    t.show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
  }

  global.EM_NOTIFY = {
    show: showToast,
    success: (body, title = 'Success') => showToast({ title, body, variant: 'success' }),
    error:   (body, title = 'Error')   => showToast({ title, body, variant: 'danger'  }),
    info:    (body, title = 'Notice')  => showToast({ title, body, variant: 'info'    }),
    warn:    (body, title = 'Warning') => showToast({ title, body, variant: 'warning' }),
  };
})(window);
