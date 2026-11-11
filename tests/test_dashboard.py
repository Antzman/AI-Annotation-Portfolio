from datetime import UTC, datetime

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
    exercise = Exercise(title=title, finalized_at=datetime.now(UTC))
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
    assert b"Annotation Dashboard" in response.data
    assert b"Manage video annotation exercises, record observations" in response.data
    assert b"Assessment Progress" in response.data
    assert b"Active Assessments" in response.data
    assert b"Completed Assessments" in response.data
    assert b"Recent Activity" in response.data
    assert b"AI Annotation Studio" in response.data
    assert b"Assessment Reports" in response.data
    assert b"Object &amp; Action Annotation" in response.data
    assert b"Movement &amp; Motion Analysis" in response.data
    assert b"Video Quality Assessment" in response.data
    assert b"Annotation Quality Review" in response.data
    assert b"Demonstration workspace" in response.data
    assert b"data may reset periodically" in response.data
    assert b"Saved section progress across 0 started assessments" in response.data
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

    object_action_response = client.get("/object-action")
    assert object_action_response.status_code == 200
    assert b"Create an assessment" in object_action_response.data

    movement_response = client.get("/movement-analysis")
    assert movement_response.status_code == 200
    assert b"No assessments available" in movement_response.data

    quality_response = client.get("/video-quality")
    assert quality_response.status_code == 200
    assert b"No assessments available" in quality_response.data

    attention_response = client.get("/attention-to-detail")
    assert attention_response.status_code == 200
    assert b"No assessments available" in attention_response.data

    report_response = client.get("/report-preview")
    assert report_response.status_code == 200
    assert b"No assessment results yet" in report_response.data

    profile_response = client.get("/about")
    assert profile_response.status_code == 200
    assert b"Annotator Profile" in profile_response.data
    assert b"Ant" in profile_response.data

    response = client.get("/static/vendor/bootstrap/bootstrap.min.css")
    assert response.status_code == 200
    assert b"bootstrap" in response.data.lower()


def test_social_preview_metadata_and_banner_are_served(app):
    client = app.test_client()

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert b"Annotation Dashboard" in dashboard.data
    assert b"AI Annotation Studio" in dashboard.data
    for metadata in (
        b'<meta property="og:type" content="website">',
        b'<meta property="og:url" content="https://ai-annotation-portfolio.onrender.com/">',
        b'<meta property="og:title" content="AI Annotation Studio | Manual Video Annotation Workspace">',
        b'<meta property="og:description" content="A structured workspace for video annotation, object and action identification, movement analysis and video quality assessment.">',
        b'<meta property="og:image" content="https://ai-annotation-portfolio.onrender.com/static/images/ai-annotation-studio-preview.png">',
        b'<meta property="og:image:width" content="1672">',
        b'<meta property="og:image:height" content="941">',
        b'<meta name="twitter:card" content="summary_large_image">',
        b'<meta name="twitter:title" content="AI Annotation Studio | Manual Video Annotation Workspace">',
        b'<meta name="twitter:description" content="A structured workspace for video annotation, object and action identification, movement analysis and video quality assessment.">',
        b'<meta name="twitter:image" content="https://ai-annotation-portfolio.onrender.com/static/images/ai-annotation-studio-preview.png">',
    ):
        assert metadata in dashboard.data

    image = client.get("/static/images/ai-annotation-studio-preview.png")
    assert image.status_code == 200
    assert image.mimetype == "image/png"
    assert image.data.startswith(b"\x89PNG\r\n\x1a\n")
