from lib import database, llm, nutrition, recommender, remark
from lib.llm import LLMError, LLMResponseError
from lib.profile import default_profile, get_profile


DEFAULT_USER_ID = "default_user"

# Only beverages are 饮品; true desserts (蛋糕/甜点) are 点心 — but most savory dim sum
# and salads belong to 主食. Categories not listed here fall through to 主食.
DRINK_CATEGORIES = {"饮料类"}
SNACK_CATEGORIES = {"甜品类"}   # Not present in current DB; reserved for future dessert dishes

MEAL_TYPE_LABELS = {
    "breakfast": "早餐",
    "lunch": "午餐",
    "dinner": "晚餐",
    "snack": "加餐",
}


class RecommendError(ValueError):
    pass


def _get_course_type(category):
    if category in DRINK_CATEGORIES:
        return "饮品"
    if category in SNACK_CATEGORIES:
        return "点心"
    return "主食"


def generate_next_meal_recommendation(payload):
    payload = payload or {}
    budget_range = _normalize_budget_range(payload.get("budget_range"))
    target = _resolve_target(payload.get("user_type", "self"), payload.get("contact_id"))
    extra_constraint = payload.get("extra_constraint") or ""
    exclude_dish_ids = payload.get("exclude_dish_ids") or []
    meal_type = payload.get("meal_type") or ""

    recent_meals = database.get_recent_meals(target["user_id"], limit=3)
    recent_meals_same_type = database.get_recent_meals_by_type(
        target["user_id"], meal_type=meal_type, limit=3
    ) if meal_type else []
    recent_analysis = nutrition.analyze_recent_meals(recent_meals)
    dishes = database.get_dishes()

    candidates = recommender.pre_filter(
        dishes,
        target["profile"],
        recent_analysis["recent_pattern"],
        budget_range,
        recent_meals,
    )

    existing_ids = {c.get("dish_id") for c in candidates}
    candidates_typed = [
        {**c, "course_type": _get_course_type(c.get("category", ""))}
        for c in candidates
    ]

    # Always include drink (and future dessert) candidates even if outside budget
    extra_typed = []
    for d in dishes:
        if d.get("dish_id") in existing_ids:
            continue
        if d.get("category") not in DRINK_CATEGORIES | SNACK_CATEGORIES:
            continue
        if recommender.is_allergen_conflict(d, target["profile"].get("avoid_ingredients")):
            continue
        extra_typed.append({**d, "score": 50, "course_type": _get_course_type(d.get("category", ""))})

    all_candidates = candidates_typed + extra_typed

    # Strict budget filter for 主食 only; drinks/snacks are add-ons
    eligible = [
        item for item in all_candidates
        if item.get("course_type") != "主食" or _price_in_budget(item.get("price"), budget_range)
    ]
    final_candidates = eligible or all_candidates

    mode = "llm"
    try:
        llm_result = llm.generate_recommendation(
            target["profile"],
            recent_meals,
            recent_analysis["recent_pattern"],
            final_candidates,
            budget_range,
            extra_constraint=extra_constraint,
            exclude_dish_ids=exclude_dish_ids,
            meal_type=meal_type,
            recent_meals_same_type=recent_meals_same_type,
        )
        recommendations = _sanitize_llm_recommendations(llm_result, final_candidates, budget_range, dishes)
        if not any(r.get("course_type") == "主食" for r in recommendations):
            recommendations = _merge_rule_recommendations(recommendations, final_candidates)
        nutrition_summary = llm_result.get("nutrition_summary") or recent_analysis["recent_pattern"]["summary"]
        health_tip = llm_result.get("health_tip") or "营养估算仅供参考，不构成医学建议。"
        budget_note = llm_result.get("budget_note") or _budget_note(budget_range)
    except (LLMError, LLMResponseError, ValueError, TypeError):
        mode = "rule_fallback"
        recommendations = _rule_recommendations(final_candidates)
        nutrition_summary = recent_analysis["recent_pattern"]["summary"]
        health_tip = "当前使用规则兜底推荐，营养估算仅供参考。"
        budget_note = _budget_note(budget_range)

    # Cap at 3 per course_type; deduplicate by dish_id
    type_counts = {}
    seen_ids = set()
    deduped = []
    for r in recommendations:
        ct = r.get("course_type", "主食")
        did = r.get("dish_id")
        if did in seen_ids:
            continue
        if type_counts.get(ct, 0) >= 3:
            continue
        seen_ids.add(did)
        type_counts[ct] = type_counts.get(ct, 0) + 1
        deduped.append(r)
    recommendations = deduped

    selected_dishes = [_candidate_for_recommendation(item, final_candidates) for item in recommendations]
    selected_dishes = [item for item in selected_dishes if item is not None]

    # Generate one remark per recommended dish
    raw_remarks = remark.generate_remarks_per_dish(target["profile"], selected_dishes)
    remark_by_id = {r["dish_id"]: r["remark"] for r in raw_remarks if isinstance(r, dict)}
    remarks_list = [
        {
            "dish_id": rec["dish_id"],
            "name": rec["name"],
            "course_type": rec.get("course_type", "主食"),
            "remark": remark_by_id.get(rec["dish_id"], "按正常口味制作，谢谢。"),
        }
        for rec in recommendations
    ]
    # Legacy single remark: join top-ranked item per category
    top_remarks = {}
    for r in remarks_list:
        ct = r["course_type"]
        if ct not in top_remarks:
            top_remarks[ct] = r["remark"]
    remark_text = " ".join(top_remarks.values())

    # Default total: sum of top-ranked item per category
    top_per_type = {}
    for r in recommendations:
        ct = r.get("course_type", "主食")
        if ct not in top_per_type:
            top_per_type[ct] = r
    total_estimated_price = round(sum(item.get("price") or 0 for item in top_per_type.values()), 1)

    record = database.add_recommendation(
        {
            "user_id": target["user_id"],
            "based_on_meal_ids": [meal["meal_id"] for meal in recent_meals],
            "recent_pattern": recent_analysis["recent_pattern"],
            "budget_range": budget_range,
            "recommendations": recommendations,
        }
    )

    return {
        "mode": mode,
        "target": {
            "user_id": target["user_id"],
            "user_type": target["user_type"],
            "name": target["profile"].get("name") or ("自己" if target["user_type"] == "self" else "亲友"),
        },
        "budget_range": budget_range,
        "recent_meals": recent_meals,
        "recent_meals_same_type": recent_meals_same_type,
        "recent_analysis": recent_analysis,
        "candidates": final_candidates[:10],
        "recommendations": recommendations,
        "total_estimated_price": total_estimated_price,
        "nutrition_summary": nutrition_summary,
        "health_tip": health_tip,
        "budget_note": budget_note,
        "remark": remark_text,
        "remarks": remarks_list,
        "record": record,
    }


