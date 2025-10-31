(() => {
  const $ = (id) => document.getElementById(id);

  // Open modal on click; degrade to full page when JS/Bootstrap isn't present
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[data-feedback-modal="1"]');
    if (!link) return;
    if (!window.bootstrap || !window.bootstrap.Modal) return; // let link navigate to fallback

    e.preventDefault();
    const modalEl = $('feedbackModal');
    if (!modalEl) return;

    const path = window.location.pathname + (window.location.search || '');
    const pathInput = $('feedbackPath');
    if (pathInput) pathInput.value = path;

    const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  });

  // Handle modal submit (AJAX POST + Plausible custom event)
  const form = $('feedbackForm');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const msgEl = $('feedbackMessage');
      const btn = $('feedbackSubmitBtn');
      const path = ($('feedbackPath') && $('feedbackPath').value) || (location.pathname + (location.search || ''));
      const message = (msgEl && msgEl.value || '').trim();
      if (!message) { window.EM_NOTIFY && EM_NOTIFY.warn('Please enter a message.'); return; }
      if (btn) btn.disabled = true;

      try {
        const res = await fetch('/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ message, path })
        });
        if (res.ok) {
          try { window.plausible && window.plausible('feedback:submitted'); } catch (_) {}
          window.EM_NOTIFY && EM_NOTIFY.success('Thanks for your feedback!');
          if (msgEl) msgEl.value = '';
          const m = $('feedbackModal');
          if (m && window.bootstrap && window.bootstrap.Modal) window.bootstrap.Modal.getOrCreateInstance(m).hide();
        } else {
          const data = await res.json().catch(() => ({}));
          window.EM_NOTIFY && EM_NOTIFY.error(data.error || 'Could not submit feedback.');
        }
      } catch {
        window.EM_NOTIFY && EM_NOTIFY.error('Network error. Please try again.');
      } finally {
        if (btn) btn.disabled = false;
      }
    });
  }
})();
