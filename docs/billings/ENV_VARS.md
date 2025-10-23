# Billing — Environment Variables (Test/Staging vs Live)

All values are read by `app/config.py` and must be set per environment (local, staging, production).

> **Never** put secrets in code or templates. Keep everything in env vars.

## Core

| Variable | Required | Purpose | Notes |
|---|---|---|---|
| `APP_BASE_URL` | ✅ | Absolute base URL used in links (emails, checkout success/cancel, portal return). | Must be **HTTPS** for staging/prod, e.g. `https://staging.<your-domain>` |
| `ENABLE_STRIPE_TAX` | ✅ | Enables automatic Stripe Tax calculation. | For this project, **exclusive tax** (tax added at checkout/invoice). Use `"true"` |

## Stripe — Keys & Webhook (per mode)

| Variable | Required | Purpose | Notes |
|---|---|---|---|
| `STRIPE_SECRET_KEY` | ✅ | Server-side secret API key. | **Test mode**: starts with `sk_test_…`. **Live**: `sk_live_…` |
| `STRIPE_PUBLISHABLE_KEY` | ✅ | Stripe.js key for client. | **Test mode**: `pk_test_…`. **Live**: `pk_live_…` |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Verifies webhook signature for `/webhooks/stripe`. | Use the **Test** endpoint’s secret on staging; **Live** on production. |

## Stripe — Price IDs (exclusive tax)

Create these in Stripe **Products → Prices** and paste the **Price IDs** here.
(Names/amounts can be changed in Stripe later; **IDs are immutable**.)

| Variable | Required | Purpose |
|---|---|---|
| `STRIPE_PRICE_PRO_MONTHLY` | ✅ | Pro (MVP) Monthly subscription Price ID (e.g., `price_…`). |
| `STRIPE_PRICE_PRO_ANNUAL` | ✅ | Pro (MVP) Annual subscription Price ID. |
| `STRIPE_PRICE_ELITE_MONTHLY` | 〰️ | Elite Monthly Price ID (optional at launch). |
| `STRIPE_PRICE_ELITE_ANNUAL` | 〰️ | Elite Annual Price ID (optional at launch). |

## Sanity Checklist

- Staging (test mode): keys are `sk_test_*`, `pk_test_*`; webhook secret from **Test** endpoint; Price IDs from **Test** products.
- Production (live): keys are `sk_live_*`, `pk_live_*`; webhook secret from **Live** endpoint; Price IDs from **Live** products.
- `APP_BASE_URL` points to the correct host (`https://staging…` vs `https://app…`).
