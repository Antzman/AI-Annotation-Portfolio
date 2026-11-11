from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import TimestampMixin


class UserProfile(TimestampMixin, db.Model):
    __tablename__ = "user_profiles"
    __table_args__ = (CheckConstraint("id = 1", name="ck_user_profile_singleton"),)

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    name: Mapped[str | None] = mapped_column(String(120))
    introduction: Mapped[str | None] = mapped_column(Text)
    experience: Mapped[str | None] = mapped_column(Text)
    technical_interests: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[str | None] = mapped_column(Text)
    contact_information: Mapped[str | None] = mapped_column(Text)
