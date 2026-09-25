# Changelog

All notable changes to LPAPP are recorded here. The project uses
[Semantic Versioning](https://semver.org/) beginning with the 0.2.0 baseline.

## [Unreleased]

### Changed

- Reframed the experimental homepage around Aqolyte LLC as the parent company for web,
  educational, and applied AI tools, with Lesson Planner presented as its first product
- Rebuilt About, Products, and Contact with the corporate design system and simplified the
  company-to-product path so the direct Lesson Planner launch appears only on Products
- Restyled worksheet setup, generation confirmation, error, and result screens with the
  Lesson Planner application theme and removed the redundant self-link from its header
- Added dedicated prior-knowledge context to the modular studio and all six legacy lesson
  formats, with server-side length validation and prompt integration
- Replaced broad demographic classifications with optional teacher-described learner support
  and restricted saved legacy submissions to the supported lesson fields
- Added validated structured activity fields for objectives, session assignment, instruction and
  transition time, grouping, materials, teacher steps, student directions, assessment, and supports
- Added per-session timing summaries that flag overbooked plans and prevent teacher-review status
  until structured activities are complete and fit within the configured session limits
- Added shared strict JSON Schemas for modular lessons, legacy lesson formats, handouts,
  and worksheets and supplied them through the Responses API Structured Outputs boundary
- Retained application-side checks for exact identifiers, ordering, timing, answer separation,
  content limits, and type-specific worksheet rules after schema-constrained generation
- Added stable consecutive numeric identifiers to modular exercises and explicit answer links;
  mismatched counts, missing links, duplicates, and nonconsecutive identifiers preserve the prior draft
- Regenerating modular exercises or their teacher key now refreshes the linked pair together while
  preserving unrelated lesson sections
- Added a browser-isolated lesson library with explicit saved/unsaved state and save, reopen,
  rename, and delete controls; the accountless prototype retains up to 25 lessons and expires
  lessons after 90 days of inactivity
- Added up to 20 recovery snapshots per lesson, including an automatic snapshot of unsaved edits
  immediately before full-plan or section-level AI generation; restoring a snapshot opens it as an
  unsaved draft and leaves the current saved copy intact
- Added source-specific handout dependency tracking. Changes to a handout's source section or
  the topic, grade, objectives, or source excerpts now identify the handout for review and pause
  export; unrelated lesson sections no longer create a false stale warning.
- Surface the affected-handout warning in both the Lesson Planner and Student Materials screens.
  If the source section is removed, the teacher must create a replacement handout rather than
  acknowledging alignment against a missing source.

### Planned

- Optional teacher accounts and shared or cloud-synchronized lesson libraries
- Independent standards retrieval and factual-content verification
- Distributed request coordination and production deployment controls
- Structured evaluation with teacher feedback

## [0.2.1] - 2026-09-17

### Changed

- Archived confirmed unreferenced legacy templates and static assets outside production
  directories while preserving them in repository history
- Documented the complete reachable route, generation, export, template, and static-asset
  surface for the local prototype

### Security and reliability

- Expanded provider-failure coverage across every generation entry point for authentication,
  exhausted credit, rate limiting, timeout, network, API-status, empty, incomplete, and
  oversized responses
- Added exact route and production-asset inventory tests so future surface changes require an
  explicit audit update
- Expanded the offline regression suite from 75 to 86 tests
- Verified long lesson and 20-item handout exports without AI calls; the installed Microsoft
  Word converter produced and preserved all content in a visually inspected 23-page PDF

### Known limits

- This closes the local-prototype Milestone 1 acceptance criteria; distributed coordination,
  production access control, Linux PDF conversion, and operational spending controls remain
  production work
- Structural and export checks still do not establish factual accuracy, standards alignment,
  answer correctness, accessibility conformance, or educational effectiveness

## [0.2.0] - 2026-09-17

This is the first formally tagged LPAPP release. Earlier commits remain available in Git
history but predate the release process.

### Added

- Modular lesson studio with preset, customized-preset, and build-from-scratch paths
- Eight instructional approaches with editable, reorderable, removable, and individually
  regenerable lesson sections
- Teacher review state and separate Word exports for lesson plans, student handouts, and
  teacher answer keys
- Practice worksheets, guided notes, reference sheets, and exit tickets with print-friendly
  and classroom color themes
- Automatic PDF routes with bounded, isolated conversion and Word fallback on Windows
- Concrete classroom-context examples for objectives, materials, learner support, standards,
  and source excerpts
- Health and version endpoints plus an offline GitHub Actions test workflow

### Changed

- Legacy lesson and worksheet forms now preserve valid submitted values after errors
- Worksheet generation uses structured item records and validates counts, identifiers,
  answers, and type-specific requirements before displaying output
- Mixed worksheets apply subtype validation to short-answer, fill-in-the-blank, and matching
  items
- Static assets load independently of the per-session request guard, improving mobile and
  concurrent browser behavior

### Security and reliability

- Added CSRF protection and explicit POST generation for legacy forms; opening a result page
  cannot trigger a paid request
- Added per-session and application-wide generation-attempt limits backed by SQLite
- Disabled automatic provider retries and bounded request and response sizes
- Rejected incomplete AI responses without replacing the previous saved draft
- Added process-local protection against overlapping requests for the same session
- Expanded the offline regression suite to 75 tests with mocked AI calls

### Known limits

- Generated facts, standards, citations, timing, and answer correctness are not independently
  verified
- The local prototype has no authentication, persistent lesson library, or multi-host quota
  coordination
- Public deployment still requires access control, durable shared state, and operational
  monitoring

[Unreleased]: https://github.com/Akqadafi/LPAPP/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/Akqadafi/LPAPP/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/Akqadafi/LPAPP/releases/tag/v0.2.0
