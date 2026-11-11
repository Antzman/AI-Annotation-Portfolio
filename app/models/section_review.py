from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

SECTION_KEYS = ("object_action", "movement", "quality", "attention_to_detail")


class SectionReview(db.Model):
    __tablename__ = "section_reviews"
    __table_args__ = (
        UniqueConstraint("exercise_id", "section_key", name="uq_section_review_exercise"),
        CheckConstraint(
            "section_key IN ('object_action', 'movement', 'quality', 'attention_to_detail')",
            name="ck_section_review_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_key: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    exercise: Mapped["Exercise"] = relationship(back_populates="section_reviews")

    def mark_reviewed(self):
        self.reviewed_at = datetime.now(UTC)


from app.models.exercise import Exercise
