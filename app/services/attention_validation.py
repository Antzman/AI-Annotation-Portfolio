from app.models.quality import ISSUE_CATEGORIES, ISSUE_SEVERITIES
from app.services.object_action_validation import normalize_timestamp

ISSUE_LABELS = {
    "missing_objects": "Missing objects",
    "unexpected_object_movement": "Unexpected object movement",
    "unclear_actions": "Unclear actions",
    "visual_obstruction": "Visual obstruction",
    "inconsistent_frames": "Inconsistent frames",
    "other": "Other observations",
}
SEVERITY_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
}


def _trimmed(form, field):
    return form.get(field, "").strip()


def validate_issue_form(form):
    values = {
        "timestamp": _trimmed(form, "timestamp"),
        "category": _trimmed(form, "category"),
        "description": _trimmed(form, "description"),
        "severity": _trimmed(form, "severity"),
        "explanation": _trimmed(form, "explanation"),
        "suggested_correction": _trimmed(form, "suggested_correction"),
    }
    errors = []

    timestamp = normalize_timestamp(values["timestamp"])
    if timestamp is None:
        errors.append(
            "Timestamp is required in MM:SS or HH:MM:SS format, optionally as a range."
        )
    else:
        values["timestamp"] = timestamp

    if values["category"] not in ISSUE_CATEGORIES:
        errors.append("Select a valid issue category.")

    if not values["description"]:
        errors.append("Issue description is required.")
    elif len(values["description"]) > 4000:
        errors.append("Issue description must be 4,000 characters or fewer.")

    if values["severity"] not in ISSUE_SEVERITIES:
        errors.append("Select a valid severity.")

    if not values["explanation"]:
        errors.append("Issue explanation is required.")
    elif len(values["explanation"]) > 4000:
        errors.append("Issue explanation must be 4,000 characters or fewer.")

    if len(values["suggested_correction"]) > 4000:
        errors.append("Suggested correction must be 4,000 characters or fewer.")

    return values, errors
