# Inspecting the Lesson Planner tests

These test files are stored locally alongside the app. They use Python unittest and mocked AI responses; they do not send prompts to OpenAI or incur API charges.

| File | Coverage |
| --- | --- |
| test_app.py | Basic routes, invalid preset selection, classroom context, reuse of saved results, Word download |
| test_builder.py | Three construction paths and eight presets, form assets, invalid inputs, CSRF, stale edits, generation failure recovery, individual regeneration, section editing/order/removal, exports, worksheet choices, escaping and draft preservation |
| test_lesson_planner.py | Legacy response parsing, prompt context and invalid preset rejection |
| test_reliability.py | All six legacy presets reject incomplete/duplicate/empty/unexpected sections; recovery of previous drafts; Word tables, merged/nested cells, lists, line breaks and content order |
| test_worksheet_generator.py | Worksheet prompting, supported question types and question-count bounds |
| test_service_errors.py | Provider authentication, credit, rate-limit, timeout, network, API-status, empty, incomplete, and oversized-response handling |
| test_surface_audit.py | Exact reachable route/method and production template/static-asset inventory |

## Latest result

2026-09-17: all 86 offline tests passed after the Milestone 1 closure audit. The suite uses
mocked AI responses and made no paid API calls. It covers every generation entry point,
provider-failure recovery, the audited route/asset surface, and long lesson and 20-item
student/teacher handout exports.

The active `codex/ui-navigation-redesign` branch has 94 passing offline tests. Coverage now
includes dedicated prior-knowledge context, teacher-described learner support, strict generated
activity records, manual structured-activity editing, multi-session instruction/transition totals,
overbooking review blocks, exports, and downstream handout invalidation. The branch remains
separate from the `v0.2.1` release on `main`.

The separate synthetic integration artifacts are stored in
`../../lesson-export-qa/milestone1-closure`. The installed Microsoft Word converter produced a
23-page PDF; representative pages were visually inspected for clipping, overlap, wrapping, and
page breaks.

## Run locally

From the lesson-planner-app directory, use an environment with requirements.txt installed:

```powershell
python -m unittest discover -s tests -v
```

The existing review environment on this computer can also run the suite:

```powershell
..\lpapp-review\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Read a test's assertions to see exactly what it verifies. A passing test does not establish the factual accuracy or teaching quality of real AI-generated lessons. The sample export is synthetic QA material, not evidence of live-model quality. Broader accessibility checks, production Linux conversion, independent standards verification, and teacher evaluation remain in the work plan.

`test_handouts.py` covers manual creation, editing, source context, separate student/teacher exports, stale lessons, input validation and atomic generation failure recovery.

`test_handout_types.py` checks all four formats, type-specific generation guidance, exit-ticket limits, and theme changes that preserve content without AI.

`test_pdf_export.py` uses simulated converter responses to check export routes, answer separation, stale-handout blocking, timeout handling, isolated profiles and temporary-file cleanup. Real LibreOffice conversion is checked separately with synthetic documents; it uses no AI credits.

### September 16 reliability increment

Added regression cases for atomic rejected saves, concurrent same-session generation/edit
requests, safe health/version responses, and malformed worksheet delimiters. These tests
mock AI calls; the concurrency test uses separate clients sharing a session and coordinates
an in-flight model response with threading events.


Legacy generation now requires an explicit CSRF-protected POST; GET /output never calls AI.
Reset is POST-only. Tests submit tokens from rendered forms and separately verify that
missing, wrong, and other-session tokens preserve saved state and cannot call generation.

September 17 coverage adds concurrent quota reservations, fixed-window resets, failed
attempt accounting, fail-closed configuration, pre-provider input rejection, and incomplete
output rejection. Counter tests use temporary databases; provider calls are mocked.

Worksheet contract tests reject missing/extra items, duplicate or noninteger IDs, missing
and empty answers, oversized fields, and malformed JSON. Route coverage verifies retry
behavior and preservation of inputs and unrelated drafts. No live model calls are made.

Type/recovery tests cover valid and broken option labels, duplicate choices, incomplete
matching maps, true/false formatting, and escaped restoration of text/select/checkbox values.

Mixed worksheet coverage checks per-item subtypes, small counts, malformed blanks, actual
blank-line delimiters, forged options, and template/backend parity across all six legacy
lesson forms. These are deterministic tests with mocked AI; they do not measure learning
outcomes or factual accuracy.
