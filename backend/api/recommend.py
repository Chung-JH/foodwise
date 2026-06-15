from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request

from lib import database, recommend
from lib.llm import LLMError


recommend_bp = Blueprint("recommend", __name__, url_prefix="/api")


@recommend_bp.post("/recommend")
def create_recommendation():
    payload = request.get_json(silent=True) or {}
    try:
        result = recommend.generate_next_meal_recommendation(payload)
    except recommend.RecommendError as exc:
        return jsonify({"error": str(exc)}), 400
    except LLMError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(result)


@recommend_bp.get("/recommend/records")
def get_recommendation_records():
    user_type = request.args.get("user_type", "self")
    contact_id = request.args.get("contact_id")
    user_id = contact_id if user_type == "contact" and contact_id else recommend.DEFAULT_USER_ID
    return jsonify({"records": recommend.get_recommendation_records(user_id)})


@recommend_bp.post("/recommend/confirm")
def confirm_recommendation():
    payload = request.get_json(silent=True) or {}

    # Support both legacy single-item and new multi-item selection
    items = payload.get("recommendations") or []
    if not items:
        single = payload.get("recommendation") or {}
        if single.get("name"):
            items = [single]
    if not items:
        return jsonify({"error": "请选择推荐菜品"}), 400

    user_type = payload.get("user_type", "self")
    user_id = payload.get("contact_id") if user_type == "contact" else recommend.DEFAULT_USER_ID
    if not user_id:
        return jsonify({"error": "请选择亲友"}), 400

    occurred_at = _now_iso()
    # meal_type from the user's selection; fall back to a DB lookup for extra fields
    meal_type = payload.get("meal_type") or "lunch"

    recognized_foods = []
    dish_ids = []
    for item in items:
        # Prefer nutrition data carried in the recommendation item (already populated
        # from the candidate dish during generation); only fall back to a DB lookup
        # when a field is missing.
        item_nutrition = item.get("estimated_nutrition") or {}
        item_levels    = item.get("levels") or {}
        item_tags      = item.get("nutrition_tags") or []
        item_category  = item.get("category") or ""

        if not (item_nutrition and item_levels and item_category):
            dish = database.get_dish_by_name(item["name"]) or {}
            item_nutrition = item_nutrition or dish.get("estimated_nutrition") or {}
            item_levels    = item_levels    or dish.get("levels") or {}
            item_tags      = item_tags      or dish.get("nutrition_tags") or []
            item_category  = item_category  or dish.get("category") or ""
            if dish.get("dish_id"):
                dish_ids.append(dish["dish_id"])
        elif item.get("dish_id"):
            dish_ids.append(item["dish_id"])

        recognized_foods.append({
            "standard_name":      item["name"],
            "course_type":        item.get("course_type", "主食"),
            "category":           item_category,
            "nutrition_tags":     item_tags,
            "estimated_nutrition": item_nutrition,
            "levels":             item_levels,
            "price":              item.get("price", 0),
        })

    total_price = round(sum(f.get("price", 0) for f in recognized_foods), 1)

    # Aggregate nutrition across all confirmed dishes
    total_nutrition = {}
    for f in recognized_foods:
        for k, v in (f.get("estimated_nutrition") or {}).items():
            try:
                total_nutrition[k] = round((total_nutrition.get(k) or 0) + float(v), 1)
            except (TypeError, ValueError):
                pass

    names = "、".join(item["name"] for item in items)

    meal = database.add_meal(
        {
            "user_id": user_id,
            "user_type": user_type,
            "occurred_at": occurred_at,
            "meal_type": meal_type,
            "raw_input": f"推荐确认：{names}",
            "input_type": "recommendation",
            "time_resolution": "explicit",
            "time_assumption": {
                "raw_time_text": "确认推荐时间",
                "resolved_occurred_at": occurred_at,
                "timezone": "Asia/Shanghai",
                "date_source": "系统确认时间",
                "time_source": "系统确认时间",
                "default_rule": "推荐确认使用当前时间",
                "confidence": 1.0,
            },
            "recognized_foods": recognized_foods,
            "dish_ids": dish_ids,
            "total_price": total_price,
            "total_nutrition": total_nutrition,
            "remark_used": payload.get("remark", ""),
            "budget_range_used": payload.get("budget_range"),
        }
    )
    return jsonify({"meal": meal, "saved": True})


def _now_iso():
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
