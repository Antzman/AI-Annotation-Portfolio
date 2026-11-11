from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Exercise, QualityAssessment, UserProfile

SECTION_DETAILS = (
    ("object_action", "Object & Action Annotation"),
    ("movement", "Movement & Motion Analysis"),
    ("quality", "Video Quality Assessment"),
    ("attention_to_detail", "Annotation Quality Review"),
)


def _exercise_section_status(exercise, key):
    if key == "object_action":
        started = bool(exercise.object_action_observations)
        complete = started
    elif key == "movement":
        started = bool(exercise.movement_observations)
        complete = started
    elif key == "quality":
        assessment = exercise.quality_assessment
        started = assessment is not None and bool(assessment.ratings)
        complete = assessment is not None and assessment.overall_score is not None
    else:
        started = bool(exercise.quality_issues)
        complete = any(
            review.section_key == "attention_to_detail"
            and review.reviewed_at is not None
            for review in exercise.section_reviews
        )
        started = started or complete

    if complete:
        return "complete"
    if started:
        return "in_progress"
    return "not_started"


def build_report_data(generated_at=None):
    profile = db.session.execute(
        select(UserProfile).order_by(UserProfile.id).limit(1)
    ).scalar_one_or_none()
    exercises = db.session.execute(
        select(Exercise)
        .options(
            selectinload(Exercise.object_action_observations),
            selectinload(Exercise.movement_observations),
            selectinload(Exercise.quality_assessment).selectinload(
                QualityAssessment.ratings
            ),
            selectinload(Exercise.quality_issues),
            selectinload(Exercise.section_reviews),
        )
        .order_by(Exercise.created_at.asc(), Exercise.id.asc())
    ).scalars().all()

    exercise_sections = {}
    section_summaries = []
    for key, label in SECTION_DETAILS:
        statuses = {
            exercise.id: _exercise_section_status(exercise, key)
            for exercise in exercises
        }
        complete_count = sum(status == "complete" for status in statuses.values())
        in_progress_count = sum(
            status == "in_progress" for status in statuses.values()
        )
        if not exercises or complete_count == 0 and in_progress_count == 0:
            status = "not_started"
        elif complete_count == len(exercises):
            status = "complete"
        else:
            status = "in_progress"
        section_summaries.append(
            {
                "key": key,
                "label": label,
                "status": status,
                "complete_count": complete_count,
                "in_progress_count": in_progress_count,
                "total_count": len(exercises),
            }
        )
        for exercise_id, exercise_status in statuses.items():
            exercise_sections.setdefault(exercise_id, {})[key] = exercise_status

    complete_assessments = sum(
        all(
            exercise_sections[exercise.id][key] == "complete"
            for key, _label in SECTION_DETAILS
        )
        for exercise in exercises
    )
    completed_quality = [
        exercise.quality_assessment.overall_score
        for exercise in exercises
        if exercise.quality_assessment
        and exercise.quality_assessment.overall_score is not None
    ]
    return {
        "generated_at": generated_at or datetime.now(UTC),
        "profile": profile,
        "exercises": exercises,
        "exercise_sections": exercise_sections,
        "sections": section_summaries,
        "total_assessments": len(exercises),
        "completed_assessments": complete_assessments,
        "completion": (
            int(
                sum(
                    section["complete_count"]
                    for section in section_summaries
                )
                * 100
                / (len(exercises) * len(SECTION_DETAILS))
                + 0.5
            )
            if exercises
            else 0
        ),
        "average_quality_score": (
            sum(completed_quality) / len(completed_quality)
            if completed_quality
            else None
        ),
        "is_complete": bool(exercises)
        and all(section["status"] == "complete" for section in section_summaries),
        "has_assessments": bool(exercises),
    }
