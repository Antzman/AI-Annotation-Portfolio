from datetime import UTC, datetime
from io import BytesIO

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    send_file,
    url_for,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Exercise, QualityAssessment
from app.services.assessment_workflow import (
    SECTION_DETAILS,
    assessment_sections,
    missing_assessment_sections,
)
from app.services.pdf_report import generate_pdf
from app.services.report_data import build_report_data
from app.services.web import database_failure

bp = Blueprint("assessment", __name__, url_prefix="/assessments")


def _load_exercise(exercise_id):
    exercise = db.session.execute(
        select(Exercise)
        .where(Exercise.id == exercise_id)
        .options(
            selectinload(Exercise.object_action_observations),
            selectinload(Exercise.movement_observations),
            selectinload(Exercise.quality_assessment).selectinload(
                QualityAssessment.ratings
            ),
            selectinload(Exercise.quality_issues),
            selectinload(Exercise.section_reviews),
        )
    ).scalar_one_or_none()
    if exercise is None:
        abort(404)
    return exercise


def _render_workflow(template, exercise, current_section):
    sections = assessment_sections(exercise)
    completed_sections = sum(
        section["status"] == "complete" for section in sections
    )
    return render_template(
        template,
        active_nav="dashboard",
        exercise=exercise,
        sections=sections,
        current_section=current_section,
        missing_sections=[
            section["label"]
            for section in sections
            if section["status"] != "complete"
        ],
        completion=round(completed_sections * 100 / len(SECTION_DETAILS)),
    )


@bp.get("/<int:exercise_id>")
def overview(exercise_id):
    return _render_workflow(
        "assessment/overview.html", _load_exercise(exercise_id), "overview"
    )


@bp.get("/<int:exercise_id>/review")
def review(exercise_id):
    return _render_workflow(
        "assessment/review.html", _load_exercise(exercise_id), "review"
    )


@bp.post("/<int:exercise_id>/finalize")
def finalize(exercise_id):
    exercise = _load_exercise(exercise_id)
    missing = missing_assessment_sections(exercise)
    if missing:
        flash(
            "Complete these sections before finalising: " + "; ".join(missing) + ".",
            "warning",
        )
        return redirect(url_for("assessment.review", exercise_id=exercise.id))

    exercise.finalized_at = datetime.now(UTC)
    try:
        db.session.commit()
    except SQLAlchemyError:
        return database_failure(
            "finalising an assessment",
            "The assessment could not be finalised. Check the local application "
            "log and try again.",
            url_for("assessment.overview", exercise_id=exercise.id),
            "dashboard",
        )
    flash("Assessment finalised. Your report is ready to preview and export.", "success")
    return redirect(url_for("assessment.overview", exercise_id=exercise.id))


@bp.post("/<int:exercise_id>/reopen")
def reopen(exercise_id):
    exercise = _load_exercise(exercise_id)
    if exercise.finalized_at is not None:
        exercise.finalized_at = None
        try:
            db.session.commit()
        except SQLAlchemyError:
            return database_failure(
                "reopening an assessment",
                "The assessment could not be reopened. Check the local application "
                "log and try again.",
                url_for("assessment.overview", exercise_id=exercise.id),
                "dashboard",
            )
        flash(
            "Assessment reopened for corrections. Existing work has been preserved.",
            "success",
        )
    return redirect(url_for("assessment.overview", exercise_id=exercise.id))


@bp.get("/<int:exercise_id>/report.pdf")
def download_report(exercise_id):
    exercise = _load_exercise(exercise_id)
    if exercise.finalized_at is None:
        abort(409, description="Finalise this assessment before exporting its PDF.")

    report = build_report_data(exercise_id=exercise.id)
    filename = secure_filename(exercise.title) or "assessment"
    response = send_file(
        BytesIO(generate_pdf(report)),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{filename}-assessment-report.pdf",
    )
    response.headers["Cache-Control"] = "no-store"
    return response