def get_recommendation_records(user_id=DEFAULT_USER_ID):
    return database.get_recommendations(user_id)


def _resolve_target(user_type, contact_id):
    if user_type == "contact":
        if not contact_id:
            raise RecommendError("请选择亲友")
        contact = database.get_contact(contact_id)
        if contact is None:
            raise RecommendError("亲友档案不存在")
        return {
            "user_id": contact["contact_id"],
            "user_type": "contact",
            "profile": _profile_from_contact(contact),
        }

    profile = get_profile(DEFAULT_USER_ID)
    return {"user_id": DEFAULT_USER_ID, "user_type": "self", "profile": profile}


def _profile_from_contact(contact):
    return {
        **default_profile(contact["contact_id"]),
        "user_id": contact["contact_id"],
        "name": contact.get("name") or "",
        "taste_description": contact.get("taste_description") or "",
        "taste_tags": contact.get("taste_tags") or [],
        "avoid_ingredients": contact.get("avoid_ingredients") or [],
        "health_goals": contact.get("health_goals") or [],
        "default_budget": contact.get("default_budget") or {},
        "remark_habits": contact.get("remark_habits") or [],
    }


def _normalize_budget_range(value):
    if isinstance(value, dict):
        minimum = value.get("min", 15)
        maximum = value.get("max", 25)
    elif isinstance(value, (list, tuple)) and len(value) >= 2:
        minimum, maximum = value[0], value[1]
    else:
        minimum, maximum = 15, 25

    try:
        minimum = int(minimum)
        maximum = int(maximum)
    except (TypeError, ValueError) as exc:
        raise RecommendError("budget_range 必须是两个数字") from exc
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    return [max(0, minimum), max(0, maximum)]


def _price_in_budget(price, budget_range):
    try:
        value = float(price)
    except (TypeError, ValueError):
        return False
    return budget_range[0] <= value <= budget_range[1]


