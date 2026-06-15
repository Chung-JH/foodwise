from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from lib import database, nutrition


DEFAULT_USER_ID = "default_user"
ALLOWED_MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack"}

meals_bp = Blueprint("meals", __name__, url_prefix="/api")


@meals_bp.delete("/meals/<meal_id>")
def delete_meal(meal_id):
    deleted = database.delete_meal(meal_id)
    if not deleted:
        return jsonify({"error": "记录不存在"}), 404
    return jsonify({"deleted": True, "meal_id": meal_id})


@meals_bp.patch("/meals/<meal_id>")
def update_meal(meal_id):
    payload = request.get_json(silent=True) or {}
    updates = {}
    if "meal_type" in payload:
        if payload["meal_type"] not in ALLOWED_MEAL_TYPES:
            return jsonify({"error": "meal_type 不合法"}), 400
        updates["meal_type"] = payload["meal_type"]
    if "occurred_at" in payload:
        updates["occurred_at"] = payload["occurred_at"]
    if "total_price" in payload:
        try:
            updates["total_price"] = float(payload["total_price"])
        except (TypeError, ValueError):
            return jsonify({"error": "total_price 必须是数字"}), 400
    if "recognized_foods" in payload:
        if not isinstance(payload["recognized_foods"], list):
            return jsonify({"error": "recognized_foods 必须是数组"}), 400
        updates["recognized_foods"] = payload["recognized_foods"]
    if not updates:
        return jsonify({"error": "没有可更新的字段"}), 400
    updated = database.update_meal(meal_id, updates)
    if updated is None:
        return jsonify({"error": "记录不存在"}), 404
    return jsonify(updated)


@meals_bp.get("/meals")
def get_meals():
    try:
        days = _parse_days()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    meal_type = request.args.get("meal_type") or None
    meals = _filter_meals_by_days(database.get_meals(DEFAULT_USER_ID), days)
    if meal_type:
        meals = [m for m in meals if m.get("meal_type") == meal_type]
    return jsonify({"days": days, "meal_count": len(meals), "meals": meals})


@meals_bp.get("/meals/stats")
def get_meal_stats():
    try:
        days = _parse_days(default=7)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    meals = _filter_meals_by_days(database.get_meals(DEFAULT_USER_ID), days)
    analysis = nutrition.analyze_recent_meals(meals)
    return jsonify({"days": days, **analysis})


def _parse_days(default=None):
    raw_days = request.args.get("days")
    if raw_days in (None, ""):
        return default
    try:
        days = int(raw_days)
    except ValueError as exc:
        raise ValueError("days 必须是正整数") from exc
    if days <= 0:
        raise ValueError("days 必须是正整数")
    return days


def _filter_meals_by_days(meals, days):
    if days is None:
        return meals

    now = datetime.now().astimezone()
    threshold = now - timedelta(days=days)
    return [
        meal
        for meal in meals
        if _parse_iso_datetime(meal.get("occurred_at")) >= threshold
    ]


def _parse_iso_datetime(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
