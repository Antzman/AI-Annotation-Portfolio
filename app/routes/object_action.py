from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Exercise, ObjectActionObservation
from app.services.assessment_workflow import assessment_sections
from app.services.object_action_validation import (
    validate_exercise_form,
    validate_observation_form,
)
from app.services.web import database_failure

bp = Blueprint("object_action", __name__, url_prefix="/object-action")


@bp.route("", methods=["GET", "POST"])
def index():
    errors = []
    values = {"title": "", "clip_reference": ""}
    if request.method == "POST":
        values, errors = validate_exercise_form(request.form)
        if not errors:
            exercise = Exercise(
                title=values["title"],
                clip_reference=values["clip_reference"] or None,
            )
            db.session.add(exercise)
            try:
                db.session.commit()
            except SQLAlchemyError:
                return database_failure(
                    "creating an exercise",
                    "The assessment could not be saved. Check the local application "
                    "log and try again.",
                    url_for("object_action.index"),
                    "object-action",
                )
            else:
                flash("Assessment created.", "success")
                return redirect(url_for("object_action.detail", exercise_id=exercise.id))

    exercises = db.session.execute(
        select(Exercise)
        .options(selectinload(Exercise.object_action_observations))
        .order_by(Exercise.created_at.desc(), Exercise.id.desc())
    ).scalars().all()
    status = 400 if errors else 200
    return (
        render_template(
            "sections/object_action/index.html",
            active_nav="object-action",
            exercises=exercises,
            values=values,
            errors=errors,
        ),
        status,
    )


@bp.route("/<int:exercise_id>", methods=["GET", "POST"])
def detail(exercise_id):
    exercise = db.get_or_404(Exercise, exercise_id)
    errors = []
    values = {
        "timestamp": "",
        "identified_object": "",
        "observed_action": "",
        "additional_observations": "",
    }
    if request.method == "POST":
        values, errors = validate_observation_form(request.form)
        if not errors:
            exercise.finalized_at = None
            observation = ObjectActionObservation(
                exercise=exercise,
                timestamp=values["timestamp"],
                identified_object=values["identified_object"],
                observed_action=values["observed_action"],
                additional_observations=values["additional_observations"] or None,
            )
            db.session.add(observation)
            try:
                db.session.commit()
            except SQLAlchemyError:
                return database_failure(
                    "adding an object/action observation",
                    "The observation could not be saved. Check the local application "
                    "log and try again.",
                    url_for("object_action.detail", exercise_id=exercise.id),
                    "object-action",
                )
            else:
                flash("Observation added.", "success")
                return redirect(
                    url_for("object_action.detail", exercise_id=exercise.id)
                )

    observations = db.session.execute(
        select(ObjectActionObservation)
        .where(ObjectActionObservation.exercise_id == exercise.id)
        .order_by(
            ObjectActionObservation.created_at.asc(),
            ObjectActionObservation.id.asc(),
        )
    ).scalars().all()

    status = 400 if errors else 200
    return (
        render_template(
            "sections/object_action/detail.html",
            active_nav="object-action",
            exercise=exercise,
            observations=observations,
            workflow_sections=assessment_sections(exercise),
            current_section="object_action",
            values=values,
            errors=errors,
        ),
        status,
    )


@bp.route("/observations/<int:observation_id>/edit", methods=["GET", "POST"])
def edit_observation(observation_id):
    observation = db.get_or_404(ObjectActionObservation, observation_id)
    values = {
        "timestamp": observation.timestamp,
        "identified_object": observation.identified_object,
        "observed_action": observation.observed_action,
        "additional_observations": observation.additional_observations or "",
    }
    errors = []

    if request.method == "POST":
        values, errors = validate_observation_form(request.form)
        if not errors:
            observation.exercise.finalized_at = None
            observation.timestamp = values["timestamp"]
            observation.identified_object = values["identified_object"]
            observation.observed_action = values["observed_action"]
            observation.additional_observations = (
                values["additional_observations"] or None
            )
            try:
                db.session.commit()
            except SQLAlchemyError:
                return database_failure(
                    "editing an object/action observation",
                    "The observation could not be updated. Check the local application "
                    "log and try again.",
                    url_for(
                        "object_action.detail",
                        exercise_id=observation.exercise_id,
                    ),
                    "object-action",
                )
            else:
                flash("Observation updated.", "success")
                return redirect(
                    url_for(
                        "object_action.detail",
                        exercise_id=observation.exercise_id,
                    )
                )

    return (
        render_template(
            "sections/object_action/edit_observation.html",
            active_nav="object-action",
            exercise=observation.exercise,
            workflow_sections=assessment_sections(observation.exercise),
            current_section="object_action",
            observation=observation,
            values=values,
            errors=errors,
        ),
        400 if errors else 200,
    )


@bp.post("/observations/<int:observation_id>/delete")
def delete_observation(observation_id):
    observation = db.get_or_404(ObjectActionObservation, observation_id)
    exercise_id = observation.exercise_id
    observation.exercise.finalized_at = None
    db.session.delete(observation)
    try:
        db.session.commit()
    except SQLAlchemyError:
        return database_failure(
            "deleting an object/action observation",
            "The observation could not be deleted. Check the local application "
            "log and try again.",
            url_for("object_action.detail", exercise_id=exercise_id),
            "object-action",
        )
    else:
        flash("Observation deleted.", "success")
    return redirect(url_for("object_action.detail", exercise_id=exercise_id))
