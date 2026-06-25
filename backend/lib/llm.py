import base64
import json
import mimetypes
import os
from pathlib import Path

from openai import OpenAI

from lib import mock_llm


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = BASE_DIR / "config" / "llm_config.json"
DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

ALLOWED_DISH_CATEGORIES = {
    "盖饭类",
    "粉面类",
    "轻食类",
    "快餐油炸类",
    "麻辣类",
    "汤粥类",
    "家常菜类",
    "面点类",
    "饮料类",
}


DISH_PHOTO_SYSTEM_PROMPT = """你是一个菜品识别与营养估算助手。根据用户上传的菜品照片或菜单截图，识别菜品并估算营养和价格。

只返回 JSON，严格按照以下示例格式，不允许输出任何其他文字或 Markdown：

{
  "dish_name": "番茄牛肉饭",
  "ingredients": ["牛肉", "番茄", "米饭"],
  "category": "盖饭类",
  "estimated_nutrition": {
    "calories_kcal": 650,
    "protein_g": 28,
    "fat_g": 18,
    "carbs_g": 85,
    "sugar_g": 8,
    "fiber_g": 4,
    "sodium_mg": 980
  },
  "levels": {
    "calorie_level": "medium",
    "protein_level": "medium",
    "fat_level": "medium",
    "carbs_level": "medium",
    "sodium_level": "medium",
    "vegetable_level": "medium"
  },
  "nutrition_tags": ["蛋白质较高", "油脂适中", "热量适中"],
  "taste_tags": ["酸甜", "咸香"],
  "suitable_goals": ["高蛋白", "均衡饮食"],
  "remark_rules": ["少油", "米饭少一点"],
  "price": 25,
  "price_source": "llm_estimated",
  "confidence": 0.85,
  "assumption": "按常见外卖一份番茄牛肉饭估算"
}

规则：
- category 只能是：盖饭类 / 粉面类 / 轻食类 / 快餐油炸类 / 麻辣类 / 汤粥类 / 家常菜类 / 面点类 / 饮料类
- levels 中每个字段只能是 low / medium / high
- estimated_nutrition 必须包含全部 7 个字段，均为数值
- 图片有价格时 price_source 为 "image_recognized"，否则为 "llm_estimated"
- confidence 为 0~1 的小数
- 只做粗略估算，不提供医学建议"""


MEAL_RECORD_SYSTEM_PROMPT = """你是一个饮食记录解析与营养估算助手。根据用户的自然语言饮食描述，识别时间、餐次、菜品，估算营养信息。

只返回 JSON，严格按照以下示例格式，不允许输出任何其他文字或 Markdown：

{
  "meal_time": {
    "occurred_at": "2026-06-14T19:30:00+08:00",
    "meal_type": "dinner",
    "time_resolution": "inferred",
    "time_assumption": {
      "raw_time_text": "今天晚上",
      "resolved_occurred_at": "2026-06-14T19:30:00+08:00",
      "timezone": "Asia/Shanghai",
      "date_source": "当前日期",
      "time_source": "晚餐默认 19:30",
      "default_rule": "早餐=08:00，午餐=12:30，晚餐=19:30，夜宵=22:30",
      "confidence": 0.9
    }
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
        "sodium_mg": 1200
      },
      "levels": {
        "calorie_level": "high",
        "protein_level": "medium",
        "fat_level": "high",
        "carbs_level": "high",
        "sodium_level": "high",
        "vegetable_level": "low"
      },
      "nutrition_tags": ["高热量", "高脂肪", "高碳水", "蔬菜偏少"],
      "price": 32,
      "price_source": "llm_estimated",
      "confidence": 0.82,
      "assumption": "按常见外卖一份炸鸡汉堡套餐估算"
    }
  ]
}

规则：
- meal_type 只能是 breakfast / lunch / dinner / snack 之一
- occurred_at 与 resolved_occurred_at 必须完全一致，格式为含时区的 ISO-8601
- 若用户未说明时间，按默认餐次时间推断：早餐=08:00，午餐=12:30，晚餐=19:30，夜宵=22:30
- category 只能是：盖饭类 / 粉面类 / 轻食类 / 快餐油炸类 / 麻辣类 / 汤粥类 / 家常菜类 / 面点类 / 饮料类
- levels 中每个字段只能是 low / medium / high，键名固定为 calorie_level / protein_level / fat_level / carbs_level / sodium_level / vegetable_level
- estimated_nutrition 必须包含全部 7 个字段（calories_kcal / protein_g / fat_g / carbs_g / sugar_g / fiber_g / sodium_mg），均为数值
- price 为该菜品在中国常见外卖平台的估算单价（人民币元），price_source 固定为 "llm_estimated"
- 有多道菜品时，recognized_foods 包含多个对象
- 只做粗略估算，不提供医学建议"""


