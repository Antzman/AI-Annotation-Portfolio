from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin


class Exercise(TimestampMixin, db.Model):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_exercise_title_nonempty"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    clip_reference: Mapped[str | None] = mapped_column(String(300))

    object_action_observations: Mapped[list["ObjectActionObservation"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan", passive_deletes=True
    )
    movement_observations: Mapped[list["MovementObservation"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan", passive_deletes=True
    )
    quality_assessment: Mapped["QualityAssessment | None"] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    quality_issues: Mapped[list["QualityIssue"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan", passive_deletes=True
    )
    section_reviews: Mapped[list["SectionReview"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan", passive_deletes=True
    )