def _sanitize_llm_recommendations(llm_result, candidates, budget_range, all_dishes=None):
    if not isinstance(llm_result, dict):
        raise LLMResponseError("推荐结果必须是 JSON 对象")
    raw_items = llm_result.get("recommendations")
    if not isinstance(raw_items, list):
        raise LLMResponseError("recommendations 必须是数组")

    by_id = {item.get("dish_id"): item for item in candidates}
    by_name = {item.get("name"): item for item in candidates}
    result = []
    seen_ids = set()
    type_counts = {}
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        candidate = by_id.get(raw.get("dish_id")) or by_name.get(raw.get("name"))

        if candidate is not None:
            # Candidate-based recommendation
            if candidate.get("dish_id") in seen_ids:
                continue
            course_type = _get_course_type(candidate.get("category", ""))
            if type_counts.get(course_type, 0) >= 3:
                continue
            if course_type == "主食" and not _price_in_budget(candidate.get("price"), budget_range):
                continue
            seen_ids.add(candidate["dish_id"])
            type_counts[course_type] = type_counts.get(course_type, 0) + 1
            result.append(_recommendation_from_candidate(candidate, raw))
        else:
            # Free-form recommendation: LLM suggested a dish not in candidates
            name = (raw.get("name") or "").strip()
            if not name:
                continue
            # If the name matches a DB dish that was filtered out (allergen/budget), skip it
            all_by_name = {d.get("name"): d for d in (all_dishes or [])}
            if name in all_by_name:
                continue
            virtual_id = f"llm-{name}"
            if virtual_id in seen_ids:
                continue
            category = raw.get("category") or ""
            course_type = raw.get("course_type") or _get_course_type(category)
            if course_type not in ("主食", "饮品", "点心"):
                course_type = _get_course_type(category)
            if type_counts.get(course_type, 0) >= 3:
                continue
            try:
                price = float(raw.get("price") or 0)
            except (TypeError, ValueError):
                price = 0
            if course_type == "主食" and not _price_in_budget(price, budget_range):
                continue
            seen_ids.add(virtual_id)
            type_counts[course_type] = type_counts.get(course_type, 0) + 1
            result.append({
                "dish_id": virtual_id,
                "name": name,
                "course_type": course_type,
                "category": category,
                "ingredients": raw.get("ingredients") or [],
                "estimated_nutrition": raw.get("estimated_nutrition") or {},
                "nutrition_tags": [],
                "remark_rules": [],
                "score": int(raw.get("score") or 0),
                "price": price,
                "reason": raw.get("reason") or "LLM 个性化推荐",
                "nutrition_highlight": raw.get("nutrition_highlight") or "",
                "is_llm_free": True,
            })
    return result


def _merge_rule_recommendations(existing, candidates):
    result = list(existing)
    seen_ids = {item["dish_id"] for item in result}
    type_counts = {item.get("course_type", "主食"): 1 for item in result}
    for candidate in candidates:
        if candidate.get("dish_id") in seen_ids:
            continue
        ct = _get_course_type(candidate.get("category", ""))
        if type_counts.get(ct, 0) >= 3:
            continue
        result.append(_recommendation_from_candidate(candidate))
        seen_ids.add(candidate.get("dish_id"))
        type_counts[ct] = type_counts.get(ct, 0) + 1
        if sum(type_counts.values()) >= 9:
            break
    return result


def _rule_recommendations(candidates):
    type_counts = {}
    result = []
    for c in candidates:
        ct = _get_course_type(c.get("category", ""))
        if type_counts.get(ct, 0) < 3:
            type_counts[ct] = type_counts.get(ct, 0) + 1
            result.append(_recommendation_from_candidate(c))
        if sum(type_counts.values()) >= 9:
            break
    return result


def _recommendation_from_candidate(candidate, raw=None):
    raw = raw or {}
    course_type = (
        raw.get("course_type")
        or candidate.get("course_type")
        or _get_course_type(candidate.get("category", ""))
    )
    return {
        "dish_id": candidate.get("dish_id"),
        "name": candidate.get("name"),
        "course_type": course_type,
        "score": int(raw.get("score") or candidate.get("score") or 0),
        "price": candidate.get("price") or raw.get("price") or 0,
        "reason": raw.get("reason")
        or f"规则预筛选得分 {int(candidate.get('score') or 0)}，符合当前预算与画像约束。",
        "nutrition_highlight": raw.get("nutrition_highlight")
        or "、".join((candidate.get("nutrition_tags") or [])[:3])
        or "营养估算仅供参考",
        "estimated_nutrition": candidate.get("estimated_nutrition") or {},
    }


def _candidate_for_recommendation(recommendation, candidates):
    for candidate in candidates:
        if candidate.get("dish_id") == recommendation.get("dish_id"):
            return candidate
    if recommendation.get("is_llm_free"):
        return {
            "dish_id": recommendation.get("dish_id"),
            "name": recommendation.get("name"),
            "category": recommendation.get("category", ""),
            "ingredients": recommendation.get("ingredients", []),
            "estimated_nutrition": recommendation.get("estimated_nutrition", {}),
            "nutrition_tags": [],
            "remark_rules": [],
            "price": recommendation.get("price", 0),
            "is_llm_free": True,
        }
    return None


def _budget_note(budget_range):
    return f"本次主食预算区间为 {budget_range[0]}-{budget_range[1]} 元。"
