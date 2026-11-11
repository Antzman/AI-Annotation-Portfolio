import sqlite3

from sqlalchemy import text

from app import create_app
from app.extensions import db


def test_legacy_global_review_table_is_preserved_during_migration(tmp_path):
    database_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(database_path)
    connection.execute(
        "CREATE TABLE section_reviews ("
        "id INTEGER PRIMARY KEY, "
        "section_key VARCHAR(32) NOT NULL UNIQUE, "
        "reviewed_at DATETIME)"
    )
    connection.execute(
        "INSERT INTO section_reviews (section_key, reviewed_at) "
        "VALUES ('attention_to_detail', '2026-01-01 00:00:00')"
    )
    connection.commit()
    connection.close()

    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
        }
    )

    with app.app_context():
        inspector = db.inspect(db.engine)
        assert "exercise_id" in {
            column["name"] for column in inspector.get_columns("section_reviews")
        }
        assert inspector.has_table("legacy_section_reviews")
        result = db.session.execute(
            text("SELECT section_key FROM legacy_section_reviews")
        ).scalar_one()
        assert result == "attention_to_detail"

        assert db.session.execute(
            text("SELECT COUNT(*) FROM section_reviews")
        ).scalar_one() == 0
