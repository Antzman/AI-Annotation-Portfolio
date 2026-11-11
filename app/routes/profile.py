from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import UserProfile
from app.services.profile_validation import PROFILE_FIELDS, validate_profile_form
from app.services.web import database_failure

bp = Blueprint("profile", __name__, url_prefix="/about")


def _empty_values():
    return {field: "" for field in PROFILE_FIELDS}


@bp.route("", methods=["GET", "POST"])
def index():
    profile = db.session.execute(
        select(UserProfile).order_by(UserProfile.id).limit(1)
    ).scalar_one_or_none()
    values = (
        {field: getattr(profile, field) or "" for field in PROFILE_FIELDS}
        if profile
        else _empty_values()
    )
    errors = []

    if request.method == "POST":
        values, errors = validate_profile_form(request.form)
        if not errors:
            if not any(values.values()):
                if profile is not None:
                    db.session.delete(profile)
                try:
                    db.session.commit()
                except SQLAlchemyError:
                    return database_failure(
                        "clearing the profile",
                        "The profile could not be cleared. Check the local application "
                        "log and try again.",
                        url_for("profile.index"),
                        "about",
                    )
                flash("Profile details cleared.", "success")
                return redirect(url_for("profile.index"))

            if profile is None:
                profile = UserProfile(id=1)
                db.session.add(profile)
            for field, value in values.items():
                setattr(profile, field, value or None)
            try:
                db.session.commit()
            except SQLAlchemyError:
                return database_failure(
                    "saving the profile",
                    "Profile details could not be saved. Check the local application "
                    "log and try again.",
                    url_for("profile.index"),
                    "about",
                )
            flash("Profile saved.", "success")
            return redirect(url_for("profile.index"))

    return (
        render_template(
            "sections/profile/index.html",
            active_nav="about",
            profile=profile,
            values=values,
            errors=errors,
        ),
        400 if errors else 200,
    )
