from copy import deepcopy


MOCK_TASTE_TAGS = ["微辣", "川菜", "汤类", "少油"]


MOCK_MEAL_RESPONSE = {
    "meal_time": {
        "occurred_at": "2026-06-12T19:30:00+08:00",
        "meal_type": "dinner",
        "time_resolution": "inferred",
        "time_assumption": {
            "raw_time_text": "昨天晚上",
            "resolved_occurred_at": "2026-06-12T19:30:00+08:00",
            "timezone": "Asia/Shanghai",
            "date_source": "由当前时间推断昨天日期",
            "time_source": "晚上默认 19:30",
            "default_rule": "早餐=08:00，午餐=12:30，晚餐=19:30，夜宵=22:30",
            "confidence": 0.75,
        },
    },
    "recognized_foods": [
        {
            "raw_text": "炸鸡汉堡套餐",
            "standard_name": "炸鸡汉堡套餐",
            "category": "快餐油炸类",
            "portion": "一份",
            "estimated_nutrition": {
                "calories_kcal": 950,
                "protein_g": 35,
                "fat_g": 45,
                "carbs_g": 110,
                "sugar_g": 18,
                "fiber_g": 3,
                "sodium_mg": 1200,
            },
            "levels": {
                "calorie_level": "high",
                "protein_level": "medium",
                "fat_level": "high",
                "carbs_level": "high",
                "sodium_level": "high",
                "vegetable_level": "low",
            },
            "nutrition_tags": ["高热量", "高脂肪", "高碳水", "蔬菜偏少"],
            "confidence": 0.82,
            "assumption": "按常见外卖一份炸鸡汉堡套餐估算",
        }
    ],
}


MOCK_DISH_PHOTO_RESPONSE = {
    "dish_name": "番茄牛肉饭",
    "ingredients": ["牛肉", "番茄", "米饭", "鸡蛋"],
    "category": "盖饭类",
    "estimated_nutrition": {
        "calories_kcal": 650,
        "protein_g": 28,
        "fat_g": 18,
        "carbs_g": 85,
        "sugar_g": 8,
        "fiber_g": 4,
        "sodium_mg": 980,
    },
    "levels": {
        "calorie_level": "medium",
        "protein_level": "medium",
        "fat_level": "medium",
        "carbs_level": "medium",
        "sodium_level": "medium",
        "vegetable_level": "medium",
    },
    "nutrition_tags": ["蛋白质较高", "油脂适中", "热量适中"],
    "taste_tags": ["酸甜", "咸香"],
    "suitable_goals": ["高蛋白", "均衡饮食"],
    "remark_rules": ["少油", "米饭少一点"],
    "price": 25,
    "price_source": "image_recognized",
    "confidence": 0.85,
    "assumption": "按常见外卖一份番茄牛肉饭估算",
}


MOCK_RECOMMENDATION_RESPONSE = {
    "recommendations": [
        # 主食 Top 3
        {
            "dish_id": "preset-gaifan-002",
            "name": "番茄牛肉饭",
            "course_type": "主食",
            "score": 92,
            "price": 26,
            "reason": "近期蔬菜偏少，番茄补充维生素，牛肉提供蛋白质，符合午餐营养需求。",
            "nutrition_highlight": "高蛋白、蔬菜适中",
        },
        {
            "dish_id": "preset-noodle-001",
            "name": "兰州牛肉面",
            "course_type": "主食",
            "score": 85,
            "price": 18,
            "reason": "脂肪较低，口味清爽，适合近期偏油饮食后的平衡。",
            "nutrition_highlight": "脂肪较低、蛋白质适中",
        },
        {
            "dish_id": "preset-salad-001",
            "name": "鸡胸肉沙拉",
            "course_type": "主食",
            "score": 78,
            "price": 28,
            "reason": "高蛋白低脂，补充膳食纤维，适合控制热量。",
            "nutrition_highlight": "高蛋白、低脂、蔬菜较多",
        },
        # 饮品 Top 3
        {
            "dish_id": "preset-drink-001",
            "name": "无糖豆浆",
            "course_type": "饮品",
            "score": 85,
            "price": 6,
            "reason": "无糖植物蛋白饮品，搭配主食不增加额外热量。",
            "nutrition_highlight": "低糖、植物蛋白",
        },
        {
            "dish_id": "preset-drink-004",
            "name": "低糖酸奶",
            "course_type": "饮品",
            "score": 78,
            "price": 9,
            "reason": "补充益生菌和钙质，低糖不增加负担。",
            "nutrition_highlight": "低糖、含益生菌",
        },
        {
            "dish_id": "preset-drink-002",
            "name": "美式咖啡",
            "course_type": "饮品",
            "score": 68,
            "price": 12,
            "reason": "午后提神，热量低，适合下午餐饮。",
            "nutrition_highlight": "低热量、提神",
        },
    ],
    "nutrition_summary": "建议主食选择高蛋白少油品类，饮品以低糖为主。",
    "health_tip": "营养估算仅供参考，不构成医学建议。",
    "budget_note": "主食在 15-25 元预算内，饮品为可选搭配。",
}


def parse_taste_text(taste_description):
    return list(MOCK_TASTE_TAGS)


def parse_meal_record(user_input, current_time):
    return deepcopy(MOCK_MEAL_RESPONSE)


def analyze_dish_photo(image_path):
    return deepcopy(MOCK_DISH_PHOTO_RESPONSE)


def generate_recommendation(
    user_profile, recent_meals, recent_pattern, candidate_dishes, budget_range
):
    return deepcopy(MOCK_RECOMMENDATION_RESPONSE)


def generate_remarks_for_dishes(user_profile, dishes):
    avoid = user_profile.get("avoid_ingredients") or []
    habits = user_profile.get("remark_habits") or []
    avoid_str = "，".join(f"不要{a}" for a in avoid if a)
    _category_hints = {
        "盖饭类": "米饭少一点",
        "粉面类": "汤少一点",
        "轻食类": "酱料分开放",
        "麻辣类": "微辣",
        "面点类": "皮薄多汁",
        "饮料类": "常温",
    }
    result = []
    for dish in dishes or []:
        parts = list(habits)
        if avoid_str:
            parts.append(avoid_str)
        hint = _category_hints.get(dish.get("category", ""))
        if hint:
            parts.append(hint)
        remark = ("，".join(parts) if parts else "按正常口味制作") + "，谢谢。"
        result.append({"dish_id": dish.get("dish_id"), "remark": remark})
    return result


def generate_remark(user_profile, dishes, dish_category):
    avoid_ingredients = user_profile.get("avoid_ingredients", [])
    habits = user_profile.get("remark_habits", [])
    parts = list(dict.fromkeys([*habits, *(f"不要{item}" for item in avoid_ingredients)]))
    if dish_category == "盖饭类":
        parts.append("米饭少一点")
    elif dish_category == "粉面类":
        parts.append("汤少一点")
    elif dish_category == "轻食类":
        parts.append("酱料分开")
    return "，".join(dict.fromkeys(parts)) + "，谢谢。"
