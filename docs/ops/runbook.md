# Electrical Estimator SaaS — Ops Runbook
Version: v1.0 (YYYY‑MM‑DD)
Owner: ___________________  Secondary: ___________________

## Purpose
Single, repeatable path for daily reliability, releases, and recovery. Mirrors the Launch Roadmap and Phase gates. (Sources: Roadmap, Phase‑0/3/5, Collaboration Rules)

## Environments & Branches (the one path)
- Staging service: auto‑deploys from **`main`**
- Production service: auto‑deploys from **`prod`** (protected)
- Releases: PR from `main` → `prod` (“Release YYYY‑MM‑DD”), then follow Cutover
- Hotfix: branch from `prod`, PR back to `prod`, then PR the same commit to `main`

## Definitions & Targets
- RTO (restore time objective): ________ (e.g., ≤ 60 min)
- RPO (data loss window, PITR): within provider retention; verify monthly drill
- Error budget thresholds (initial): p95 latency ________, 5xx rate ________

---

## Daily Checklist (10–15 min)
[ ] Staging & Prod health green (`/healthz` returns 200)  
[ ] Sentry: new criticals triaged & assigned  
[ ] Stripe: failed webhooks/invoices reviewed; redeliver if needed  
[ ] Logs: scan for unusual 5xx bursts or auth spikes  
[ ] PITR continuity: “last recoverable time” < 24h and advancing; note “OK” in ops log

Artifacts: screenshot or brief note in Ops Log (date/time, initials)

## Weekly Checklist
[ ] Staging smoke passes: login → estimate → save/load → PDF export → (Stripe test in staging)  
[ ] Rate‑limit/auth: no abnormal blocks on login/reset/signup  
[ ] DB growth note: size delta and any index/slow‑query flags  
[ ] SEO endpoints: `/robots.txt` & `/sitemap.xml` reachable

Artifacts: “Staging green” note; tickets opened for anomalies

## Monthly Checklist
[ ] **PITR Restore Drill** (to a throwaway DB): restore → point a temp app → run smoke  
    Record: restore start/end, point‑in‑time restored, pass/fail, RTO achieved  
[ ] Dependency patch cycle (low‑risk): apply → staging smoke  
[ ] Secrets/Env inventory review: verify prod vars/keys match checklist

Artifacts: Drill log (timings + result), dependency notes, env checklist diff

## Quarterly Checklist
[ ] **DR Exercise** (table‑top + practical): rebuild clean staging from notes → restore from PITR → measure RTO/RPO  
[ ] Security/Privacy posture review (CSP/HSTS/cookies/Terms/Privacy/subprocessors)  
[ ] Alerting & limiter review; adjust thresholds if needed

Artifacts: DR report with timings; policy review notes

---

## Pre‑Release (T‑24h → T‑1h)
[ ] Freeze scope; staging (`main`) green on smoke  
[ ] Prepare **Release PR**: `main` → `prod` (protected)  
[ ] Comms drafted (if user‑visible changes)  
[ ] Migrations follow **expand/contract** (no destructive drops in this release)  
[ ] (If needed) lower DNS TTL to 300s

## Cutover (T=0)
1) Merge Release PR to `prod` → production deploy starts  
2) Run DB migrations (if applicable)  
3) Health check `/healthz` = 200  
4) **Production smoke**: login → create sample estimate → export PDF → Stripe live paths healthy  
5) Announce live (if applicable)

Stabilization (first 60 min)
- Monitor Sentry, logs, 5xx rate, p95 latency
- Verify webhooks & limiter OK

## Rollback (when thresholds are exceeded)
- **Code rollback**: revert `prod` to previous good commit; redeploy  
- **Feature flags**: disable new flags/entitlements immediately  
- **Database**: expand/contract strategy avoids DB rollback; if data risk: **PITR restore to a new DB**, validate, repoint app

### Rollback (fast path — PR Revert)

> One path only. No force‑pushes. Always revert the **Release PR** targeting `prod`.

1) GitHub → **Pull requests** → **Closed** → open the last **Release PR (`master` → `prod`)**.  
2) Click **Revert** (top‑right). GitHub creates a new PR with **base = `prod`**.  
3) **Create pull request** (Draft is fine), then **Squash and merge** to apply the revert.  
4) Watch Render **production** redeploy (it follows `prod`).  
5) Verify **/healthz = 200**, Sentry/logs stable, Stripe webhooks delivering.  
6) Add an Ops Log line noting the revert and open follow‑ups (root cause, forward‑fix).

_Timebox:_ if stabilization fails > 5 minutes (error budget thresholds breached), execute this **immediately**. 


Artifacts: incident note (symptoms, TTD/MTTR, action), follow‑ups ticketed

---

## Live Testing & Safety
- Ship new features **dark** behind server‑controlled flags (start with staff‑only → allowlist → widen)  
- Use expand/contract migrations in two releases (add/backfill → drop later)  
- Keep a “golden path” dataset in staging to mirror prod flows

---

## Ops Log (append entries)
- YYYY‑MM‑DD — Daily OK (initials): …  
- YYYY‑MM‑DD — Weekly smoke (pass/fail): …  
- YYYY‑MM‑DD — Monthly restore drill: start/end, RTO, result: …  
- YYYY‑MM‑DD — Release vYYYY.MM.DD: pass/fail, notes: …

---
