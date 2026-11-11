from app.models.quality import QUALITY_CATEGORIES

QUALITY_LABELS = {
    "visual_clarity": "Visual clarity",
    "camera_angle": "Camera angle",
    "object_visibility": "Object visibility",
    "movement_visibility": "Movement visibility",
    "overall_footage_quality": "Overall footage quality",
}


def validate_quality_form(form):
    values = {}
    errors = []
    saved_rating_count = 0

    for category in QUALITY_CATEGORIES:
        score_text = form.get(f"score_{category}", "").strip()
        explanation = form.get(f"explanation_{category}", "").strip()
        score = None

        if not score_text and not explanation:
            values[category] = {"score": "", "explanation": ""}
            continue

        if not score_text:
            errors.append(f"{QUALITY_LABELS[category]} needs a score.")
        elif (
            not score_text.isascii()
            or not score_text.isdecimal()
            or len(score_text) > 2
        ):
            errors.append(f"{QUALITY_LABELS[category]} score must be a whole number.")
        else:
            score = int(score_text)
            if not 1 <= score <= 10:
                errors.append(f"{QUALITY_LABELS[category]} score must be from 1 to 10.")

        if not explanation:
            errors.append(f"{QUALITY_LABELS[category]} needs an explanation.")
        elif len(explanation) > 4000:
            errors.append(
                f"{QUALITY_LABELS[category]} explanation must be 4,000 characters or fewer."
            )

        if score is not None and 1 <= score <= 10 and explanation:
            saved_rating_count += 1
            values[category] = {"score": score, "explanation": explanation}
        else:
            values[category] = {"score": score_text, "explanation": explanation}

    if saved_rating_count == 0 and not errors:
        errors.append("Enter at least one rating and explanation before saving a draft.")

    return values, errors
