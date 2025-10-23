# Staging (Test Mode) Checklist — S3-03b.10

This runbook verifies end-to-end billing on **staging** using **Stripe Test mode**, **exclusive tax**, and **Checkout + Customer Portal**. Do this **before** switching production to Live.

---

## 0) Pre-flight (code)
- Repo at/after commits:
  - `S3-03b.10a` (models/migration)
  - `S3-03b.10b` (service + env wiring)
  - `S3-03b.10c` (billing blueprint)
  - `S3-03b.10d` (Stripe webhook)
  - `S3-03b.10e` (entitlements + gating)
  - `S3-03b.10f` (nav/copy)
- `/billing` loads. No inline scripts/styles were added.

---

## 1) Stripe Dashboard — Test products & prices (exclusive tax)
1. In **Stripe Dashboard → Products**, create **two** products (or reuse):
   - **Pro** (MVP): add **Monthly** and **Annual** **recurring** prices.
   - (Optional) **Elite**: add **Monthly/Annual** as placeholders.
2. For each Price:
   - **Currency**: USD
   - **Tax behavior**: **Exclusive** (tax added at checkout/invoice).
   - **Billing scheme**: Per unit (qty=1).
3. (Recommended) Set a **product tax code** appropriate for SaaS/software to let Stripe Tax apply correct rules.
4. Copy each **Price ID** and paste into staging env vars (see `ENV_VARS.md`).

> You’ll enable **Automatic tax** in the Checkout session (already done in code) and in Stripe Tax settings.

---

## 2) Stripe Dashboard — Enable Stripe Tax & Customer Portal
1. **Settings → Tax**: turn on **Stripe Tax** and enable automatic calculation in test mode.
2. **Settings → Billing → Customer portal**:
   - Enable **Update payment method**
   - Enable **Upgrade/Downgrade plan** (optional now)
   - Enable **Cancel subscription** and choose **“at period end”** or **“immediately”** per your policy
   - Set **Return URL** to `${APP_BASE_URL}/billing`

---

## 3) Stripe Dashboard — Test webhook endpoint
1. **Developers → Webhooks → Add endpoint**:
   - **Endpoint URL**: `${APP_BASE_URL}/webhooks/stripe`
   - **Mode**: **Test**
   - **Events**:
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.paid`
     - `invoice.payment_failed`
     - (Optional) `customer.subscription.trial_will_end`
2. Copy the generated **Signing secret** and set `STRIPE_WEBHOOK_SECRET` on staging.

---

## 4) Staging service — set env & deploy
Set the following on your **staging** service:
- `APP_BASE_URL=https://<staging-host>`
- `ENABLE_STRIPE_TAX=true`
- `STRIPE_SECRET_KEY=sk_test_…`
- `STRIPE_PUBLISHABLE_KEY=pk_test_…`
- `STRIPE_WEBHOOK_SECRET=whsec_…`
- `STRIPE_PRICE_PRO_MONTHLY=price_…`
- `STRIPE_PRICE_PRO_ANNUAL=price_…`
- (Optional) ELITE price IDs

Redeploy the service so the app factory picks up new env values.

---

## 5) E2E Success path (subscribe)
1. Sign in to staging, go to **/billing**.
2. Click **Subscribe Monthly** (Pro).
3. On Stripe Checkout, pay with success test card:
   - Number: **4242 4242 4242 4242**
   - Exp: any future date; CVC: any 3 digits; ZIP: any 5 digits
4. After redirect to **/billing/success**, wait a moment for webhooks to post.
5. Verify in app:
   - Return to **/billing** → “Your organization has an active subscription.”
   - **Open Customer Portal** works.
6. Verify in DB:
   - `subscriptions` row for your `org_id` shows `status = active`, `price_id = STRIPE_PRICE_PRO_MONTHLY`.
   - `entitlements_json` includes `"exports.pdf"` and `"exports.csv"`.

---

## 6) E2E Failure path (payment failure)
1. Repeat subscription flow but use **decline** test card to force failure:
   - Number: **4000 0000 0000 0341** (declines on off-session invoice collections / attached default PM)
2. Expect **invoice.payment_failed** webhook and **non-active** subscription (e.g., `incomplete`/`past_due`).
3. App behavior:
   - Pro-gated actions (e.g., **PDF/CSV export**) return **403** (server-side decorator).
   - **/billing** suggests **Open Customer Portal** only if a customer exists; otherwise re-subscribe.

*(You can also use the Stripe CLI to trigger `invoice.payment_failed` in test mode while `stripe listen` forwards to your `/webhooks/stripe`.)*

---

## 7) Customer Portal — cancellation (at period end vs immediate)
1. With an **active** sub, open **Customer Portal** from **/billing**.
2. Click **Cancel**:
   - Choose **“at period end”** → verify DB shows `cancel_at_period_end=true` and `current_period_end` set; access continues until then.
   - Choose **“immediately”** (if enabled) → access should revoke (status becomes `canceled`).
3. App reflects status and messaging accordingly on **/billing**.

---

## 8) Optional advanced: Stripe Test Clocks
Use **Test Clocks** to move time forward and simulate renewals and retries without waiting in real time:
- Create a test clock; create a test subscription tied to that clock; advance time to the next period to fire renewal webhooks.
- This is optional for staging since the success/failure flows above already validate webhook handling.

---

## 9) Operational checks
- **Webhook logs**: Verify `billing_event_logs` increasing with event types and `signature_valid=true`.
- **Idempotency**: Re-send the same event from Stripe → your endpoint returns 200 with `duplicate=true` (in response JSON).
- **Security**: Confirm no secrets printed to app logs. CSRF is **not** applied to webhooks; Stripe signature check is.

---

## 10) Sign-off
- ✅ Success path: active sub, entitlements present, portal opens.
- ✅ Failure path: non-active sub, Pro routes gated (403).
- ✅ Cancellation: both **at period end** and **immediate** (if enabled) reflected in DB and UI.
- ✅ Webhooks: all relevant events received and applied.
- ✅ Taxes: line items show **tax added** at Checkout/invoice (exclusive tax policy).
