import sqlite3

import pytest

from lib import database


REQUIRED_TABLES = {
    "users",
    "contacts",
    "dishes",
    "order_history",
    "recommendation_records",
    "notes_templates",
}

REQUIRED_CATEGORIES = {
    "盖饭类",
    "粉面类",
    "轻食类",
    "快餐油炸类",
    "麻辣类",
    "汤粥类",
    "家常菜类",
    "面点类",
    "饮料类",
}


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "mealmate.db"
    monkeypatch.setenv("MEALMATE_DB_PATH", str(db_path))
    database.init_db()
    return db_path


def test_init_db_creates_six_tables_and_imports_preset_dishes(isolated_db):
    with sqlite3.connect(isolated_db) as conn:
        table_rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {row[0] for row in table_rows}
    assert REQUIRED_TABLES.issubset(table_names)

    dishes = database.get_dishes()
    categories = {dish["category"] for dish in dishes}

    assert len(dishes) >= 30
    assert len(dishes) <= 50
    assert REQUIRED_CATEGORIES.issubset(categories)
    assert all(dish["price_source"] == "preset" for dish in dishes)
    assert all(isinstance(dish["ingredients"], list) for dish in dishes)
    assert all(isinstance(dish["estimated_nutrition"], dict) for dish in dishes)


def test_init_db_is_idempotent_for_preset_dishes(isolated_db):
    first_count = len(database.get_dishes())

    database.init_db()

    assert len(database.get_dishes()) == first_count


def test_user_save_and_get_round_trip_json_fields(isolated_db):
    user = database.save_user(
        {
            "user_id": "user-1",
            "name": "小明",
            "taste_description": "喜欢微辣，偏爱汤类",
            "taste_tags": ["微辣", "汤类"],
            "avoid_ingredients": ["香菜", "葱"],
            "health_goals": ["少油", "高蛋白"],
            "body_data": {"height_cm": 175, "weight_kg": 68},
            "default_budget": {
                "breakfast": [8, 15],
                "lunch": [15, 30],
                "dinner": [20, 40],
            },
            "remark_habits": ["少油", "不要香菜"],
        }
    )

    loaded = database.get_user("user-1")

    assert user["user_id"] == "user-1"
    assert loaded["taste_tags"] == ["微辣", "汤类"]
    assert loaded["avoid_ingredients"] == ["香菜", "葱"]
    assert loaded["body_data"]["height_cm"] == 175
    assert loaded["default_budget"]["lunch"] == [15, 30]
    assert loaded["created_at"]
    assert loaded["updated_at"]


def test_contacts_crud(isolated_db):
    contact = database.add_contact(
        {
            "owner_user_id": "user-1",
            "name": "妈妈",
            "taste_description": "清淡，少盐",
            "taste_tags": ["清淡"],
            "avoid_ingredients": ["辣椒"],
            "health_goals": ["少盐"],
            "default_budget": {"lunch": [18, 28], "dinner": [20, 35]},
            "remark_habits": ["少盐"],
        }
    )

    assert contact["contact_id"]
    assert database.get_contacts("user-1")[0]["avoid_ingredients"] == ["辣椒"]

    updated = database.update_contact(
        contact["contact_id"],
        {
            "name": "妈妈",
            "taste_description": "清淡，少油",
            "taste_tags": ["清淡", "少油"],
            "avoid_ingredients": ["辣椒", "香菜"],
            "health_goals": ["少盐", "少油"],
            "default_budget": {"lunch": [20, 30]},
            "remark_habits": ["少盐", "少油"],
        },
    )

    assert updated["taste_tags"] == ["清淡", "少油"]
    assert database.delete_contact(contact["contact_id"]) is True
    assert database.get_contacts("user-1") == []


