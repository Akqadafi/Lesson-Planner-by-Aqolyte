# Inspecting the Lesson Planner tests

These test files are stored locally alongside the app. They use Python unittest and mocked AI responses; they do not send prompts to OpenAI or incur API charges.

| File | Coverage |
| --- | --- |
| test_app.py | Basic routes, invalid preset selection, classroom context, reuse of saved results, Word download |
| test_builder.py | Three construction paths and eight presets, form assets, invalid inputs, CSRF, stale edits, generation failure recovery, individual regeneration, section editing/order/removal, exports, worksheet choices, escaping and draft preservation |
| test_lesson_planner.py | Legacy response parsing, prompt context and invalid preset rejection |
| test_reliability.py | All six legacy presets reject incomplete/duplicate/empty/unexpected sections; recovery of previous drafts; Word tables, merged/nested cells, lists, line breaks and content order |
| test_worksheet_generator.py | Worksheet prompting, supported question types and question-count bounds |

## Latest result

2026-09-15: all 50 tests passed after adding PDF export routes and failure handling.
Detailed output: ../../lesson-export-qa/test-results.txt
Sample Word export: ../../lesson-export-qa/table-sample.docx
Sample rendered PDF: ../../lesson-export-qa/table-sample.pdf

## Run locally

From the lesson-planner-app directory, use an environment with requirements.txt installed:

```powershell
python -m unittest discover -s tests -v
```

The existing review environment on this computer can also run the suite:

```powershell
..\lpapp-review\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Read a test's assertions to see exactly what it verifies. A passing test does not establish the factual accuracy or teaching quality of real AI-generated lessons. The sample export is synthetic QA material, not evidence of live-model quality. Multi-page export checks, broad browser checks, independent standards verification and teacher evaluation remain in the work plan.

`test_handouts.py` covers manual creation, editing, source context, separate student/teacher exports, stale lessons, input validation and atomic generation failure recovery.

`test_handout_types.py` checks all four formats, type-specific generation guidance, exit-ticket limits, and theme changes that preserve content without AI.

`test_pdf_export.py` uses simulated converter responses to check export routes, answer separation, stale-handout blocking, timeout handling, isolated profiles and temporary-file cleanup. Real LibreOffice conversion is checked separately with synthetic documents; it uses no AI credits.

### September 16 reliability increment

Added regression cases for atomic rejected saves, concurrent same-session generation/edit
requests, safe health/version responses, and malformed worksheet delimiters. These tests
mock AI calls; the concurrency test uses separate clients sharing a session and coordinates
an in-flight model response with threading events.
