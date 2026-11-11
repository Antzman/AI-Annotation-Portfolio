from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Exercise, QualityAssessment, UserProfile
from app.services.assessment_workflow import SECTION_DETAILS, section_status


def build_report_data(generated_at=None, exercise_id=None):
    profile = db.session.execute(
        select(UserProfile).order_by(UserProfile.id).limit(1)
    ).scalar_one_or_none()
    exercise_statement = (
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
    )
    if exercise_id is not None:
        exercise_statement = exercise_statement.where(Exercise.id == exercise_id)
    exercises = db.session.execute(exercise_statement).scalars().all()

    exercise_sections = {}
    section_summaries = []
    for key, label in SECTION_DETAILS:
        statuses = {
            exercise.id: section_status(exercise, key)
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

    finalized_assessments = sum(
        exercise.finalized_at is not None for exercise in exercises
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
        "started_assessments": len(exercises),
        "completed_assessments": finalized_assessments,
        "in_progress_assessments": len(exercises) - finalized_assessments,
        "finalized_assessments": finalized_assessments,
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
        "is_finalized": bool(exercises)
        and all(exercise.finalized_at is not None for exercise in exercises),
        "has_assessments": bool(exercises),
    }