def test_dishes_crud_and_lookup_by_name(isolated_db):
    dish = database.add_dish(
        {
            "dish_id": "dish-custom",
            "name": "测试鸡胸饭",
            "category": "盖饭类",
            "ingredients": ["鸡胸肉", "米饭", "西兰花"],
            "estimated_nutrition": {
                "calories_kcal": 520,
                "protein_g": 38,
                "fat_g": 12,
                "carbs_g": 68,
                "sodium_mg": 720,
            },
            "levels": {
                "calorie_level": "medium",
                "protein_level": "high",
                "fat_level": "low",
                "carbs_level": "medium",
                "sodium_level": "medium",
                "vegetable_level": "high",
            },
            "nutrition_tags": ["高蛋白", "少油"],
            "taste_tags": ["清淡"],
            "suitable_goals": ["高蛋白", "少油"],
            "remark_rules": ["少油", "酱汁分开"],
            "price": 24,
            "price_source": "preset",
            "confidence": 0.95,
        }
    )

    loaded = database.get_dish_by_name("测试鸡胸饭")

    assert dish["dish_id"] == "dish-custom"
    assert loaded["ingredients"] == ["鸡胸肉", "米饭", "西兰花"]
    assert loaded["estimated_nutrition"]["protein_g"] == 38
    assert any(item["name"] == "测试鸡胸饭" for item in database.get_dishes())


def test_order_history_crud_and_recent_sorting(isolated_db):
    old_meal = database.add_meal(
        {
            "meal_id": "meal-old",
            "user_id": "user-1",
            "user_type": "self",
            "occurred_at": "2026-06-12T12:30:00+08:00",
            "meal_type": "lunch",
            "raw_input": "昨天中午吃了黄焖鸡",
            "input_type": "text",
            "time_resolution": "inferred",
            "time_assumption": {
                "resolved_occurred_at": "2026-06-12T12:30:00+08:00"
            },
            "recognized_foods": [{"standard_name": "黄焖鸡米饭"}],
            "dish_ids": ["dish-1"],
            "total_price": 22,
            "total_nutrition": {"calories_kcal": 720},
            "remark_used": "少油，谢谢。",
            "budget_range_used": [15, 30],
        }
    )
    new_meal = database.add_meal(
        {
            "meal_id": "meal-new",
            "user_id": "user-1",
            "user_type": "self",
            "occurred_at": "2026-06-13T19:30:00+08:00",
            "meal_type": "dinner",
            "raw_input": "今天晚上吃了轻食",
            "input_type": "text",
            "time_resolution": "explicit",
            "time_assumption": {
                "resolved_occurred_at": "2026-06-13T19:30:00+08:00"
            },
            "recognized_foods": [{"standard_name": "鸡胸肉沙拉"}],
            "dish_ids": ["dish-2"],
            "total_price": 26,
            "total_nutrition": {"calories_kcal": 430},
            "budget_range_used": [20, 35],
        }
    )

    meals = database.get_meals("user-1")
    recent = database.get_recent_meals("user-1", limit=1)

    assert old_meal["recognized_foods"][0]["standard_name"] == "黄焖鸡米饭"
    assert new_meal["total_nutrition"]["calories_kcal"] == 430
    assert [meal["meal_id"] for meal in meals] == ["meal-new", "meal-old"]
    assert [meal["meal_id"] for meal in recent] == ["meal-new"]


def test_recommendation_records_crud(isolated_db):
    record = database.add_recommendation(
        {
            "rec_id": "rec-1",
            "user_id": "user-1",
            "based_on_meal_ids": ["meal-1", "meal-2"],
            "recent_pattern": {"fat_level": "high", "vegetable_level": "low"},
            "budget_range": [15, 25],
            "recommendations": [{"dish_id": "dish-1", "name": "番茄牛肉饭"}],
        }
    )

    loaded = database.get_recommendations("user-1")

    assert record["recent_pattern"]["fat_level"] == "high"
    assert loaded[0]["recommendations"][0]["name"] == "番茄牛肉饭"


def test_note_templates_crud(isolated_db):
    template = database.add_note_template(
        {
            "template_id": "note-1",
            "user_id": "user-1",
            "dish_category": "粉面类",
            "generated_remark": "少油，不要香菜，谢谢。",
            "user_edited_remark": "少油，不要香菜，汤少一点，谢谢。",
        }
    )

    loaded = database.get_note_templates("user-1")
    filtered = database.get_note_templates("user-1", dish_category="粉面类")

    assert template["dish_category"] == "粉面类"
    assert loaded[0]["user_edited_remark"].endswith("谢谢。")
    assert filtered[0]["template_id"] == "note-1"
