(() => {
  const $ = (id) => document.getElementById(id);

  // Open modal from navbar link; degrade to /feedback page if Bootstrap JS isn't available.
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[data-feedback-modal="1"]');
    if (!link) return;
    if (!window.bootstrap || !window.bootstrap.Modal) return; // let it navigate to the fallback page
    e.preventDefault();

    const modalEl = $('feedbackModal');
    if (!modalEl) return;

    const pathInput = $('feedbackPath');
    if (pathInput) {
      const path = window.location.pathname + (window.location.search || '');
      pathInput.value = path;
    }
    window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
  });

  // Submit (AJAX). Falls back to normal form POST if JS fails.
  const form = $('feedbackForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    // If the form has method+action+csrf+names (it does), HTML POST works;
    // we enhance to JSON+toast here.
    e.preventDefault();

    const msgEl = $('feedbackMessage');
    const btn   = $('feedbackSubmitBtn');
    const message = (msgEl && msgEl.value || '').trim();
    const path   = ($('feedbackPath') && $('feedbackPath').value) || (location.pathname + (location.search || ''));

    if (!message) {
      window.EM_NOTIFY && EM_NOTIFY.warn('Please enter a message.');
      return;
    }

    if (btn) btn.disabled = true;

    // Ensure CSRF header per collaboration rules (main.js also injects this). :contentReference[oaicite:3]{index=3}
    const csrf = (document.querySelector('meta[name="csrf-token"]') || {}).getAttribute?.('content');

    try {
      const res = await fetch('/feedback', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...(csrf ? { 'X-CSRFToken': csrf } : {}),
        },
        body: JSON.stringify({ message, path }),
      });

      if (res.ok) {
        try { window.plausible && window.plausible('feedback:submitted'); } catch (_) {}

        window.EM_NOTIFY && EM_NOTIFY.success('Thanks for your feedback!');
        if (msgEl) msgEl.value = '';
        const modal = document.getElementById('feedbackModal');
        if (modal && window.bootstrap && window.bootstrap.Modal) {
          window.bootstrap.Modal.getOrCreateInstance(modal).hide();
        }
        return;
      }

      const data = await res.json().catch(() => ({}));
      window.EM_NOTIFY && EM_NOTIFY.error(data.error || 'Could not submit feedback.');
    } catch (_) {
      window.EM_NOTIFY && EM_NOTIFY.error('Network error. Please try again.');
    } finally {
      if (btn) btn.disabled = false;
    }
  });
})();
