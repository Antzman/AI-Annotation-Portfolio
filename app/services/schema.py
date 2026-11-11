from sqlalchemy import inspect, text


def migrate_legacy_section_reviews(engine):
    inspector = inspect(engine)
    if "section_reviews" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("section_reviews")}
    if "exercise_id" in columns:
        return

    if "legacy_section_reviews" in inspector.get_table_names():
        raise RuntimeError(
            "Cannot migrate section reviews: legacy_section_reviews already exists."
        )

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE section_reviews RENAME TO legacy_section_reviews")
        )


def migrate_quality_issue_timestamps(engine):
    inspector = inspect(engine)
    if "quality_issues" not in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TRIGGER IF NOT EXISTS "
                "trg_quality_issue_timestamp_insert "
                "BEFORE INSERT ON quality_issues "
                "WHEN NEW.timestamp IS NULL OR length(trim(NEW.timestamp)) = 0 "
                "BEGIN SELECT RAISE(ABORT, 'quality issue timestamp is required'); END"
            )
        )
        connection.execute(
            text(
                "CREATE TRIGGER IF NOT EXISTS "
                "trg_quality_issue_timestamp_update "
                "BEFORE UPDATE OF timestamp ON quality_issues "
                "WHEN NEW.timestamp IS NULL OR length(trim(NEW.timestamp)) = 0 "
                "BEGIN SELECT RAISE(ABORT, 'quality issue timestamp is required'); END"
            )
        )
