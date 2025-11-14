# Release PR — Promote to Production (`prod`)
> Use this template **only** when promoting from the staging branch (`master`) to `prod`.

**Release tag:** vYYYY.MM.DD  
**Source commit (short SHA):** ________  
**Change type:** Release / Hotfix

---

## Pre‑Flight (must be ✅ before merge)
> Reference: [Staging Smoke Test script](docs/ops/smoke-staging.md)
- [ ] **Staging green** on smoke: login → estimate create/save → export (PDF) → (Stripe test in staging). Link run/output.
- [ ] **Migrations:** expand/contract only; no destructive drops in this release.
- [ ] **Feature exposure:** default safe; new features behind flags/entitlements.
- [ ] **Env inventory (prod) verified:** `DATABASE_URL`, `SECRET_KEY`, `STRIPE_LIVE_KEYS`, `STRIPE_WEBHOOK_SECRET`, `REDIS_URL`, `SENTRY_DSN`, `APP_BASE_URL`, mail creds, analytics. Note any changes.
- [ ] **Security headers:** HTTPS redirect, HSTS, CSP (Stripe + prints) clean; cookies secure.
- [ ] **Runbook owners on call** and aware of T=0 window.

## Cutover Plan (T=0)
- [ ] Change freeze announced (30 min prior).
- [ ] PITR **last restorable time** recorded: __________
- [ ] Health endpoint confirmed (`/healthz`) and Render healthCheck aligned.
- [ ] (If needed) DNS TTL lowered to 300s.

## Post‑Deploy (Stabilization 15–30 min)
- [ ] `/healthz` returns 200.
- [ ] **Production smoke:** login → sample estimate → export PDF → (live Stripe path healthy).
- [ ] **Monitoring:** Sentry shows no new critical surges; 5xx rate & p95 latency within thresholds.
- [ ] **Webhooks:** Stripe deliveries successful (no undelivered events).

## Rollback Plan (fill before merge)
- [ ] Previous good tag: **vYYYY.MM.DD‑X**
- [ ] **Code rollback:** revert `prod` to the tag above; redeploy.
- [ ] **DB stance:** expand/contract means no DB rollback; if data risk, **PITR restore to a new DB**, validate, then repoint.
- [ ] Communication plan prepared (internal + user‑visible if needed).

## Approvals
- [ ] **Owner:** __________
- [ ] **Reviewer:** __________

## Release Notes (user‑visible)
- …

## Links
- Runbook: `docs/ops/runbook.md`
- Roadmap / Phases reference
