# AI Annotation Portfolio

A local-first web application for documenting manual video-annotation assessments and producing a professional PDF portfolio. Users watch clips independently and enter their observations; the application does not upload, store, process, or analyze video files.

## Status

Phases 1–8 are complete, including the Flask foundation, dashboard, four assessment sections, profile editing, report preview, and PDF export. The full 41-test suite and Windows local smoke checks pass.

## Free and local by design

- Python, Flask, Flask-SQLAlchemy, SQLAlchemy, SQLite, ReportLab Community Edition, and pytest are free to use and open source.
- Python dependencies are listed in `requirements.txt`; the Flask ecosystem uses BSD licenses, SQLAlchemy and pytest use the MIT License, and ReportLab Community Edition uses an open-source BSD-style license.
- SQLite is embedded and stores data in a local file. No cloud database, hosted service, paid software, API, or AI service is required.
- Bootstrap 5.3.8 is served as a local static asset under its MIT License, with the upstream license notice in `app/static/vendor/bootstrap/LICENSE`; the app makes no CDN requests.
- The app targets Windows 11, Visual Studio Code, Python virtual environments, and PowerShell. No hosting or deployment dependency is planned.

Recheck upstream package and asset license notices when selecting exact versions. Do not add a dependency, service, or asset that requires a paid subscription or commercial license.

## Local setup

From PowerShell in the project directory:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
flask --app run.py run --debug
```

The application uses a SQLite database at `instance\portfolio.db`, created automatically when the app starts. Do not put personal portfolio data or generated reports under version control.

To run the tests:

```powershell
python -m pytest
```

## Profile and reports

Use **About** to save or edit your name, introduction, experience, interests, skills, and contact information. The **Report Preview** page presents saved assessment results and marks incomplete work explicitly. Download a PDF from the preview page; export is unavailable until at least one assessment exists. Partial sections remain identified as incomplete, and an overall quality score is shown only when all five category ratings are saved. The PDF is generated locally with ReportLab and includes page numbers and wrapped, divided tables.

Set a stable `SECRET_KEY` in the environment when you want sessions to survive app restarts or before deploying beyond local development. This project currently has no deployment target.

## Project map

```text
app/
  models/       SQLAlchemy models
  routes/       Flask blueprints
  services/     validation, completion rules, and PDF generation
  static/       local CSS, JavaScript, and Bootstrap assets
  templates/    shared layout and section/report pages
instance/       local SQLite database and instance configuration
tests/          automated tests
```

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for phase gates and [DATABASE_DESIGN.md](DATABASE_DESIGN.md) for the relational schema.
