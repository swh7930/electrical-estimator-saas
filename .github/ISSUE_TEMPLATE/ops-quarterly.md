# 🧭 Quarterly Ops Checklist
- [ ] **DR exercise** (table‑top + practical): rebuild clean staging → restore from PITR → measure RTO/RPO
- [ ] **Security/Privacy**: CSP/HSTS/cookies/Terms/Privacy/subprocessors review
- [ ] **Alerting & limiter** thresholds reviewed
- [ ] **Key rotations** (Stripe webhook secret, others as planned); session strategy considered for SECRET_KEY
- [ ] **Performance & cost**: p95 target + one cost action set
- [ ] **Ops log**: add quarterly summary

Refs: `docs/ops/runbook.md` (Quarterly). 
