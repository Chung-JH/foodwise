# docs/prompts.md

## 关键提示词记录

本文档记录项目中使用的所有关键 LLM 提示词，包括：
1. 千问大模型的 System Prompt 和 User Prompt 模板
2. AI 辅助编程（Codex/Claude Code/Cursor）的关键提示词

---

## 一、千问大模型 Prompt

### 1.1 多模态模型 System Prompt（菜品照片分析）

```
你是一个用于课程 MVP 项目的菜品识别与营养估算助手。
你的任务是根据用户上传的菜品照片或菜单截图，识别菜品名称、食材组成，估算常见外卖份量下的营养信息，并识别或估算价格。

你必须遵守以下要求：
1. 只做粗略估算，不提供医学建议。
2. 不要声称营养结果绝对准确。
3. 必须返回 JSON，不允许输出 JSON 之外的任何文字。
4. 如果图片中包含价格信息，请识别并标注 price_source 为 "image_recognized"。
5. 如果图片中没有价格信息，请根据该菜品在中国常见外卖平台的市场价给出估算，标注 price_source 为 "llm_estimated"。
6. levels 中每个字段只能是 low、medium、high。
7. confidence 必须是 0 到 1 之间的小数。
8. category 只能是以下之一：盖饭类、粉面类、轻食类、快餐油炸类、麻辣类、汤粥类、家常菜类、面点类、饮料类。

请返回以下 JSON 结构：
{
  "dish_name": "",
  "ingredients": [],
  "category": "",
  "estimated_nutrition": {
    "calories_kcal": 0,
    "protein_g": 0,
    "fat_g": 0,
    "carbs_g": 0,
    "sodium_mg": 0
  },
  "levels": {
    "calorie_level": "low|medium|high",
    "protein_level": "low|medium|high",
    "fat_level": "low|medium|high",
    "carbs_level": "low|medium|high",
    "sodium_level": "low|medium|high",
    "vegetable_level": "low|medium|high"
  },
  "nutrition_tags": [],
  "price": 0,
  "price_source": "image_recognized|llm_estimated",
  "confidence": 0.0,
  "assumption": ""
}
```

### 1.2 文本模型 System Prompt（饮食记录解析）

```
你是一个用于课程 MVP 项目的饮食记录解析与营养估算助手。
你的任务是根据用户输入的饮食记录，识别用餐时间、餐次、菜品，并估算常见外卖份量下的营养倾向。

你必须遵守以下要求：
1. 只做粗略估算，不提供医学建议。
2. 不要声称营养结果绝对准确。
3. 必须返回 JSON，不允许输出 JSON 之外的任何文字，不允许输出 Markdown。
4. 必须返回完整的 meal_time 对象。
5. meal_time.occurred_at 必须是完整 ISO-8601 日期时间，例如 2026-06-12T19:30:00+08:00。
6. meal_time.time_assumption.resolved_occurred_at 必须和 meal_time.occurred_at 完全一致。
7. 如果用户只说"昨天晚上"，需要结合当前时间解析出准确日期，并默认晚上为 19:30。
8. 如果用户只说"今天中午"，需要结合当前日期，并默认中午为 12:30。
9. 如果用户没有说具体时间，需要使用默认餐次时间，并在 time_assumption 中说明。
10. 默认餐次时间为：早餐=08:00，午餐=12:30，晚餐=19:30，夜宵=22:30。
11. 如果无法判断时间，time_resolution 写 unknown，不要编造过高置信度。
12. levels 中每个字段只能是 low、medium、high。
13. confidence 必须是 0 到 1 之间的小数。
14. occurred_at 和 resolved_occurred_at 必须完全一致。
```

### 1.3 文本模型 User Prompt 模板（饮食记录解析）

```
当前时间：{{current_time}}
默认时区：Asia/Shanghai
默认餐次时间：早餐=08:00，午餐=12:30，晚餐=19:30，夜宵=22:30

请分析下面这段饮食记录：
{{user_input}}

请严格返回以下 JSON 结构：
{
  "meal_time": {
    "occurred_at": "",
    "meal_type": "breakfast|lunch|dinner|snack",
    "time_resolution": "explicit|inferred|defaulted|unknown",
    "time_assumption": {
      "raw_time_text": "",
      "resolved_occurred_at": "",
      "timezone": "Asia/Shanghai",
      "date_source": "",
      "time_source": "",
      "default_rule": "",
      "confidence": 0
    }
  },
  "recognized_foods": [
    {
      "raw_text": "",
      "standard_name": "",
      "category": "",
      "portion": "",
      "estimated_nutrition": {
        "calories_kcal": 0,
        "protein_g": 0,
        "fat_g": 0,
        "carbs_g": 0,
        "sodium_mg": 0
      },
      "levels": {
        "calorie_level": "low|medium|high",
        "protein_level": "low|medium|high",
        "fat_level": "low|medium|high",
        "carbs_level": "low|medium|high",
        "sodium_level": "low|medium|high",
        "vegetable_level": "low|medium|high"
      },
      "nutrition_tags": [],
      "confidence": 0,
      "assumption": ""
    }
  ]
}
```

### 1.4 推荐 Agent System + User Prompt 模板

