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
})();

