# Changelog

All notable changes to LPAPP are recorded here. The project uses
[Semantic Versioning](https://semver.org/) beginning with the 0.2.0 baseline.

## [Unreleased]

### Changed

- Reframed the experimental homepage around Aqolyte LLC as the parent company for web,
  educational, and applied AI tools, with Lesson Planner presented as its first product
- Rebuilt About, Products, and Contact with the corporate design system and simplified the
  company-to-product path so the direct Lesson Planner launch appears only on Products

### Planned

- Persistent teacher accounts and saved lesson libraries
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
