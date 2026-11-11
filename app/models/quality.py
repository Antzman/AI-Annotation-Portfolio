from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin

QUALITY_CATEGORIES = (
    "visual_clarity",
    "camera_angle",
    "object_visibility",
    "movement_visibility",
    "overall_footage_quality",
)
ISSUE_CATEGORIES = (
    "missing_objects",
    "unexpected_object_movement",
    "unclear_actions",
    "visual_obstruction",
    "inconsistent_frames",
    "other",
)
ISSUE_SEVERITIES = ("low", "medium", "high")


class QualityAssessment(TimestampMixin, db.Model):
    __tablename__ = "quality_assessments"
    __table_args__ = (
        UniqueConstraint("exercise_id", name="uq_quality_assessment_exercise"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )

    exercise: Mapped["Exercise"] = relationship(back_populates="quality_assessment")
    ratings: Mapped[list["QualityRating"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def overall_score(self):
        if len(self.ratings) != len(QUALITY_CATEGORIES):
            return None
        if {rating.category for rating in self.ratings} != set(QUALITY_CATEGORIES):
            return None
        return sum(rating.score for rating in self.ratings) / len(QUALITY_CATEGORIES)


class QualityRating(db.Model):
    __tablename__ = "quality_ratings"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id", "category", name="uq_quality_rating_category"
        ),
        CheckConstraint(
            "category IN ('visual_clarity', 'camera_angle', 'object_visibility', "
            "'movement_visibility', 'overall_footage_quality')",
            name="ck_quality_rating_category",
        ),
        CheckConstraint("score BETWEEN 1 AND 10", name="ck_quality_rating_score"),
        CheckConstraint(
            "length(trim(explanation)) > 0", name="ck_quality_rating_explanation"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("quality_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    assessment: Mapped["QualityAssessment"] = relationship(back_populates="ratings")


class QualityIssue(TimestampMixin, db.Model):
    __tablename__ = "quality_issues"
    __table_args__ = (
        CheckConstraint(
            "timestamp IS NOT NULL AND length(trim(timestamp)) > 0",
            name="ck_quality_issue_timestamp",
        ),
        CheckConstraint(
            "category IN ('missing_objects', 'unexpected_object_movement', "
            "'unclear_actions', 'visual_obstruction', 'inconsistent_frames', 'other')",
            name="ck_quality_issue_category",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high')", name="ck_quality_issue_severity"
        ),
        CheckConstraint(
            "length(trim(description)) > 0", name="ck_quality_issue_description"
        ),
        CheckConstraint(
            "length(trim(explanation)) > 0", name="ck_quality_issue_explanation"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_correction: Mapped[str | None] = mapped_column(Text)

    exercise: Mapped["Exercise"] = relationship(back_populates="quality_issues")
