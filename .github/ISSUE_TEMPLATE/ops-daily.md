# ✅ Daily Ops Checklist
Follow the Runbook — Daily section. Mark each item and add brief notes. (Owner: you)

- [ ] **Health**: staging & production `/healthz` return 200
- [ ] **Errors**: Sentry triaged; no new critical spikes
- [ ] **Logs**: no unusual 5xx bursts / slow endpoints
- [ ] **Stripe**: failed webhooks/invoices handled (or tickets opened)
- [ ] **Rate limits**: no abnormal login/reset/signup blocks
- [ ] **PITR**: note “last restorable time” is fresh (within retention); record time in comment
- [ ] **Ops log**: append a one‑liner in `docs/ops/ops-log.md`

Refs: `docs/ops/runbook.md` (Daily). 
