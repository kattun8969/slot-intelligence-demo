# Community API foundation (not deployed)
This is a **server-side prototype** for Issue #66. No public endpoint, D1 database, production API key, or domain has been configured. The GitHub Pages UI is still local-only.

## API
- POST /api/reports: bearer 64-char hex anonymous edit secret; JSON {condition:{machine,origin,games,difference,differenceKind,cycle,points,hint},vote:"play"|"skip"}. Generates UUID.
- PATCH /api/reports/:id: same bearer secret; JSON {result,net}. Records previous state in revisions.
- DELETE /api/reports/:id: same secret, soft withdrawal.
- GET /api/summary?machine=...: returns **raw** counts by exact condition hash and vote, excluding withdrawn/quarantined.
- GET /api/health: readiness.

## Before production (required)
1. Configure a Cloudflare Worker with D1 binding `DB`, set `ALLOWED_ORIGIN` to exact public site origin, run `backend/schema.sql`.
2. Connect the frontend via a configurable API URL and a per-user secure edit token; use HTTPS, no hardcoded service secrets. Implement confirmation and network error UX.
3. Implement server-side **abuse protection** beyond the current basic owner-token rate limit: IP-derived short-lived throttling with privacy controls, Turnstile, suspicious identical-payload burst detection, quarantine + review/appeal. Client-generated tokens alone do **not** prevent Sybil attacks.
4. Add verified machine/condition definitions, integer/value constraints by machine, and authoritative expected-value/median data from ②. The API currently records null analysis snapshots: never present this as a validated snapshot.
5. Add a read API for own report, support editing the condition/vote as well as result, and add durable revision history and idempotency keys.
6. Schedule aggregate snapshots at 10:00, 16:00, 22:00 JST (Cloudflare cron is UTC), with freshness timestamps. GET /api/summary currently computes live raw counts, **not** scheduled aggregates.
7. Add automated tests, data retention and privacy policy, secure admin moderation endpoint, observability, deployment checks and rollout plan.
8. Avoid representing crowd-sourced positive-report rate as win probability or expected value.

**Status:** foundation only; do not merge as a finished feature or enable public posting until these gates are complete.
