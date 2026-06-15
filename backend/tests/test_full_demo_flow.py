from app import create_app
from lib import database, llm
from lib.llm import LLMError


def _meal_payload(name, occurred_at, category, tags, nutrition, price):
    return {
        "user_id": "default_user",
        "user_type": "self",
        "occurred_at": occurred_at,
        "meal_type": "lunch" if "12:30" in occurred_at else "dinner",
        "raw_input": f"联调预置：{name}",
        "input_type": "text",
        "time_resolution": "explicit",
        "time_assumption": {
            "raw_time_text": "联调预置时间",
            "resolved_occurred_at": occurred_at,
            "timezone": "Asia/Shanghai",
            "date_source": "测试固定日期",
            "time_source": "测试固定餐次时间",
            "default_rule": "早餐=08:00，午餐=12:30，晚餐=19:30",
            "confidence": 1.0,
        },
        "recognized_foods": [
            {
                "raw_text": name,
                "standard_name": name,
                "category": category,
                "portion": "一份",
                "estimated_nutrition": nutrition,
                "levels": {
                    "calorie_level": "high",
                    "protein_level": "medium",
                    "fat_level": "high",
                    "carbs_level": "medium",
                    "sodium_level": "high",
                    "vegetable_level": "low",
                },
                "nutrition_tags": tags,
                "confidence": 0.9,
                "assumption": "联调测试预置",
            }
        ],
        "dish_ids": [],
        "total_price": price,
        "total_nutrition": nutrition,
        "remark_used": None,
        "budget_range_used": None,
    }


def test_mock_demo_success_path_profile_log_history_recommend_and_remark(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()

    profile_response = client.post(
        "/api/profile",
        json={
            "name": "自己",
            "taste_description": "喜欢微辣，午餐想吃少油高蛋白",
            "avoid_ingredients": ["香菜", "葱"],
            "health_goals": ["少油", "高蛋白"],
            "default_budget": {
                "breakfast": [8, 15],
                "lunch": [15, 30],
                "dinner": [15, 30],
            },
            "remark_habits": ["少油"],
        },
    )
    assert profile_response.status_code == 200
    profile = profile_response.get_json()
    assert profile["avoid_ingredients"] == ["香菜", "葱"]
    assert "微辣" in profile["taste_tags"]

    database.add_meal(
        _meal_payload(
            "黄焖鸡米饭",
            "2026-06-13T12:30:00+08:00",
            "盖饭类",
            ["热量偏高", "油脂偏高"],
            {"calories_kcal": 780, "protein_g": 32, "fat_g": 36, "carbs_g": 88},
            22,
        )
    )
    database.add_meal(
        _meal_payload(
            "麻辣烫",
            "2026-06-14T12:30:00+08:00",
            "麻辣类",
            ["钠偏高", "油脂偏高"],
            {"calories_kcal": 820, "protein_g": 28, "fat_g": 42, "carbs_g": 86},
            24,
        )
    )

    log_response = client.post(
        "/api/log-meal", json={"text": "昨天晚上吃了炸鸡汉堡套餐和可乐"}
    )
    assert log_response.status_code == 200
    logged_meal = log_response.get_json()["meal"]
    assert logged_meal["time_assumption"]["resolved_occurred_at"] == logged_meal["occurred_at"]
    assert logged_meal["time_resolution"] == "inferred"
    assert logged_meal["recognized_foods"][0]["standard_name"] == "炸鸡汉堡套餐"

    meals_response = client.get("/api/meals")
    assert meals_response.status_code == 200
    meals = meals_response.get_json()["meals"]
    occurred_times = [meal["occurred_at"] for meal in meals]
    assert occurred_times == sorted(occurred_times, reverse=True)
    assert len(meals) == 3

    recommend_response = client.post(
        "/api/recommend",
        json={"budget_range": [15, 25], "user_type": "self"},
    )
    assert recommend_response.status_code == 200
    result = recommend_response.get_json()
    assert result["mode"] == "llm"
    assert len(result["recommendations"]) >= 3
    assert result["recent_analysis"]["meal_count"] == 3
    assert "少油" in result["remark"]
    assert "不要香菜" in result["remark"]
    assert "不要葱" in result["remark"]
    assert result["remark"].endswith("谢谢。")

    for item in result["recommendations"]:
        if item.get("course_type") == "主食":
            assert 15 <= item["price"] <= 25
        dish = database.get_dish_by_name(item["name"])
        assert dish is not None
        assert "香菜" not in dish["ingredients"]
        assert "葱" not in dish["ingredients"]

    confirm_response = client.post(
        "/api/recommend/confirm",
        json={
            "recommendation": result["recommendations"][0],
            "remark": result["remark"],
            "budget_range": [15, 25],
            "user_type": "self",
        },
    )
    assert confirm_response.status_code == 200
    confirmed_meal = confirm_response.get_json()["meal"]
    assert confirmed_meal["remark_used"] == result["remark"]
    assert confirmed_meal["time_assumption"]["resolved_occurred_at"] == confirmed_meal["occurred_at"]


def test_real_api_mode_degrades_to_rule_fallback_and_contact_recommendation_differs(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "false")

    def fail_llm(*args, **kwargs):
        raise LLMError("测试环境不调用真实外部 API")

    monkeypatch.setattr(llm, "generate_recommendation", fail_llm)

    app = create_app()
    client = app.test_client()
    database.save_user(
        {
            "user_id": "default_user",
            "name": "自己",
            "taste_description": "微辣",
            "taste_tags": ["微辣"],
            "avoid_ingredients": ["香菜", "葱"],
            "health_goals": ["高蛋白"],
            "default_budget": {"lunch": [15, 25]},
            "remark_habits": ["少油"],
        }
    )
    contact = database.add_contact(
        {
            "owner_user_id": "default_user",
            "name": "妈妈",
            "taste_description": "清淡，喜欢汤类",
            "taste_tags": ["清淡", "汤类"],
            "avoid_ingredients": ["辣椒"],
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

    assert self_response.status_code == 200
    assert contact_response.status_code == 200
    self_data = self_response.get_json()
    contact_data = contact_response.get_json()
    assert self_data["mode"] == "rule_fallback"
    assert contact_data["mode"] == "rule_fallback"
    assert self_data["target"]["user_type"] == "self"
    assert contact_data["target"]["user_type"] == "contact"
    assert [item["name"] for item in self_data["recommendations"]] != [
        item["name"] for item in contact_data["recommendations"]
    ]
