import sqlite3

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.services.schema import (
    migrate_exercise_finalization,
    migrate_quality_issue_timestamps,
)


def test_legacy_quality_issues_reject_missing_timestamps_after_migration(tmp_path):
    database_path = tmp_path / "legacy-quality.db"
    connection = sqlite3.connect(database_path)
    connection.execute(
        "CREATE TABLE quality_issues (id INTEGER PRIMARY KEY, timestamp VARCHAR(80))"
    )
    connection.commit()
    connection.close()

    engine = create_engine(f"sqlite:///{database_path}")
    migrate_quality_issue_timestamps(engine)

    with engine.begin() as connection:
        with pytest.raises(IntegrityError, match="quality issue timestamp is required"):
            connection.execute(
                text("INSERT INTO quality_issues (timestamp) VALUES (NULL)")
            )
        with pytest.raises(IntegrityError, match="quality issue timestamp is required"):
            connection.execute(
                text("INSERT INTO quality_issues (timestamp) VALUES ('  ')")
            )

    engine.dispose()


def test_exercise_finalization_migration_preserves_existing_assessments(tmp_path):
    database_path = tmp_path / "legacy-exercises.db"
    connection = sqlite3.connect(database_path)
    connection.execute(
        "CREATE TABLE exercises (id INTEGER PRIMARY KEY, title TEXT NOT NULL)"
    )
    connection.execute(
        "INSERT INTO exercises (id, title) VALUES (7, 'Dog assessment')"
    )
    connection.commit()
    connection.close()

    engine = create_engine(f"sqlite:///{database_path}")
    migrate_exercise_finalization(engine)
    migrate_exercise_finalization(engine)

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(exercises)")
        }
        assert "finalized_at" in columns
        assert connection.execute(
            text("SELECT id, title, finalized_at FROM exercises WHERE id = 7")
        ).one() == (7, "Dog assessment", None)
    engine.dispose()
