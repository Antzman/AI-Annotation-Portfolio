import re
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

from app.models import (
    Exercise,
    MovementObservation,
    ObjectActionObservation,
    QualityAssessment,
    QualityIssue,
    QualityRating,
    SectionReview,
    UserProfile,
)
from app.models.quality import QUALITY_CATEGORIES
from app.services.pdf_report import _draw_page
from app.services.report_data import build_report_data


def _populate_complete_assessment(session, long_text=False):
    long_text = ("Long observation text & evidence. " * 120) if long_text else ""
    exercise = Exercise(title="Living room assessment", clip_reference="clip-2026-04")
    exercise.object_action_observations.append(
        ObjectActionObservation(
            timestamp="00:00-00:03",
            identified_object="Person",
            observed_action="Walks into the room.",
            additional_observations=long_text or "Faces the camera.",
        )
    )
    exercise.movement_observations.append(
        MovementObservation(
            timestamp="00:00-00:03",
            movement_description="Walks at an even pace.",
            visibility="clearly_visible",
            plausibility="plausible",
            reasoning="The motion is consistent from frame to frame.",
            inconsistencies=long_text or None,
        )
    )
    exercise.quality_assessment = QualityAssessment(
        ratings=[
            QualityRating(
                category=category,
                score=8,
                explanation=f"Observed evidence for {category}. {long_text}",
            )
            for category in QUALITY_CATEGORIES
        ]
    )
    exercise.quality_issues.append(
        QualityIssue(
            timestamp="00:04-00:05",
            category="visual_obstruction",
            description="A foreground item briefly blocks the subject.",
            severity="medium",
            explanation=f"The interaction is partially obscured. {long_text}",
            suggested_correction="Annotate the action as partially visible.",
        )
    )
    review = SectionReview(
        section_key="attention_to_detail",
        reviewed_at=datetime.now(UTC),
    )
    exercise.section_reviews.append(review)
    session.add(exercise)
    profile = session.get(UserProfile, 1)
    profile.name = "Jordan Reviewer"
    profile.introduction = "I focus on clear, evidence-led annotation."
    profile.experience = "Assessment practice."
    profile.technical_interests = "Video quality and movement."
    profile.skills = "Careful observation\nConsistent timestamps"
    profile.contact_information = "jordan@example.test"
    session.commit()
    return exercise


def test_report_preview_marks_empty_report_and_blocks_empty_pdf(app):
    client = app.test_client()

    preview = client.get("/report-preview")
    assert preview.status_code == 200
    assert b"No assessment results yet" in preview.data
    assert b"Download PDF" in preview.data
    assert b"disabled" in preview.data

    response = client.get("/report-preview/download")
    assert response.status_code == 409
    assert b"Create at least one assessment" in response.data


def test_incomplete_report_identifies_missing_results_without_scores(app, session):
    exercise = Exercise(title="Partial quality assessment")
    exercise.quality_assessment = QualityAssessment(
        ratings=[
            QualityRating(
                category="visual_clarity",
                score=7,
                explanation="The subject is usually clear.",
            )
        ]
    )
    session.add(exercise)
    session.commit()

    report = build_report_data()
    assert report["is_complete"] is False
    assert report["completion"] == 0
    assert report["exercises"][0].quality_assessment.overall_score is None

    preview = app.test_client().get("/report-preview")
    assert preview.status_code == 200
    assert b"Draft report" in preview.data
    assert b"1 of 5 category ratings saved" in preview.data
    assert b"No overall score is reported" in preview.data
    assert b"not been marked reviewed" in preview.data


def test_report_pdf_is_paginated_detailed_and_downloadable(app, session):
    _populate_complete_assessment(session, long_text=True)
    client = app.test_client()

    preview = client.get("/report-preview")
    assert preview.status_code == 200
    assert b"Jordan Reviewer" in preview.data
    assert b"Object &amp; Action Annotation" in preview.data
    assert b"Movement &amp; Motion Analysis" in preview.data
    assert b"Video Quality Assessment" in preview.data
    assert b"Annotation Quality Review" in preview.data
    assert b"Observed evidence for visual_clarity" in preview.data
    assert b"Suggested correction" in preview.data
    assert b"Complete" in preview.data

    response = client.get("/report-preview/download")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert "attachment;" in response.headers["Content-Disposition"]
    assert response.data.startswith(b"%PDF-")
    assert response.data.rstrip().endswith(b"%%EOF")
    assert len(re.findall(rb"/Type\s*/Page\b", response.data)) >= 2


def test_pdf_page_footer_includes_current_page_number():
    canvas = Mock()

    _draw_page(canvas, SimpleNamespace(page=3))

    canvas.drawRightString.assert_called_once()
    assert canvas.drawRightString.call_args.args[-1] == "Page 3"


def test_report_preview_escapes_profile_markup(app, session):
    profile = session.get(UserProfile, 1)
    profile.name = "<script>alert(1)</script>"
    session.add(Exercise(title="Safe display"))
    session.commit()

    response = app.test_client().get("/report-preview")

    assert response.status_code == 200
    assert b"&lt;script&gt;" in response.data
    assert b"<script>alert(1)</script>" not in response.data
