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

## September 17 increment

Added shared-entry-point generation attempt limits using local SQLite transactions,
per-session hourly and app-wide daily windows. Failed attempts count; automatic SDK
retries are disabled. Added aggregate request-size bounds and rejection of incomplete,
empty, malformed or oversized provider text. Quotas do not establish dollar budgets,
distributed-host protection, or durable request idempotency. Legacy worksheet structure
and broader field/enum audits remain open.

## September 17 worksheet contract increment

Closed the basic legacy worksheet completeness gap: exact item count, consecutive integer
IDs, bounded/nonempty questions and answers, no unexpected fields, and explicit malformed
output recovery. Added legacy lesson context text/list validation before AI calls.
Still pending: type-specific checks (e.g. four multiple-choice options), factual/answer
verification, enum audit, complete form-value recovery, and API-enforced schemas.

## Question-type and recovery increment

Added multiple-choice, true/false, matching and blank-format checks. Legacy form validation
errors now retain submitted text, selects and checkboxes, with escaped values. Remaining:
per-item subtype validation for Mix, semantic answer checks, full enum/claims audit, and
production coordination/idempotency. Milestone 1 remains open.


## Mixed worksheets, allowed choices and claims audit

Added per-item mixed worksheet types and deterministic short-answer/blank/matching rotation;
all subtype checks apply. Exposed Mixed in the form and fixed literal newline delimiters.
Validated legacy state, socioeconomic, approach and culture selections against supported
choices; retained bounded free-text experiential context. Tests check all six form option
sets against backend choices. Updated reachable home/features/contact/entry pages and
legacy prompts: no contact submission service, no permanent library, no independently
verified facts/standards. Existing unused templates are not evidence of delivered features.
Remaining Milestone 1 closure work: runtime assets/obsolete-route cleanup, full browser
walkthrough and export checks, durable idempotency and production session coordination.
Semantic accuracy and API-enforced schemas remain later milestones.

## Workflow review and cleanup

Added an end-to-end HTTP workflow test using tokens/revisions read from rendered forms:
manual outline, edit, review, lesson Word export, handout creation/edit, separate student
and teacher exports, source-change export block, acknowledgement, and successful re-export.
No AI calls occur. Added navigation/local-asset coverage across ten entry pages; fixed the
missing favicon reference by using the existing logo. Removed an unused document import.
Unreferenced historical text/template artifacts were identified but retained pending a
repository archive decision; no user-authored historical content was deleted.
This is HTTP/document-content verification, not a visual browser or live-model evaluation.
Remaining release work: visual/mobile/accessibility walkthrough, production session
coordination and idempotency, and GitHub/CI. Do not claim Milestone 1 is fully closed.

## Continuous integration — September 17

Added a GitHub Actions workflow that runs the complete offline unittest suite on pull
requests and pushes to `main` or `codex/modular-lesson-builder`. It uses read-only
repository permissions, placeholder credentials, Python 3.12, cached dependencies, a
15-minute timeout, and cancellation of superseded runs. It does not call the OpenAI API,
perform real PDF conversion, publish an image, or deploy the app. The complete local suite
passed 75 tests before the workflow was committed.

## Browser/mobile review — September 17

Inspected the existing lesson editor at desktop/default and 390x844 viewport sizes,
plus worksheet and handout setup at mobile width. Did not alter the user's draft or
call AI. Fixed legacy half-width mobile forms, enlarged mobile controls, and exempted
static GET/HEAD requests from session serialization so concurrent stylesheet/script/image
loads cannot receive busy responses. A regression test verifies static loading while a
generation request holds the session lock; all four targeted audit tests passed.
After restart, visually verified the wider worksheet and restored logo and inspected
handout setup. Reset viewport to normal. This is a focused visual review, not a full
accessibility certification or all-device test; keyboard/screen-reader and long-content
edge cases remain for broader usability testing.