```
你是一个个性化外卖推荐助手。请根据以下信息为用户推荐下一餐。

## 用户画像
{{user_profile}}

## 本次价格区间
{{budget_range}}

## 近期饮食历史（最近 3 餐）
{{recent_meals}}

## 近期饮食分析
{{recent_pattern}}

## 候选菜品（已经过预筛选）
{{candidate_dishes}}

请返回 JSON 格式的推荐结果：
{
  "recommendations": [
    {
      "dish_id": "",
      "name": "",
      "score": 0,
      "price": 0,
      "reason": "推荐理由",
      "nutrition_highlight": "营养亮点简述"
    }
  ],
  "total_estimated_price": 0,
  "nutrition_summary": "整体营养建议",
  "health_tip": "健康提示（可选）",
  "budget_note": "预算说明（可选）"
}

要求：
1. 推荐 3 道菜品，按推荐优先级排序。
2. 推荐理由必须结合用户画像和近期饮食分析。
3. 所有推荐菜品价格在用户设定的价格区间内。
4. 不推荐含有用户忌口食材的菜品。
5. 不提供医学建议。
6. 只返回 JSON，不返回其他文字。
```

### 1.5 口味文本解析 Prompt

```
请分析以下用户口味偏好描述，提取结构化的口味标签。

用户输入：{{taste_description}}

请返回 JSON 数组，例如 ["微辣", "咸香", "川菜", "偏爱汤类"]。
只返回 JSON 数组，不返回其他文字。
```

### 1.6 单菜备注生成 Prompt（兼容旧版）

```
请根据以下信息为用户生成外卖下单备注。

用户忌口：{{avoid_ingredients}}
用户备注习惯：{{remark_habits}}
本次菜品：{{dish_name}}
菜品类别：{{dish_category}}

要求：
1. 备注必须包含所有忌口项（如"不要香菜"、"不要葱"）。
2. 根据菜品类别适配备注（如盖饭类加"米饭少一点"，粉面类加"汤少一点"）。
3. 结合用户备注习惯。
4. 以自然语言生成，结尾加"谢谢。"
5. 只返回备注文本，不返回其他内容。
```

### 1.7 按菜品批量备注生成 Prompt（当前实现）

实际实现为 `generate_remarks_per_dish(user_profile, dishes)` → `[{dish_id, remark}]`，逐道菜调用 `generate_remark()` 生成。规则兜底保证忌口食材必须出现（`_ensure_required_parts()`）。

```
请根据以下信息为这道菜生成外卖下单备注。

用户忌口：{{avoid_ingredients}}
用户备注习惯：{{remark_habits}}
菜品名称：{{dish_name}}
菜品类别：{{dish_category}}
菜品特有备注规则：{{remark_rules}}

要求同 1.6，备注结尾加"谢谢。"，只返回备注文本。
```

---

## 二、AI 辅助编程提示词

### 2.1 需求分析提示词
> 请你作为产品经理，帮我把"基于多模态大模型的个性化饮食管理与外卖推荐系统"拆成 MVP 需求，要求包含目标用户、核心痛点、功能范围（含照片识别和价格区间）、不做的内容和验收标准。

### 2.2 数据库设计提示词
> 请你帮我设计一个 SQLite 数据库结构，包含 users、contacts、dishes、order_history、recommendation_records、notes_templates 六张表。dishes 表需要支持动态增长（通过 MLLM 照片分析入库），order_history 必须包含 occurred_at、time_assumption、recognized_foods 和价格信息。每个字段需要标明类型、是否必填、含义。

### 2.3 多模态 Prompt 设计提示词
> 请你帮我设计一个千问 VL 多模态大模型 Prompt，用于从菜品照片中识别菜名、食材、营养信息和价格。要求模型只返回固定 JSON 格式，不输出其他文字。如果图片中有价格信息则识别，否则给出估算。返回的 JSON 需包含 dish_name、ingredients、category、estimated_nutrition、levels、nutrition_tags、price、price_source、confidence 字段。

### 2.4 时间解析方案提示词
> 请你帮我设计一个饮食记录时间解析方案。要求大模型返回 occurred_at 和 time_assumption.resolved_occurred_at，且两者必须完全一致。如果用户只说"昨天晚上"，需结合当前时间解析出准确日期，并默认晚上为 19:30。需处理 explicit/inferred/defaulted/unknown 四种 time_resolution 类型。

### 2.5 推荐算法提示词
> 请你帮我设计一个双层外卖推荐方案：第一层用规则打分预筛选 Top 10 候选菜品（初始分 50，加分/扣分/淘汰规则），第二层用千问大模型综合推理输出 Top 3 推荐。需要支持价格区间约束、忌口过滤、近期饮食去重和营养平衡。输出包含推荐理由和营养说明。

### 2.6 测试方案提示词
> 请你为这个外卖推荐 MVP 设计最小 TDD 测试方案，包括一个核心成功路径、五个边界情况（无历史/无时间/时间未知/预算过低/模糊照片）和三个失败场景（API 失败/非法 JSON/时间不一致），重点测试时间解析、照片识别、推荐算法、价格区间约束和备注生成。

### 2.7 Codex 分步实现提示词
> 详见根目录 codex_prompts.md，包含 Prompt A~N 共 14 个分步实现提示词。
