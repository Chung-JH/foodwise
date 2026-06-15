from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from lib import database, llm, time_parser


DEFAULT_USER_ID = "default_user"
PHOTO_MEAL_TYPE = "snack"
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


class MealLogError(ValueError):
    pass


def current_time_iso():
    return datetime.now(SHANGHAI_TZ).isoformat(timespec="seconds")


def log_text_meal(text, current_time=None, user_id=DEFAULT_USER_ID):
    text = str(text or "").strip()
    if not text:
        raise MealLogError("饮食记录文本不能为空")

    current_time = current_time or current_time_iso()
    parsed = llm.parse_meal_record(text, current_time)
    meal_time = _validate_parsed_meal(parsed)
    foods = parsed["recognized_foods"]
    dish_ids = [_ensure_dish_from_food(food) for food in foods]

    meal = database.add_meal(
        {
            "user_id": user_id,
            "user_type": "self",
            "occurred_at": meal_time["occurred_at"],
            "meal_type": meal_time.get("meal_type") or "snack",
            "raw_input": text,
            "input_type": "text",
            "time_resolution": meal_time["time_resolution"],
            "time_assumption": meal_time["time_assumption"],
            "recognized_foods": foods,
            "dish_ids": dish_ids,
            "total_price": _sum_prices(foods),
            "total_nutrition": _sum_nutrition(foods),
            "budget_range_used": None,
            "remark_used": None,
        }
    )

    return {
        "meal": meal,
        "parsed": parsed,
        "dish_ids": dish_ids,
        "saved": True,
    }


def analyze_photo(image_path, user_price=None):
    analysis = llm.analyze_dish_photo(str(image_path))
    analysis = _normalize_photo_price(analysis, user_price)
    _validate_photo_analysis(analysis)
    dish = _ensure_dish_from_photo(analysis, str(image_path))
    return {
        "analysis": analysis,
        "dish": dish,
        "image_path": str(image_path),
    }


def save_photo_meal(analysis, occurred_at=None, user_price=None, user_id=DEFAULT_USER_ID):
    if not isinstance(analysis, dict):
        raise MealLogError("照片分析结果必须是对象")

    analysis = _normalize_photo_price(analysis, user_price)
    _validate_photo_analysis(analysis)
    dish = _ensure_dish_from_photo(analysis, analysis.get("image_path"))
    meal_time = _photo_meal_time(occurred_at)
    food = _food_from_photo_analysis(analysis)

    meal = database.add_meal(
        {
            "user_id": user_id,
            "user_type": "self",
            "occurred_at": meal_time["occurred_at"],
            "meal_type": PHOTO_MEAL_TYPE,
            "raw_input": f"照片记录：{analysis['dish_name']}",
            "input_type": "photo",
            "time_resolution": meal_time["time_resolution"],
            "time_assumption": meal_time["time_assumption"],
            "recognized_foods": [food],
            "dish_ids": [dish["dish_id"]],
            "total_price": analysis.get("price"),
            "total_nutrition": analysis["estimated_nutrition"],
            "budget_range_used": None,
            "remark_used": None,
        }
    )

    return {
        "meal": meal,
        "analysis": analysis,
        "dish": dish,
        "saved": True,
    }


def _validate_parsed_meal(parsed):
    if not isinstance(parsed, dict):
        raise MealLogError("LLM 返回必须是 JSON 对象")

    meal_time = parsed.get("meal_time")
    try:
        time_parser.validate_meal_time(meal_time)
    except ValueError as exc:
        raise MealLogError(str(exc)) from exc

    foods = parsed.get("recognized_foods")
    if not isinstance(foods, list) or not foods:
        raise MealLogError("recognized_foods 必须是非空数组")
    for food in foods:
        _validate_food(food)
    return meal_time


def _validate_food(food):
    if not isinstance(food, dict):
        raise MealLogError("recognized_foods 中每项必须是对象")
    required_text_fields = ["raw_text", "standard_name", "category", "portion", "assumption"]
    for field in required_text_fields:
        if not str(food.get(field) or "").strip():
            raise MealLogError(f"菜品字段 {field} 不能为空")
    if not isinstance(food.get("estimated_nutrition"), dict):
        raise MealLogError("estimated_nutrition 必须是对象")
    if not isinstance(food.get("levels"), dict):
        raise MealLogError("levels 必须是对象")
    if not isinstance(food.get("nutrition_tags"), list):
        raise MealLogError("nutrition_tags 必须是数组")
    confidence = food.get("confidence")
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        raise MealLogError("confidence 必须在 0 到 1 之间")


