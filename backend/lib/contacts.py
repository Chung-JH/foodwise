from lib import database, llm
from lib.profile import DEFAULT_BUDGET


DEFAULT_OWNER_ID = "default_user"


def list_contacts(owner_user_id=DEFAULT_OWNER_ID):
    return database.get_contacts(owner_user_id)


def create_contact(payload, owner_user_id=DEFAULT_OWNER_ID):
    data = _normalize_payload(payload)
    return database.add_contact({**data, "owner_user_id": owner_user_id})


def update_contact(contact_id, payload):
    if not database.get_contact(contact_id):
        return None
    data = _normalize_payload(payload)
    return database.update_contact(contact_id, data)


def delete_contact(contact_id):
    return database.delete_contact(contact_id)


def _normalize_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("请求体必须是 JSON 对象")

    name = _clean_text(payload.get("name"))
    if not name:
        raise ValueError("亲友姓名不能为空")

    taste_description = _clean_text(payload.get("taste_description"))
    return {
        "name": name,
        "taste_description": taste_description,
        "taste_tags": _parse_taste_tags(taste_description, payload.get("taste_tags")),
        "avoid_ingredients": _to_text_list(payload.get("avoid_ingredients")),
        "health_goals": _to_text_list(payload.get("health_goals")),
        "default_budget": _normalize_budget(payload.get("default_budget")),
        "remark_habits": _to_text_list(payload.get("remark_habits")),
    }


def _parse_taste_tags(taste_description, fallback):
    if taste_description:
        tags = llm.parse_taste_text(taste_description)
        return _to_text_list(tags)
    return _to_text_list(fallback)


def _normalize_budget(value):
    if not isinstance(value, dict):
        return {key: list(item) for key, item in DEFAULT_BUDGET.items()}
    result = {}
    for meal_type, default_range in DEFAULT_BUDGET.items():
        item = value.get(meal_type, default_range)
        if isinstance(item, dict):
            raw_min = item.get("min", default_range[0])
            raw_max = item.get("max", default_range[1])
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            raw_min, raw_max = item[0], item[1]
        else:
            raw_min, raw_max = default_range
        try:
            min_value = int(raw_min)
            max_value = int(raw_max)
        except (TypeError, ValueError):
            min_value, max_value = default_range
        if min_value > max_value:
            min_value, max_value = max_value, min_value
        result[meal_type] = [max(0, min_value), max(0, max_value)]
    return result


def _to_text_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        items = value.replace("，", ",").split(",")
    elif isinstance(value, list):
        items = value
    else:
        items = [value]

    result = []
    seen = set()
    for item in items:
        text = _clean_text(item)
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()
