from flask import current_app, render_template

from app.extensions import db


def database_failure(action, message, back_url, active_nav):
    db.session.rollback()
    current_app.logger.exception("Database error while %s.", action)
    return (
        render_template(
            "errors/database.html",
            active_nav=active_nav,
            message=message,
            back_url=back_url,
        ),
        500,
    )
