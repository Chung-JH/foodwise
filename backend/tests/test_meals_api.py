from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import create_app
from lib import database


TZ = ZoneInfo("Asia/Shanghai")


def iso_days_ago(days, hour=12):
    value = datetime.now(TZ) - timedelta(days=days)
    return value.replace(hour=hour, minute=30, second=0, microsecond=0).isoformat()


def add_history_meal(meal_id, occurred_at, category="快餐油炸类", price=25):
    return database.add_meal(
        {
            "meal_id": meal_id,
            "user_id": "default_user",
            "user_type": "self",
            "occurred_at": occurred_at,
            "meal_type": "lunch",
            "raw_input": f"{meal_id} 测试记录",
            "input_type": "text",
            "time_resolution": "explicit",
            "time_assumption": {
                "raw_time_text": "测试时间",
                "resolved_occurred_at": occurred_at,
                "timezone": "Asia/Shanghai",
                "date_source": "测试",
                "time_source": "测试",
                "default_rule": "测试",
                "confidence": 1.0,
            },
            "recognized_foods": [
                {
                    "standard_name": meal_id,
                    "category": category,
                    "nutrition_tags": ["高热量", "高脂肪", "蔬菜偏少"],
                    "levels": {
                        "calorie_level": "high",
                        "fat_level": "high",
                        "vegetable_level": "low",
                        "protein_level": "medium",
                    },
                }
            ],
            "dish_ids": [f"dish-{meal_id}"],
            "total_price": price,
            "total_nutrition": {
                "calories_kcal": 900,
                "protein_g": 25,
                "fat_g": 35,
                "carbs_g": 95,
                "sodium_mg": 1100,
            },
        }
    )


def test_get_meals_returns_descending_and_supports_days_filter(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))

    app = create_app()
    client = app.test_client()
    add_history_meal("old", iso_days_ago(10))
    add_history_meal("new", iso_days_ago(1))

    all_response = client.get("/api/meals")
    recent_response = client.get("/api/meals?days=7")

    assert all_response.status_code == 200
    assert [meal["meal_id"] for meal in all_response.get_json()["meals"]] == [
        "new",
        "old",
    ]
    assert recent_response.status_code == 200
    assert [meal["meal_id"] for meal in recent_response.get_json()["meals"]] == ["new"]


def test_get_meals_stats_returns_nutrition_and_spending_summary(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))

    app = create_app()
    client = app.test_client()
    add_history_meal("meal-1", iso_days_ago(1), price=20)
    add_history_meal("meal-2", iso_days_ago(2), price=30)

    response = client.get("/api/meals/stats?days=7")

    assert response.status_code == 200
    data = response.get_json()
    assert data["days"] == 7
    assert data["meal_count"] == 2
    assert data["stats"]["total_spending"] == 50
    assert data["stats"]["average_spending"] == 25
    assert "偏油" in data["recent_pattern"]["flags"]
    assert "热量偏高" in data["recent_pattern"]["flags"]
    assert "多蔬菜" in data["prefer_next"]
