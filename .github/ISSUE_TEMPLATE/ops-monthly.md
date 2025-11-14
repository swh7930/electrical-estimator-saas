# 🗓️ Monthly Ops Checklist
> Reference: [Env Inventory checklist](docs/ops/env-inventory.md) — open and complete it before ticking the items below.

- [ ] **PITR restore drill** to a NEW DB: restore → point temp app → smoke test; record start/end + RTO
- [ ] **Dependency patch** cycle reviewed/applied in staging
- [ ] **Secrets/Env**: production inventory verified (DB URL, SECRET_KEY, STRIPE live keys, webhook secret, Redis, Sentry, APP_BASE_URL, mail, analytics)
- [ ] **Ops log**: record drill timing and findings

Refs: `docs/ops/runbook.md` (Monthly). 
