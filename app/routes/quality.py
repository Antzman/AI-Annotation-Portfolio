from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Exercise, QualityAssessment, QualityRating
from app.models.quality import QUALITY_CATEGORIES
from app.services.quality_validation import QUALITY_LABELS, validate_quality_form
from app.services.web import database_failure

bp = Blueprint("quality", __name__, url_prefix="/video-quality")


def _initial_values(assessment):
    existing = {
        rating.category: rating for rating in assessment.ratings
    } if assessment else {}
    return {
        category: {
            "score": existing[category].score if category in existing else "",
            "explanation": (
                existing[category].explanation if category in existing else ""
            ),
        }
        for category in QUALITY_CATEGORIES
    }


@bp.get("")
def index():
    exercises = db.session.execute(
        select(Exercise)
        .options(
            selectinload(Exercise.quality_assessment).selectinload(
                QualityAssessment.ratings
            )
        )
        .order_by(Exercise.created_at.desc(), Exercise.id.desc())
    ).scalars().all()
    return render_template(
        "sections/quality/index.html",
        active_nav="video-quality",
        exercises=exercises,
    )


@bp.route("/<int:exercise_id>", methods=["GET", "POST"])
def detail(exercise_id):
    exercise = db.get_or_404(Exercise, exercise_id)
    assessment = exercise.quality_assessment
    values = _initial_values(assessment)
    errors = []

    if request.method == "POST":
        values, errors = validate_quality_form(request.form)
        if not errors:
            if assessment is None:
                assessment = QualityAssessment(exercise=exercise)
                db.session.add(assessment)
            existing = {rating.category: rating for rating in assessment.ratings}
            for category in QUALITY_CATEGORIES:
                value = values[category]
                rating = existing.get(category)
                if value["score"] == "" and not value["explanation"]:
                    if rating:
                        assessment.ratings.remove(rating)
                    continue
                if rating is None:
                    rating = QualityRating(category=category)
                    assessment.ratings.append(rating)
                rating.score = value["score"]
                rating.explanation = value["explanation"]

            try:
                db.session.commit()
            except SQLAlchemyError:
                return database_failure(
                    "saving a quality assessment",
                    "The quality assessment could not be saved. Check the local "
                    "application log and try again.",
                    url_for("quality.detail", exercise_id=exercise.id),
                    "video-quality",
                )
            flash("Quality assessment saved.", "success")
            return redirect(url_for("quality.detail", exercise_id=exercise.id))

    if assessment is not None:
        overall_score = assessment.overall_score
        rating_count = len(assessment.ratings)
    else:
        overall_score = None
        rating_count = 0

    return (
        render_template(
            "sections/quality/detail.html",
            active_nav="video-quality",
            exercise=exercise,
            assessment=assessment,
            values=values,
            errors=errors,
            quality_categories=QUALITY_CATEGORIES,
            quality_labels=QUALITY_LABELS,
            overall_score=overall_score,
            rating_count=rating_count,
        ),
        400 if errors else 200,
    )
