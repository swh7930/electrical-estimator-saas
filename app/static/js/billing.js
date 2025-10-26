// billing.js — Stripe.js redirectToCheckout integration (staging/production)

(function () {
  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $all(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

  // Lazy-load Stripe instance using publishable key from server
  let stripePromise = null;
  async function getStripe() {
    if (!stripePromise) {
      const resp = await fetch("/billing/stripe-pk", { credentials: "same-origin" });
      if (!resp.ok) throw new Error("Failed to obtain Stripe publishable key");
      const data = await resp.json();
      if (!data || !data.publishable_key) throw new Error("Publishable key missing");
      stripePromise = Promise.resolve(window.Stripe(data.publishable_key));
    }
    return stripePromise;
  }

  async function createSession(priceId) {
    // Always send CSRF explicitly (defensive even with main.js wrapper)
    var meta = document.querySelector('meta[name="csrf-token"]');
    var csrf = meta ? meta.getAttribute('content') : '';

    const resp = await fetch("/billing/checkout.json", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify({ price_id: priceId })
    });
    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(text || "Checkout session creation failed");
    }
    const data = await resp.json();
    if (!data || !data.sessionId) throw new Error("Missing sessionId");
    return data.sessionId;
  }

  function setDisabled(form, disabled) {
    $all("button, input[type=submit]", form).forEach(function (el) { el.disabled = !!disabled; });
  }

  async function onSubmit(ev) {
    ev.preventDefault(); // Avoid cross-origin form redirect; use Stripe.js instead.
    const form = ev.currentTarget;
    const priceInput = $('input[name="price_id"]', form);
    const priceId = priceInput && priceInput.value;
    if (!priceId) { console.error("price_id not found"); return; }

    try {
      setDisabled(form, true);
      const sessionId = await createSession(priceId);
      const stripe = await getStripe();
      const result = await stripe.redirectToCheckout({ sessionId: sessionId });
      if (result && result.error) {
        console.error(result.error);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDisabled(form, false);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Target only the plan subscribe forms (portal form uses a different action)
    const forms = $all('form[action$="/billing/checkout"]');
    if (!forms.length) return;
    forms.forEach(function (form) {
      form.addEventListener("submit", onSubmit, { passive: false });
    });
  });
})();
