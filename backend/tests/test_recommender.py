from lib.recommender import is_allergen_conflict, pre_filter, score_dish


def dish(
    name,
    price=20,
    ingredients=None,
    taste_tags=None,
    suitable_goals=None,
    nutrition_tags=None,
    levels=None,
    category="盖饭类",
):
    return {
        "dish_id": f"dish-{name}",
        "name": name,
        "price": price,
        "ingredients": ingredients or [],
        "taste_tags": taste_tags or [],
        "suitable_goals": suitable_goals or [],
        "nutrition_tags": nutrition_tags or [],
        "levels": levels or {},
        "category": category,
    }


def test_allergen_conflict_filters_dish():
    item = dish("香菜牛肉饭", ingredients=["牛肉", "香菜"])

    assert is_allergen_conflict(item, ["香菜"]) is True
    assert (
        score_dish(
            item,
            user_profile={"avoid_ingredients": ["香菜"]},
            recent_pattern={},
            budget_range=[15, 25],
        )
        is None
    )


def test_budget_over_range_deducts_points():
    item = dish("贵价沙拉", price=30)

    score = score_dish(
        item,
        user_profile={"avoid_ingredients": []},
        recent_pattern={},
        budget_range=[15, 25],
    )

    assert score == 30


def test_taste_preference_match_adds_points():
    item = dish("微辣牛肉饭", taste_tags=["微辣", "咸香"])

    score = score_dish(
        item,
        user_profile={"taste_tags": ["微辣"], "avoid_ingredients": []},
        recent_pattern={},
        budget_range=[15, 25],
    )

    assert score == 75


def test_recent_fat_pattern_rewards_low_fat_dish():
    item = dish("清蒸鸡胸饭", levels={"fat_level": "low"})

    score = score_dish(
        item,
        user_profile={"avoid_ingredients": []},
        recent_pattern={"flags": ["偏油"], "fat_level": "high"},
        budget_range=[15, 25],
    )

    assert score == 85


def test_pre_filter_returns_top_10_sorted_by_score():
    dishes = [
        dish(f"菜品-{index}", price=18 + index, taste_tags=["微辣"] if index % 2 == 0 else [])
        for index in range(12)
    ]
    dishes.append(dish("香菜冲突", ingredients=["香菜"], price=18))

    result = pre_filter(
        dishes,
        user_profile={"taste_tags": ["微辣"], "avoid_ingredients": ["香菜"]},
        recent_pattern={},
        budget_range=[15, 25],
        recent_meals=[],
    )

    assert len(result) == 10
    assert all(item["name"] != "香菜冲突" for item in result)
    scores = [item["score"] for item in result]
    assert scores == sorted(scores, reverse=True)


def test_recent_same_category_deducts_points_in_pre_filter():
    item = dish("番茄牛肉饭", category="盖饭类", price=20)

    result = pre_filter(
        [item],
        user_profile={"avoid_ingredients": []},
        recent_pattern={},
        budget_range=[15, 25],
        recent_meals=[
            {
                "recognized_foods": [
                    {"standard_name": "黄焖鸡米饭", "category": "盖饭类"}
                ]
            }
        ],
    )

    assert result[0]["score"] == 50
