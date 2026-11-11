import re

from app.models import UserProfile

CSRF_PATTERN = re.compile(rb'name="_csrf_token" value="([^"]+)"')


def _token(response):
    match = CSRF_PATTERN.search(response.data)
    assert match is not None
    return match.group(1).decode()


def _profile_form(token, **overrides):
    values = {
        "_csrf_token": token,
        "name": "  Alex Example  ",
        "introduction": "I document observable evidence with care.",
        "experience": "Manual annotation practice.",
        "technical_interests": "Movement analysis and data quality.",
        "skills": "Timestamped descriptions\nEvidence-based reasoning",
        "contact_information": "alex@example.test",
    }
    values.update(overrides)
    return values


def test_profile_can_be_saved_and_included_in_report_preview(app, session):
    client = app.test_client()
    page = client.get("/about")
    assert b'value="Ant"' in page.data
    assert b"South African technology enthusiast" in page.data
    response = client.post(
        "/about",
        data=_profile_form(_token(page)),
    )

    assert response.status_code == 302
    profile = session.query(UserProfile).one()
    assert profile.id == 1
    assert profile.name == "Alex Example"
    assert profile.skills == "Timestamped descriptions\nEvidence-based reasoning"

    preview = client.get("/report-preview")
    assert preview.status_code == 200
    assert b"Assessment Reports" in preview.data
    assert b"Alex Example" in preview.data
    assert b"Evidence-based reasoning" in preview.data
    assert b"alex@example.test" in preview.data


def test_profile_lengths_are_validated_and_data_can_be_cleared(app, session):
    client = app.test_client()
    page = client.get("/about")
    invalid = client.post(
        "/about",
        data=_profile_form(_token(page), name="A" * 121),
    )
    assert invalid.status_code == 400
    assert b"Name must be 120 characters or fewer" in invalid.data
    assert session.query(UserProfile).one().name == "Ant"

    page = client.get("/about")
    saved = client.post("/about", data=_profile_form(_token(page)))
    assert saved.status_code == 302
    page = client.get("/about")
    cleared = client.post(
        "/about",
        data={
            "_csrf_token": _token(page),
            "name": "",
            "introduction": "",
            "experience": "",
            "technical_interests": "",
            "skills": "",
            "contact_information": "",
        },
    )
    assert cleared.status_code == 302
    cleared_profile = session.query(UserProfile).one()
    assert all(
        getattr(cleared_profile, field) is None
        for field in (
            "name",
            "introduction",
            "experience",
            "technical_interests",
            "skills",
            "contact_information",
        )
    )
