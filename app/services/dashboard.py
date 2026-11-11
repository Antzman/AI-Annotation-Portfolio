from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.extensions import db
from app.models import (
    Exercise,
    MovementObservation,
    ObjectActionObservation,
    QualityAssessment,
    QualityIssue,
    SectionReview,
)


@dataclass(frozen=True)
class Activity:
    occurred_at: datetime
    label: str
    detail: str


SECTION_LABELS = (
    ("object_action", "Object & Action Identification"),
    ("movement", "Movement Analysis"),
    ("quality", "Video Quality Assessment"),
    ("attention_to_detail", "Attention to Detail"),
)


def _utc_key(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _activity_rows(model, label, detail_factory, timestamp_field):
    statement = select(model)
    if model is not Exercise:
        statement = statement.options(joinedload(model.exercise))
    if model is SectionReview:
        statement = statement.where(SectionReview.reviewed_at.is_not(None))
    rows = db.session.execute(
        statement.order_by(timestamp_field.desc()).limit(8)
    ).scalars()
    return [
        Activity(
            occurred_at=getattr(row, timestamp_field.key),
            label=label,
            detail=detail_factory(row),
        )
        for row in rows
    ]


def get_dashboard_data():
    exercises = db.session.execute(
        select(Exercise).options(
            selectinload(Exercise.object_action_observations),
            selectinload(Exercise.movement_observations),
            selectinload(Exercise.quality_assessment).selectinload(
                QualityAssessment.ratings
            ),
            selectinload(Exercise.quality_issues),
            selectinload(Exercise.section_reviews),
        )
    ).scalars().all()

    checks = {
        "object_action": [
            bool(exercise.object_action_observations) for exercise in exercises
        ],
        "movement": [bool(exercise.movement_observations) for exercise in exercises],
        "quality": [
            exercise.quality_assessment is not None
            and exercise.quality_assessment.overall_score is not None
            for exercise in exercises
        ],
        "attention_to_detail": [
            any(
                review.section_key == "attention_to_detail"
                and review.reviewed_at is not None
                for review in exercise.section_reviews
            )
            for exercise in exercises
        ],
    }
    started_checks = {
        "object_action": checks["object_action"],
        "movement": checks["movement"],
        "quality": [
            exercise.quality_assessment is not None
            and bool(exercise.quality_assessment.ratings)
            for exercise in exercises
        ],
        "attention_to_detail": [
            bool(exercise.quality_issues)
            or any(
                review.reviewed_at is not None
                for review in exercise.section_reviews
            )
            for exercise in exercises
        ],
    }

    sections = []
    completed_checks = 0
    for key, label in SECTION_LABELS:
        complete_count = sum(checks[key])
        started_count = sum(started_checks[key])
        completed_checks += complete_count
        total_count = len(exercises)
        if total_count == 0 or started_count == 0:
            status = "not_started"
        elif complete_count == total_count:
            status = "complete"
        else:
            status = "in_progress"
        sections.append(
            {
                "key": key,
                "label": label,
                "status": status,
                "complete_count": complete_count,
                "started_count": started_count,
                "total_count": total_count,
            }
        )

    total_checks = len(exercises) * len(SECTION_LABELS)
    completion = (
        int(completed_checks * 100 / total_checks + 0.5) if total_checks else 0
    )
    assessment_checks = [
        [checks[key][index] for key, _label in SECTION_LABELS]
        for index in range(len(exercises))
    ]
    completed_assessments = sum(all(values) for values in assessment_checks)
    in_progress_assessments = sum(any(values) and not all(values) for values in assessment_checks)

    activities = []
    activities.extend(
        _activity_rows(
            Exercise, "Assessment created", lambda row: row.title, Exercise.created_at
        )
    )
    activities.extend(
        _activity_rows(
            ObjectActionObservation,
            "Object/action observation",
            lambda row: f"{row.identified_object}: {row.observed_action}",
            ObjectActionObservation.created_at,
        )
    )
    activities.extend(
        _activity_rows(
            MovementObservation,
            "Movement observation",
            lambda row: row.movement_description,
            MovementObservation.created_at,
        )
    )
    activities.extend(
        _activity_rows(
            QualityAssessment,
            "Quality assessment updated",
            lambda row: row.exercise.title,
            QualityAssessment.updated_at,
        )
    )
    activities.extend(
        _activity_rows(
            QualityIssue,
            "Detail issue recorded",
            lambda row: row.description,
            QualityIssue.created_at,
        )
    )
    activities.extend(
        _activity_rows(
            SectionReview,
            "Attention review completed",
            lambda row: row.exercise.title,
            SectionReview.reviewed_at,
        )
    )
    activities.sort(key=lambda activity: _utc_key(activity.occurred_at), reverse=True)

    return {
        "completion": completion,
        "completed_assessments": completed_assessments,
        "in_progress_assessments": in_progress_assessments,
        "total_assessments": len(exercises),
        "sections": sections,
        "recent_activity": activities[:8],
    }
