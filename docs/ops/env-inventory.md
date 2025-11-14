# Env Inventory — Production & Staging (Monthly)
Owner: __________   Date: __________   Reviewed release/tag: __________

> Purpose: verify that all required environment variables & connection points exist and are correct in **PROD** (and STAGING as needed). Do **NOT** store secrets here. Record presence, intent, and the **last 4** of any tokens only.  
> Where to check: Render → Service → **Settings → Environment** (app) and Render → **PostgreSQL** (DB) → Connection / Backups.

---

## A. Application Base & Security
- [ ] **APP_BASE_URL (prod)** present; matches public domain (https). Note: __________
- [ ] **SECRET_KEY (prod)** present; not default/dev value. Rotated in last 12 months?  ☐ Yes ☐ No  Note: __________
- [ ] **SESSION cookies** secure flags enforced in prod (Secure/HttpOnly/SameSite). Note: __________

## B. Database (PostgreSQL)
- [ ] **DATABASE_URL / SQLALCHEMY URI (prod)** present; correct host/DB name. Note: __________
- [ ] **TLS required** on DB connection if policy requires. Note: __________
- [ ] **PITR enabled**; retention window known. Note: __________
- [ ] **Prod PITR “Last restorable time”** (copy time only): __________ (UTC)
- [ ] **Staging DB URL** present (no prod secrets in staging). Note: __________

## C. Redis / Rate Limiting
- [ ] **REDIS_URL (prod)** present and reachable. Note: __________
- [ ] Limiter uses Redis in **prod**; memory only in **dev**. Note: __________

## D. Observability
- [ ] **SENTRY_DSN (prod)** present; environment=production set. Note: __________
- [ ] Log format is JSON in prod (request IDs / correlation). Note: __________

## E. Email (SMTP / Provider)
- [ ] **MAIL_SERVER / Port / TLS** present for prod. Note: __________
- [ ] **MAIL_USERNAME** present (no test creds). Note: __________
- [ ] **MAIL_PASSWORD / API key** present (last 4: ____). Note: __________
- [ ] **MAIL_DEFAULT_SENDER / From** verified. Note: __________

## F. Billing (Stripe — LIVE)
- [ ] **STRIPE_SECRET_KEY (prod)** present (last 4: ____). Note: __________
- [ ] **STRIPE_PUBLISHABLE_KEY (prod)** present (last 4: ____). Note: __________
- [ ] **STRIPE_WEBHOOK_SECRET (prod)** present (last 4: ____). Note: __________
- [ ] Stripe dashboard → webhook endpoint URL points to prod `/webhooks/stripe` and delivers OK. Note: __________

## G. Analytics / SEO
- [ ] Analytics env (e.g., **PLAUSIBLE** or GA) present; domain configured. Note: __________
- [ ] `/robots.txt` and `/sitemap.xml` served in prod. Note: __________

## H. Misc / App-specific
- [ ] Any **feature flag** or entitlement envs present as needed. Note: __________
- [ ] Any 3rd‑party API keys present (names + last 4 only). Note: __________

---

### Sign‑off
Reviewer initials: ___   Date: ___   Issues opened (links): ____________________

> Reference: Runbook (Monthly checklist: “Secrets/Env inventory review”) and Phase‑3.9 “Secrets & Env Inventory”. Do not paste any secret values into this file.  