def _validate_photo_analysis(analysis):
    required_fields = [
        "dish_name",
        "ingredients",
        "category",
        "estimated_nutrition",
        "levels",
        "nutrition_tags",
        "price",
        "price_source",
        "confidence",
        "assumption",
    ]
    for field in required_fields:
        if field not in analysis:
            raise MealLogError(f"照片分析缺少字段 {field}")
    if not str(analysis["dish_name"]).strip():
        raise MealLogError("dish_name 不能为空")
    if analysis["category"] not in llm.ALLOWED_DISH_CATEGORIES:
        raise MealLogError("category 不合法")
    if not isinstance(analysis["ingredients"], list):
        raise MealLogError("ingredients 必须是数组")
    if not isinstance(analysis["estimated_nutrition"], dict):
        raise MealLogError("estimated_nutrition 必须是对象")
    if not isinstance(analysis["levels"], dict):
        raise MealLogError("levels 必须是对象")
    if not isinstance(analysis["nutrition_tags"], list):
        raise MealLogError("nutrition_tags 必须是数组")
    if analysis["price_source"] not in {"image_recognized", "user_input", "llm_estimated", "preset"}:
        raise MealLogError("price_source 不合法")
    if not isinstance(analysis["price"], (int, float)) or analysis["price"] < 0:
        raise MealLogError("price 必须是非负数字")
    confidence = analysis["confidence"]
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        raise MealLogError("confidence 必须在 0 到 1 之间")


def _ensure_dish_from_food(food):
    name = food["standard_name"]
    existing = database.get_dish_by_name(name)
    if existing:
        return existing["dish_id"]

    dish = database.add_dish(
        {
            "name": name,
            "category": food["category"],
            "ingredients": [],
            "estimated_nutrition": food["estimated_nutrition"],
            "levels": food["levels"],
            "nutrition_tags": food["nutrition_tags"],
            "taste_tags": [],
            "suitable_goals": [],
            "remark_rules": [],
            "price": food.get("price", 0) or 0,
            "price_source": food.get("price_source", "llm_estimated"),
            "llm_analysis_raw": food,
            "confidence": food["confidence"],
        }
    )
    return dish["dish_id"]


def _ensure_dish_from_photo(analysis, image_path=None):
    name = analysis["dish_name"]
    existing = database.get_dish_by_name(name)
    if existing:
        return existing

    return database.add_dish(
        {
            "name": name,
            "category": analysis["category"],
            "ingredients": analysis["ingredients"],
            "estimated_nutrition": analysis["estimated_nutrition"],
            "levels": analysis["levels"],
            "nutrition_tags": analysis["nutrition_tags"],
            "taste_tags": analysis.get("taste_tags", []),
            "suitable_goals": analysis.get("suitable_goals", []),
            "remark_rules": analysis.get("remark_rules", []),
            "price": analysis["price"],
            "price_source": analysis["price_source"],
            "image_path": image_path,
            "llm_analysis_raw": analysis,
            "confidence": analysis["confidence"],
        }
    )


def _normalize_photo_price(analysis, user_price):
    if user_price in (None, ""):
        return analysis
    try:
        price = float(user_price)
    except (TypeError, ValueError) as exc:
        raise MealLogError("价格必须是数字") from exc
    return {**analysis, "price": price, "price_source": "user_input"}


def _photo_meal_time(occurred_at):
    occurred_at = _normalize_occurred_at(occurred_at)
    meal_time = {
        "occurred_at": occurred_at,
        "meal_type": PHOTO_MEAL_TYPE,
        "time_resolution": "explicit",
        "time_assumption": {
            "raw_time_text": "用户确认照片记录时间",
            "resolved_occurred_at": occurred_at,
            "timezone": "Asia/Shanghai",
            "date_source": "用户在页面确认",
            "time_source": "用户在页面确认",
            "default_rule": "照片记录默认使用用户确认时间",
            "confidence": 1.0,
        },
    }
    time_parser.validate_meal_time(meal_time)
    return meal_time


def _normalize_occurred_at(value):
    if value:
        text = str(value).strip()
        if text.endswith("Z"):
            return text.replace("Z", "+00:00")
        if "+" in text[10:] or text[10:].count("-") > 0:
            return text
        return f"{text}:00+08:00" if len(text) == 16 else f"{text}+08:00"
    return current_time_iso()


def _food_from_photo_analysis(analysis):
    return {
        "raw_text": analysis["dish_name"],
        "standard_name": analysis["dish_name"],
        "category": analysis["category"],
        "portion": "一份",
        "estimated_nutrition": analysis["estimated_nutrition"],
        "levels": analysis["levels"],
        "nutrition_tags": analysis["nutrition_tags"],
        "price": analysis["price"],
        "price_source": analysis["price_source"],
        "confidence": analysis["confidence"],
        "assumption": analysis["assumption"],
    }


def _sum_prices(foods):
    prices = [food.get("price") for food in foods if isinstance(food.get("price"), (int, float))]
    return sum(prices) if prices else 0


def _sum_nutrition(foods):
    totals = {}
    for food in foods:
        nutrition = food.get("estimated_nutrition") or {}
        for key, value in nutrition.items():
            if isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0) + value
    return totals
