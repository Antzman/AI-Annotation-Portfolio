import re

from app.models import Exercise, QualityIssue, SectionReview
from app.services.attention_validation import (
    ISSUE_LABELS,
    SEVERITY_LABELS,
    validate_issue_form,
)
from app.services.dashboard import get_dashboard_data


CSRF_PATTERN = re.compile(rb'name="_csrf_token" value="([^"]+)"')


def _token(response):
    match = CSRF_PATTERN.search(response.data)
    assert match is not None
    return match.group(1).decode()


def _create_exercise(session, title="Detail review"):
    exercise = Exercise(title=title, clip_reference="clip-reference")
    session.add(exercise)
    session.commit()
    return exercise


def _form(token, **overrides):
    values = {
        "_csrf_token": token,
        "timestamp": "00:00-00:03",
        "category": "missing_objects",
        "description": "A small item is not visible in the final frame.",
        "severity": "medium",
        "explanation": "The object was visible earlier but disappears without an action.",
        "suggested_correction": "Mark the final object location as uncertain.",
    }
    values.update(overrides)
    return values


def test_issue_validation_requires_timestamp_category_and_severity():
    _values, errors = validate_issue_form(
        {
            "timestamp": "",
            "category": "not-a-category",
            "description": "Object disappears",
            "severity": "critical",
            "explanation": "The object is no longer visible.",
            "suggested_correction": "",
        }
    )

    assert any("Timestamp is required" in error for error in errors)
    assert any("valid issue category" in error for error in errors)
    assert any("valid severity" in error for error in errors)
    assert ISSUE_LABELS["inconsistent_frames"] == "Inconsistent frames"
    assert SEVERITY_LABELS == {"low": "Low", "medium": "Medium", "high": "High"}


def test_attention_section_can_be_marked_reviewed_with_no_issues(app, session):
    exercise = _create_exercise(session)
    client = app.test_client()
    detail_url = f"/attention-to-detail/{exercise.id}"
    page = client.get(detail_url)
    assert page.status_code == 200
    assert b"No issues are recorded" in page.data

    response = client.post(
        f"{detail_url}/mark-reviewed",
        data={"_csrf_token": _token(page)},
    )

    assert response.status_code == 302
    review = session.query(SectionReview).one()
    assert review.section_key == "attention_to_detail"
    assert review.reviewed_at is not None
    dashboard = get_dashboard_data()
    status = next(
        item
        for item in dashboard["sections"]
        if item["key"] == "attention_to_detail"
    )
    assert status["status"] == "complete"

    page = client.get(detail_url)
    assert b"Review complete" in page.data
    assert b"Confirm review again" in page.data


def test_issue_crud_resets_review_and_supports_multiple_entries(app, session):
    exercise = _create_exercise(session)
    client = app.test_client()
    detail_url = f"/attention-to-detail/{exercise.id}"
    page = client.get(detail_url)

    invalid = client.post(
        detail_url,
        data=_form(_token(page), category="unknown-category", severity="urgent"),
    )
    assert invalid.status_code == 400
    assert b"Select a valid issue category" in invalid.data
    assert session.query(QualityIssue).count() == 0

    reviewed = client.post(
        f"{detail_url}/mark-reviewed",
        data={"_csrf_token": _token(invalid)},
    )
    assert reviewed.status_code == 302
    review = session.query(SectionReview).one()
    assert review.reviewed_at is not None

    page = client.get(detail_url)
    first = client.post(detail_url, data=_form(_token(page)))
    assert first.status_code == 302
    issue = session.query(QualityIssue).one()
    assert issue.timestamp == "00:00-00:03"
    assert review.reviewed_at is None

    page = client.get(detail_url)
    second = client.post(
        detail_url,
        data=_form(
            _token(page),
            timestamp="00:03-00:06",
            category="visual_obstruction",
            description="A foreground object briefly blocks the action.",
            severity="high",
            explanation="The hand-object interaction cannot be seen clearly.",
            suggested_correction="Annotate the interaction as partially occluded.",
        ),
    )
    assert second.status_code == 302
    assert session.query(QualityIssue).count() == 2

    edit_url = f"/attention-to-detail/issues/{issue.id}/edit"
    edit_page = client.get(edit_url)
    edited = client.post(
        edit_url,
        data=_form(
            _token(edit_page),
            timestamp="00:00-00:02",
            category="unclear_actions",
            description="The person reaches toward an unclear object.",
            severity="low",
            explanation="The object is outside the visible frame.",
            suggested_correction="Use an action label indicating uncertainty.",
        ),
    )
    assert edited.status_code == 302
    detail = client.get(detail_url)
    assert b"The person reaches toward an unclear object." in detail.data
    assert b"Low severity" in detail.data
    assert b"Review not complete" in detail.data

    delete_url = f"/attention-to-detail/issues/{issue.id}/delete"
    deleted = client.post(
        delete_url, data={"_csrf_token": _token(detail)}
    )
    assert deleted.status_code == 302
    assert session.query(QualityIssue).count() == 1
    detail = client.get(detail_url)
    assert b"The person reaches toward an unclear object." not in detail.data
    assert b"A foreground object briefly blocks the action." in detail.data


def test_issue_routes_require_csrf_and_timestamp(app, session):
    exercise = _create_exercise(session)
    client = app.test_client()
    detail_url = f"/attention-to-detail/{exercise.id}"
    page = client.get(detail_url)

    response = client.post(detail_url, data=_form(""))
    assert response.status_code == 400
    assert session.query(QualityIssue).count() == 0

    response = client.post(
        detail_url,
        data=_form(_token(page), timestamp="not-a-timestamp"),
    )
    assert response.status_code == 400
    assert b"Timestamp is required" in response.data
    assert session.query(QualityIssue).count() == 0


def test_attention_index_shows_review_state_and_issue_count(app, session):
    exercise = _create_exercise(session)
    exercise.quality_issues.append(
        QualityIssue(
            timestamp="00:01",
            category="other",
            description="Unexpected background change.",
            severity="low",
            explanation="The background changes in the final moment.",
        )
    )
    session.commit()

    response = app.test_client().get("/attention-to-detail")

    assert response.status_code == 200
    assert b"Review needed" in response.data
    assert b"1 issue" in response.data
