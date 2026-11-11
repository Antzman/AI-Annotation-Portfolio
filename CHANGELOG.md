# Changelog

All notable project changes will be documented here.

## Unreleased

- Added the initial Flask project structure and Phase 1 foundation; 9 database tests pass.
- Added SQLAlchemy models and local SQLite initialization.
- Added database design, development phases, and free/open-source dependency policy.
- Added the data-backed dashboard, responsive navigation, and locally vendored Bootstrap 5.3.8 (MIT).
- Added safe preservation of pre-Phase-2 global review records during exercise-scoped review migration.
- Verified the Phase 2 dashboard/navigation suite: 14 tests pass.
- Added Object & Action assessment creation and multiple-observation create/edit/delete workflows with server-side validation and CSRF checks.
- Added explicit database failure pages and verified the Phase 3 suite: 19 tests pass.
- Added per-exercise Movement Analysis create/edit/delete workflows, strict visibility/plausibility validation, and rating display.
- Verified the Phase 4 suite: 23 tests pass.
- Added partial-draft and complete Video Quality workflows with paired score explanations, 1–10 validation, server-calculated average, and live local preview.
- Verified the Phase 5 suite: 28 tests pass.
- Added Attention to Detail issue create/edit/delete workflows, severity/category validation, and explicit reviewed-with-no-issues completion.
- Added a backward-compatible SQLite timestamp trigger migration and verified the Phase 6 suite: 34 tests pass.
- Added profile editing, detailed report preview, and local ReportLab PDF export with saved-data-only summaries, clear incomplete states, wrapped tables, and page numbers.
- Verified empty-report blocking, partial-result accuracy, escaped profile content, long-text multi-page PDF output, and page footers; all 41 tests pass.
- Completed final Windows/PowerShell validation: all seven routes loaded at a mobile viewport without horizontal overflow, Python compilation and `pip check` passed, and package/Bootstrap license notices were reviewed.
