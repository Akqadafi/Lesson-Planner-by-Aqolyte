# Reliability audit — September 16, 2026

Scope: current local feature branch; no paid API calls or production deployment.

## Fixed in this increment

- Builder saves now edit a deep copy. A validation failure in a later section cannot leave earlier sections partially changed in the session.
- A bounded, per-session WSGI guard rejects overlapping requests with HTTP 409 before Flask loads session data. Covers legacy generation, builder, handouts, navigation, and exports in the current single-process app. Locks release after Flask saves the session, including failure paths. This is not a rate limiter, idempotency store, or multi-process lock.
- Worksheet topics and delimiters have generator-level bounds; the legacy form rejects overlong/multiline delimiters before altering saved state.
- Removed the contradictory classroom-ready wording from the worksheet prompt.
- Explicit HttpOnly/SameSite=Lax session cookies; secure cookies configurable for HTTPS. Local HTTP keeps Secure disabled.
- Added minimal /health and /version responses. Health indicates process responsiveness, not provider or database readiness.

## Remaining findings / priority

1. CLOSED: Legacy POST routes now require session CSRF tokens. /clear_cache accepts POST only. /output GET displays saved content or a generation confirmation; only an explicit protected generate POST may call AI. Successful generation redirects to GET. Rendered forms and recovery/download submissions carry tokens.
2. Shared session concurrency protection is required before multi-worker deployment. Current process-local guard deliberately returns retry responses rather than queuing stale requests. A rejected racing edit is not saved; reload after the current request finishes.
3. Per-visitor quotas, burst limits, global budgets and request idempotency remain absent. Cookie-based session serialization is not abuse protection.
4. Legacy worksheet output remains free text without structural question/answer completeness validation. API-enforced schemas remain pending.
5. Complete legacy field/enum limits, saved-input recovery, response-size limits, and visible claims audit. Existing strict section-count checks do not establish factual accuracy.
6. Durable plan storage, standards verification and quality evaluation remain separate later milestones.

Next increment: generation quotas/idempotency and broader legacy validation/output contracts. Do not mark Milestone 1 complete yet.
