from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Exercise, QualityAssessment
from app.services.assessment_workflow import SECTION_DETAILS, section_status
from app.services.attention_validation import ISSUE_LABELS, SEVERITY_LABELS
from app.models.quality import QUALITY_CATEGORIES
from app.services.quality_validation import QUALITY_LABELS


def _assessment_status(exercise, statuses):
    if exercise.finalized_at is not None:
        return "Completed"
    if any(status != "not_started" for status in statuses.values()):
        return "In Progress"
    return "Draft"


def _assessment_conclusion(summary):
    if summary["completed_sections"] == len(SECTION_DETAILS):
        return f'{summary["title"]}: all four assessment sections are complete.'
    incomplete = ", ".join(
        f'{section["label"]} ({section["status"]})'
        for section in summary["sections"]
        if section["status"] != "Complete"
    )
    return (
        f'{summary["title"]}: {summary["completed_sections"]} of '
        f'{len(SECTION_DETAILS)} assessment sections are complete. '
        f"Incomplete sections: {incomplete}."
    )


def build_report_data(generated_at=None, exercise_id=None):
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
    assessment_summaries = []
    section_summaries = []
    for exercise in exercises:
        statuses = {
            key: section_status(exercise, key)
            for key, _label in SECTION_DETAILS
        }
        exercise_sections[exercise.id] = statuses
        sections = [
            {
                "key": key,
                "label": label,
                "status": statuses[key].replace("_", " ").title(),
            }
            for key, label in SECTION_DETAILS
        ]
        completed_sections = sum(
            status == "complete" for status in statuses.values()
        )
        assessment_summaries.append(
            {
                "id": exercise.id,
                "title": exercise.title,
                "clip_reference": exercise.clip_reference,
                "status": _assessment_status(exercise, statuses),
                "completed_sections": completed_sections,
                "total_sections": len(SECTION_DETAILS),
                "progress": int(
                    completed_sections * 100 / len(SECTION_DETAILS) + 0.5
                ),
                "sections": sections,
                "missing_quality_ratings": [
                    QUALITY_LABELS[category]
                    for category in QUALITY_CATEGORIES
                    if not exercise.quality_assessment
                    or category
                    not in {
                        rating.category
                        for rating in exercise.quality_assessment.ratings
                    }
                ],
            }
        )

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
    finalized_assessments = sum(
        exercise.finalized_at is not None for exercise in exercises
    )
    completed_sections = sum(
        summary["completed_sections"] for summary in assessment_summaries
    )
    total_sections = len(exercises) * len(SECTION_DETAILS)
    completed_quality = [
        exercise.quality_assessment.overall_score
        for exercise in exercises
        if exercise.quality_assessment
        and exercise.quality_assessment.overall_score is not None
    ]
    return {
        "generated_at": generated_at or datetime.now(UTC),
        "exercises": exercises,
        "exercise_sections": exercise_sections,
        "assessment_summaries": assessment_summaries,
        "sections": section_summaries,
        "total_assessments": len(exercises),
        "started_assessments": len(exercises),
        "completed_assessments": finalized_assessments,
        "in_progress_assessments": len(exercises) - finalized_assessments,
        "finalized_assessments": finalized_assessments,
        "completed_sections": completed_sections,
        "total_sections": total_sections,
        "completion": int(completed_sections * 100 / total_sections + 0.5)
        if total_sections
        else 0,
        "overall_conclusion": (
            f"Across {len(exercises)} assessment(s), {completed_sections} of "
            f"{total_sections} assessment sections are complete."
            if exercises
            else "No assessment results are available."
        ),
        "status": (
            "Completed"
            if exercises and finalized_assessments == len(exercises)
            else "In Progress"
            if any(summary["status"] != "Draft" for summary in assessment_summaries)
            else "Draft"
        ),
        "conclusions": (
            [_assessment_conclusion(summary) for summary in assessment_summaries]
            if assessment_summaries
            else ["No assessment results are available."]
        ),
        "quality_labels": QUALITY_LABELS,
        "issue_labels": ISSUE_LABELS,
        "severity_labels": SEVERITY_LABELS,
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
