from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Exercise, QualityIssue, SectionReview
from app.services.attention_validation import (
    ISSUE_LABELS,
    SEVERITY_LABELS,
    validate_issue_form,
)
from app.services.web import database_failure

bp = Blueprint("attention", __name__, url_prefix="/attention-to-detail")


def _empty_values():
    return {
        "timestamp": "",
        "category": "",
        "description": "",
        "severity": "",
        "explanation": "",
        "suggested_correction": "",
    }


def _review_for(exercise):
    return next(
        (
            review
            for review in exercise.section_reviews
            if review.section_key == "attention_to_detail"
        ),
        None,
    )


def _clear_review(exercise):
    review = _review_for(exercise)
    if review is not None:
        review.reviewed_at = None


def _render_issues(exercise):
    return db.session.execute(
        select(QualityIssue)
        .where(QualityIssue.exercise_id == exercise.id)
        .order_by(QualityIssue.created_at.asc(), QualityIssue.id.asc())
    ).scalars().all()


@bp.get("")
def index():
    exercises = db.session.execute(
        select(Exercise)
        .options(
            selectinload(Exercise.quality_issues),
            selectinload(Exercise.section_reviews),
        )
        .order_by(Exercise.created_at.desc(), Exercise.id.desc())
    ).scalars().all()
    return render_template(
        "sections/attention/index.html",
        active_nav="attention-to-detail",
        exercises=exercises,
    )


@bp.route("/<int:exercise_id>", methods=["GET", "POST"])
def detail(exercise_id):
    exercise = db.get_or_404(Exercise, exercise_id)
    values = _empty_values()
    errors = []
    if request.method == "POST":
        values, errors = validate_issue_form(request.form)
        if not errors:
            issue = QualityIssue(
                exercise=exercise,
                timestamp=values["timestamp"],
                category=values["category"],
                description=values["description"],
                severity=values["severity"],
                explanation=values["explanation"],
                suggested_correction=values["suggested_correction"] or None,
            )
            db.session.add(issue)
            _clear_review(exercise)
            try:
                db.session.commit()
            except SQLAlchemyError:
                return database_failure(
                    "adding an attention-to-detail issue",
                    "The issue could not be saved. Check the local application log "
                    "and try again.",
                    url_for("attention.detail", exercise_id=exercise.id),
                    "attention-to-detail",
                )
            flash("Issue recorded. Review this section before marking it complete.", "success")
            return redirect(url_for("attention.detail", exercise_id=exercise.id))

    return (
        render_template(
            "sections/attention/detail.html",
            active_nav="attention-to-detail",
            exercise=exercise,
            issues=_render_issues(exercise),
            review=_review_for(exercise),
            values=values,
            errors=errors,
            issue_labels=ISSUE_LABELS,
            severity_labels=SEVERITY_LABELS,
        ),
        400 if errors else 200,
    )


@bp.route("/issues/<int:issue_id>/edit", methods=["GET", "POST"])
def edit_issue(issue_id):
    issue = db.get_or_404(QualityIssue, issue_id)
    exercise = issue.exercise
    values = {
        "timestamp": issue.timestamp,
        "category": issue.category,
        "description": issue.description,
        "severity": issue.severity,
        "explanation": issue.explanation,
        "suggested_correction": issue.suggested_correction or "",
    }
    errors = []
    if request.method == "POST":
        values, errors = validate_issue_form(request.form)
        if not errors:
            issue.timestamp = values["timestamp"]
            issue.category = values["category"]
            issue.description = values["description"]
            issue.severity = values["severity"]
            issue.explanation = values["explanation"]
            issue.suggested_correction = values["suggested_correction"] or None
            _clear_review(exercise)
            try:
                db.session.commit()
            except SQLAlchemyError:
                return database_failure(
                    "editing an attention-to-detail issue",
                    "The issue could not be updated. Check the local application log "
                    "and try again.",
                    url_for("attention.detail", exercise_id=exercise.id),
                    "attention-to-detail",
                )
            flash("Issue updated. Review this section before marking it complete.", "success")
            return redirect(url_for("attention.detail", exercise_id=exercise.id))

    return (
        render_template(
            "sections/attention/edit_issue.html",
            active_nav="attention-to-detail",
            exercise=exercise,
            issue=issue,
            values=values,
            errors=errors,
            issue_categories=ISSUE_LABELS,
            severity_options=SEVERITY_LABELS,
        ),
        400 if errors else 200,
    )


@bp.post("/issues/<int:issue_id>/delete")
def delete_issue(issue_id):
    issue = db.get_or_404(QualityIssue, issue_id)
    exercise = issue.exercise
    exercise_id = exercise.id
    _clear_review(exercise)
    db.session.delete(issue)
    try:
        db.session.commit()
    except SQLAlchemyError:
        return database_failure(
            "deleting an attention-to-detail issue",
            "The issue could not be deleted. Check the local application log and "
            "try again.",
            url_for("attention.detail", exercise_id=exercise_id),
            "attention-to-detail",
        )
    flash("Issue deleted. Review this section before marking it complete.", "success")
    return redirect(url_for("attention.detail", exercise_id=exercise_id))


@bp.post("/<int:exercise_id>/mark-reviewed")
def mark_reviewed(exercise_id):
    exercise = db.get_or_404(Exercise, exercise_id)
    review = _review_for(exercise)
    if review is None:
        review = SectionReview(
            exercise=exercise,
            section_key="attention_to_detail",
        )
        db.session.add(review)
    review.mark_reviewed()
    try:
        db.session.commit()
    except SQLAlchemyError:
        return database_failure(
            "marking attention to detail reviewed",
            "The review status could not be saved. Check the local application "
            "log and try again.",
            url_for("attention.detail", exercise_id=exercise.id),
            "attention-to-detail",
        )
    flash("Annotation Quality Review marked as reviewed.", "success")
    return redirect(url_for("attention.detail", exercise_id=exercise.id))
