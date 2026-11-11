import sqlite3
import hmac
import secrets
from pathlib import Path

from flask import Flask, abort, request, session
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.config import Config
from app.extensions import db
from app.services.schema import (
    migrate_legacy_section_reviews,
    migrate_quality_issue_timestamps,
)
from app.services.profile_defaults import ensure_default_profile


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(connection, _connection_record):
    if isinstance(connection, sqlite3.Connection):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    @app.context_processor
    def provide_csrf_token():
        def csrf_token():
            token = session.get("_csrf_token")
            if token is None:
                token = secrets.token_urlsafe(32)
                session["_csrf_token"] = token
            return token

        return {"csrf_token": csrf_token}

    @app.before_request
    def validate_csrf_token():
        if request.method == "POST":
            expected = session.get("_csrf_token")
            supplied = request.form.get("_csrf_token", "")
            if not expected or not supplied or not hmac.compare_digest(
                expected, supplied
            ):
                abort(400, description="The form token is missing or expired.")

    from app import models  # noqa: F401

    with app.app_context():
        migrate_legacy_section_reviews(db.engine)
        db.create_all()
        migrate_quality_issue_timestamps(db.engine)
        ensure_default_profile()

    from app.routes import dashboard
    from app.routes import attention
    from app.routes import movement
    from app.routes import object_action
    from app.routes import profile
    from app.routes import quality
    from app.routes import report

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(attention.bp)
    app.register_blueprint(movement.bp)
    app.register_blueprint(object_action.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(quality.bp)
    app.register_blueprint(report.bp)

    return app
