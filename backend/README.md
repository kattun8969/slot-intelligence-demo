# Community API foundation (not deployed)
This is a **server-side prototype** for Issue #66. No public endpoint, D1 database, production API key, or domain has been configured. The GitHub Pages UI is still local-only.

## API
- POST /api/reports: bearer 64-char hex anonymous edit secret; JSON {condition:{machine,origin,games,difference,differenceKind,cycle,points,hint},vote:"play"|"skip"}. Generates UUID.
- PATCH /api/reports/:id: same bearer secret; JSON {result,net}. Records previous state in revisions.
- DELETE /api/reports/:id: same secret, soft withdrawal.
- GET /api/summary?machine=...: returns the latest **scheduled snapshot** of counts by exact condition hash, vote and result, excluding withdrawn/quarantined.
- GET /api/health: readiness.

## Before production (required)
1. Configure a Cloudflare Worker with D1 binding `DB`, set `ALLOWED_ORIGIN` to exact public site origin, run `backend/schema.sql`.
2. The frontend now supports an optional meta community-api-base URL and per-browser edit token; it remains local-only while the meta value is empty. **Before enabling API** update the HTML Content-Security-Policy connect-src from 'none' to the exact HTTPS Worker origin, set meta community-api-base to the deployed Worker URL, and test browser CORS/preflight. Protect edit tokens against XSS and provide a recovery/export flow.
3. Implement server-side **abuse protection** beyond the current basic owner-token rate limit and simple same-condition burst quarantine (12 recent matching votes in 10 minutes): IP-derived short-lived throttling with privacy controls, Turnstile, suspicious identical-payload burst detection, quarantine + review/appeal. Client-generated tokens alone do **not** prevent Sybil attacks.
4. Add verified machine/condition definitions, integer/value constraints by machine, and authoritative expected-value/median data from ②. The checked-in data/ev/counter-rules.json currently has an empty rules array, so /api/analysis explicitly returns available:false. The API records null analysis snapshots: never present this as a validated snapshot.
5. Authenticated read and condition/vote editing are now in code, but need integration tests; add idempotency keys, robust duplicate handling for edited conditions, and test race conditions.
6. Deploy the scheduled snapshot job at 10:00, 16:00, 22:00 JST (UTC 01:00/07:00/13:00); see wrangler.example.toml. Scheduled snapshot logic exists but has not been deployed or end-to-end tested.
7. Add automated tests, data retention and privacy policy, secure admin moderation endpoint, observability, deployment checks and rollout plan.
8. Avoid representing crowd-sourced positive-report rate as win probability or expected value.

**Status:** foundation only; do not merge as a finished feature or enable public posting until these gates are complete.
