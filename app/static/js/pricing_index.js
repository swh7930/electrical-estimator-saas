// pricing_index.js — page-scoped behaviors for /pricing (no inline JS)
// Collaboration Rules: file-scoped IIFE; external JS only.
(() => {
  const $ = (id) => document.getElementById(id);

  // Safe Plausible wrapper (no-ops when analytics disabled)
  function track(name, props) {
    try {
      if (window.plausible && typeof window.plausible === 'function') {
        window.plausible(name, props ? { props } : undefined);
      }
    } catch (_) { /* no-op */ }
  }

  document.addEventListener('DOMContentLoaded', () => {
    // 1) Page view
    let state = 'guest';
    if ($('manageBillingCta')) state = 'active';
    else if ($('upgradeProCta')) state = 'member';
    track('pricing:view', { state });

    // 2) Plan clicks (Pro)
    const proMonthlyBtn = $('subscribeProMonthly');
    if (proMonthlyBtn) {
      proMonthlyBtn.addEventListener('click', () => {
        track('pricing:plan_click', { plan: 'pro', term: 'monthly' });
      });
    }

    const proAnnualBtn = $('subscribeProAnnual');
    if (proAnnualBtn) {
      proAnnualBtn.addEventListener('click', () => {
        track('pricing:plan_click', { plan: 'pro', term: 'annual' });
      });
    }

    // 3) Upgrade button (signed-in, not active)
    const upgradeForm = $('upgradeProCta');
    if (upgradeForm) {
      upgradeForm.addEventListener('submit', () => {
        track('pricing:plan_click', { plan: 'pro', term: 'monthly' });
      });
    }

    // 4) Portal opened (signed-in, active)
    const portalForm = $('manageBillingCta');
    if (portalForm) {
      portalForm.addEventListener('submit', () => {
        track('billing:portal_opened', { origin: 'pricing' });
      });
    }
  });

  // 5) Back-link handshake (consistent with libraries/admin pages)
  document.addEventListener('click', (e) => {
    const a = e.target.closest('#pricingBackLink');
    if (!a) return;
    e.preventDefault();
    try {
      const rt   = a.getAttribute('data-rt')   || '';
      const href = a.getAttribute('data-href') || '';
      const ref  = document.referrer || '';
      // Estimator return prefers history.back(), with safe fallback
      if (rt.startsWith('estimator') && /\/(estimator|estimates)\b/.test(ref)) {
        history.back();
        return;
      }
      if (href) window.location.assign(href);
    } catch (_) { /* no-op */ }
  });

})();

