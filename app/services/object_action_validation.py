import re

TIME_PATTERN = re.compile(r"^\d{1,3}:[0-5]\d(?::[0-5]\d)?$")
RANGE_PATTERN = re.compile(r"\s*[-\u2013\u2014]\s*")


def _trimmed(form, field):
    return form.get(field, "").strip()


def validate_exercise_form(form):
    values = {
        "title": _trimmed(form, "title"),
        "clip_reference": _trimmed(form, "clip_reference"),
    }
    errors = []

    if not values["title"]:
        errors.append("Exercise title is required.")
    elif len(values["title"]) > 160:
        errors.append("Exercise title must be 160 characters or fewer.")

    if len(values["clip_reference"]) > 300:
        errors.append("Clip reference must be 300 characters or fewer.")

    return values, errors


def normalize_timestamp(value):
    value = value.strip()
    parts = RANGE_PATTERN.split(value)
    if len(parts) not in (1, 2) or not all(TIME_PATTERN.fullmatch(part) for part in parts):
        return None

    def to_seconds(part):
        components = [int(component) for component in part.split(":")]
        if len(components) == 2:
            return components[0] * 60 + components[1]
        return components[0] * 3600 + components[1] * 60 + components[2]

    if len(parts) == 2 and to_seconds(parts[1]) < to_seconds(parts[0]):
        return None
    return "-".join(parts)


def validate_observation_form(form):
    values = {
        "timestamp": _trimmed(form, "timestamp"),
        "identified_object": _trimmed(form, "identified_object"),
        "observed_action": _trimmed(form, "observed_action"),
        "additional_observations": _trimmed(form, "additional_observations"),
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

    if not values["identified_object"]:
        errors.append("Identified object is required.")
    elif len(values["identified_object"]) > 160:
        errors.append("Identified object must be 160 characters or fewer.")

    if not values["observed_action"]:
        errors.append("Observed action is required.")
    elif len(values["observed_action"]) > 4000:
        errors.append("Observed action must be 4,000 characters or fewer.")

    if len(values["additional_observations"]) > 4000:
        errors.append("Additional observations must be 4,000 characters or fewer.")

    return values, errors
