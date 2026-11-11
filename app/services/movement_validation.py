from app.services.object_action_validation import normalize_timestamp

VISIBILITY_OPTIONS = (
    ("clearly_visible", "Clearly visible"),
    ("partially_visible", "Partially visible"),
    ("obstructed", "Obstructed"),
    ("unclear", "Unclear"),
)
PLAUSIBILITY_OPTIONS = (
    ("plausible", "Plausible"),
    ("uncertain", "Uncertain"),
    ("implausible", "Implausible"),
)
VISIBILITY_VALUES = {value for value, _label in VISIBILITY_OPTIONS}
PLAUSIBILITY_VALUES = {value for value, _label in PLAUSIBILITY_OPTIONS}


def _trimmed(form, field):
    return form.get(field, "").strip()


def validate_movement_form(form):
    values = {
        "timestamp": _trimmed(form, "timestamp"),
        "movement_description": _trimmed(form, "movement_description"),
        "visibility": _trimmed(form, "visibility"),
        "plausibility": _trimmed(form, "plausibility"),
        "inconsistencies": _trimmed(form, "inconsistencies"),
        "reasoning": _trimmed(form, "reasoning"),
    }
    errors = []

    normalized_timestamp = normalize_timestamp(values["timestamp"])
    if normalized_timestamp is None:
        errors.append(
            "Timestamp must be MM:SS or HH:MM:SS, optionally as a range "
            "(for example, 00:03-00:06)."
        )
    else:
        values["timestamp"] = normalized_timestamp

    if not values["movement_description"]:
        errors.append("Movement description is required.")
    elif len(values["movement_description"]) > 4000:
        errors.append("Movement description must be 4,000 characters or fewer.")

    if values["visibility"] not in VISIBILITY_VALUES:
        errors.append("Select a valid movement visibility option.")

    if values["plausibility"] not in PLAUSIBILITY_VALUES:
        errors.append("Select a valid physical plausibility option.")

    if len(values["inconsistencies"]) > 4000:
        errors.append("Observed inconsistencies must be 4,000 characters or fewer.")

    if not values["reasoning"]:
        errors.append("Explanation and reasoning are required.")
    elif len(values["reasoning"]) > 4000:
        errors.append("Explanation and reasoning must be 4,000 characters or fewer.")

    return values, errors
