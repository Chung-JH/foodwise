from copy import deepcopy

from lib import database, llm


DEFAULT_USER_ID = "default_user"
DEFAULT_BUDGET = {
    "breakfast": [8, 15],
    "lunch": [15, 30],
    "dinner": [20, 40],
}


def default_profile(user_id=DEFAULT_USER_ID):
    return {
        "user_id": user_id,
        "name": "",
        "taste_description": "",
        "taste_tags": [],
        "avoid_ingredients": [],
        "health_goals": [],
        "body_data": {},
        "default_budget": deepcopy(DEFAULT_BUDGET),
        "remark_habits": [],
        "created_at": None,
        "updated_at": None,
    }


def get_profile(user_id=DEFAULT_USER_ID):
    stored = database.get_user(user_id)
    if stored is None:
        return default_profile(user_id)
    return {**default_profile(user_id), **stored}


def save_profile(payload, user_id=DEFAULT_USER_ID):
    if not isinstance(payload, dict):
        raise ValueError("请求体必须是 JSON 对象")

    taste_description = _clean_text(payload.get("taste_description"))
    current = get_profile(user_id)
    current_desc = current.get("taste_description", "")

    if taste_description and taste_description != current_desc:
        # Description changed — regenerate tags via LLM
        taste_tags = _parse_taste_tags(taste_description)
    elif "taste_tags" in payload and isinstance(payload["taste_tags"], list):
        # Description unchanged — use manually edited tags from payload
        taste_tags = _to_text_list(payload["taste_tags"])
    else:
        taste_tags = current.get("taste_tags", [])

    profile = {
        **current,
        "user_id": user_id,
        "name": _clean_text(payload.get("name")),
        "taste_description": taste_description,
        "taste_tags": taste_tags,
        "avoid_ingredients": _to_text_list(payload.get("avoid_ingredients")),
        "health_goals": _to_text_list(payload.get("health_goals")),
        "body_data": payload.get("body_data") if isinstance(payload.get("body_data"), dict) else {},
        "default_budget": _normalize_budget(payload.get("default_budget")),
        "remark_habits": _to_text_list(payload.get("remark_habits")),
    }
    return database.save_user(profile)


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _to_text_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.replace("，", ",").split(",")
    elif isinstance(value, list):
        raw_items = value
    else:
        raw_items = [value]

    result = []
    seen = set()
    for item in raw_items:
        text = _clean_text(item)
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _normalize_budget(value):
    if not isinstance(value, dict):
        return deepcopy(DEFAULT_BUDGET)

    normalized = {}
    for meal_type, default_range in DEFAULT_BUDGET.items():
        item = value.get(meal_type, default_range)
        normalized[meal_type] = _normalize_budget_range(item, default_range)
    return normalized


def _normalize_budget_range(value, default_range):
    if isinstance(value, dict):
        min_value = value.get("min", default_range[0])
        max_value = value.get("max", default_range[1])
    elif isinstance(value, (list, tuple)) and len(value) >= 2:
        min_value, max_value = value[0], value[1]
    else:
        min_value, max_value = default_range

    try:
        min_value = int(min_value)
        max_value = int(max_value)
    except (TypeError, ValueError):
        min_value, max_value = default_range

    min_value = max(0, min_value)
    max_value = max(0, max_value)
    if min_value > max_value:
        min_value, max_value = max_value, min_value
    return [min_value, max_value]


def _parse_taste_tags(taste_description):
    if not taste_description:
        return []
    tags = llm.parse_taste_text(taste_description)
    if not isinstance(tags, list):
        raise ValueError("taste_tags 必须是数组")
    return _to_text_list(tags)
