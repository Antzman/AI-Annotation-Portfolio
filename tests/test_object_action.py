import re

from app.models import Exercise, ObjectActionObservation
from app.services.object_action_validation import normalize_timestamp


CSRF_PATTERN = re.compile(rb'name="_csrf_token" value="([^"]+)"')


def _token(response):
    match = CSRF_PATTERN.search(response.data)
    assert match is not None
    return match.group(1).decode()


def test_timestamp_validation_accepts_single_times_and_ranges():
    assert normalize_timestamp("00:03") == "00:03"
    assert normalize_timestamp("00:03–00:06") == "00:03-00:06"
    assert normalize_timestamp("01:02:03 - 01:02:09") == "01:02:03-01:02:09"
    assert normalize_timestamp("00:10-00:03") is None
    assert normalize_timestamp("00:60") is None
    assert normalize_timestamp("00:01-00:02-00:03") is None


def test_create_exercise_requires_csrf_and_valid_title(app, session):
    client = app.test_client()

    response = client.post("/object-action", data={"title": "Missing token"})
    assert response.status_code == 400
    assert session.query(Exercise).count() == 0

    token = _token(client.get("/object-action"))
    response = client.post(
        "/object-action",
        data={"_csrf_token": token, "title": "  ", "clip_reference": ""},
    )
    assert response.status_code == 400
    assert b"Exercise title is required" in response.data
    assert session.query(Exercise).count() == 0


def test_exercise_and_multiple_observations_can_be_created_edited_and_deleted(
    app, session
):
    client = app.test_client()
    token = _token(client.get("/object-action"))
    response = client.post(
        "/object-action",
        data={
            "_csrf_token": token,
            "title": "  Entering a room  ",
            "clip_reference": "  Clip 01  ",
        },
    )
    assert response.status_code == 302
    assert response.location.endswith("/object-action/1")
    exercise = session.query(Exercise).one()
    assert exercise.title == "Entering a room"
    assert exercise.clip_reference == "Clip 01"

    detail_url = response.location
    detail = client.get(detail_url)
    token = _token(detail)
    first = client.post(
        detail_url,
        data={
            "_csrf_token": token,
            "timestamp": "00:00–00:03",
            "identified_object": "Person",
            "observed_action": "Walks into the room",
            "additional_observations": "Faces the camera",
        },
    )
    assert first.status_code == 302
    first_observation = session.query(ObjectActionObservation).one()
    assert first_observation.timestamp == "00:00-00:03"

    detail = client.get(detail_url)
    token = _token(detail)
    second = client.post(
        detail_url,
        data={
            "_csrf_token": token,
            "timestamp": "00:03-00:06",
            "identified_object": "Chair",
            "observed_action": "Person pulls chair backwards",
            "additional_observations": "",
        },
    )
    assert second.status_code == 302
    assert session.query(ObjectActionObservation).count() == 2

    edit_url = f"/object-action/observations/{first_observation.id}/edit"
    edit_page = client.get(edit_url)
    updated = client.post(
        edit_url,
        data={
            "_csrf_token": _token(edit_page),
            "timestamp": "00:00-00:04",
            "identified_object": "Person",
            "observed_action": "Walks and pauses",
            "additional_observations": "Updated note",
        },
    )
    assert updated.status_code == 302
    assert first_observation.observed_action == "Walks and pauses"

    detail = client.get(detail_url)
    assert b"Walks and pauses" in detail.data
    assert b"Person pulls chair backwards" in detail.data

    delete_url = f"/object-action/observations/{first_observation.id}/delete"
    deleted = client.post(
        delete_url, data={"_csrf_token": _token(detail)}
    )
    assert deleted.status_code == 302
    assert session.query(ObjectActionObservation).count() == 1
    detail = client.get(detail_url)
    assert b"Person pulls chair backwards" in detail.data
    assert b"Walks and pauses" not in detail.data


def test_invalid_observation_values_are_not_saved(app, session):
    client = app.test_client()
    token = _token(client.get("/object-action"))
    response = client.post(
        "/object-action",
        data={"_csrf_token": token, "title": "Timestamp validation"},
    )
    detail_url = response.location
    detail = client.get(detail_url)

    response = client.post(
        detail_url,
        data={
            "_csrf_token": _token(detail),
            "timestamp": "00:10-00:02",
            "identified_object": "Person",
            "observed_action": "Walks",
        },
    )

    assert response.status_code == 400
    assert b"Timestamp must be MM:SS or HH:MM:SS" in response.data
    assert session.query(ObjectActionObservation).count() == 0


def test_edit_and_delete_methods_reject_get_requests(app):
    client = app.test_client()
    token = _token(client.get("/object-action"))
    response = client.post(
        "/object-action",
        data={"_csrf_token": token, "title": "Read-only route test"},
    )
    detail_url = response.location
    detail = client.get(detail_url)
    response = client.post(
        detail_url,
        data={
            "_csrf_token": _token(detail),
            "timestamp": "00:01",
            "identified_object": "Person",
            "observed_action": "Stands",
        },
    )
    assert response.status_code == 302
    detail = client.get(detail_url)
    observation_id = re.search(rb"/observations/(\d+)/edit", detail.data).group(1).decode()

    assert client.get(f"/object-action/observations/{observation_id}/delete").status_code == 405
