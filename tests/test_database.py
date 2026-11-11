import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
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


def test_app_factory_creates_database_and_instance_folder(app):
    assert app.instance_path
    with app.app_context():
        assert db.inspect(db.engine).has_table("exercises")
        assert db.inspect(db.engine).has_table("quality_ratings")


def test_profile_is_limited_to_singleton_row(session):
    session.add(UserProfile(name="Portfolio owner"))
    session.commit()

    session.add(UserProfile(id=2, name="Second profile"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_exercise_requires_nonblank_title(session):
    session.add(Exercise(title="   "))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_observations_and_issues_are_removed_with_exercise(session):
    exercise = Exercise(title="Walking clip")
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
            reasoning="The motion is consistent across the clip.",
        )
    )
    exercise.quality_issues.append(
        QualityIssue(
            timestamp="00:01",
            category="visual_obstruction",
            description="Brief partial obstruction",
            severity="low",
            explanation="A foreground object briefly covers the subject.",
        )
    )
    session.add(exercise)
    session.commit()
    exercise_id = exercise.id

    session.delete(exercise)
    session.commit()

    assert db.session.get(Exercise, exercise_id) is None
    assert db.session.query(ObjectActionObservation).count() == 0
    assert db.session.query(MovementObservation).count() == 0
    assert db.session.query(QualityIssue).count() == 0


def test_movement_controlled_values_are_constrained(session):
    exercise = Exercise(title="Walking clip")
    exercise.movement_observations.append(
        MovementObservation(
            timestamp="00:01",
            movement_description="Steps forward",
            visibility="mostly_visible",
            plausibility="plausible",
            reasoning="The step appears consistent.",
        )
    )
    session.add(exercise)

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_quality_rating_bounds_uniqueness_and_complete_score(session):
    exercise = Exercise(title="Quality clip")
    assessment = QualityAssessment()
    assessment.ratings = [
        QualityRating(
            category=category,
            score=8,
            explanation=f"Reason for {category}.",
        )
        for category in QUALITY_CATEGORIES
    ]
    exercise.quality_assessment = assessment
    session.add(exercise)
    session.commit()

    assert assessment.overall_score == 8

    session.add(
        QualityRating(
            assessment=assessment,
            category="visual_clarity",
            score=9,
            explanation="Duplicate category.",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_quality_assessment_score_is_none_until_all_categories_exist(session):
    exercise = Exercise(title="Incomplete assessment")
    assessment = QualityAssessment(
        ratings=[
            QualityRating(
                category="visual_clarity",
                score=7,
                explanation="The subject is generally clear.",
            )
        ]
    )
    exercise.quality_assessment = assessment
    session.add(exercise)
    session.commit()

    assert assessment.overall_score is None


def test_quality_rating_rejects_out_of_range_score(session):
    exercise = Exercise(title="Rating validation")
    assessment = QualityAssessment(
        ratings=[
            QualityRating(
                category="visual_clarity",
                score=11,
                explanation="Out of range.",
            )
        ]
    )
    exercise.quality_assessment = assessment
    session.add(exercise)

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_section_review_rejects_unknown_section_key(session):
    session.add(SectionReview(section_key="unknown_section"))

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