RECOMMENDATION_SYSTEM_PROMPT = """你是一个个性化外卖推荐助手，熟悉中国饮食习惯。根据用户画像、本次餐型、同餐型历史记录和候选菜品，推荐主食 Top3、饮品 Top3 和点心 Top3（若有）。

只返回 JSON，严格按照以下示例格式，不允许输出任何其他文字或 Markdown：

{
  "recommendations": [
    {
      "dish_id": "preset-gaifan-002",
      "name": "番茄牛肉饭",
      "course_type": "主食",
      "score": 92,
      "price": 26,
      "reason": "近期蔬菜偏少，番茄补充维生素，牛肉提供蛋白质，符合午餐营养需求。",
      "nutrition_highlight": "高蛋白、蔬菜适中"
    },
    {
      "dish_id": "preset-noodle-001",
      "name": "兰州牛肉面",
      "course_type": "主食",
      "score": 85,
      "price": 18,
      "reason": "脂肪较低，口味清爽，适合近期偏油饮食后的平衡。",
      "nutrition_highlight": "脂肪较低、蛋白质适中"
    },
    {
      "dish_id": "preset-salad-001",
      "name": "鸡胸肉沙拉",
      "course_type": "主食",
      "score": 78,
      "price": 28,
      "reason": "高蛋白低脂，补充膳食纤维，适合控制热量。",
      "nutrition_highlight": "高蛋白、低脂、蔬菜较多"
    },
    {
      "dish_id": "preset-drink-001",
      "name": "无糖豆浆",
      "course_type": "饮品",
      "score": 85,
      "price": 6,
      "reason": "无糖植物蛋白饮品，搭配主食不增加额外热量。",
      "nutrition_highlight": "低糖、植物蛋白"
    },
    {
      "dish_id": "preset-drink-004",
      "name": "低糖酸奶",
      "course_type": "饮品",
      "score": 78,
      "price": 9,
      "reason": "补充益生菌和钙质，低糖不增加负担。",
      "nutrition_highlight": "低糖、含益生菌"
    },
    {
      "dish_id": "preset-drink-002",
      "name": "美式咖啡",
      "course_type": "饮品",
      "score": 68,
      "price": 12,
      "reason": "午后提神，热量低，可搭配轻食。",
      "nutrition_highlight": "低热量、提神"
    }
  ],
  "nutrition_summary": "建议主食选择高蛋白少油品类，饮品以低糖为主。",
  "health_tip": "营养估算仅供参考，不构成医学建议。",
  "budget_note": "主食在预算区间内，饮品为可选搭配。"
}

餐型约束（最高优先级）：
- 早餐（breakfast）：清淡易消化为主，优先粥/豆浆/鸡蛋/包子/煎饼/面包等；避免重油、辛辣、高热量油炸食品
- 午餐（lunch）：保证充足能量，蛋白质丰富、饱腹感强；主食+菜品组合，热量可适当偏高
- 晚餐（dinner）：偏清淡低热量，减少高脂高碳水；避免重油、辛辣；适合汤品、轻食、蔬菜丰富的菜品
- 加餐（snack）：避免与同日正餐重复；分量适中不宜过饱；可考虑下午茶场景（甜品/饮品/轻食）或夜宵场景（热汤/粥/小食）；口味和品类应有变化

其他规则：
- 优先从候选菜品中推荐；若候选菜品不足或无法满足用户需求，可自由推荐其他合理菜品
- 推荐候选菜品时：dish_id 使用候选列表中的值，price 也使用候选列表中的价格
- 自由推荐时：dish_id 填写 ""，必须同时提供 category（只能取：盖饭类/粉面类/轻食类/快餐油炸类/麻辣类/汤粥类/家常菜类/面点类/饮料类 之一）、ingredients（主要食材列表，3-5 项）和合理的 price 估算
- course_type 只能是：主食 / 饮品 / 点心
- 点心仅指甜品类（蛋糕、甜面包、甜点、冰淇淋）；沙拉、轻食碗、包子、饺子、煎饼属于主食
- 每种 course_type 最多推荐 3 个，按 score 从高到低排列
- 主食必须有（至少 1 个，尽量 3 个）；候选中有饮料类则推荐饮品；有甜品类才推荐点心
- score 为 0~100 的整数，越高越优先；同等条件下，更换近期重复品类的菜品得分更高
- 不推荐含用户忌口食材的菜品
- 不提供医学建议"""


class LLMError(RuntimeError):
    pass


class LLMConfigError(LLMError):
    pass


class LLMResponseError(LLMError):
    pass


