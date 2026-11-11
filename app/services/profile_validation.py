PROFILE_FIELDS = {
    "name": ("Name", 120),
    "introduction": ("Professional introduction", 4000),
    "experience": ("Relevant experience", 4000),
    "technical_interests": ("Technical interests", 4000),
    "skills": ("Skills", 4000),
    "contact_information": ("Contact information", 500),
}


def validate_profile_form(form):
    values = {
        field: form.get(field, "").strip()
        for field in PROFILE_FIELDS
    }
    errors = [
        f"{label} must be {limit} characters or fewer."
        for field, (label, limit) in PROFILE_FIELDS.items()
        if len(values[field]) > limit
    ]
    return values, errors
