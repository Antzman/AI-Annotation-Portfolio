import re

from app.models import Exercise, MovementObservation
from app.services.movement_validation import (
    PLAUSIBILITY_OPTIONS,
    VISIBILITY_OPTIONS,
    validate_movement_form,
)


CSRF_PATTERN = re.compile(rb'name="_csrf_token" value="([^"]+)"')


def _token(response):
    match = CSRF_PATTERN.search(response.data)
    assert match is not None
    return match.group(1).decode()


def _create_exercise(session, title="Movement assessment"):
    exercise = Exercise(title=title, clip_reference="clip-reference")
    session.add(exercise)
    session.commit()
    return exercise


def _valid_form(token, **overrides):
    values = {
        "_csrf_token": token,
        "timestamp": "00:00-00:03",
        "movement_description": "Steps forward and turns to the left.",
        "visibility": "clearly_visible",
        "plausibility": "plausible",
        "inconsistencies": "",
        "reasoning": "The motion is consistent from beginning to end.",
    }
    values.update(overrides)
    return values


def test_movement_form_restricts_visibility_and_plausibility_values():
    values, errors = validate_movement_form(
        {
            "timestamp": "00:01",
            "movement_description": "Moves forward",
            "visibility": "mostly_visible",
            "plausibility": "impossible",
            "reasoning": "The movement appears consistent.",
        }
    )

    assert values["visibility"] == "mostly_visible"
    assert any("visibility option" in error for error in errors)
    assert any("plausibility option" in error for error in errors)
    assert {value for value, _label in VISIBILITY_OPTIONS} == {
        "clearly_visible",
        "partially_visible",
        "obstructed",
        "unclear",
    }
    assert {value for value, _label in PLAUSIBILITY_OPTIONS} == {
        "plausible",
        "uncertain",
        "implausible",
    }


def test_movement_section_lists_assessments_and_empty_state(app, session):
    client = app.test_client()
    response = client.get("/movement-analysis")
    assert response.status_code == 200
    assert b"No assessments available" in response.data

    _create_exercise(session)
    response = client.get("/movement-analysis")

    assert response.status_code == 200
    assert b"Movement assessment" in response.data
    assert b"0 observations" in response.data


def test_movement_observations_can_be_created_edited_and_deleted(app, session):
    exercise = _create_exercise(session)
    client = app.test_client()
    detail_url = f"/movement-analysis/{exercise.id}"
    page = client.get(detail_url)
    assert page.status_code == 200
    token = _token(page)

    invalid = client.post(
        detail_url,
        data=_valid_form(token, visibility="unknown", plausibility="plausible"),
    )
    assert invalid.status_code == 400
    assert b"Select a valid movement visibility option" in invalid.data
    assert session.query(MovementObservation).count() == 0

    first = client.post(detail_url, data=_valid_form(_token(invalid)))
    assert first.status_code == 302
    observation = session.query(MovementObservation).one()
    assert observation.visibility == "clearly_visible"
    assert observation.plausibility == "plausible"
    assert observation.timestamp == "00:00-00:03"

    page = client.get(detail_url)
    second = client.post(
        detail_url,
        data=_valid_form(
            _token(page),
            timestamp="00:03-00:06",
            movement_description="Sits down.",
            visibility="partially_visible",
            plausibility="uncertain",
            inconsistencies="The leg briefly disappears behind the chair.",
            reasoning="The seat is visible, but the lower body is partly blocked.",
        ),
    )
    assert second.status_code == 302
    assert session.query(MovementObservation).count() == 2

    edit_url = f"/movement-analysis/observations/{observation.id}/edit"
    edit_page = client.get(edit_url)
    edited = client.post(
        edit_url,
        data=_valid_form(
            _token(edit_page),
            timestamp="00:00-00:04",
            movement_description="Steps forward, then pauses.",
            visibility="unclear",
            plausibility="implausible",
            inconsistencies="Foot position changes abruptly.",
            reasoning="The apparent change may indicate an inconsistent frame.",
        ),
    )
    assert edited.status_code == 302

    detail = client.get(detail_url)
    assert b"Steps forward, then pauses." in detail.data
    assert b"Unclear" in detail.data
    assert b"Implausible" in detail.data
    assert b"Foot position changes abruptly." in detail.data
    assert b"Sits down." in detail.data

    delete_url = f"/movement-analysis/observations/{observation.id}/delete"
    deleted = client.post(delete_url, data={"_csrf_token": _token(detail)})
    assert deleted.status_code == 302
    assert session.query(MovementObservation).count() == 1
    detail = client.get(detail_url)
    assert b"Steps forward, then pauses." not in detail.data
    assert b"Sits down." in detail.data


def test_movement_post_requires_csrf_token_and_reasoning(app, session):
    exercise = _create_exercise(session)
    client = app.test_client()
    detail_url = f"/movement-analysis/{exercise.id}"
    page = client.get(detail_url)

    no_token = client.post(detail_url, data=_valid_form(""))
    assert no_token.status_code == 400
    assert session.query(MovementObservation).count() == 0

    invalid = client.post(
        detail_url,
        data=_valid_form(_token(page), reasoning="   "),
    )
    assert invalid.status_code == 400
    assert b"Explanation and reasoning are required" in invalid.data
    assert session.query(MovementObservation).count() == 0
