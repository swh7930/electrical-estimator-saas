# Staging Smoke Test (10 minutes)
Purpose: Quick end‑to‑end verification before promoting `master` → `prod`. Use this only on **staging**.  
Refs: Runbook §“Pre‑Release / Staging green on smoke”, §“Cutover” and Phase 3.6.  
Do not change production data or keys during this test.

## Pre‑reqs
- Staging URL: https://<staging-host>/
- Test user creds (staging): __________
- Stripe **test** mode configured in staging (not live).

## Steps

1) Health & Auth (2 min)
- Open `https://<staging-host>/healthz` → **200** expected.  
- Log in with the **staging** test user; confirm landing page loads without 5xx.  
- Log out, then log in again (cookie/session check).

2) Create or Open an Estimate (3 min)
- From dashboard, **create a new estimate** (or open an existing test estimate).  
- Add one **Assembly** and at least one **Material**; change quantities; totals must update.  
- Save the estimate; navigate away (e.g., Home), then return and verify the saved data persists.

3) Export (WeasyPrint) (2 min)
- Export the estimate to **PDF**.  
- Open the PDF and visually confirm: header/footer render, line items present, currency formatting, no missing CSS (base_url works).

4) Billing & Entitlements (2 min)
- If your test user is **Free**, try a Pro‑gated action → should show gating/upgrade path.  
- If testing checkout: start a **Stripe test** checkout (staging only) using `4242 4242 4242 4242`, any future expiry, any CVC.  
- After success, confirm you return to the app and that entitlements update for the test account.

5) Webhooks & Errors (1 min)
- In Stripe dashboard (staging project), ensure the latest event delivered to `…/webhooks/stripe` is **Succeeded** (no retries pending).  
- Glance at Sentry or staging logs for any new **critical** errors during this run.

## Pass/Fail Criteria
- ✅ `/healthz` = 200; login/session OK.  
- ✅ Create → save → reload estimate works; totals recalc correctly.  
- ✅ PDF export renders correctly (no missing styles).  
- ✅ Entitlement gate behaves as expected; if checkout tested, webhook delivered.  
- ✅ No new critical errors in Sentry/logs.

## Notes (paste into Release PR)
- Tester: ___   Date/Time (UTC): ___  
- Staging URL: ___   Estimate ID (if used): ___  
- Stripe test charge ID (if used): ___  
- Issues found: (links)

---
