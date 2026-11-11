from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Exercise, MovementObservation
from app.services.movement_validation import (
    PLAUSIBILITY_OPTIONS,
    VISIBILITY_OPTIONS,
    validate_movement_form,
)
from app.services.web import database_failure

bp = Blueprint("movement", __name__, url_prefix="/movement-analysis")


def _empty_values():
    return {
        "timestamp": "",
        "movement_description": "",
        "visibility": "",
        "plausibility": "",
        "inconsistencies": "",
        "reasoning": "",
    }


def _render_observations(exercise):
    return db.session.execute(
        select(MovementObservation)
        .where(MovementObservation.exercise_id == exercise.id)
        .order_by(MovementObservation.created_at.asc(), MovementObservation.id.asc())
    ).scalars().all()


@bp.get("")
def index():
    exercises = db.session.execute(
        select(Exercise)
        .options(selectinload(Exercise.movement_observations))
        .order_by(Exercise.created_at.desc(), Exercise.id.desc())
    ).scalars().all()
    return render_template(
        "sections/movement/index.html",
        active_nav="movement-analysis",
        exercises=exercises,
    )


@bp.route("/<int:exercise_id>", methods=["GET", "POST"])
def detail(exercise_id):
    exercise = db.get_or_404(Exercise, exercise_id)
    values = _empty_values()
    errors = []
    if request.method == "POST":
        values, errors = validate_movement_form(request.form)
        if not errors:
            observation = MovementObservation(
                exercise=exercise,
                timestamp=values["timestamp"],
                movement_description=values["movement_description"],
                visibility=values["visibility"],
                plausibility=values["plausibility"],
                inconsistencies=values["inconsistencies"] or None,
                reasoning=values["reasoning"],
            )
            db.session.add(observation)
            try:
                db.session.commit()
            except SQLAlchemyError:
                return database_failure(
                    "adding a movement observation",
                    "The movement observation could not be saved. Check the local "
                    "application log and try again.",
                    url_for("movement.detail", exercise_id=exercise.id),
                    "movement-analysis",
                )
            flash("Movement observation added.", "success")
            return redirect(url_for("movement.detail", exercise_id=exercise.id))

    return (
        render_template(
            "sections/movement/detail.html",
            active_nav="movement-analysis",
            exercise=exercise,
            observations=_render_observations(exercise),
            values=values,
            errors=errors,
            visibility_options=VISIBILITY_OPTIONS,
            plausibility_options=PLAUSIBILITY_OPTIONS,
        ),
        400 if errors else 200,
    )


@bp.route("/observations/<int:observation_id>/edit", methods=["GET", "POST"])
def edit_observation(observation_id):
    observation = db.get_or_404(MovementObservation, observation_id)
    values = {
        "timestamp": observation.timestamp,
        "movement_description": observation.movement_description,
        "visibility": observation.visibility,
        "plausibility": observation.plausibility,
        "inconsistencies": observation.inconsistencies or "",
        "reasoning": observation.reasoning,
    }
    errors = []
    if request.method == "POST":
        values, errors = validate_movement_form(request.form)
        if not errors:
            observation.timestamp = values["timestamp"]
            observation.movement_description = values["movement_description"]
            observation.visibility = values["visibility"]
            observation.plausibility = values["plausibility"]
            observation.inconsistencies = values["inconsistencies"] or None
            observation.reasoning = values["reasoning"]
            try:
                db.session.commit()
            except SQLAlchemyError:
                return database_failure(
                    "editing a movement observation",
                    "The movement observation could not be updated. Check the local "
                    "application log and try again.",
                    url_for(
                        "movement.detail",
                        exercise_id=observation.exercise_id,
                    ),
                    "movement-analysis",
                )
            flash("Movement observation updated.", "success")
            return redirect(
                url_for("movement.detail", exercise_id=observation.exercise_id)
            )

    return (
        render_template(
            "sections/movement/edit_observation.html",
            active_nav="movement-analysis",
            exercise=observation.exercise,
            observation=observation,
            values=values,
            errors=errors,
            visibility_options=VISIBILITY_OPTIONS,
            plausibility_options=PLAUSIBILITY_OPTIONS,
        ),
        400 if errors else 200,
    )


@bp.post("/observations/<int:observation_id>/delete")
def delete_observation(observation_id):
    observation = db.get_or_404(MovementObservation, observation_id)
    exercise_id = observation.exercise_id
    db.session.delete(observation)
    try:
        db.session.commit()
    except SQLAlchemyError:
        return database_failure(
            "deleting a movement observation",
            "The movement observation could not be deleted. Check the local "
            "application log and try again.",
            url_for("movement.detail", exercise_id=exercise_id),
            "movement-analysis",
        )
    flash("Movement observation deleted.", "success")
    return redirect(url_for("movement.detail", exercise_id=exercise_id))
