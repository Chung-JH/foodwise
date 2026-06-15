from datetime import datetime


VALID_TIME_RESOLUTIONS = {"explicit", "inferred", "defaulted", "unknown"}

DEFAULT_MEAL_TIMES = {
    "breakfast": "08:00",
    "lunch": "12:30",
    "dinner": "19:30",
    "snack": "22:30",
}


def _parse_iso_datetime(value, field_name):
    if not value:
        raise ValueError(f"{field_name} 不能为空")

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} 必须是完整 ISO-8601 日期时间") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} 必须带时区")

    return parsed


def validate_meal_time(meal_time: dict) -> bool:
    if not isinstance(meal_time, dict):
        raise ValueError("meal_time 必须是对象")

    occurred_at = meal_time.get("occurred_at")
    _parse_iso_datetime(occurred_at, "occurred_at")

    time_assumption = meal_time.get("time_assumption")
    if not isinstance(time_assumption, dict):
        raise ValueError("time_assumption 不能为空")

    resolved_occurred_at = time_assumption.get("resolved_occurred_at")
    _parse_iso_datetime(resolved_occurred_at, "resolved_occurred_at")

    if occurred_at != resolved_occurred_at:
        raise ValueError("occurred_at 与 resolved_occurred_at 不一致")

    time_resolution = meal_time.get("time_resolution")
    if time_resolution not in VALID_TIME_RESOLUTIONS:
        raise ValueError("time_resolution 不合法")

    if time_resolution == "unknown":
        raise ValueError("无法判断用餐时间，请用户补充")

    confidence = time_assumption.get("confidence")
    if not isinstance(confidence, (int, float)):
        raise ValueError("时间置信度必须在 0 到 1 之间")
    if confidence < 0 or confidence > 1:
        raise ValueError("时间置信度必须在 0 到 1 之间")

    return True


def get_default_meal_time(meal_type: str) -> str:
    if meal_type not in DEFAULT_MEAL_TIMES:
        raise ValueError("meal_type 不合法")
    return DEFAULT_MEAL_TIMES[meal_type]


def sort_meals_by_time(meals: list) -> list:
    return sorted(
        meals,
        key=lambda meal: _parse_iso_datetime(meal.get("occurred_at"), "occurred_at"),
        reverse=True,
    )
