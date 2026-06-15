from lib.nutrition import analyze_recent_meals


def meal(
    meal_id,
    category,
    tags,
    levels,
    calories=650,
    protein=24,
    price=25,
):
    return {
        "meal_id": meal_id,
        "occurred_at": f"2026-06-1{meal_id}T12:30:00+08:00",
        "meal_type": "lunch",
        "total_price": price,
        "total_nutrition": {
            "calories_kcal": calories,
            "protein_g": protein,
            "fat_g": 30,
            "carbs_g": 80,
            "sodium_mg": 900,
        },
        "recognized_foods": [
            {
                "standard_name": f"测试菜品 {meal_id}",
                "category": category,
                "nutrition_tags": tags,
                "levels": levels,
                "estimated_nutrition": {
                    "calories_kcal": calories,
                    "protein_g": protein,
                    "fat_g": 30,
                    "carbs_g": 80,
                    "sodium_mg": 900,
                },
            }
        ],
    }


def test_high_fat_and_high_calorie_meals_are_detected():
    result = analyze_recent_meals(
        [
            meal(
                1,
                "快餐油炸类",
                ["高热量", "高脂肪"],
                {"fat_level": "high", "calorie_level": "high", "vegetable_level": "low"},
                calories=980,
            ),
            meal(
                2,
                "麻辣类",
                ["高热量", "高脂肪", "口味较重"],
                {"fat_level": "high", "calorie_level": "high", "vegetable_level": "low"},
                calories=920,
            ),
        ]
    )

    assert "偏油" in result["recent_pattern"]["flags"]
    assert "热量偏高" in result["recent_pattern"]["flags"]
    assert "少油" in result["prefer_next"]
    assert "高热量菜品" in result["avoid_next"]


def test_repeated_fast_food_detects_low_vegetable_pattern():
    result = analyze_recent_meals(
        [
            meal(
                1,
                "快餐油炸类",
                ["高热量", "蔬菜偏少"],
                {"fat_level": "high", "calorie_level": "high", "vegetable_level": "low"},
            ),
            meal(
                2,
                "快餐油炸类",
                ["高脂肪", "蔬菜偏少"],
                {"fat_level": "high", "calorie_level": "medium", "vegetable_level": "low"},
            ),
            meal(
                3,
                "快餐油炸类",
                ["蔬菜偏少"],
                {"fat_level": "medium", "calorie_level": "medium", "vegetable_level": "low"},
            ),
        ]
    )

    assert "蔬菜偏少" in result["recent_pattern"]["flags"]
    assert "快餐油炸类" in result["recent_pattern"]["repeated_categories"]
    assert "多蔬菜" in result["prefer_next"]
    assert "连续重复品类" in result["avoid_next"]


def test_empty_history_returns_default_analysis():
    result = analyze_recent_meals([])

    assert result["meal_count"] == 0
    assert result["recent_pattern"]["flags"] == []
    assert result["recent_pattern"]["summary"] == "暂无饮食历史"
    assert result["prefer_next"] == ["均衡饮食"]
    assert result["avoid_next"] == []
    assert result["stats"]["total_spending"] == 0
