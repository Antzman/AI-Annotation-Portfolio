# Project Plan

## Product scope

Build a responsive, local-first Flask application for manually recording video-annotation observations and presenting them in a PDF portfolio. Users provide text references to clips; the application will not accept video uploads, call external APIs, or perform video processing or AI analysis.

The interface will use a fixed desktop sidebar that adapts for small screens, a blue/white/light-grey palette, accessible forms, and Bootstrap 5 served locally with its MIT license notice. SQLite data and generated reports remain on the user's machine.

## Proposed project structure

```text
app/
  models/
  routes/
  services/
  templates/
    components/
    dashboard/
    sections/
    report/
  static/
    css/
    js/
    vendor/bootstrap/
instance/
tests/
README.md
PROJECT_PLAN.md
DATABASE_DESIGN.md
CHANGELOG.md
requirements.txt
```

Routes will be grouped in Flask blueprints; persistence will use SQLAlchemy models; cross-section completion logic and PDF generation will live in services. Templates will share a layout and reusable navigation/form components.

## Data and completion rules

The schema and relationships are described in [DATABASE_DESIGN.md](DATABASE_DESIGN.md). The dashboard will calculate completion from persisted records, not hardcoded sample values:

1. Object & Action Identification is complete when at least one valid observation exists.
2. Movement Analysis is complete when at least one valid observation exists.
3. Video Quality Assessment is complete when all five category ratings and their explanations are saved for an assessment.
4. Attention to Detail is complete when the user explicitly marks the section reviewed. A reviewed section may contain zero issues, so users can truthfully record that none were observed.

Portfolio completion is the percentage of the four required section checks completed across all exercises. An assessment counts as complete only when all four checks are complete for that exercise. A section is complete when every assessment meets its rule, in progress when some do, and not started when none do. Report preview/export will label incomplete sections and will never invent scores, observations, or a completed result. Quality scores will be calculated only from saved ratings.

## Development phases and approval gates

Implementation starts only after approval of the proposed database design and phase sequence. After each phase, run the focused automated tests for that phase and report the command and result before proceeding.

### Phase 1 — Flask foundation and database — Complete

- Create the Flask application factory, configuration, SQLAlchemy initialization, and initial schema.
- Keep the SQLite path under `instance\`; add safe local defaults and database integrity validation.
- Add model/relationship and app-startup tests.
- **Exit check:** app starts locally; schema creates successfully; tests cover model constraints and relationships. Verified: 9 tests pass.

### Phase 2 — Dashboard and navigation — Complete

- Add shared layout, responsive sidebar/navigation, dashboard cards, recent activity, and data-backed section statuses.
- Serve Bootstrap 5.3.8 locally under its MIT license; do not rely on a CDN.
- Add dashboard and navigation tests, including the empty-database state.
- **Exit check:** all status indicators and completion percentage match database-backed rules. Verified: 14 tests pass.

### Phase 3 — Object & Action Identification — Complete

- Add exercise and object/action observation create, list, edit, and delete flows.
- Validate required text fields and timestamp format; protect form submissions with CSRF tokens; retain clip references as text only.
- Add route and validation tests.
- **Exit check:** multiple observations per exercise persist and can be safely edited/deleted. Verified: 19 tests pass.

### Phase 4 — Movement Analysis — Complete

- Add movement observations with controlled visibility and plausibility values.
- Add route, allowed-value, and validation tests.
- **Exit check:** invalid controlled values are rejected and saved observations display consistently. Verified: 23 tests pass.

### Phase 5 — Video Quality Assessment — Complete

- Add the five 1–10 ratings, an explanation per rating, and a calculated overall score.
- Add bounds, required-explanation, and score-calculation tests.
- **Exit check:** incomplete ratings cannot be presented as complete and the score is derived only from saved values. Verified: 28 tests pass.

### Phase 6 — Attention to Detail — Complete

- Add categorized issue entry, severity, explanation, suggested correction, and explicit reviewed/no-issues completion.
- Add controlled-value and section-status tests.
- **Exit check:** users can record multiple issues or mark a review complete with no issues without ambiguity. Issue changes invalidate prior review state. Verified: 34 tests pass.

### Phase 7 — Report Preview and PDF generation — Complete

- Add a preview assembled from actual profile and assessment data, then local ReportLab PDF export.
- Include cover, optional profile introduction/skills, results, assessment score/explanations, incomplete-section notices, conclusion, generation date, tables, and page numbers.
- Add profile editing, report preview and download tests, including escaped user content, long text, multi-page PDF output, and numbered page footers.
- **Exit check:** exported report clearly distinguishes incomplete work and contains no empty or fabricated result. Verified: all 41 tests pass.

### Phase 8 — Testing and refinement — Complete

- Run the full test suite; refine accessibility, responsive behavior, validation, error handling, and documentation.
- Verify setup and launch instructions on Windows/PowerShell without external services.
- **Exit check:** tests pass; requirements and license notices are reviewed; a clean local setup follows the README. Verified: all 41 tests pass, Python compilation and `pip check` pass, all seven application routes return successfully at a 390px viewport without horizontal overflow, and dependency metadata confirms free BSD/MIT licenses. The browser smoke test used an isolated temporary SQLite database.

## Free-only dependency policy

The planned Python runtime dependencies are Flask, Flask-SQLAlchemy (which installs SQLAlchemy), and ReportLab Community Edition. pytest is a test-only dependency. SQLite comes with Python and needs no server. Bootstrap is a static, locally served asset under MIT, not a pip dependency or CDN request. Recheck exact package/asset licenses when versions are selected; reject paid services, subscription features, and dependencies with incompatible commercial-only terms.
