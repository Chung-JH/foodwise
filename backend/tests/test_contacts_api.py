from app import create_app
from lib import database


def test_contacts_crud_api_round_trip(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()

    create_response = client.post(
        "/api/contacts",
        json={
            "name": "妈妈",
            "taste_description": "清淡，少盐，不吃辣",
            "avoid_ingredients": "辣椒，香菜",
            "health_goals": ["少油"],
            "default_budget": {"lunch": [20, 35], "dinner": {"min": 22, "max": 40}},
            "remark_habits": "少盐,少油",
        },
    )
    assert create_response.status_code == 201
    created = create_response.get_json()
    assert created["contact_id"]
    assert created["owner_user_id"] == "default_user"
    assert created["avoid_ingredients"] == ["辣椒", "香菜"]
    assert "川菜" in created["taste_tags"]

    list_response = client.get("/api/contacts")
    assert list_response.status_code == 200
    assert list_response.get_json()["contacts"][0]["contact_id"] == created["contact_id"]

    update_response = client.put(
        f"/api/contacts/{created['contact_id']}",
        json={
            "name": "妈妈",
            "taste_description": "喜欢汤类，口味清淡",
            "avoid_ingredients": ["葱"],
            "health_goals": ["少盐"],
            "default_budget": {"lunch": [18, 30]},
            "remark_habits": ["不要葱"],
        },
    )
    assert update_response.status_code == 200
    updated = update_response.get_json()
    assert updated["avoid_ingredients"] == ["葱"]
    assert updated["default_budget"]["lunch"] == [18, 30]
    assert database.get_contact(created["contact_id"])["remark_habits"] == ["不要葱"]

    delete_response = client.delete(f"/api/contacts/{created['contact_id']}")
    assert delete_response.status_code == 200
    assert delete_response.get_json()["deleted"] is True
    assert database.get_contacts("default_user") == []


def test_contact_api_validates_required_name(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))

    app = create_app()
    client = app.test_client()

    response = client.post("/api/contacts", json={"taste_description": "清淡"})

    assert response.status_code == 400
    assert "亲友姓名不能为空" in response.get_json()["error"]


def test_contact_api_returns_404_for_missing_contact(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))

    app = create_app()
    client = app.test_client()

    update_response = client.put("/api/contacts/not-found", json={"name": "不存在"})
    delete_response = client.delete("/api/contacts/not-found")

    assert update_response.status_code == 404
    assert delete_response.status_code == 404
