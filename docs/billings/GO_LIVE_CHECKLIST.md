# Go-Live Checklist — Stripe Billing (LIVE mode)

This is the final switch list for production. It assumes staging (test mode) has passed **all** checks in `STAGING_CHECKLIST.md` and code is at/after:
- S3-03b.10a … 10h (models, service, blueprint, webhook, entitlements, nav, tests, docs)

---

## 0) Preconditions (must be true)
- ✅ Staging sign-off complete (success/failure/cancel flows, taxes, gating, portal).
- ✅ Production domain and TLS are active (e.g., `https://app.<your-domain>`).
- ✅ `APP_BASE_URL` will be set to the production URL.
- ✅ You have access to Stripe **Live** mode.

---

## 1) Stripe — **Live** Products & Prices (exclusive tax)
1. In **Stripe Dashboard → Products** (Live mode):
   - Create **Pro** product with **two Prices**:
     - **Pro Monthly** — recurring, USD, **exclusive tax**, per-unit.
     - **Pro Annual** — recurring, USD, **exclusive tax**, per-unit.
   - (Optional at launch) **Elite** product with Monthly/Annual (same settings).
2. (Recommended) Assign an appropriate **tax code** (SaaS/software) at the product level so Stripe Tax applies correct rules.
3. Copy each **Price ID** (e.g., `price_live_...`) for the env vars in Section 4.

> **Do not** change tax behavior after creation. To change inclusive/exclusive later, create new Prices and archive the old ones.

---

## 2) Stripe — Customer Portal (Live)
1. **Settings → Billing → Customer portal** (Live mode):
   - Enable: **Update payment method**, **Change plan** (optional), **Cancel subscription**.
   - Cancellation default: choose **“at period end”** or **“immediately”** to match your desired policy.
   - **Return URL**: `https://app.<your-domain>/billing`.

---

## 3) Stripe — Webhook endpoint (Live)
1. **Developers → Webhooks → Add endpoint** (Live mode):
   - **Endpoint URL**: `https://app.<your-domain>/webhooks/stripe`
   - **Events**:
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.paid`
     - `invoice.payment_failed`
     - (Optional) `customer.subscription.trial_will_end`
2. Copy the **Signing secret** (format `whsec_...`).

---

## 4) Production service — environment variables (Live)
Set these on your production service (Render/host), then redeploy:

| Variable | Value (Live) |
|---|---|
| `APP_BASE_URL` | `https://app.<your-domain>` |
| `ENABLE_STRIPE_TAX` | `true` |
| `STRIPE_SECRET_KEY` | `sk_live_…` |
| `STRIPE_PUBLISHABLE_KEY` | `pk_live_…` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_…` (from the **Live** webhook endpoint) |
| `STRIPE_PRICE_PRO_MONTHLY` | `price_live_…` |
| `STRIPE_PRICE_PRO_ANNUAL` | `price_live_…` |
| `STRIPE_PRICE_ELITE_MONTHLY` | `price_live_…` (optional) |
| `STRIPE_PRICE_ELITE_ANNUAL` | `price_live_…` (optional) |

> Re-check there are **no** `*_test_*` values left in production.

---

## 5) Smoke test (Live)
Choose **one** of the following safe patterns:

**A) Real charge + immediate refund (simplest)**
1. Sign in to production as a test org owner and go to **/billing**.
2. Click **Subscribe Monthly** (Pro).
3. Complete Checkout with a real card.
4. After redirect to **/billing/success**, wait for webhook processing (usually instant).
5. Verify: **/billing** shows “active”; **Open Customer Portal** works.
6. In Stripe Dashboard → Payments/Invoices, **refund** the charge (full).

**B) 100% off promotion code (no charge)**
1. In Stripe (Live), create a **Coupon** (100% off) and a **Promotion code**.
2. Complete Checkout using that promotion code.
3. Proceed with the same verifications as A).  
> Remove/disable the promo code after the smoke test.

**DB checks (production)**
- `subscriptions` row for your org shows:
  - `status = active` (or `trialing` if later used),
  - correct `price_id` (live),
  - `entitlements_json` contains `"exports.pdf"` and `"exports.csv"`.
- `billing_event_logs` contains the recent Stripe events with `signature_valid=true`.

---

## 6) Negative path (Live) — payment failure
1. Temporarily set a **very small charge** on your price (or use a card you know will fail) — optional if inconvenient; you can simulate later by clearing the default payment method and waiting for renewal.
2. Trigger a failure (e.g., PM removal before renewal).
3. Verify `invoice.payment_failed` arrives; local `subscriptions.status` becomes **past_due**.
4. Pro-gated routes (e.g., export) return **403** (server enforcement).

> If you can’t conveniently simulate a live failure, verify the “past_due” grooming during the first real renewal cycle.

---

## 7) Cancellation flow (Portal)
1. From **/billing**, open **Customer Portal**.
2. Cancel “**at period end**” → verify DB shows `cancel_at_period_end=true` and `current_period_end` set; app still shows active until that date.
3. (If enabled) Cancel “**immediately**” → verify status moves to `canceled` and Pro-gated routes return 403.

---

## 8) Monitoring & alerts (first week)
- Watch **application logs** around `/webhooks/stripe` for any non-2xx.
- Confirm `billing_event_logs` increments for each payment and renewal.
- Consider enabling Stripe email alerts for failed payments.

---

## 9) Backout / rollback (zero-risk)
If anything looks off:
1. **Disable** the Live webhook endpoint in Stripe (to stop updates).
2. Switch production env to **Test** keys + **Test** price IDs (Section 4, test values).
3. Redeploy; traffic returns to test mode safely.
4. Fix, then re-enable Live webhook and restore Live keys/IDs.

---

## 10) Secrets rotation (webhook) — zero downtime
When rotating `STRIPE_WEBHOOK_SECRET`:
1. In Stripe, **add a second** webhook endpoint pointing to the same URL and copy its new secret.
2. Add the new secret to production, deploy, and verify deliveries.
3. Remove the old endpoint/secret from Stripe and from your env.

---

## 11) Legal & UX
- Footer or pricing page includes links to **Terms**, **Privacy**, and **Refund Policy**.
- **/billing** copy states: “Taxes are added at checkout.” (exclusive tax).
- Cancellation language is present and accurate: “Manage payment methods, change plan, or cancel anytime in the Customer Portal.”

---

## 12) Final Go-Live sign-off
- ✅ First successful live subscription observed (and refunded if using path A).
- ✅ Webhooks processed and `subscriptions` reflects `active`.
- ✅ Gating (decorators) enforce access.
- ✅ Customer Portal works (update PM, cancel).
- ✅ Monitoring in place; rollback tested on paper.

