BASE_SCORE = 50


def is_allergen_conflict(dish, avoid_ingredients) -> bool:
    avoid_set = {str(item).strip() for item in (avoid_ingredients or []) if str(item).strip()}
    if not avoid_set:
        return False

    ingredients = {str(item).strip() for item in (dish.get("ingredients") or [])}
    return bool(ingredients & avoid_set)


def score_dish(dish, user_profile, recent_pattern, budget_range) -> int | None:
    user_profile = user_profile or {}
    recent_pattern = recent_pattern or {}

    if is_allergen_conflict(dish, user_profile.get("avoid_ingredients")):
        return None

    score = BASE_SCORE
    price = _number(dish.get("price"))
    budget_min, budget_max = _budget_bounds(budget_range)
    if price is not None and budget_min <= price <= budget_max:
        score += 15
    else:
        score -= 20

    if _overlaps(dish.get("taste_tags"), user_profile.get("taste_tags")):
        score += 10
    if _overlaps(dish.get("suitable_goals"), user_profile.get("health_goals")):
        score += 20

    flags = set(recent_pattern.get("flags") or [])
    levels = dish.get("levels") or {}
    category = dish.get("category")

    if "偏油" in flags or recent_pattern.get("fat_level") == "high":
        if levels.get("fat_level") == "low" or "少油" in (dish.get("nutrition_tags") or []):
            score += 20
        if category == "快餐油炸类":
            score -= 25

    if "热量偏高" in flags or recent_pattern.get("calorie_level") == "high":
        if levels.get("calorie_level") == "medium" or "热量适中" in (dish.get("nutrition_tags") or []):
            score += 15
        if levels.get("calorie_level") == "high" or "高热量" in (dish.get("nutrition_tags") or []):
            score -= 20

    if "蔬菜偏少" in flags or recent_pattern.get("vegetable_level") == "low":
        if levels.get("vegetable_level") == "high" or _has_any_tag(dish, {"多蔬菜", "蔬菜较多"}):
            score += 15

    if levels.get("protein_level") == "high" or _has_any_tag(dish, {"高蛋白", "蛋白质较高"}):
        score += 10

    if ("口味较重" in flags or recent_pattern.get("taste_level") == "heavy") and category == "麻辣类":
        score -= 15

    return int(score)


def pre_filter(dishes, user_profile, recent_pattern, budget_range, recent_meals) -> list[dict]:
    recent_categories = _recent_categories(recent_meals)
    scored = []
    for dish in dishes:
        score = score_dish(dish, user_profile, recent_pattern, budget_range)
        if score is None:
            continue
        if dish.get("category") in recent_categories:
            score -= 15
        scored.append({**dish, "score": int(score)})

    return sorted(scored, key=lambda item: item["score"], reverse=True)[:10]


def _budget_bounds(budget_range):
    if isinstance(budget_range, dict):
        minimum = budget_range.get("min")
        maximum = budget_range.get("max")
    elif isinstance(budget_range, (list, tuple)) and len(budget_range) >= 2:
        minimum, maximum = budget_range[0], budget_range[1]
    else:
        minimum, maximum = 0, float("inf")

    minimum = _number(minimum)
    maximum = _number(maximum)
    minimum = 0 if minimum is None else minimum
    maximum = float("inf") if maximum is None else maximum
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    return minimum, maximum


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _overlaps(left, right):
    return bool({str(item) for item in (left or [])} & {str(item) for item in (right or [])})


def _has_any_tag(dish, tags):
    return bool(set(dish.get("nutrition_tags") or []) & tags)


def _recent_categories(recent_meals):
    categories = set()
    for meal in recent_meals or []:
        for food in meal.get("recognized_foods") or []:
            category = food.get("category")
            if category:
                categories.add(category)
    return categories