def _coerce_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _load_config_file():
    config_path = Path(os.getenv("MEALMATE_LLM_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    if not config_path.exists():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise LLMConfigError("LLM 配置 JSON 格式不合法") from exc


def _load_llm_config():
    file_config = _load_config_file()

    api_key = os.getenv("DASHSCOPE_API_KEY") or file_config.get("api_key")
    if api_key == "your_api_key_here":
        api_key = None

    return {
        "dashscope_base_url": os.getenv("DASHSCOPE_BASE_URL")
        or file_config.get("dashscope_base_url")
        or DEFAULT_DASHSCOPE_BASE_URL,
        "api_key": api_key,
        "qwen_vl_model": os.getenv("QWEN_VL_MODEL")
        or file_config.get("qwen_vl_model")
        or "qwen-vl-plus",
        "qwen_text_model": os.getenv("QWEN_TEXT_MODEL")
        or file_config.get("qwen_text_model")
        or "qwen-plus",
        "use_mock_llm": _coerce_bool(
            os.getenv("USE_MOCK_LLM", file_config.get("use_mock_llm")), default=True
        ),
    }


def _use_mock_llm():
    return _load_llm_config()["use_mock_llm"]


def _validate_json_response(response):
    if isinstance(response, dict):
        return response
    if not isinstance(response, str):
        raise LLMResponseError("模型返回不是合法 JSON")
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError as exc:
        raise LLMResponseError("模型返回不是合法 JSON") from exc
    if not isinstance(parsed, dict):
        raise LLMResponseError("模型返回 JSON 必须是对象")
    return parsed


def _client_and_config():
    config = _load_llm_config()
    if not config["api_key"]:
        raise LLMConfigError("缺少 DASHSCOPE_API_KEY，请在 config/llm_config.json 中配置")
    return OpenAI(api_key=config["api_key"], base_url=config["dashscope_base_url"]), config


def _call_qwen_text(system_prompt, user_prompt) -> dict:
    client, config = _client_and_config()
    try:
        response = client.chat.completions.create(
            model=config["qwen_text_model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise LLMError(f"调用千问文本模型失败：{exc}") from exc

    content = response.choices[0].message.content
    return _validate_json_response(content)


def _image_to_content_url(image_path_or_base64):
    value = str(image_path_or_base64)
    if value.startswith("data:image/") or value.startswith("http://") or value.startswith(
        "https://"
    ):
        return value

    path = Path(value)
    if path.exists():
        mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    return f"data:image/jpeg;base64,{value}"


def _call_qwen_vl(system_prompt, image_path_or_base64, user_prompt) -> dict:
    client, config = _client_and_config()
    image_url = _image_to_content_url(image_path_or_base64)
    try:
        response = client.chat.completions.create(
            model=config["qwen_vl_model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise LLMError(f"调用千问 VL 模型失败：{exc}") from exc

    content = response.choices[0].message.content
    return _validate_json_response(content)


def parse_taste_text(taste_description) -> list[str]:
    if _use_mock_llm():
        return mock_llm.parse_taste_text(taste_description)

    result = _call_qwen_text(
        "你是口味偏好结构化助手。请把用户的自然语言口味描述解析为 JSON，只返回 taste_tags 数组。",
        f"用户口味描述：{taste_description}\n请返回 JSON：{{\"taste_tags\": []}}",
    )
    tags = result.get("taste_tags")
    if not isinstance(tags, list):
        raise LLMResponseError("taste_tags 必须是数组")
    return [str(tag) for tag in tags]


def parse_meal_record(user_input, current_time) -> dict:
    if _use_mock_llm():
        return mock_llm.parse_meal_record(user_input, current_time)

    user_prompt = f"""当前时间：{current_time}
时区：Asia/Shanghai

饮食记录：{user_input}"""
    return _call_qwen_text(MEAL_RECORD_SYSTEM_PROMPT, user_prompt)


def analyze_dish_photo(image_path) -> dict:
    if _use_mock_llm():
        return mock_llm.analyze_dish_photo(image_path)

    user_prompt = "请分析这张菜品照片或菜单截图，返回菜名、食材、营养估算、价格和置信度 JSON。"
    return _call_qwen_vl(DISH_PHOTO_SYSTEM_PROMPT, image_path, user_prompt)


def generate_recommendation(
    user_profile, recent_meals, recent_pattern, candidate_dishes, budget_range,
    extra_constraint=None, exclude_dish_ids=None, meal_type=None,
    recent_meals_same_type=None,
) -> dict:
    if _use_mock_llm():
        return mock_llm.generate_recommendation(
            user_profile, recent_meals, recent_pattern, candidate_dishes, budget_range
        )

    meal_type_labels = {
        "breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "snack": "加餐",
    }
    meal_type_label = meal_type_labels.get(meal_type, "") if meal_type else ""

    extra_sections = []

    # Meal type is the primary constraint — place it first and prominently
    if meal_type and meal_type_label:
        mt_note = {
            "breakfast": "清淡易消化，适合早餐场景",
            "lunch":     "蛋白质充足、饱腹感强，适合午餐场景",
            "dinner":    "低热量清淡，适合晚餐场景",
            "snack":     "分量适中，避免与正餐重复，适合下午茶或夜宵场景",
        }.get(meal_type, "")
        extra_sections.append(
            f"## 本次餐型（最高优先级约束）\n"
            f"{meal_type_label}（{meal_type}）\n"
            f"要求：{mt_note}"
        )

    if recent_meals_same_type:
        extra_sections.append(
            f"## 该用户近期同餐型历史（最近 {len(recent_meals_same_type)} 次{meal_type_label}）\n"
            f"用于判断偏好和避免重复品类：\n"
            f"{json.dumps(recent_meals_same_type, ensure_ascii=False)}"
        )

    if extra_constraint and str(extra_constraint).strip():
        extra_sections.append(f"## 本次额外要求\n{extra_constraint}")

    if exclude_dish_ids:
        extra_sections.append(
            f"## 请勿重复推荐（上次已展示，每类必须换不同选项）\n"
            f"{json.dumps(exclude_dish_ids, ensure_ascii=False)}"
        )

    base_prompt = f"""## 用户画像
{json.dumps(user_profile, ensure_ascii=False)}

## 本次价格区间（主食参考）
{json.dumps(budget_range, ensure_ascii=False)}

## 近期整体饮食历史（最近 3 餐，含所有餐型）
{json.dumps(recent_meals, ensure_ascii=False)}

## 近期整体饮食分析
{json.dumps(recent_pattern, ensure_ascii=False)}

## 候选菜品（已预筛选，含主食、饮品、点心）
{json.dumps(candidate_dishes, ensure_ascii=False)}"""

    user_prompt = ("\n\n".join(extra_sections) + "\n\n" + base_prompt) if extra_sections else base_prompt
    return _call_qwen_text(RECOMMENDATION_SYSTEM_PROMPT, user_prompt)


REMARKS_PER_DISH_SYSTEM_PROMPT = """你是外卖下单备注助手。根据用户忌口习惯和每道菜品，为每道菜分别生成独立的下单备注。

只返回 JSON，严格按照以下示例格式，不允许输出任何其他文字或 Markdown：

{
  "remarks": [
    {
      "dish_id": "preset-gaifan-002",
      "remark": "米饭少一点，不要香菜，谢谢。"
    },
    {
      "dish_id": "preset-drink-001",
      "remark": "常温，不加糖，谢谢。"
    }
  ]
}

规则：
- 每道菜品输出一条备注，dish_id 与输入列表一一对应
- 备注包含：用户忌口（如"不要香菜"）、菜品 remark_rules 中的要求
- 饮品备注可包含温度（热/冰/常温）、甜度
- 用户 remark_habits 体现在相关菜品中
- 每条备注以"谢谢。"结尾；若无特殊要求，写"按正常口味制作，谢谢。"
- 备注文字简洁自然，不超过 50 字"""


def generate_remarks_for_dishes(user_profile, dishes) -> list:
    if _use_mock_llm():
        return mock_llm.generate_remarks_for_dishes(user_profile, dishes)

    dish_list = [
        {
            "dish_id": d.get("dish_id"),
            "name": d.get("name"),
            "category": d.get("category"),
            "remark_rules": d.get("remark_rules") or [],
        }
        for d in (dishes or [])
    ]
    result = _call_qwen_text(
        REMARKS_PER_DISH_SYSTEM_PROMPT,
        f"用户画像：{json.dumps(user_profile, ensure_ascii=False)}\n"
        f"菜品列表：{json.dumps(dish_list, ensure_ascii=False)}",
    )
    remarks = result.get("remarks")
    if not isinstance(remarks, list):
        raise LLMResponseError("remarks 必须是数组")
    return remarks


def generate_remark(user_profile, dishes, dish_category) -> str:
    if _use_mock_llm():
        return mock_llm.generate_remark(user_profile, dishes, dish_category)

    result = _call_qwen_text(
        "你是外卖下单备注助手。请根据用户忌口、备注习惯和菜品类别生成自然中文备注，只返回 JSON。",
        f"""用户画像：{json.dumps(user_profile, ensure_ascii=False)}
菜品：{json.dumps(dishes, ensure_ascii=False)}
菜品类别：{dish_category}
请返回 JSON：{{"remark": "少油，不要香菜，谢谢。"}}""",
    )
    remark = result.get("remark")
    if not isinstance(remark, str) or not remark.strip():
        raise LLMResponseError("remark 必须是非空字符串")
    return remark.strip()
