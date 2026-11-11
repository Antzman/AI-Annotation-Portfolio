from app.models import (
    Exercise,
    MovementObservation,
    ObjectActionObservation,
    QualityAssessment,
    QualityRating,
    SectionReview,
)
from app.models.quality import QUALITY_CATEGORIES
from app.services.dashboard import get_dashboard_data


def _complete_exercise(session, title):
    exercise = Exercise(title=title)
    exercise.object_action_observations.append(
        ObjectActionObservation(
            timestamp="00:00-00:03",
            identified_object="Person",
            observed_action="Walks into the room",
        )
    )
    exercise.movement_observations.append(
        MovementObservation(
            timestamp="00:00-00:03",
            movement_description="Walks into the room",
            visibility="clearly_visible",
            plausibility="plausible",
            reasoning="The motion is consistent.",
        )
    )
    exercise.quality_assessment = QualityAssessment(
        ratings=[
            QualityRating(
                category=category,
                score=8,
                explanation=f"Reason for {category}.",
            )
            for category in QUALITY_CATEGORIES
        ]
    )
    review = SectionReview(section_key="attention_to_detail")
    review.mark_reviewed()
    exercise.section_reviews.append(review)
    session.add(exercise)
    return exercise


def test_dashboard_empty_database_shows_zero_completion_and_not_started(app):
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Portfolio completion" in response.data
    assert b"0 of 0 assessments complete" in response.data
    assert response.data.count(b"Not started") == 4
    assert b"No activity yet" in response.data


def test_dashboard_calculates_progress_from_each_exercise(session, app):
    complete = _complete_exercise(session, "Complete assessment")
    incomplete = Exercise(title="In-progress assessment")
    incomplete.object_action_observations.append(
        ObjectActionObservation(
            timestamp="00:01",
            identified_object="Chair",
            observed_action="Moves backwards",
        )
    )
    session.add(incomplete)
    session.commit()

    dashboard = get_dashboard_data()

    assert dashboard["total_assessments"] == 2
    assert dashboard["completed_assessments"] == 1
    assert dashboard["in_progress_assessments"] == 1
    assert dashboard["completion"] == 63
    assert [section["status"] for section in dashboard["sections"]] == [
        "complete",
        "in_progress",
        "in_progress",
        "in_progress",
    ]
    assert dashboard["sections"][3]["complete_count"] == 1


def test_dashboard_renders_persisted_recent_activity(app, session):
    _complete_exercise(session, "Kitchen chair clip")
    session.commit()

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Object/action observation" in response.data
    assert b"Kitchen chair clip" in response.data


def test_navigation_routes_and_vendor_assets_are_local(app):
    client = app.test_client()

    for path in (
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert b"This section is not available yet" in response.data
        assert b"https://" not in response.data

    object_action_response = client.get("/object-action")
    assert object_action_response.status_code == 200
    assert b"Create an assessment" in object_action_response.data
    assert b"https://" not in object_action_response.data

    movement_response = client.get("/movement-analysis")
    assert movement_response.status_code == 200
    assert b"No assessments available" in movement_response.data
    assert b"https://" not in movement_response.data

    quality_response = client.get("/video-quality")
    assert quality_response.status_code == 200
    assert b"No assessments available" in quality_response.data
    assert b"https://" not in quality_response.data

    attention_response = client.get("/attention-to-detail")
    assert attention_response.status_code == 200
    assert b"No assessments available" in attention_response.data
    assert b"https://" not in attention_response.data

    report_response = client.get("/report-preview")
    assert report_response.status_code == 200
    assert b"No assessment data yet" in report_response.data
    assert b"https://" not in report_response.data

    profile_response = client.get("/about")
    assert profile_response.status_code == 200
    assert b"Professional information" in profile_response.data
    assert b"https://" not in profile_response.data

    response = client.get("/static/vendor/bootstrap/bootstrap.min.css")
    assert response.status_code == 200
    assert b"bootstrap" in response.data.lower()
