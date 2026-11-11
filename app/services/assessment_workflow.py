from app.models.quality import QUALITY_CATEGORIES

SECTION_DETAILS = (
    ("object_action", "Object & Action Annotation"),
    ("movement", "Movement & Motion Analysis"),
    ("quality", "Video Quality Assessment"),
    ("attention_to_detail", "Annotation Quality Review"),
)


def section_status(exercise, key):
    if key == "object_action":
        started = bool(exercise.object_action_observations)
        complete = started
    elif key == "movement":
        started = bool(exercise.movement_observations)
        complete = started
    elif key == "quality":
        assessment = exercise.quality_assessment
        started = assessment is not None and bool(assessment.ratings)
        complete = (
            assessment is not None
            and len(assessment.ratings) == len(QUALITY_CATEGORIES)
            and {rating.category for rating in assessment.ratings}
            == set(QUALITY_CATEGORIES)
        )
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


def assessment_sections(exercise):
    return [
        {
            "key": key,
            "label": label,
            "status": section_status(exercise, key),
        }
        for key, label in SECTION_DETAILS
    ]


def missing_assessment_sections(exercise):
    return [
        section["label"]
        for section in assessment_sections(exercise)
        if section["status"] != "complete"
    ]
