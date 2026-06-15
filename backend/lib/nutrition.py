from collections import Counter


HIGH_FAT_CATEGORIES = {"快餐油炸类", "麻辣类"}
HEAVY_TASTE_CATEGORIES = {"麻辣类", "快餐油炸类"}


def analyze_recent_meals(meals: list) -> dict:
    meals = meals or []
    if not meals:
        return _empty_analysis()

    foods = _flatten_foods(meals)
    category_counts = Counter(food.get("category") for food in foods if food.get("category"))
    repeated_categories = [
        category for category, count in category_counts.items() if count >= 2
    ]

    meal_count = len(meals)
    food_count = max(len(foods), 1)
    fat_hits = _count_level_or_tag(foods, "fat_level", "high", {"高脂肪", "油脂偏高"})
    calorie_hits = _count_level_or_tag(
        foods, "calorie_level", "high", {"高热量", "热量偏高"}
    )
    vegetable_low_hits = _count_level_or_tag(
        foods, "vegetable_level", "low", {"蔬菜偏少", "蔬菜不足"}
    )
    protein_high_hits = _count_level_or_tag(
        foods, "protein_level", "high", {"高蛋白", "蛋白质较高"}
    )
    protein_low_hits = _count_level_or_tag(
        foods, "protein_level", "low", {"蛋白质偏少", "蛋白质不足"}
    )
    heavy_taste_hits = _count_tag(foods, {"口味较重", "钠偏高", "高钠"}) + sum(
        1 for food in foods if food.get("category") in HEAVY_TASTE_CATEGORIES
    )

    flags = []
    if fat_hits / food_count >= 0.5 or _category_ratio(foods, HIGH_FAT_CATEGORIES) >= 0.5:
        flags.append("偏油")
    if calorie_hits / food_count >= 0.5 or _average_calories(meals) >= 800:
        flags.append("热量偏高")
    if vegetable_low_hits / food_count >= 0.5:
        flags.append("蔬菜偏少")
    if protein_low_hits / food_count >= 0.5:
        flags.append("蛋白质偏少")
    elif protein_high_hits / food_count >= 0.5:
        flags.append("蛋白质较充足")
    if heavy_taste_hits / food_count >= 0.5:
        flags.append("口味较重")
    if repeated_categories:
        flags.append("品类重复")

    recent_pattern = {
        "flags": flags,
        "fat_level": _pattern_level("偏油", flags),
        "calorie_level": _pattern_level("热量偏高", flags),
        "vegetable_level": "low" if "蔬菜偏少" in flags else "ok",
        "protein_level": _protein_pattern(flags),
        "taste_level": "heavy" if "口味较重" in flags else "ok",
        "repeated_categories": repeated_categories,
        "summary": _summary(flags),
    }

    prefer_next = ["均衡饮食"]
    if "偏油" in flags:
        prefer_next.insert(0, "少油")
    if "热量偏高" in flags:
        prefer_next.insert(0, "热量适中")
    if "蔬菜偏少" in flags:
        prefer_next.insert(0, "多蔬菜")
    if "蛋白质偏少" in flags:
        prefer_next.insert(0, "高蛋白")

    avoid_next = []
    if "偏油" in flags:
        avoid_next.append("油炸类")
    if "热量偏高" in flags:
        avoid_next.append("高热量菜品")
    if "口味较重" in flags:
        avoid_next.append("重口味")
    if repeated_categories:
        avoid_next.append("连续重复品类")

    return {
        "meal_count": meal_count,
        "recent_pattern": recent_pattern,
        "prefer_next": prefer_next,
        "avoid_next": avoid_next,
        "stats": _build_stats(meals),
    }


def _empty_analysis():
    return {
        "meal_count": 0,
        "recent_pattern": {
            "flags": [],
            "fat_level": "unknown",
            "calorie_level": "unknown",
            "vegetable_level": "unknown",
            "protein_level": "unknown",
            "taste_level": "unknown",
            "repeated_categories": [],
            "summary": "暂无饮食历史",
        },
        "prefer_next": ["均衡饮食"],
        "avoid_next": [],
        "stats": {
            "total_spending": 0,
            "average_spending": 0,
            "total_nutrition": {},
            "average_nutrition": {},
        },
    }


def _flatten_foods(meals):
    foods = []
    for meal in meals:
        for food in meal.get("recognized_foods") or []:
            if isinstance(food, dict):
                foods.append(food)
    return foods


def _count_level_or_tag(foods, level_key, level_value, tags):
    return sum(
        1
        for food in foods
        if (food.get("levels") or {}).get(level_key) == level_value
        or bool(set(food.get("nutrition_tags") or []) & tags)
    )


def _count_tag(foods, tags):
    return sum(1 for food in foods if bool(set(food.get("nutrition_tags") or []) & tags))


def _category_ratio(foods, categories):
    if not foods:
        return 0
    return sum(1 for food in foods if food.get("category") in categories) / len(foods)


def _average_calories(meals):
    values = [
        (meal.get("total_nutrition") or {}).get("calories_kcal")
        for meal in meals
        if isinstance((meal.get("total_nutrition") or {}).get("calories_kcal"), (int, float))
    ]
    return sum(values) / len(values) if values else 0


def _pattern_level(flag, flags):
    return "high" if flag in flags else "ok"


def _protein_pattern(flags):
    if "蛋白质偏少" in flags:
        return "low"
    if "蛋白质较充足" in flags:
        return "high"
    return "ok"


def _summary(flags):
    if not flags:
        return "近期饮食整体较均衡"
    return "近期饮食" + "、".join(flags)


def _build_stats(meals):
    total_spending = sum(
        meal.get("total_price") or 0
        for meal in meals
        if isinstance(meal.get("total_price") or 0, (int, float))
    )
    total_nutrition = {}
    for meal in meals:
        nutrition = meal.get("total_nutrition") or {}
        for key, value in nutrition.items():
            if isinstance(value, (int, float)):
                total_nutrition[key] = total_nutrition.get(key, 0) + value

    meal_count = len(meals)
    average_nutrition = {
        key: round(value / meal_count, 1) for key, value in total_nutrition.items()
    }
    return {
        "total_spending": round(total_spending, 1),
        "average_spending": round(total_spending / meal_count, 1) if meal_count else 0,
        "total_nutrition": total_nutrition,
        "average_nutrition": average_nutrition,
    }


def _unique(values):
    result = []
    seen = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result
