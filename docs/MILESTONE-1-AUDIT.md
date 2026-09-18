# Milestone 1 route, failure, and export audit

Date: September 17, 2026

Scope: the local single-process LPAPP prototype at the `v0.2.1` release candidate. Tests use
mocked AI responses and do not consume API credits.

## Reachable surface

`tests/test_surface_audit.py` records the complete Flask route/method inventory and the
production template/static inventory. It fails when a route or production asset appears
without an explicit audit update. Historical unreferenced files were moved to
`archive/legacy-ui` and are no longer served from production directories.

| Entry point | Paid generation | Primary safeguards | Failure behavior |
| --- | --- | --- | --- |
| Legacy lesson `/home` → `/output` | Explicit CSRF-protected POST only | Field bounds, allowed choices, complete section contract, attempt limits | Keeps inputs and previous lesson; safe 502/503 page |
| Legacy worksheet `/worksheet` → `/output` | Explicit CSRF-protected POST only | Topic/grade/count/type bounds, structured items, type-specific checks, attempt limits | Keeps worksheet inputs and modular draft; safe 502/503 page |
| Modular lesson `/builder/` | Generate or regenerate POST only | CSRF, revision token, section contract, content bounds, same-session request guard | Keeps last saved draft; renders safe 400/503 message |
| Handouts `/handouts/` | Generate POST only | CSRF, revision token, source linkage, exact item/answer contract, attempt limits | Keeps last saved handout; renders safe 400/503 message |

GET requests do not generate content. Legacy generation and reset are POST-only. Word/PDF
exports operate on saved content and do not call the model.

## Provider failures

The shared OpenAI boundary maps authentication, exhausted-credit, ordinary rate-limit,
timeout, connection, API-status, incomplete, empty, and oversized-response failures to
actionable messages without returning provider payloads. Route tests verify that all four
generation entry points preserve saved state when this boundary fails.

Automatic SDK retries are disabled. Attempts are reserved before contacting the provider;
failed calls count. The local SQLite counter supplies per-session hourly and application-wide
daily ceilings. These are request caps, not dollar budgets or distributed abuse protection.

## Exports

Automated tests cover Word export content, tables, merged/nested cells, lists, line breaks,
student/teacher answer separation, all four handout types, unavailable/invalid converters,
timeouts, temporary-directory isolation, stale-material blocking, and long lesson and
20-item handout exports. PDF route tests mock conversion.

The separate local integration check used synthetic content and made no AI call. The installed
Microsoft Word converter produced a 23-page Letter-size PDF from a 120-step lesson. Content
checks found the final lesson marker, question 20, answer exclusion in the student handout,
and answer inclusion in the teacher copy. Visual inspection of the first, middle, and final
PDF pages found clean margins, line wrapping, page breaks, and no clipping or overlap. Evidence
is stored under `lesson-export-qa/milestone1-closure` in the shared workspace.

## Acceptance result

Milestone 1 is complete for the local prototype. All reachable generation paths require an
explicit protected POST; invalid and failed requests preserve saved work; the audited route and
asset surface is regression tested; provider failures are translated into safe, useful messages;
and long export behavior is demonstrated in the installed local converter environment. The 86
offline tests pass without API calls. The production limits below remain assigned to Milestone 5
and do not weaken this local acceptance result.

## Explicit production limits after Milestone 1

- Same-session request serialization is process-local; multi-worker coordination and durable
  idempotency belong to production Milestone 5.
- Windows Word automation is a local converter, not a server deployment design. Linux hosting
  requires an installed and verified LibreOffice environment.
- Structural checks do not establish factual accuracy, standards alignment, correct answers,
  instructional quality, accessibility conformance, or classroom effectiveness.
- Secrets, session files, and quota databases are excluded from Git and require separate
  operational backup and retention controls if deployed.
