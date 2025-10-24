# Entitlements & Server-Side Gating (MVP)

**Plans**
- **PRO (MVP)**: `core.app`, `assemblies.core`, `libraries.manage`, `customers.crud`, `exports.pdf`, `exports.csv`, `billing.portal`
- **ELITE**: placeholder superset (future add-ons)

**Status rules**
- Allowed: `active` (and `trialing`, if used)
- Blocked: `past_due`, `incomplete`, `incomplete_expired`, `unpaid`, `canceled`
- `cancel_at_period_end`: still allowed until `current_period_end`

**Enforcement**
- **Coarse gate** (`enforce_active_subscription`) runs at blueprint level for **/estimator**, **/estimates**, **/libraries**.
  - HTML → 303 redirect to `/billing` + flash
  - JSON → `403 {"error":"entitlement_required","missing":"active_subscription"}`
- **Fine gate** (`@require_entitlement`) already on exports; extend as we add Elite features.

**Always allow**
- `/billing` (plans/checkout/portal), auth flows, and help/docs.

**Privacy**
- No secrets in logs; gating depends on `Subscription.status` and `entitlements_json` snapshot only.
