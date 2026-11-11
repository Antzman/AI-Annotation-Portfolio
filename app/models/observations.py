from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin


class ObjectActionObservation(TimestampMixin, db.Model):
    __tablename__ = "object_action_observations"
    __table_args__ = (
        CheckConstraint("length(trim(timestamp)) > 0", name="ck_object_action_timestamp"),
        CheckConstraint(
            "length(trim(identified_object)) > 0", name="ck_object_action_object"
        ),
        CheckConstraint(
            "length(trim(observed_action)) > 0", name="ck_object_action_action"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[str] = mapped_column(String(80), nullable=False)
    identified_object: Mapped[str] = mapped_column(String(160), nullable=False)
    observed_action: Mapped[str] = mapped_column(Text, nullable=False)
    additional_observations: Mapped[str | None] = mapped_column(Text)

    exercise: Mapped["Exercise"] = relationship(
        back_populates="object_action_observations"
    )


class MovementObservation(TimestampMixin, db.Model):
    __tablename__ = "movement_observations"
    __table_args__ = (
        CheckConstraint("length(trim(timestamp)) > 0", name="ck_movement_timestamp"),
        CheckConstraint(
            "length(trim(movement_description)) > 0",
            name="ck_movement_description",
        ),
        CheckConstraint(
            "visibility IN ('clearly_visible', 'partially_visible', 'obstructed', 'unclear')",
            name="ck_movement_visibility",
        ),
        CheckConstraint(
            "plausibility IN ('plausible', 'uncertain', 'implausible')",
            name="ck_movement_plausibility",
        ),
        CheckConstraint("length(trim(reasoning)) > 0", name="ck_movement_reasoning"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[str] = mapped_column(String(80), nullable=False)
    movement_description: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False)
    plausibility: Mapped[str] = mapped_column(String(16), nullable=False)
    inconsistencies: Mapped[str | None] = mapped_column(Text)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    exercise: Mapped["Exercise"] = relationship(back_populates="movement_observations")
