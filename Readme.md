# LPAPP

LPAPP is a Flask application that uses OpenAI to generate classroom lesson plans and worksheets. Teachers choose a lesson format, enter class context, and can download the generated material as a Word document.

## Features

- Eight studio approaches and six legacy lesson-plan formats, including WebQuest/SAMR, concept-based, skills-based, scaffolded reading, and discovery learning
- Configurable grade, class size, standards, and learner context
- Short-answer, fill-in-the-blank, matching, mixed, and multiple-choice worksheets
- In-memory Word document export
- Server-side sessions so generated content is not stored in browser cookies
- A browser-isolated local lesson library with saved/unsaved state and recovery snapshots

## Local setup

1. Install Python 3.11 or newer.
2. Run `setup_and_run.bat`, or create a virtual environment manually:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`.
4. Add a current OpenAI API key and a long, random Flask secret to `.env`.
5. Start the app:

   ```powershell
   python app.py
   ```

Then open <http://127.0.0.1:5000>.

The default model is `gpt-5.4-mini`. Set `OPENAI_MODEL` in `.env` to use another Responses API-compatible model.

## Tests

Tests mock the OpenAI boundary and do not make network requests:

```powershell
python -m unittest discover -s tests -v
```

GitHub Actions runs the same offline suite on pull requests and pushes to `main`,
`codex/modular-lesson-builder`, or `codex/ui-navigation-redesign`. The workflow supplies placeholders rather than real API
credentials, grants read-only repository access, cancels superseded runs, and does not
deploy the application. PDF route tests mock conversion; production converter checks remain
separate from CI.

## Releases and recovery

The application follows semantic versioning. `VERSION` is the single application version,
`CHANGELOG.md` records user-visible changes, and annotated Git tags preserve release
snapshots. See [docs/VERSIONING.md](docs/VERSIONING.md) for the release checklist and
safe rollback procedures. Committed code and release tags are backed up to GitHub; ignored
runtime files such as `.env`, session data, and quota databases require a separate encrypted
backup when they become operationally important.

## Security

Never commit `.env`, API keys, generated logs, or user data. See [SECURITY.md](SECURITY.md) for credential-rotation guidance.


## Modular lesson studio

Open `/builder/` to use a preset, customize a preset, or build from scratch.
The six existing instructional types remain available. Exploration now includes inquiry;
Skill Development includes explicit instruction. Backward Design and multi-session
Project-Based Learning are additional presets. Classroom, station-based and blended
learning are delivery options across approaches.

1. Choose a path, approach, sections, grade, session duration and classroom context.
2. Create an outline. This makes no AI request. Write sections yourself or generate them.
3. Save edits before rearranging, adding/removing or regenerating sections.
4. Review factual claims, standards, activities, exercise answers and timing.
5. Mark the draft teacher-reviewed and download Word. Any change clears that status.

The current modular draft is stored in the browser's server-side session. Use **Save to library**
to retain it in local SQLite storage, reopen it later, rename or delete it, and inspect recovery
versions. Separate tabs share the current draft; stale submissions are rejected. Opening legacy
worksheets preserves the modular draft.

The accountless library uses an opaque owner identifier stored in the browser's signed session.
Every read and mutation is scoped to that identifier. It retains up to 25 lessons, 20 snapshots
per lesson, and removes lessons after 90 days without a save. Full-plan and section-level AI
generation first snapshots any unsaved edits. Restoring a snapshot opens it as an unsaved draft,
so the current saved copy remains available until the teacher explicitly saves. Clearing site data
can remove access to this local library; Word and PDF exports remain the portable backup.

### What checks mean

AI output must be JSON containing every requested section exactly once with nonempty
text. Invalid output and API failures leave the previous draft intact. Input bounds,
CSRF protection on builder mutations, and revision checks guard the editing workflow.
The app flags missing objectives, assessment, answer keys and source context.

Source excerpts are teacher supplied. URLs are not fetched; citations, source quality,
standards alignment, factual accuracy, timing and answer correctness are NOT independently
verified. Prompt instructions request evidence and uncertainty labels but do not guarantee
compliance. Teacher review is an acknowledgement, not certification. Independent retrieval,
claim verification and mathematical answer validation remain future work.

The app is a local prototype: it has no authentication, cross-device library, deployment rate
limits, or independent educational-quality evaluation. Do not expose its paid generation
routes publicly without access and usage controls. Do not enter student identifying records.

Tests use mocked AI responses. Real-model output quality must be evaluated separately.


## Student practice handouts

After saving a lesson section, open Student handouts from the builder. Create an outline
with 1–20 exercises; enter questions and answers manually or generate them from the
selected section. Save before exporting separate student and teacher Word copies.
The print-friendly design supports 10–18 pt text, 1–8 writing lines and Letter/A4 paper.
Answers are stored separately and omitted from the student export; teachers must still
check that prompts themselves do not reveal answers. All content remains unverified.

A lesson content/configuration change flags the handout and pauses export until the teacher
regenerates it or acknowledges reviewing its alignment. One worksheet is stored within
the current session draft; starting a new lesson replaces it. Handouts are not yet stored as
independent library records, and image uploads remain pending. Automatic PDF downloads require a configured converter (see below).
No additional graphics packages are required for this initial text-based workflow.


### Handout types and themes

Choose Practice worksheet, Guided notes, Reference sheet or Exit ticket when creating
an outline. Exit tickets allow up to five checks. Reference sheets contain student-facing
explanations and examples, with no blank writing lines; teacher-only guidance remains separate.

Print-friendly exports use black text. Clean classroom adds restrained teal, blue or plum
accents to handout labels and sections. Both preserve the content, numbering and answer
separation. Theme changes require no AI generation. Existing session worksheets default
to Practice / Print-friendly. One handout per lesson remains the current limit.


## Automatic PDF downloads

Lesson Studio, student/teacher handouts, and the legacy lesson/worksheet results offer PDF
alongside Word. PDF conversion uses the same DOCX document; no AI call is made.
For server hosting, install LibreOffice on the machine running Flask. On Windows the default location is
C:\Program Files\LibreOffice\program\soffice.com; on Linux use `soffice` on PATH.
For another installation location set LIBREOFFICE_PATH to the executable (not a command).

Each request has an isolated temporary directory and LibreOffice profile. Two conversions
can run at once; further requests receive a retry message. Conversion has a 60-second
limit, validates the PDF signature and cleans temporary documents after completion.
Missing converters, timeout and invalid output leave drafts unchanged; Word is available.
Use matching fonts on deployment hosts and visually check long exports. The local app
remains a prototype; public hosting still needs access and resource controls.


### Windows desktop conversion

The default PDF_BACKEND=auto prefers LibreOffice and, on Windows with Microsoft Word
registered, falls back to an isolated PowerShell conversion using Word. PDF_BACKEND=word
or PDF_BACKEND=libreoffice selects explicitly. Word conversion is intended for a signed-in
local desktop, not unattended production hosting. It runs one job at a time, disables
macros and closes the document/application after conversion. A timeout stops the spawned
converter and its recorded Word process. LibreOffice remains the deployment recommendation.

The LibreOffice installation attempt on this computer was cancelled because its download
was too slow; the existing Word installation supplies local PDF downloads.

### Local request safety

The current single-process app rejects simultaneous requests for the same session with
HTTP 409. Wait for the active request to finish, then reload before retrying. This prevents
local overlapping operations from overwriting session drafts. It is not cross-worker
locking, rate limiting, or durable idempotency. Production requires shared coordination.
`SESSION_COOKIE_SECURE=true` enables HTTPS-only cookies on a TLS deployment; leave it off
for the local HTTP preview. `/health` reports process responsiveness; `/version` reports
the application version. See RELIABILITY-AUDIT.md for remaining release blockers.


Legacy generation now requires an explicit CSRF-protected POST; GET /output never calls AI.
Reset is POST-only. Tests submit tokens from rendered forms and separately verify that
missing, wrong, and other-session tokens preserve saved state and cannot call generation.

## Generation limits and boundary validation

All real AI requests reserve an attempt in SQLite before contacting the provider.
Defaults: 10 attempts per browser session per fixed UTC hour and 100 attempts across
this app per UTC day. Configure GENERATION_SESSION_HOURLY and GENERATION_GLOBAL_DAILY
with positive integers. Failures count because a failed response may still incur cost.
Automatic SDK retries are disabled so one reservation cannot silently send a second
request. Editing, manual handout creation and exports do not consume attempts.

The default counter database is instance/generation-limits.sqlite3. Processes sharing
that local database use atomic transactions; configure GENERATION_LIMIT_DB to place it
on persistent local storage. This does not solve session-write coordination. Separate
hosts/databases have separate quotas; do not deploy this as a distributed budget system.
Cookie clearing can reset the visitor identity, but cannot reset the shared daily count.
These are attempt caps, not dollar spending limits or comprehensive abuse protection.
Invalid settings or an unavailable counter database pause generation safely.

Requests exceeding 150,000 content characters are rejected before reserving an attempt.
Only completed provider responses with nonempty text of at most 200,000 characters are
accepted. Existing 12,000 output-token cap still applies. These structural checks do not
verify factual accuracy or establish legacy worksheet question/answer completeness.

## Legacy worksheet completeness

Legacy worksheet generation now requests JSON records with consecutive integer IDs and
nonempty question/answer fields. The app checks the exact requested count, fields, IDs,
and 4,000-character per-field limits before rendering the existing numbered worksheet
and answer-key view. Invalid output returns a retry page without saving partial content;
inputs and the separate modular draft remain intact. This is application-side validation,
not API-enforced Structured Outputs, factual verification, or proof of answer correctness.
Legacy lesson context fields now have type/length bounds and cultural-context list limits.

## Question types and form recovery

Multiple-choice worksheets require exactly four distinct A-D options and an answer label
with explanation. True/false answers require an explicit truth value and explanation.
Matching items require 2-10 labeled entries in each column and complete one-to-one answer
mappings. Fill-in-the-blank items require a blank. Short-answer, essay and legacy Mix retain
the basic completeness contract; Mix does not yet validate each item's subtype. These are
format checks, not semantic correctness or independent verification.

Invalid legacy lesson/worksheet submissions re-render escaped submitted values and an
error message, retaining text, selections and checkboxes without changing saved content.


Mixed worksheets cycle through short answer, fill-in-the-blank and matching. Each item
includes a validated subtype; all matching/blank checks apply. The worksheet form now
exposes Mixed. Double Line Breaks now renders actual blank lines. Legacy select/checkbox
values are checked against the supported options, with template-parity regression coverage.
The preview contact page explicitly states it has no messaging service.
