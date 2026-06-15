from io import BytesIO

from app import create_app
from lib import database


def test_log_text_meal_parses_saves_and_adds_dish(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/log-meal",
        json={"text": "昨天晚上吃了炸鸡汉堡套餐和可乐"},
    )

    assert response.status_code == 200
    result = response.get_json()
    meal = result["meal"]
    parsed_time = result["parsed"]["meal_time"]

    assert result["saved"] is True
    assert parsed_time["occurred_at"] == parsed_time["time_assumption"]["resolved_occurred_at"]
    assert meal["occurred_at"] == "2026-06-12T19:30:00+08:00"
    assert meal["time_assumption"]["resolved_occurred_at"] == meal["occurred_at"]
    assert meal["recognized_foods"][0]["standard_name"] == "炸鸡汉堡套餐"
    assert database.get_meals("default_user")[0]["meal_id"] == meal["meal_id"]
    assert database.get_dish_by_name("炸鸡汉堡套餐") is not None


def test_log_text_meal_rejects_unknown_time_without_saving(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))

    from lib import log_meal

    def fake_parse_meal_record(user_input, current_time):
        return {
            "meal_time": {
                "occurred_at": "2026-06-12T19:30:00+08:00",
                "meal_type": "dinner",
                "time_resolution": "unknown",
                "time_assumption": {
                    "raw_time_text": "",
                    "resolved_occurred_at": "2026-06-12T19:30:00+08:00",
                    "timezone": "Asia/Shanghai",
                    "date_source": "",
                    "time_source": "",
                    "default_rule": "",
                    "confidence": 0.2,
                },
            },
            "recognized_foods": [
                {
                    "raw_text": "汉堡",
                    "standard_name": "汉堡",
                    "category": "快餐油炸类",
                    "portion": "一份",
                    "estimated_nutrition": {"calories_kcal": 600},
                    "levels": {"calorie_level": "high"},
                    "nutrition_tags": ["高热量"],
                    "confidence": 0.7,
                    "assumption": "测试",
                }
            ],
        }

    monkeypatch.setattr(log_meal.llm, "parse_meal_record", fake_parse_meal_record)

    app = create_app()
    client = app.test_client()

    response = client.post("/api/log-meal", json={"text": "吃了汉堡"})

    assert response.status_code == 400
    assert "无法判断用餐时间" in response.get_json()["error"]
    assert database.get_meals("default_user") == []


def test_log_text_meal_adds_new_dish_when_not_in_library(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))

    from lib import log_meal

    def fake_parse_meal_record(user_input, current_time):
        return {
            "meal_time": {
                "occurred_at": "2026-06-12T12:30:00+08:00",
                "meal_type": "lunch",
                "time_resolution": "explicit",
                "time_assumption": {
                    "raw_time_text": "2026-06-12 中午",
                    "resolved_occurred_at": "2026-06-12T12:30:00+08:00",
                    "timezone": "Asia/Shanghai",
                    "date_source": "用户明确给出",
                    "time_source": "中午默认 12:30",
                    "default_rule": "午餐=12:30",
                    "confidence": 0.9,
                },
            },
            "recognized_foods": [
                {
                    "raw_text": "测试新增鸡肉饭",
                    "standard_name": "测试新增鸡肉饭",
                    "category": "盖饭类",
                    "portion": "一份",
                    "estimated_nutrition": {"calories_kcal": 580, "protein_g": 32},
                    "levels": {"calorie_level": "medium", "protein_level": "high"},
                    "nutrition_tags": ["高蛋白"],
                    "price": 21,
                    "price_source": "llm_estimated",
                    "confidence": 0.86,
                    "assumption": "测试新增文本菜品",
                }
            ],
        }

    monkeypatch.setattr(log_meal.llm, "parse_meal_record", fake_parse_meal_record)

    app = create_app()
    client = app.test_client()

    response = client.post("/api/log-meal", json={"text": "中午吃了测试新增鸡肉饭"})

    assert response.status_code == 200
    dish = database.get_dish_by_name("测试新增鸡肉饭")
    assert dish is not None
    assert dish["price"] == 21
    assert dish["llm_analysis_raw"]["standard_name"] == "测试新增鸡肉饭"


def test_photo_upload_analyzes_and_adds_dish(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    monkeypatch.setattr("api.log_meal.UPLOAD_DIR", upload_dir)

    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/log-meal/photo",
        data={"image": (BytesIO(b"fake image"), "dish.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    result = response.get_json()
    analysis = result["analysis"]

    assert analysis["dish_name"] == "番茄牛肉饭"
    assert analysis["price"] == 25
    assert result["dish"]["name"] == "番茄牛肉饭"
    assert upload_dir.exists()
    assert database.get_dish_by_name("番茄牛肉饭") is not None


def test_photo_upload_adds_new_dish_when_not_in_library(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setattr("api.log_meal.UPLOAD_DIR", upload_dir)

    from lib import log_meal

    def fake_analyze_dish_photo(image_path):
        return {
            "dish_name": "测试新增牛肉汤",
            "ingredients": ["牛肉", "青菜"],
            "category": "汤粥类",
            "estimated_nutrition": {
                "calories_kcal": 420,
                "protein_g": 30,
                "fat_g": 12,
                "carbs_g": 45,
                "sodium_mg": 760,
            },
            "levels": {
                "calorie_level": "medium",
                "protein_level": "high",
                "fat_level": "medium",
                "carbs_level": "medium",
                "sodium_level": "medium",
                "vegetable_level": "medium",
            },
            "nutrition_tags": ["高蛋白", "热量适中"],
            "price": 23,
            "price_source": "llm_estimated",
            "confidence": 0.8,
            "assumption": "测试新增菜品",
        }

    monkeypatch.setattr(log_meal.llm, "analyze_dish_photo", fake_analyze_dish_photo)

    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/log-meal/photo",
        data={"image": (BytesIO(b"fake image"), "new-dish.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    dish = database.get_dish_by_name("测试新增牛肉汤")
    assert dish is not None
    assert dish["price"] == 23
    assert dish["price_source"] == "llm_estimated"
    assert dish["llm_analysis_raw"]["dish_name"] == "测试新增牛肉汤"


def test_photo_save_writes_order_history_with_manual_price(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    app = create_app()
    client = app.test_client()
    photo_response = client.post(
        "/api/log-meal/photo",
        data={"image": (BytesIO(b"fake image"), "dish.jpg")},
        content_type="multipart/form-data",
    )
    analysis = photo_response.get_json()["analysis"]

    response = client.post(
        "/api/log-meal/photo/save",
        json={
            "analysis": analysis,
            "occurred_at": "2026-06-14T12:30",
            "price": 28,
        },
    )

    assert response.status_code == 200
    result = response.get_json()
    meal = result["meal"]

    assert result["saved"] is True
    assert meal["input_type"] == "photo"
    assert meal["occurred_at"] == "2026-06-14T12:30:00+08:00"
    assert meal["time_assumption"]["resolved_occurred_at"] == meal["occurred_at"]
    assert meal["recognized_foods"][0]["price"] == 28
    assert database.get_meals("default_user")[0]["meal_id"] == meal["meal_id"]
