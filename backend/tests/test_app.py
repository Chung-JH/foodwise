from pathlib import Path

from app import create_app


def test_health_check_returns_ok(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))

    app = create_app()
    client = app.test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert db_path.exists()


def test_database_initializes_required_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))

    create_app()

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {row[0] for row in rows}
    assert {
        "users",
        "contacts",
        "dishes",
        "order_history",
        "recommendation_records",
        "notes_templates",
    }.issubset(table_names)
