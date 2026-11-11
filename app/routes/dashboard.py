from flask import Blueprint, abort, render_template

from app.services.dashboard import get_dashboard_data

bp = Blueprint("dashboard", __name__)

PLACEHOLDERS = {
}


@bp.get("/")
def index():
    return render_template(
        "dashboard/index.html",
        active_nav="dashboard",
        dashboard=get_dashboard_data(),
    )


@bp.get("/<section_key>")
def placeholder(section_key):
    if section_key not in PLACEHOLDERS:
        abort(404)
    title, description, phase = PLACEHOLDERS[section_key]
    return render_template(
        "sections/placeholder.html",
        active_nav=section_key,
        title=title,
        description=description,
        phase=phase,
    )
