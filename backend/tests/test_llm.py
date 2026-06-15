import json

import pytest

from lib import llm


def test_mock_parse_taste_text_returns_tags(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    tags = llm.parse_taste_text("喜欢川菜但不能太辣，偏爱汤类")

    assert isinstance(tags, list)
    assert "微辣" in tags
    assert "川菜" in tags


def test_mock_parse_meal_record_returns_complete_structure(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    result = llm.parse_meal_record(
        "昨天晚上吃了炸鸡汉堡套餐和可乐",
        "2026-06-13T10:00:00+08:00",
    )

    meal_time = result["meal_time"]
    food = result["recognized_foods"][0]

    assert meal_time["occurred_at"] == "2026-06-12T19:30:00+08:00"
    assert (
        meal_time["occurred_at"]
        == meal_time["time_assumption"]["resolved_occurred_at"]
    )
    assert meal_time["time_resolution"] == "inferred"
    assert food["standard_name"] == "炸鸡汉堡套餐"
    assert food["levels"]["fat_level"] == "high"
    assert isinstance(food["estimated_nutrition"]["calories_kcal"], int)


def test_mock_analyze_dish_photo_returns_qwen_vl_shape(monkeypatch, tmp_path):
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    image_path = tmp_path / "dish.jpg"
    image_path.write_bytes(b"fake image")

    result = llm.analyze_dish_photo(str(image_path))

    assert result["dish_name"]
    assert result["category"] in llm.ALLOWED_DISH_CATEGORIES
    assert result["price_source"] in {
        "image_recognized",
        "user_input",
        "llm_estimated",
        "preset",
    }
    assert 0 <= result["confidence"] <= 1
    assert isinstance(result["ingredients"], list)
    assert isinstance(result["estimated_nutrition"], dict)


def test_mock_generate_recommendation_returns_top_three(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    result = llm.generate_recommendation(
        user_profile={"avoid_ingredients": ["香菜", "葱"], "taste_tags": ["微辣"]},
        recent_meals=[],
        recent_pattern={"fat_level": "high", "vegetable_level": "low"},
        candidate_dishes=[
            {"dish_id": "dish-1", "name": "鸡胸肉沙拉", "price": 24},
            {"dish_id": "dish-2", "name": "番茄牛肉饭", "price": 25},
            {"dish_id": "dish-3", "name": "冬瓜排骨汤", "price": 22},
        ],
        budget_range=[15, 25],
    )

    assert len(result["recommendations"]) >= 3
    assert "budget_note" in result
    assert "nutrition_summary" in result
    assert all("reason" in item for item in result["recommendations"])


def test_mock_generate_remark_returns_text(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    remark = llm.generate_remark(
        user_profile={"avoid_ingredients": ["香菜", "葱"], "remark_habits": ["少油"]},
        dishes=[{"name": "番茄牛肉饭", "category": "盖饭类"}],
        dish_category="盖饭类",
    )

    assert "不要香菜" in remark
    assert "不要葱" in remark
    assert remark.endswith("谢谢。")


def test_validate_json_response_accepts_dict_and_json_string():
    payload = {"taste_tags": ["微辣", "川菜"]}

    assert llm._validate_json_response(payload) == payload
    assert llm._validate_json_response(json.dumps(payload, ensure_ascii=False)) == payload


def test_validate_json_response_rejects_invalid_json():
    with pytest.raises(llm.LLMResponseError, match="模型返回不是合法 JSON"):
        llm._validate_json_response("不是 JSON")


def test_validate_json_response_rejects_non_object_json():
    with pytest.raises(llm.LLMResponseError, match="模型返回 JSON 必须是对象"):
        llm._validate_json_response("[1, 2, 3]")


def test_llm_config_can_be_loaded_from_json_file(monkeypatch, tmp_path):
    config_path = tmp_path / "llm_config.json"
    config_path.write_text(
        json.dumps(
            {
                "dashscope_base_url": "https://example.test/v1",
                "api_key": "test-key",
                "qwen_vl_model": "qwen-vl-test",
                "qwen_text_model": "qwen-text-test",
                "use_mock_llm": True,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MEALMATE_LLM_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    config = llm._load_llm_config()

    assert config["api_key"] == "test-key"
    assert config["qwen_vl_model"] == "qwen-vl-test"
    assert config["qwen_text_model"] == "qwen-text-test"
    assert config["use_mock_llm"] is True


def test_prompts_contain_required_plan_constraints():
    assert "只返回 JSON" in llm.DISH_PHOTO_SYSTEM_PROMPT
    assert "price_source" in llm.DISH_PHOTO_SYSTEM_PROMPT
    assert "category 只能是" in llm.DISH_PHOTO_SYSTEM_PROMPT
    assert "time_assumption" in llm.MEAL_RECORD_SYSTEM_PROMPT
    assert "occurred_at 与 resolved_occurred_at 必须完全一致" in llm.MEAL_RECORD_SYSTEM_PROMPT
    assert "每种 course_type 最多推荐 3 个" in llm.RECOMMENDATION_SYSTEM_PROMPT
