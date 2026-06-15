from lib import llm
from lib.llm import LLMError, LLMResponseError


CATEGORY_REMARKS = {
    "盖饭类": ["米饭少一点"],
    "粉面类": ["汤少一点"],
    "轻食类": ["酱料分开放"],
    "麻辣类": ["微辣"],
}


def generate_remarks_per_dish(user_profile, dishes) -> list:
    """Generate one remark per dish; returns [{dish_id, remark}, ...]."""
    try:
        result = llm.generate_remarks_for_dishes(user_profile or {}, dishes or [])
        validated = []
        for item in result:
            if isinstance(item, dict) and item.get("dish_id") and item.get("remark"):
                validated.append({"dish_id": item["dish_id"], "remark": str(item["remark"])})
        if validated:
            return validated
    except (LLMError, LLMResponseError, ValueError, TypeError):
        pass
    # Rule fallback
    return [
        {"dish_id": d.get("dish_id"), "remark": _generate_remark_rule(user_profile, [d])}
        for d in (dishes or [])
    ]


def generate_remark(user_profile, dishes, use_llm=True) -> str:
    if use_llm:
        try:
            text = _generate_remark_llm(user_profile, dishes)
            return _ensure_required_parts(text, user_profile)
        except LLMError:
            pass
    return _generate_remark_rule(user_profile, dishes)


def _generate_remark_llm(user_profile, dishes) -> str:
    category = _primary_category(dishes)
    return llm.generate_remark(user_profile or {}, dishes or [], category)


def _generate_remark_rule(user_profile, dishes) -> str:
    user_profile = user_profile or {}
    dishes = dishes or []

    parts = []
    parts.extend(_as_list(user_profile.get("remark_habits")))
    parts.extend(_avoid_parts(user_profile.get("avoid_ingredients")))
    for item in dishes:
        parts.extend(_as_list(item.get("remark_rules")))
    for item in dishes:
        parts.extend(CATEGORY_REMARKS.get(item.get("category"), []))

    parts = _unique_clean(parts)
    if not parts:
        parts = ["按正常口味制作"]
    return _ensure_thanks("，".join(parts))


def _primary_category(dishes):
    for dish in dishes or []:
        if dish.get("category"):
            return dish["category"]
    return ""


def _avoid_parts(avoid_ingredients):
    parts = []
    for item in _as_list(avoid_ingredients):
        if item.startswith(("不要", "不吃", "忌")):
            parts.append(item)
        else:
            parts.append(f"不要{item}")
    return parts


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.replace("，", ",").split(",")]
    if isinstance(value, list):
        return [str(item).strip() for item in value]
    return [str(value).strip()]


def _unique_clean(values):
    result = []
    seen = set()
    for value in values:
        text = str(value).strip().strip("，,。 ")
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _ensure_thanks(text):
    text = str(text or "").strip().rstrip("，,。 ")
    if not text:
        text = "按正常口味制作"
    if text.endswith("谢谢"):
        return f"{text}。"
    if "谢谢" in text:
        return f"{text}。" if not text.endswith("。") else text
    return f"{text}，谢谢。"


def _ensure_required_parts(text, user_profile):
    text = _ensure_thanks(text)
    required_parts = _avoid_parts((user_profile or {}).get("avoid_ingredients"))
    missing_parts = [part for part in required_parts if part not in text]
    if not missing_parts:
        return text

    body = text.rstrip("。")
    if body.endswith("谢谢"):
        body = body[: -len("谢谢")].rstrip("，, ")
    parts = _unique_clean([body, *missing_parts])
    return _ensure_thanks("，".join(parts))
