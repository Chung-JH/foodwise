from app import create_app
from lib import database, llm
from lib.llm import LLMError


def save_default_user(**overrides):
    payload = {
        "user_id": "default_user",
        "name": "自己",
        "taste_description": "喜欢微辣",
        "taste_tags": ["微辣"],
        "avoid_ingredients": ["香菜"],
        "health_goals": ["高蛋白"],
        "default_budget": {"lunch": [15, 25], "dinner": [15, 25]},
        "remark_habits": ["少油"],
    }
    payload.update(overrides)
    return database.save_user(payload)


def test_recommend_no_history_returns_top_three_and_record(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()
    save_default_user()

    response = client.post(
        "/api/recommend",
        json={"budget_range": [15, 25], "user_type": "self", "contact_id": None},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert len(data["recommendations"]) >= 3
    assert data["remark"].endswith("谢谢。")
    assert data["recent_analysis"]["meal_count"] == 0
    assert data["record"]["rec_id"]
    assert database.get_recommendations("default_user")[0]["rec_id"] == data["record"]["rec_id"]


def test_recommend_filters_avoid_ingredients_and_budget(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()
    save_default_user(avoid_ingredients=["香菜", "葱"])

    response = client.post("/api/recommend", json={"budget_range": [15, 25]})

    assert response.status_code == 200
    data = response.get_json()
    for item in data["recommendations"]:
        dish = database.get_dish_by_name(item["name"])
        if item.get("course_type") == "主食":
            assert 15 <= item["price"] <= 25
        assert "香菜" not in dish["ingredients"]
        assert "葱" not in dish["ingredients"]


def test_recommend_falls_back_to_rule_when_llm_unavailable(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "false")

    def fail_llm(*args, **kwargs):
        raise LLMError("LLM 不可用")

    monkeypatch.setattr(llm, "generate_recommendation", fail_llm)

    app = create_app()
    client = app.test_client()
    save_default_user()

    response = client.post("/api/recommend", json={"budget_range": [15, 25]})

    assert response.status_code == 200
    data = response.get_json()
    assert data["mode"] == "rule_fallback"
    assert len(data["recommendations"]) >= 3
    assert all("规则预筛选" in item["reason"] for item in data["recommendations"])


def test_contact_profile_changes_rule_recommendations(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setattr(llm, "generate_recommendation", lambda *args, **kwargs: (_ for _ in ()).throw(LLMError("off")))

    app = create_app()
    client = app.test_client()
    save_default_user(taste_tags=["微辣"], health_goals=[])
    contact = database.add_contact(
        {
            "owner_user_id": "default_user",
            "name": "妈妈",
            "taste_description": "清淡",
            "taste_tags": ["清淡"],
            "avoid_ingredients": [],
            "health_goals": ["少油"],
            "default_budget": {"lunch": [15, 25]},
            "remark_habits": ["少盐"],
        }
    )

    self_response = client.post(
        "/api/recommend",
        json={"budget_range": [15, 25], "user_type": "self"},
    )
    contact_response = client.post(
        "/api/recommend",
        json={
            "budget_range": [15, 25],
            "user_type": "contact",
            "contact_id": contact["contact_id"],
        },
    )

    self_names = [item["name"] for item in self_response.get_json()["recommendations"]]
    contact_names = [item["name"] for item in contact_response.get_json()["recommendations"]]
    assert self_response.status_code == 200
    assert contact_response.status_code == 200
    assert self_response.get_json()["target"]["user_id"] == "default_user"
    assert contact_response.get_json()["target"]["user_id"] == contact["contact_id"]
    assert self_names != contact_names


def test_recommend_records_endpoint_returns_history(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()
    save_default_user()
    client.post("/api/recommend", json={"budget_range": [15, 25]})

    response = client.get("/api/recommend/records")

    assert response.status_code == 200
    assert response.get_json()["records"][0]["recommendations"]


def test_confirm_recommendation_saves_order_history(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()
    save_default_user()
    recommend_response = client.post("/api/recommend", json={"budget_range": [15, 25]})
    item = recommend_response.get_json()["recommendations"][0]

    response = client.post(
        "/api/recommend/confirm",
        json={
            "recommendation": item,
            "remark": "少油，不要香菜，谢谢。",
            "budget_range": [15, 25],
            "user_type": "self",
        },
    )

    assert response.status_code == 200
    meal = response.get_json()["meal"]
    assert meal["input_type"] == "recommendation"
    assert meal["remark_used"] == "少油，不要香菜，谢谢。"
    assert meal["time_assumption"]["resolved_occurred_at"] == meal["occurred_at"]
    assert database.get_meals("default_user")[0]["meal_id"] == meal["meal_id"]


def test_contacts_endpoint_returns_contacts_for_dropdown(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))

    app = create_app()
    client = app.test_client()
    contact = database.add_contact(
        {
            "owner_user_id": "default_user",
            "name": "妈妈",
            "taste_description": "清淡",
            "taste_tags": ["清淡"],
            "avoid_ingredients": [],
            "health_goals": [],
            "default_budget": {"lunch": [15, 25]},
            "remark_habits": ["少盐"],
        }
    )

    response = client.get("/api/contacts")

    assert response.status_code == 200
    assert response.get_json()["contacts"][0]["contact_id"] == contact["contact_id"]
