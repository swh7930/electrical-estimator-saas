(function (global) {
  // Escapes text to prevent HTML injection inside toast markup
  function escapeHtml(str) {
    return (str || '').replace(/[&<>"']/g, (m) => (
      { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[m]
    ));
  }

  // Ensure the toast container exists and is correctly positioned.
  // If it's missing (e.g., on a page that didn't include base.html), create it.
  function ensureStack() {
    let stack = document.getElementById('toastStack');
    if (stack) return stack;

    stack = document.createElement('div');
    stack.id = 'toastStack';
    stack.className = 'toast-container position-fixed top-0 end-0 p-3';
    stack.style.zIndex = '1200';
    document.body.appendChild(stack);
    return stack;
  }

  // Show a Bootstrap toast. Falls back to alert() if Bootstrap JS isn't available.
  function showToast({ title = '', body = '', variant = 'primary', delay = 4000 } = {}) {
    const stack = ensureStack();

    if (!global.bootstrap || !global.bootstrap.Toast) {
      // Fallback for pages where Bootstrap's JS isn't loaded
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

  // Public API
  global.EM_NOTIFY = {
    show: showToast,
    success: (body, title = 'Success') => showToast({ title, body, variant: 'success' }),
    error:   (body, title = 'Error')   => showToast({ title, body, variant: 'danger'  }),
    info:    (body, title = 'Notice')  => showToast({ title, body, variant: 'info'    }),
    warn:    (body, title = 'Warning') => showToast({ title, body, variant: 'warning' }),
  };
})(window);
