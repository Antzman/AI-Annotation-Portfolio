import re

from app.models import (
    Exercise,
    MovementObservation,
    ObjectActionObservation,
    QualityIssue,
    QualityRating,
)
from app.models.quality import QUALITY_CATEGORIES
from app.services.dashboard import get_dashboard_data

CSRF_PATTERN = re.compile(rb'name="_csrf_token" value="([^"]+)"')


def _token(response):
    match = CSRF_PATTERN.search(response.data)
    assert match is not None
    return match.group(1).decode()


def _quality_form(token):
    form = {"_csrf_token": token}
    for index, category in enumerate(QUALITY_CATEGORIES, start=6):
        form[f"score_{category}"] = str(index)
        form[f"explanation_{category}"] = f"Evidence for {category}."
    return form


def test_assessment_workflow_navigation_review_finalize_and_pdf(app, session):
    client = app.test_client()
    start_page = client.get("/object-action")
    started = client.post(
        "/object-action",
        data={
            "_csrf_token": _token(start_page),
            "title": "Dog",
            "clip_reference": "Dog clip 01",
        },
    )
    assert started.status_code == 302
    exercise = session.query(Exercise).one()
    exercise_id = exercise.id

    overview_url = f"/assessments/{exercise_id}"
    overview = client.get(overview_url)
    assert overview.status_code == 200
    assert b'class="assessment-nav-link active"' in overview.data
    for section_path in (
        f"/object-action/{exercise_id}",
        f"/movement-analysis/{exercise_id}",
        f"/video-quality/{exercise_id}",
        f"/attention-to-detail/{exercise_id}",
    ):
        assert section_path.encode() in overview.data
    assert b"Final Review" in overview.data

    review_url = f"{overview_url}/review"
    review = client.get(review_url)
    assert b'class="assessment-nav-link active"' in review.data
    blocked = client.post(
        f"{overview_url}/finalize",
        data={"_csrf_token": _token(start_page)},
    )
    assert blocked.status_code == 302
    assert exercise.finalized_at is None

    object_url = f"/object-action/{exercise_id}"
    object_page = client.get(object_url)
    client.post(
        object_url,
        data={
            "_csrf_token": _token(object_page),
            "timestamp": "00:00-00:03",
            "identified_object": "Dog",
            "observed_action": "Walks into the room",
            "additional_observations": "Tail is visible.",
        },
    )
    observation = session.query(ObjectActionObservation).one()

    movement_url = f"/movement-analysis/{exercise_id}"
    movement_page = client.get(movement_url)
    client.post(
        movement_url,
        data={
            "_csrf_token": _token(movement_page),
            "timestamp": "00:01-00:04",
            "movement_description": "The dog walks forward.",
            "visibility": "clearly_visible",
            "plausibility": "plausible",
            "inconsistencies": "None observed.",
            "reasoning": "The movement is continuous across the clip.",
        },
    )

    quality_url = f"/video-quality/{exercise_id}"
    quality_page = client.get(quality_url)
    client.post(quality_url, data=_quality_form(_token(quality_page)))

    attention_url = f"/attention-to-detail/{exercise_id}"
    attention_page = client.get(attention_url)
    client.post(
        attention_url,
        data={
            "_csrf_token": _token(attention_page),
            "timestamp": "00:02",
            "category": "visual_obstruction",
            "description": "A bowl is briefly obscured.",
            "severity": "low",
            "explanation": "The bowl is partially behind the dog.",
            "suggested_correction": "Mark as partially visible.",
        },
    )
    attention_page = client.get(attention_url)
    client.post(
        f"{attention_url}/mark-reviewed",
        data={"_csrf_token": _token(attention_page)},
    )

    object_page = client.get(object_url)
    assert b"Walks into the room" in object_page.data
    client.post(
        object_url,
        data={
            "_csrf_token": _token(object_page),
            "timestamp": "00:04-00:06",
            "identified_object": "Dog",
            "observed_action": "Turns toward the camera",
            "additional_observations": "",
        },
    )
    assert session.query(ObjectActionObservation).count() == 2

    edit_url = f"/object-action/observations/{observation.id}/edit"
    edit_page = client.get(edit_url)
    edited = client.post(
        edit_url,
        data={
            "_csrf_token": _token(edit_page),
            "timestamp": "00:00-00:04",
            "identified_object": "Dog",
            "observed_action": "Walks and pauses in the room",
            "additional_observations": "Tail is visible.",
        },
    )
    assert edited.status_code == 302
    assert observation.exercise_id == exercise_id

    review = client.get(review_url)
    assert review.status_code == 200
    assert b"Walks and pauses in the room" in review.data
    assert b"The dog walks forward." in review.data
    assert b"Visual Clarity" in review.data
    assert b"A bowl is briefly obscured." in review.data
    assert b"Submit &amp; Finalise Assessment" in review.data
    assert session.query(MovementObservation).one().exercise_id == exercise_id
    assert session.query(QualityRating).count() == len(QUALITY_CATEGORIES)
    assert session.query(QualityIssue).one().exercise_id == exercise_id

    dashboard = get_dashboard_data()
    assert dashboard["started_assessments"] == 1
    assert dashboard["completed_assessments"] == 0
    assert dashboard["in_progress_assessments"] == 1

    finalized = client.post(
        f"{overview_url}/finalize",
        data={"_csrf_token": _token(review)},
    )
    assert finalized.status_code == 302
    assert exercise.finalized_at is not None

    dashboard = get_dashboard_data()
    assert dashboard["completed_assessments"] == 1
    assert dashboard["in_progress_assessments"] == 0

    pdf_response = client.get(f"{overview_url}/report.pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.mimetype == "application/pdf"
    assert pdf_response.data.startswith(b"%PDF-")
    assert "Dog-assessment-report.pdf" in pdf_response.headers["Content-Disposition"]

    report_page = client.get("/report-preview")
    assert report_page.status_code == 200
    assert b"Completed" in report_page.data
    assert f'href="{overview_url}"'.encode() in report_page.data

    overview = client.get(overview_url)
    reopened = client.post(
        f"{overview_url}/reopen",
        data={"_csrf_token": _token(overview)},
    )
    assert reopened.status_code == 302
    assert exercise.finalized_at is None
