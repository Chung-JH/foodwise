from app import create_app
from lib import database


def test_get_profile_returns_default_profile(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()

    response = client.get("/api/profile")

    assert response.status_code == 200
    profile = response.get_json()
    assert profile["user_id"] == "default_user"
    assert profile["taste_tags"] == []
    assert profile["default_budget"]["breakfast"] == [8, 15]


def test_post_profile_parses_taste_tags_and_persists(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()

    payload = {
        "name": "小明",
        "taste_description": "喜欢川菜但不能太辣，偏爱汤类",
        "avoid_ingredients": "香菜，葱",
        "health_goals": ["少油", "高蛋白"],
        "default_budget": {
            "breakfast": {"min": 9, "max": 16},
            "lunch": [18, 32],
            "dinner": {"min": 24, "max": 45},
        },
        "remark_habits": "少油,不要香菜,米饭少一点",
    }

    post_response = client.post("/api/profile", json=payload)
    get_response = client.get("/api/profile")

    assert post_response.status_code == 200
    saved = post_response.get_json()
    loaded = get_response.get_json()
    stored = database.get_user("default_user")

    assert saved == loaded
    assert loaded == stored
    assert loaded["name"] == "小明"
    assert loaded["taste_description"] == payload["taste_description"]
    assert "川菜" in loaded["taste_tags"]
    assert "微辣" in loaded["taste_tags"]
    assert loaded["avoid_ingredients"] == ["香菜", "葱"]
    assert loaded["default_budget"]["lunch"] == [18, 32]
    assert loaded["remark_habits"] == ["少油", "不要香菜", "米饭少一点"]
    assert loaded["created_at"]
    assert loaded["updated_at"]
