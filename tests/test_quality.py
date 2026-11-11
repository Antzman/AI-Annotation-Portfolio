import re

from app.models import Exercise, QualityAssessment, QualityRating
from app.models.quality import QUALITY_CATEGORIES
from app.services.dashboard import get_dashboard_data
from app.services.quality_validation import validate_quality_form


CSRF_PATTERN = re.compile(rb'name="_csrf_token" value="([^"]+)"')


def _token(response):
    match = CSRF_PATTERN.search(response.data)
    assert match is not None
    return match.group(1).decode()


def _create_exercise(session, title="Quality assessment"):
    exercise = Exercise(title=title, clip_reference="clip-reference")
    session.add(exercise)
    session.commit()
    return exercise


def _form(token, scores=None, explanations=None):
    scores = scores or {}
    explanations = explanations or {}
    values = {"_csrf_token": token}
    for category in QUALITY_CATEGORIES:
        values[f"score_{category}"] = str(scores.get(category, ""))
        values[f"explanation_{category}"] = explanations.get(category, "")
    return values


def test_quality_validation_allows_complete_pairs_and_rejects_invalid_values():
    values, errors = validate_quality_form(
        _form(
            "token",
            scores={"visual_clarity": "8"},
            explanations={"visual_clarity": "The subject remains distinct."},
        )
    )
    assert errors == []
    assert values["visual_clarity"] == {
        "score": 8,
        "explanation": "The subject remains distinct.",
    }

    _values, errors = validate_quality_form(
        _form(
            "token",
            scores={"visual_clarity": "11", "camera_angle": "7"},
            explanations={"camera_angle": "The view is mostly level."},
        )
    )
    assert any("must be from 1 to 10" in error for error in errors)
    assert any("needs an explanation" in error for error in errors)

    _values, errors = validate_quality_form(
        _form(
            "token",
            explanations={"visual_clarity": "An explanation without a score."},
        )
    )
    assert any("needs a score" in error for error in errors)


def test_quality_route_saves_partial_draft_without_a_misleading_score(app, session):
    exercise = _create_exercise(session)
    client = app.test_client()
    detail_url = f"/video-quality/{exercise.id}"
    page = client.get(detail_url)
    assert page.status_code == 200
    assert b"0 of 5 ratings complete" in page.data

    empty = client.post(detail_url, data=_form(_token(page)))
    assert empty.status_code == 400
    assert b"Enter at least one rating and explanation" in empty.data
    assert session.query(QualityAssessment).count() == 0

    saved = client.post(
        detail_url,
        data=_form(
            _token(empty),
            scores={"visual_clarity": "7"},
            explanations={"visual_clarity": "The subject is usually clear."},
        ),
    )
    assert saved.status_code == 302
    assessment = session.query(QualityAssessment).one()
    assert len(assessment.ratings) == 1
    assert assessment.overall_score is None

    dashboard = get_dashboard_data()
    quality_status = next(
        section for section in dashboard["sections"] if section["key"] == "quality"
    )
    assert quality_status["status"] == "in_progress"

    page = client.get(detail_url)
    assert b"1 of 5 ratings complete" in page.data
    assert b"7 / 10" in page.data
    assert b"OVERALL SCORE" in page.data


def test_overall_score_requires_five_ratings_and_recalculates_on_edit(app, session):
    exercise = _create_exercise(session)
    client = app.test_client()
    detail_url = f"/video-quality/{exercise.id}"

    scores = dict(
        zip(QUALITY_CATEGORIES, (7, 8, 6, 9, 8), strict=True)
    )
    explanations = {
        category: f"Evidence supporting the {category} rating."
        for category in QUALITY_CATEGORIES
    }
    page = client.get(detail_url)
    response = client.post(
        detail_url, data=_form(_token(page), scores, explanations)
    )
    assert response.status_code == 302

    assessment = session.query(QualityAssessment).one()
    assert len(assessment.ratings) == 5
    assert assessment.overall_score == 7.6

    page = client.get(detail_url)
    response = client.post(
        detail_url,
        data=_form(
            _token(page),
            {**scores, "visual_clarity": 9},
            explanations,
        ),
    )
    assert response.status_code == 302
    session.expire_all()
    assessment = session.query(QualityAssessment).one()
    assert assessment.overall_score == 8
    page = client.get(detail_url)
    assert b"8.0 / 10" in page.data


def test_clearing_a_rating_keeps_the_assessment_incomplete(app, session):
    exercise = _create_exercise(session)
    client = app.test_client()
    detail_url = f"/video-quality/{exercise.id}"
    scores = {category: 5 for category in QUALITY_CATEGORIES}
    explanations = {category: f"Reason for {category}." for category in QUALITY_CATEGORIES}

    page = client.get(detail_url)
    client.post(detail_url, data=_form(_token(page), scores, explanations))
    page = client.get(detail_url)

    response = client.post(
        detail_url,
        data=_form(
            _token(page),
            {"visual_clarity": 5},
            {"visual_clarity": "Only this category remains."},
        ),
    )

    assert response.status_code == 302
    session.expire_all()
    assessment = session.query(QualityAssessment).one()
    assert [rating.category for rating in assessment.ratings] == ["visual_clarity"]
    assert assessment.overall_score is None


def test_quality_post_requires_csrf_token_and_rejects_fractional_score(app, session):
    exercise = _create_exercise(session)
    client = app.test_client()
    detail_url = f"/video-quality/{exercise.id}"
    page = client.get(detail_url)

    response = client.post(
        detail_url,
        data=_form(
            "",
            scores={"visual_clarity": "7.5"},
            explanations={"visual_clarity": "The clip is clear enough."},
        ),
    )
    assert response.status_code == 400
    assert session.query(QualityAssessment).count() == 0

    response = client.post(
        detail_url,
        data=_form(
            _token(page),
            scores={"visual_clarity": "7.5"},
            explanations={"visual_clarity": "The clip is clear enough."},
        ),
    )
    assert response.status_code == 400
    assert b"score must be a whole number" in response.data
    assert session.query(QualityAssessment).count() == 0
