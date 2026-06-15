# 慧食 FoodWise —— 最终实施方案

## 基于多模态大模型的个性化饮食管理与外卖推荐系统

---

## 1. 项目定位

### 1.1 项目名称

慧食 FoodWise：基于多模态大模型的个性化饮食管理与外卖推荐系统

### 1.2 一句话描述

用户通过拍照上传菜品或自然语言输入饮食记录，千问多模态大模型自动识别菜品并分析营养成分，系统结合用户画像、预算偏好、历史饮食记录和营养目标，智能推荐下一餐外卖并自动生成个性化下单备注，支持为亲友代点。

### 1.3 目标用户

经常点外卖的大学生、上班族、健身人群等。

### 1.4 核心痛点

1. **选择困难**：每天不知道吃什么，决策疲劳
2. **饮食重复与营养失衡**：无意识地重复吃高油高热量食物，缺乏营养感知
3. **备注重复输入**：每次下单都要手动输入相同的忌口备注
4. **帮亲友点餐记不住偏好**：帮别人点餐时记不住对方的口味和忌口
5. **预算与品质难平衡**：有时想省钱、有时想犒劳自己，但每次都要手动筛价格

### 1.5 项目核心设计哲学

**"LLM 即引擎"**——能交给大模型分析判断的，就不写死逻辑。系统尽可能通过 LLM 动态分析更新信息，而非硬编码规则。同时以 SQLite 数据库持久化所有数据，保证系统状态可追溯。

---

## 2. MVP 边界

### 2.1 MVP 阶段做什么

1. 用户画像 CRUD（含默认价格区间设置）
2. 至少 1 个亲友档案管理
3. **上传菜品照片 → 千问多模态大模型（Qwen-VL）识别菜品、分析营养、识别/估算价格 → 结构化入库**
4. 自然语言饮食记录输入 → 千问文本大模型解析时间、菜品、营养
5. 饮食历史持久化存储与展示
6. 每次推荐前可选/调整价格区间
7. 核心推荐链路：画像 + 预算 + 历史 + 菜品库 → LLM 推荐 → 展示结果与理由和价格
8. 备注自动生成 + 可编辑复制
9. 点餐历史记录与简单营养 + 消费统计展示
10. SQLite 数据库持久化所有数据
11. Mock 模式（仅供开发调试）与真实 API 模式切换
12. 完整 README 和运行说明

### 2.2 MVP 阶段不做什么

1. 不接入真实美团、饿了么等外卖平台 API
2. 不做真实下单和支付
3. 不做真实用户认证和权限管理
4. 不做云端部署
5. 不做实时菜单爬取和价格更新
6. 不提供医学级营养建议（LLM 估算，标注"仅供参考"）
7. 不做多用户并发支持
8. 不做复杂的价格走势分析或比价功能
9. 不做复杂机器学习推荐模型
10. 不依赖真实商家库存、配送时间

---

## 3. 系统架构

### 3.1 整体架构

```
展示层（React + Tailwind CSS）
       ↕
API 路由层（Flask）
       ↕
Agent 调度层
       ↕
 ┌─────────────────┬──────────────────┐
 │  千问 VL (Qwen-VL)  │  千问文本 (Qwen-Plus)  │
 │  图像理解 + 营养分析  │  推荐推理 + 备注生成   │
 │  + 价格识别          │  + 数据结构化          │
 └─────────────────┴──────────────────┘
       ↕
 SQLite 数据库持久层
 (users / contacts / dishes / order_history / notes_templates)
```

### 3.2 两个核心功能必须分开

本项目不能设计成一次性问答（用户输入最近吃了什么 → 系统马上推荐下一餐）。必须拆成两个独立功能：

- **功能 1：记录一餐**（文本输入或照片上传 → LLM 解析 → 存入数据库）
- **功能 2：推荐下一餐**（读取历史记录 + 用户画像 + 价格区间 → LLM 推荐）

原因：用户吃过什么应该成为长期历史数据，系统后续推荐要读取这些历史记录，而不是只依赖当前一次输入。

---

## 4. 功能模块详细设计

### 4.1 模块 1：用户画像管理

用户创建和编辑自己的饮食档案。**口味偏好由用户自由文本描述，千问 LLM 解析为结构化数据存入数据库**，而不是勾选预设标签。

画像字段：
- `user_id`：用户唯一标识
- `name`：用户姓名
- `taste_description`：口味偏好原始文本（如"喜欢川菜但不能太辣，偏爱汤类"）
- `taste_tags`：LLM 解析后的结构化口味标签（JSON 数组）
- `avoid_ingredients`：忌口/过敏原（数组，如 ["香菜", "葱"]）
- `health_goals`：健康目标（数组，如 ["少油", "高蛋白"]）
- `body_data`：身体数据（可选，JSON，如 {height: 175, weight: 70}）
- `default_budget`：默认价格区间（JSON，如 {breakfast: [8,15], lunch: [15,30], dinner: [20,40]}）
- `remark_habits`：常用备注习惯（数组，如 ["少油", "不要香菜", "米饭少一点"]）
- `created_at`：创建时间
- `updated_at`：更新时间

**LLM 驱动点：** 用户输入"喜欢川菜但不能太辣" → LLM 自动解析为 `taste_tags: ["微辣", "咸香", "川菜"]`，比预设标签更灵活。

### 4.2 模块 2：菜品照片识别与营养分析（核心差异化功能）

用户上传菜品照片或菜单截图，调用千问多模态大模型（Qwen-VL）进行识别和分析。

**MLLM 输出的结构化信息：**

```json
{
  "dish_name": "番茄牛肉饭",
  "ingredients": ["牛肉", "番茄", "米饭", "鸡蛋"],
  "category": "盖饭类",
  "estimated_nutrition": {
    "calories_kcal": 650,
    "protein_g": 28,
    "fat_g": 18,
    "carbs_g": 85,
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
  "price": 25,
  "price_source": "image_recognized",
  "confidence": 0.85,
  "assumption": "按常见外卖一份番茄牛肉饭估算"
}
```

**价格处理策略：**
- 如果上传的是菜单截图，MLLM 直接从图片中识别价格（`price_source: "image_recognized"`）
- 如果上传的是菜品实拍照片无价格信息，提供输入框让用户手动补充（`price_source: "user_input"`）
- 兜底：由 LLM 根据菜品类型和常见市场价给出估算参考值（`price_source: "llm_estimated"`），标注为"估算价格"

**关键设计：** 菜品库不是预先构造的静态 JSON，而是通过用户上传照片 + MLLM 分析**不断动态增长**的知识库。同时系统初始化时预置 30-50 个常见外卖菜品作为基础数据。

### 4.3 模块 3：自然语言饮食记录（文本输入方式）

除照片上传外，用户也可通过自然语言输入饮食记录。

**用户操作流程：**
1. 用户进入"记录一餐"页面，输入如："昨天晚上吃了炸鸡汉堡套餐和可乐"
2. 系统调用千问文本大模型，完成：识别用餐时间、识别餐次、识别菜品、估算营养信息、给出营养标签
3. 返回结构化 JSON
4. 用户确认后保存到数据库

**记录一餐流程图：**

```
用户输入自然语言饮食记录（或上传照片）
 ↓
前端提交到 /api/log-meal
 ↓
后端读取当前时间 current_time
 ↓
后端调用千问 LLM API（文本模型或多模态模型）
 ↓
LLM 解析用餐时间、餐次、菜品、营养
 ↓
后端校验 LLM 返回 JSON
 ↓
检查 occurred_at 与 resolved_occurred_at 是否一致
 ↓
生成 meal_id 和 created_at
 ↓
检查菜品是否已在 dishes 表中，新菜品自动入库
 ↓
写入 order_history 表
 ↓
返回保存结果
```

### 4.4 模块 4：价格区间选择

**长期层面（画像设置）：** 用户在画像中设置默认预算范围，可按餐次区分（早餐/午餐/晚餐各自不同的默认区间）。

**临时层面（每次推荐时）：** 在触发推荐前，系统展示一个价格区间选择器（滑动条或快捷档位），预填用户的默认值，用户可临时调整。

**LLM 驱动点：** 快捷档位由 LLM 根据菜品库中的实际价格分布动态生成。比如菜品库中大部分菜品集中在 12-28 元区间，LLM 建议"经济（12-18）、日常（18-25）、改善（25+）"三档，而不是硬编码为"0-15/15-30/30-50"。

**价格区间在推荐中的作用：** LLM 不是简单地"过滤掉超出预算的菜品"，而是综合考虑：
- 在预算范围内找到营养最匹配的组合
- 如果预算紧张但用户营养缺口大，建议"性价比最高的蛋白质来源"
- 如果预算宽裕，推荐品质更好的选项并说明理由
- 输出每道推荐菜品的单价与组合总价

### 4.5 模块 5：智能推荐 Agent（核心决策引擎）

推荐过程采用 **LLM 推理为主 + 规则打分为辅** 的双层架构。

**第一层：规则预筛选（本地算法）**

在调用 LLM 之前，先用本地规则算法对候选菜品做初步打分和过滤，减少 LLM 的输入量，提高效率。

初始分 50 分。

加分规则：
| 条件 | 加分 |
|------|------|
| 预算内 | +15 |
| 符合用户口味偏好 | +10 |
| 符合用户健康目标 | +20 |
| 最近偏油且菜品少油 | +20 |
| 最近热量偏高且菜品热量适中 | +15 |
| 最近蔬菜偏少且菜品蔬菜较多 | +15 |
| 蛋白质较高 | +10 |

扣分规则：
| 条件 | 扣分 |
|------|------|
| 超预算 | -20 |
| 最近刚吃过同类菜 | -15 |
| 最近偏油且菜品属于油炸类 | -25 |
| 最近热量偏高且菜品高热量 | -20 |
| 最近口味较重且菜品属于麻辣类 | -15 |

直接淘汰：
- 菜品 ingredients 包含用户 avoid_ingredients 的 → 直接淘汰

时间权重：
| 时间范围 | 权重 |
|---------|------|
| 上一餐 | 1.0 |
| 最近 24 小时 | 0.8 |
| 最近 3 天 | 0.5 |
| 最近 7 天 | 0.3 |
| 超过 7 天 | 不参与推荐 |

**第二层：LLM 综合推理（千问文本模型）**

将规则预筛选后的 Top 10 候选菜品，连同完整的用户画像、近期饮食历史、价格区间等上下文，交给千问 LLM 做最终推理。

LLM 输出：
- 推荐菜品列表（排序 Top 3）
- 每道菜的推荐理由（为什么适合这个用户）
- 单品价格与组合总价
- 营养补充说明（如"你今天碳水摄入偏高，建议晚餐以高蛋白低碳为主"）
- 如果检测到近期饮食模式有问题则给出健康提示
- 如果预算与营养需求存在矛盾时给出平衡建议

**双层架构的优势：** 规则层保证基本的忌口过滤和预算筛选不依赖 LLM（确定性强），LLM 层负责复杂的综合推理和自然语言理由生成（灵活性强）。当 LLM API 不可用时，可以直接退化到纯规则打分模式。

**推荐下一餐流程图：**

```
用户点击"生成下一餐推荐"
 ↓
设定/确认本次价格区间（预填默认值）
 ↓
读取用户画像（或亲友画像）
 ↓
读取饮食历史（最近 3 餐或最近 7 天）
 ↓
分析近期饮食标签 → 生成 recent_pattern
 ↓
读取菜品库（dishes 表）
 ↓
第一层：规则预筛选 → Top 10 候选
 ↓
第二层：LLM 综合推理 → Top 3 推荐 + 理由
 ↓
生成下单备注
 ↓
保存推荐记录到 order_history
 ↓
前端展示结果
```

### 4.6 模块 6：智能备注生成

采用 **LLM 生成 + 规则兜底** 的双模式。

**LLM 模式（优先）：** 根据用户画像中的忌口和偏好，结合本次选择的具体菜品，由千问 LLM 生成自然语言的下单备注。比起简单拼接，LLM 可以根据不同菜品类型做适配（如点汤面时自动加"汤面分离"）。

**规则兜底模式（LLM 不可用时）：**

```
读取用户 remark_habits
 ↓
读取菜品 remark_rules
 ↓
合并 → 去重
 ↓
根据菜品类别补充备注
 ↓
拼接成一句自然语言 + "谢谢。"
```

不同类别备注示例：
- 盖饭类：少油，不要香菜，不要葱，米饭少一点，谢谢。
- 粉面类：微辣，不要香菜，不要葱，汤少一点，谢谢。
- 轻食类：酱料分开放，少油，不要香菜，谢谢。
- 麻辣类：微辣，少油，不要香菜，不要葱，谢谢。

**用户反馈学习：** 用户可编辑修改后确认，修改过的备注反馈回系统（存入 notes_templates 表），LLM 后续生成时参考用户的历史修改偏好。

### 4.7 模块 7：亲友档案共享

用户可为亲友创建独立的饮食档案，包括口味、忌口、健康目标和默认预算偏好。切换"帮谁点"后：
- 推荐引擎和备注生成均基于对方画像运作
- 价格区间切换为对方的默认值（可临时调整）
- 点餐历史关联到对方的 contact_id

### 4.8 模块 8：饮食历史与消费营养追踪

每次推荐确认后，选择的菜品、营养信息和消费金额写入历史数据库。系统可展示：
- 近期饮食时间线（按 occurred_at 倒序）
- 营养趋势（热量、蛋白质等随时间变化）
- 消费趋势（如"本周外卖平均每餐 23.5 元"）

**LLM 驱动点：** 统计数据由 LLM 生成个性化文字总结（如"你本周蛋白质摄入达标，但蔬菜偏少，外卖支出较上周下降 8%"），而不是固定模板填数字。

---

## 5. 时间解析设计

### 5.1 为什么要严格处理时间

推荐下一餐时，系统需要知道：
- 用户上一餐是什么时候吃的
- 最近 24 小时吃了什么
- 最近 3 餐是否偏油
- 最近 7 天是否经常吃重口味
- 某条记录是否已过期，不应影响推荐

因此，饮食记录必须保存准确的 `occurred_at`。

### 5.2 时间字段设计

LLM 返回的 `meal_time` 必须包含：

```json
{
  "meal_time": {
    "occurred_at": "2026-06-12T19:30:00+08:00",
    "meal_type": "dinner",
    "time_resolution": "inferred",
    "time_assumption": {
      "raw_time_text": "昨天晚上",
      "resolved_occurred_at": "2026-06-12T19:30:00+08:00",
      "timezone": "Asia/Shanghai",
      "date_source": "由当前时间 2026-06-13 推断昨天为 2026-06-12",
      "time_source": "用户只说晚上，系统默认晚餐时间为 19:30",
      "default_rule": "早餐=08:00，午餐=12:30，晚餐=19:30，夜宵=22:30",
      "confidence": 0.75
    }
  }
}
```

### 5.3 时间解析类型

`time_resolution` 可选值：

| 值 | 含义 | 示例 |
|---|------|------|
| explicit | 用户明确给出日期和时间 | "2026年6月12日晚上7点" |
| inferred | 用户给出模糊时间，系统推断 | "昨天晚上" |
| defaulted | 用户没说时间，系统默认当前餐次 | "吃了黄焖鸡" |
| unknown | 无法判断时间，需要用户补充 | "前几天吃了点东西" |

### 5.4 默认餐次时间

| 餐次 | 默认时间 |
|------|---------|
| 早餐 | 08:00 |
| 午餐 | 12:30 |
| 晚餐 | 19:30 |
| 夜宵 | 22:30 |

### 5.5 时间校验规则

后端保存前必须校验：
1. `occurred_at` 必须是完整 ISO-8601 日期时间
2. `occurred_at` 必须带时区（如 `+08:00`）
3. `time_assumption.resolved_occurred_at` 必须等于 `occurred_at`
4. `time_resolution` 必须属于 explicit / inferred / defaulted / unknown
5. `confidence` 必须在 0 到 1 之间
6. `unknown` 类型不能直接保存，必须让用户补充时间

```python
def validate_meal_time(meal_time):
    if not meal_time.get("occurred_at"):
        raise ValueError("occurred_at 不能为空")
    if meal_time["occurred_at"] != meal_time["time_assumption"]["resolved_occurred_at"]:
        raise ValueError("occurred_at 与 resolved_occurred_at 不一致")
    if meal_time["time_resolution"] not in ["explicit", "inferred", "defaulted", "unknown"]:
        raise ValueError("time_resolution 不合法")
    if meal_time["time_resolution"] == "unknown":
        raise ValueError("无法判断用餐时间，请用户补充")
    conf = meal_time["time_assumption"]["confidence"]
    if conf < 0 or conf > 1:
        raise ValueError("时间置信度必须在 0 到 1 之间")
```

---

## 6. 数据库设计（SQLite）

### 6.1 users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | TEXT PRIMARY KEY | 用户唯一标识 |
| name | TEXT | 用户姓名 |
| taste_description | TEXT | 口味偏好原始文本 |
| taste_tags | TEXT (JSON) | LLM 解析后的结构化口味标签 |
| avoid_ingredients | TEXT (JSON) | 忌口/过敏原数组 |
| health_goals | TEXT (JSON) | 健康目标数组 |
| body_data | TEXT (JSON) | 身体数据（可选） |
| default_budget | TEXT (JSON) | 默认价格区间 {breakfast:[min,max], lunch:[min,max], dinner:[min,max]} |
| remark_habits | TEXT (JSON) | 常用备注习惯数组 |
| created_at | TEXT | 创建时间 ISO-8601 |
| updated_at | TEXT | 更新时间 ISO-8601 |

### 6.2 contacts 表（亲友）

| 字段 | 类型 | 说明 |
|------|------|------|
| contact_id | TEXT PRIMARY KEY | 亲友唯一标识 |
| owner_user_id | TEXT FK | 归属用户 ID |
| name | TEXT | 亲友姓名 |
| taste_description | TEXT | 口味描述 |
| taste_tags | TEXT (JSON) | 结构化口味标签 |
| avoid_ingredients | TEXT (JSON) | 忌口信息 |
| health_goals | TEXT (JSON) | 健康目标 |
| default_budget | TEXT (JSON) | 亲友默认价格区间 |
| remark_habits | TEXT (JSON) | 备注习惯 |
| created_at | TEXT | 创建时间 |

### 6.3 dishes 表（菜品库，动态增长）

| 字段 | 类型 | 说明 |
|------|------|------|
| dish_id | TEXT PRIMARY KEY | 菜品唯一标识 |
| name | TEXT | 菜名 |
| shop_name | TEXT | 店铺名（可选） |
| category | TEXT | 分类（盖饭类/粉面类/轻食类/快餐油炸类/麻辣类/汤粥类/家常菜类/面点类/饮料类） |
| ingredients | TEXT (JSON) | 食材列表数组 |
| estimated_nutrition | TEXT (JSON) | 营养数据 {calories_kcal, protein_g, fat_g, carbs_g, sodium_mg} |
| levels | TEXT (JSON) | 营养水平 {calorie_level, protein_level, fat_level, carbs_level, sodium_level, vegetable_level}，每个值为 low/medium/high |
| nutrition_tags | TEXT (JSON) | 语义标签数组（如 ["高蛋白", "油脂适中"]） |
| taste_tags | TEXT (JSON) | 口味标签数组（如 ["酸甜", "咸香"]） |
| suitable_goals | TEXT (JSON) | 适合的健康目标（如 ["高蛋白", "少油"]） |
| remark_rules | TEXT (JSON) | 该菜品的备注规则（如 ["少油", "米饭少一点"]） |
| price | REAL | 价格 |
| price_source | TEXT | 价格来源："image_recognized" / "user_input" / "llm_estimated" / "preset" |
| image_path | TEXT | 原始图片路径（可选） |
| llm_analysis_raw | TEXT | MLLM 分析原文（可选，用于追溯） |
| confidence | REAL | MLLM 分析置信度 |
| created_at | TEXT | 录入时间 |

### 6.4 order_history 表（饮食历史）

| 字段 | 类型 | 说明 |
|------|------|------|
| meal_id | TEXT PRIMARY KEY | 记录唯一标识 |
| user_id | TEXT | 用户 ID 或亲友 contact_id |
| user_type | TEXT | "self" 或 "contact" |
| occurred_at | TEXT | 实际用餐时间 ISO-8601 |
| created_at | TEXT | 记录创建时间 ISO-8601 |
| meal_type | TEXT | breakfast / lunch / dinner / snack |
| raw_input | TEXT | 用户原始输入文本 |
| input_type | TEXT | "text" 或 "photo" |
| time_resolution | TEXT | explicit / inferred / defaulted |
| time_assumption | TEXT (JSON) | 时间解析依据 |
| recognized_foods | TEXT (JSON) | 识别出的菜品列表及营养估算 |
| dish_ids | TEXT (JSON) | 关联的菜品 ID 数组 |
| total_price | REAL | 本餐总价 |
| total_nutrition | TEXT (JSON) | 当餐营养总计 |
| remark_used | TEXT | 使用的备注文本 |
| budget_range_used | TEXT (JSON) | 本次使用的价格区间 |

### 6.5 recommendation_records 表

| 字段 | 类型 | 说明 |
|------|------|------|
| rec_id | TEXT PRIMARY KEY | 推荐记录 ID |
| user_id | TEXT | 用户 ID |
| created_at | TEXT | 推荐生成时间 |
| based_on_meal_ids | TEXT (JSON) | 本次推荐依据的历史饮食记录 ID |
| recent_pattern | TEXT (JSON) | 近期饮食倾向分析 |
| budget_range | TEXT (JSON) | 使用的价格区间 |
| recommendations | TEXT (JSON) | 推荐结果（Top 3，含 food_id, name, score, reason, remark, price） |

### 6.6 notes_templates 表（备注学习）

| 字段 | 类型 | 说明 |
|------|------|------|
| template_id | TEXT PRIMARY KEY | 模板 ID |
| user_id | TEXT | 用户 ID |
| dish_category | TEXT | 菜品类别 |
| generated_remark | TEXT | LLM 生成的备注 |
| user_edited_remark | TEXT | 用户修改后的备注 |
| created_at | TEXT | 时间戳 |

---

## 7. 大模型 API 设计

### 7.1 大模型职责分工

| 模型 | 职责 |
|------|------|
| 千问 VL（Qwen-VL） | 菜品照片识别、营养分析、价格识别、菜单图片理解 |
| 千问文本（Qwen-Plus / Qwen-Turbo） | 自然语言饮食记录解析、时间解析、推荐推理、备注生成、口味偏好结构化、饮食报告生成、价格档位动态生成 |

### 7.2 多模态模型 System Prompt（菜品照片分析）

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
```

### 7.3 文本模型 System Prompt（饮食记录解析）

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

### 7.4 文本模型 User Prompt 模板（饮食记录解析）

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

### 7.5 推荐 Agent Prompt 模板

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
      "reason": "推荐理由（包含近期饮食分析、营养补充建议、预算考量）",
      "nutrition_highlight": "营养亮点简述"
    }
  ],
  "total_estimated_price": 0,
  "nutrition_summary": "整体营养建议",
  "health_tip": "如果发现近期饮食问题，给出提示（可选）",
  "budget_note": "预算相关说明（可选）"
}

要求：
1. 推荐 3 道菜品，按推荐优先级排序。
2. 推荐理由必须结合用户画像和近期饮食分析，说明为什么推荐这道菜。
3. 所有推荐菜品的价格必须在用户设定的价格区间内。
4. 不推荐含有用户忌口食材的菜品。
5. 不提供医学建议。
6. 只返回 JSON，不返回其他文字。
```

---

## 8. Mock 模式设计

Mock 模式（`use_mock_llm: true`）仅供开发调试使用，正式运行时使用真实 API（`use_mock_llm: false`）。

### 8.1 LLM 配置

`backend/config/llm_config.json`（gitignored）：
```json
{
  "dashscope_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "api_key": "your_api_key_here",
  "qwen_vl_model": "qwen-vl-plus",
  "qwen_text_model": "qwen-plus",
  "use_mock_llm": false
}
```
也可通过环境变量 `USE_MOCK_LLM=true/false` 覆盖配置文件。

### 8.2 Mock 逻辑

- `USE_MOCK_LLM=true`：不调用真实 API，返回预设的 Mock 结果
- `USE_MOCK_LLM=false`：调用真实千问 API

Mock 返回结果必须包含完整的数据结构（时间解析、营养分析、推荐结果等），与真实 API 返回格式完全一致。

### 8.3 Mock 数据示例

```python
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
            "confidence": 0.75
        }
    },
    "recognized_foods": [
        {
            "raw_text": "炸鸡汉堡套餐",
            "standard_name": "炸鸡汉堡套餐",
            "category": "快餐油炸类",
            "portion": "一份",
            "estimated_nutrition": {"calories_kcal": 950, "protein_g": 35, "fat_g": 45, "carbs_g": 110, "sodium_mg": 1200},
            "levels": {"calorie_level": "high", "protein_level": "medium", "fat_level": "high", "carbs_level": "high", "sodium_level": "high", "vegetable_level": "low"},
            "nutrition_tags": ["高热量", "高脂肪", "高碳水", "蔬菜偏少"],
            "confidence": 0.82,
            "assumption": "按常见外卖一份炸鸡汉堡套餐估算"
        }
    ]
}
```

---

## 9. LLM 驱动 vs 硬编码 对比总览

| 环节 | 传统硬编码方式 | 本项目 LLM 驱动方式 |
|------|-------------|-------------------|
| 口味偏好录入 | 勾选预设标签 | 自由文本 → LLM 解析结构化 |
| 菜品营养信息 | 人工查表写入 JSON | 上传照片 → MLLM 识别分析写入数据库 |
| 菜品价格信息 | 手动录入固定值 | MLLM 从菜单图识别 + LLM 估价兜底 |
| 价格档位划分 | 硬编码 0-15/15-30/30+ | LLM 根据菜品库实际价格分布动态生成 |
| 推荐逻辑 | 纯 if-else 规则过滤 | 规则预筛选 + LLM 综合推理（双层） |
| 预算冲突处理 | 不处理或简单截断 | LLM 给出平衡建议与性价比方案 |
| 备注生成 | 字符串拼接 | LLM 生成自然语言（规则兜底） |
| 营养标签分类 | 预定义标签映射 | LLM 自动打标 |
| 饮食报告 | 固定模板填数字 | LLM 生成个性化文字总结（含消费分析） |

---

## 10. 技术栈

| 层面 | 技术选择 | 说明 |
|------|---------|------|
| 前端 | React + Tailwind CSS | 美观高效，适合 MVP 展示 |
| 后端 | Python Flask | 处理图片上传、调用千问 API、操作 SQLite |
| 多模态大模型 | 通义千问 VL（Qwen-VL） | 通过阿里云 DashScope API 调用，图像理解 + 营养分析 |
| 文本大模型 | 通义千问（Qwen-Plus / Qwen-Turbo） | 推荐推理、备注生成、数据结构化 |
| 数据库 | SQLite | 轻量、单文件部署、无需额外服务 |
| 图片存储 | 本地文件系统 | 数据库存路径引用 |
| 测试框架 | pytest | Python 后端测试 |
| 开发工具 | VS Code / Cursor / Cline | AI 辅助编程 |
| Demo 保障 | 真实 API 模式（Mock 模式仅供开发调试） | LLM 返回 JSON 校验 + 规则兜底 |

---

## 11. 项目目录结构

```
foodwise/
├── frontend/                     # 前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx          # 首页（品牌名：慧食 / FoodWise）
│   │   │   ├── Profile.jsx       # 用户偏好设置
│   │   │   ├── LogMeal.jsx       # 记录一餐（文本+拍照）
│   │   │   ├── MealHistory.jsx   # 饮食历史（含 recharts 图表）
│   │   │   ├── Recommend.jsx     # 推荐下一餐（按主食/饮品/点心分类）
│   │   │   └── Contacts.jsx      # 亲友档案管理
│   │   ├── components/
│   │   │   ├── BrandLogo.jsx     # 品牌 Logo
│   │   │   ├── BudgetSlider.jsx  # 价格区间选择器
│   │   │   ├── PhotoUpload.jsx   # 照片上传组件
│   │   │   ├── NutritionCard.jsx # 营养信息标签展示
│   │   │   └── RemarkEditor.jsx  # 备注编辑与复制
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── backend/                      # 后端
│   ├── app.py                    # Flask 主入口（注册 5 个蓝图）
│   ├── api/
│   │   ├── profile.py            # 用户画像 API
│   │   ├── log_meal.py           # 记录一餐 API（文本+照片）
│   │   ├── meals.py              # 饮食历史 API（含统计、删除、更新）
│   │   ├── recommend.py          # 推荐 API（含确认保存）
│   │   └── contacts.py           # 亲友档案 API
│   ├── lib/
│   │   ├── llm.py                # 千问 API 封装（文本+多模态）
│   │   ├── mock_llm.py           # Mock LLM
│   │   ├── database.py           # SQLite 数据库操作
│   │   ├── time_parser.py        # 时间解析与校验
│   │   ├── nutrition.py          # 近期饮食分析
│   │   ├── recommender.py        # 推荐打分算法（规则层）
│   │   ├── remark.py             # 备注生成（按菜品独立生成）
│   │   ├── log_meal.py           # 记餐业务逻辑
│   │   ├── recommend.py          # 推荐业务逻辑
│   │   ├── profile.py            # 画像业务逻辑
│   │   └── contacts.py           # 亲友业务逻辑
│   ├── config/
│   │   └── llm_config.json       # LLM 配置（gitignored）
│   ├── data/
│   │   ├── init_dishes.json      # 预置菜品数据（30+ 道）
│   │   └── mealmate.db           # SQLite 数据库文件（gitignored）
│   ├── uploads/                  # 用户上传的图片（gitignored）
│   └── tests/                    # 13 个测试文件，67 个用例
│       ├── conftest.py
│       ├── test_app.py
│       ├── test_full_demo_flow.py
│       ├── test_database.py
│       ├── test_contacts_api.py
│       ├── test_log_meal_api.py
│       ├── test_meals_api.py
│       ├── test_nutrition.py
│       ├── test_profile_api.py
│       ├── test_recommend_api.py
│       ├── test_recommender.py
│       ├── test_remark.py
│       ├── test_time_parser.py
│       └── test_llm.py
│
├── docs/                         # SDD 文档
│   ├── idea.md
│   ├── spec.md
│   ├── plan.md
│   ├── tasks.md
│   └── prompts.md                # 关键提示词记录
│
├── FoodWise_Final_Plan.md        # 最终实施方案（本文件）
├── codex_prompts.md              # Codex 分步实现提示词
├── AGENTS.md
├── README.md                     # 运行说明和 Demo 步骤
├── requirements.txt              # 根目录依赖（conda 环境安装入口）
└── start.sh                      # 一键启动前后端脚本
```

---

## 12. API 设计

### 12.1 用户画像

- `GET /api/profile` → 获取当前用户画像
- `POST /api/profile` → 保存/更新用户画像

### 12.2 亲友档案

- `GET /api/contacts` → 获取亲友列表
- `POST /api/contacts` → 创建亲友档案
- `PUT /api/contacts/<contact_id>` → 更新亲友档案
- `DELETE /api/contacts/<contact_id>` → 删除亲友档案

### 12.3 记录一餐

- `POST /api/log-meal` → 提交文本饮食记录（调用千问文本模型）
- `POST /api/log-meal/photo` → 提交照片饮食记录（调用千问 VL 模型）

### 12.4 饮食历史

- `GET /api/meals` → 获取饮食历史（支持按时间范围筛选）
- `GET /api/meals/stats` → 获取近期营养和消费统计

### 12.5 推荐

- `POST /api/recommend` → 生成下一餐推荐（传入 budget_range、user_type、extra_constraint 等）
- `GET /api/recommend/records` → 获取推荐历史记录
- `POST /api/recommend/confirm` → 确认选择，保存到 order_history

---

## 13. 页面设计

### 13.1 首页 /

- 项目名称：慧食 / FoodWise
- 项目简介
- 主要入口按钮：[设置偏好] [记录一餐] [查看历史] [推荐下一餐] [亲友档案]

### 13.2 用户偏好页 /profile

- 口味偏好自由文本输入（LLM 自动解析为标签）
- 忌口/过敏原设置
- 默认价格区间设置（按餐次区分）
- 健康目标设置
- 身体数据（可选）
- 备注习惯设置

### 13.3 记录一餐页 /log

- 自然语言文本输入框
- **照片上传按钮**（调用千问 VL）
- 解析结果展示：时间、菜品、营养标签、价格
- 时间解析依据展示
- 确认保存按钮

### 13.4 饮食历史页 /meals

- 按 occurred_at 倒序展示
- 每条记录显示：实际用餐时间、菜品、营养标签、价格、时间解析依据
- 近期营养趋势和消费统计摘要（LLM 生成文字）

### 13.5 推荐下一餐页 /recommend

- 选择为谁点（自己 / 亲友下拉选择）
- **价格区间选择器**（滑动条 + 快捷档位）
- 近期饮食分析展示
- 额外限制条件输入（extra_constraint）
- 推荐结果按主食 / 饮品 / 点心分课型展示（勾选组合）
- 勾选菜品后显示营养合计与总价
- DishRemarksPanel：每道菜独立备注（可编辑 + 复制）
- "换一批"按钮（排除当前推荐菜，重新生成）
- 确认选择 → 调用 /api/recommend/confirm 保存到历史

### 13.6 亲友档案页 /contacts

- 亲友列表
- 新建/编辑亲友档案（口味、忌口、预算、健康目标）

**Demo 链路（课堂展示路径）：**
`/profile` 设置偏好 → `/log` 上传菜品照片 → `/log` 文本记录一餐 → `/meals` 查看历史 → `/recommend` 设定价格区间 + 推荐下一餐 → 勾选菜品 → 复制备注 → 切换亲友 → 再次推荐

---

## 14. 测试方案

### 14.1 核心成功路径

**输入：**
- 用户偏好：微辣，不吃香菜、不吃葱，午餐预算 15-30 元，目标少油高蛋白
- 饮食历史：昨天中午吃了黄焖鸡米饭；昨天晚上吃了炸鸡汉堡套餐和可乐；今天中午吃了麻辣烫
- 本次价格区间：15-25 元

**预期结果：**
- 系统保存 3 条带 occurred_at 的饮食历史
- 每条记录有 time_assumption，且 occurred_at 与 resolved_occurred_at 完全一致
- 系统分析出偏油、热量偏高、蔬菜偏少、口味较重
- 系统推荐价格在 15-25 元内、相对清淡、高蛋白、少油的菜
- 推荐结果不包含香菜和葱
- 系统生成备注如：少油，不要香菜，不要葱，米饭少一点，谢谢

### 14.2 边界情况 1：用户没有饮食历史

- 预期：提示"暂无足够历史记录，将根据用户偏好进行推荐"，仍可基于偏好推荐，不报错

### 14.3 边界情况 2：用户没有明确时间

- 输入："吃了黄焖鸡"
- 预期：time_resolution = defaulted，使用当前日期和默认餐次时间，前端展示推测时间让用户确认

### 14.4 边界情况 3：用户时间无法判断

- 输入："前几天吃了点东西"
- 预期：time_resolution = unknown，不直接保存，前端提示用户补充具体时间

### 14.5 边界情况 4：用户预算过低

- 输入：budget_range = [0, 10]
- 预期：超预算菜品被扣分，如果推荐结果过少，提示"当前预算下可推荐菜品较少，建议适当放宽预算"

### 14.6 边界情况 5：上传模糊/无关照片

- 输入：上传一张非食物照片
- 预期：MLLM 返回低置信度，前端提示"无法识别菜品，请上传更清晰的菜品或菜单照片"

### 14.7 失败场景 1：大模型 API 失败

- 预期：Mock 模式自动启用，或页面提示"服务暂时不可用，请稍后重试"，系统不崩溃，不写入错误记录

### 14.8 失败场景 2：大模型返回非法 JSON

- 预期：系统捕获 JSON 解析错误，页面提示"模型返回格式错误，请重试"，不写入数据库

### 14.9 失败场景 3：occurred_at 与 resolved_occurred_at 不一致

- 预期：后端拒绝保存，返回错误"occurred_at 与 resolved_occurred_at 不一致"

### 14.10 自动化测试文件

- `test_time_parser.py`：时间校验（一致性、时区、unknown 拒绝、排序）
- `test_nutrition.py`：近期饮食分析（偏油/热量偏高/蔬菜偏少/无历史默认）
- `test_recommender.py`：推荐打分（忌口过滤、预算加扣分、偏好匹配、排序）
- `test_remark.py`：备注生成（忌口包含、去重、自然语言）
- `test_database.py`：数据库读写（CRUD、约束校验）
- `test_llm.py`：Mock 模式返回格式校验

---

## 15. 开发实施阶段

### 阶段 1：项目初始化与 SDD 文档（Day 1）

**任务：**
1. 创建项目目录结构
2. 初始化前端（React + Tailwind）和后端（Flask）
3. 配置 SQLite 数据库初始化脚本
4. 编写 SDD 文档：idea.md、spec.md、plan.md、tasks.md、prompts.md
5. 创建 README.md

**验收：** 项目能启动，首页能打开，数据库初始化成功

### 阶段 2：数据库与基础数据（Day 1-2）

**任务：**
1. 实现 SQLite 数据库建表脚本（所有 6 张表）
2. 创建预置菜品数据（30-50 个常见外卖菜品 JSON，涵盖 9 个类别）
3. 实现数据库 CRUD 操作封装（database.py）
4. 编写 test_database.py

**验收：** 数据库可读写，预置菜品导入成功，测试通过

### 阶段 3：时间解析与校验模块（Day 2）

**任务：**
1. 实现 time_parser.py（校验、排序、默认时间）
2. 编写 test_time_parser.py（5+ 测试用例）

**验收：** 时间校验逻辑全部通过测试

### 阶段 4：千问 LLM 调用封装（Day 2-3）

**任务：**
1. 封装千问文本模型 API 调用（llm.py）
2. 封装千问 VL 多模态 API 调用（llm.py）
3. 实现 Mock 模式（mock_llm.py）
4. 编写 System Prompt 和 User Prompt 模板
5. 处理 API 失败和 JSON 解析失败
6. 编写 test_llm.py

**验收：** Mock 模式下返回完整 JSON，真实 API 模式能调通

### 阶段 5：用户画像功能（Day 3）

**任务：**
1. 实现 profile API（GET/POST）
2. 实现 LLM 解析口味偏好文本为结构化标签
3. 实现前端 Profile 页面（表单 + 保存）
4. 实现亲友档案 CRUD

**验收：** 偏好保存后刷新仍存在，口味文本被 LLM 正确解析

### 阶段 6：记录一餐功能（Day 3-4）

**任务：**
1. 实现 log-meal API（文本输入 → 千问文本模型）
2. 实现 log-meal/photo API（照片上传 → 千问 VL）
3. 后端校验 LLM 返回（时间一致性、JSON 格式）
4. 新菜品自动入库 dishes 表
5. 前端 LogMeal 页面（文本框 + 照片上传 + 解析结果展示 + 确认保存）

**验收：** 文本输入和照片上传均能正确解析、校验、保存

### 阶段 7：饮食历史页面（Day 4）

**任务：**
1. 实现 meals API（按时间倒序）
2. 前端 MealHistory 页面

**验收：** 历史记录按时间倒序展示，信息完整

### 阶段 8：近期饮食分析（Day 4）

**任务：**
1. 实现 nutrition.py（分析最近 3 餐/7 天）
2. 生成 recent_pattern / prefer_next / avoid_next
3. 编写 test_nutrition.py

**验收：** 分析结果符合预期规则

### 阶段 9：推荐打分算法（Day 4-5）

**任务：**
1. 实现 recommender.py（规则预筛选层）
2. 实现 LLM 推荐推理层（千问文本模型）
3. 实现价格区间约束逻辑
4. 编写 test_recommender.py

**验收：** 忌口过滤、预算约束、偏好匹配、排序均正确

### 阶段 10：备注生成（Day 5）

**任务：**
1. 实现 remark.py（LLM 生成 + 规则兜底）
2. 编写 test_remark.py

**验收：** 备注包含忌口、去重、自然语言

### 阶段 11：推荐页面集成（Day 5）

**任务：**
1. 实现 recommend API
2. 前端 Recommend 页面（选择用户/亲友、价格区间选择器、推荐结果、备注编辑、一键复制）
3. 保存推荐记录

**验收：** 完整推荐链路可运行

### 阶段 12：联调与验收（Day 5-6）

**任务：**
1. 全链路联调测试（Mock 模式 + 真实 API 模式）
2. 修复 Bug
3. 补充集成测试（test_app.py、test_full_demo_flow.py 等）

**验收：** Demo 链路流畅，pytest 全部通过（67 个用例），Mock 模式下可完整演示

### 阶段 13：文档完善与交付（Day 6）

**任务：**
1. 完善 README（安装、运行、测试、Demo 步骤）
2. 完善 prompts.md（记录所有关键提示词）
3. 准备课堂 PPT

---

## 16. 核心 Demo 链路（课堂展示用）

**展示时间分配：** 总计 5 分钟展示 + 1-2 分钟问答

**链路 A：主链路演示（约 3 分钟）**

1. 展示用户画像设置
2. **上传菜品照片** → 千问 VL 识别菜品、分析营养、识别价格 → 入库
3. 文本输入"昨天晚上吃了炸鸡汉堡套餐和可乐" → 千问文本模型解析时间和营养 → 保存
4. 查看饮食历史（含时间解析依据）
5. **设定价格区间**（滑动条，预填默认值）
6. 点击推荐 → Agent 综合分析 → 展示 Top 3 推荐（菜名+理由+价格+营养）
7. 展示自动生成的备注 → 一键复制

**链路 B：亲友代点演示（约 1 分钟）**

8. 切换到亲友档案 → 价格区间自动切换
9. 基于亲友画像重新推荐 → 展示不同的推荐结果

**话术模板：**

> 我们这个项目解决的是点外卖时不知道吃什么、容易重复吃高油高热量食物、每次都要手动填写备注、以及帮亲友点餐记不住对方口味的问题。
>
> 首先，用户可以设置自己的口味、忌口、预算和饮食目标，这里口味偏好是自由文本输入，由千问大模型自动解析为结构化标签。
>
> 然后，用户可以通过两种方式记录饮食：一是直接拍照上传菜品，千问多模态大模型会自动识别菜品、分析营养成分并估算价格；二是用自然语言描述，比如"昨天晚上吃了炸鸡汉堡套餐和可乐"，系统会解析出实际用餐时间，并在 time_assumption 中说明推理依据。
>
> 当用户需要推荐下一餐时，先选择价格区间，系统读取最近 3 餐，分析出近期饮食偏油、热量偏高、蔬菜偏少，再结合预算和忌口，从菜品库中智能推荐，并自动生成可一键复制的下单备注。
>
> 下一步迭代方向包括：接入真实外卖平台、增加用户反馈机制、扩充菜品库、以及增加饮食趋势可视化图表。

---

## 17. 项目局限

1. 营养估算来自大模型，结果只作为粗略参考，不构成医学建议
2. 菜品库初始规模有限（30-50 个），需要用户持续上传积累
3. 没有接入真实外卖平台
4. 没有真实订单和支付
5. 没有多用户认证系统
6. MLLM 对复杂菜品图片的识别可能不准确
7. 价格估算可能与实际市场价存在偏差
8. 模糊时间解析存在不确定性
9. 大模型可能返回格式错误，需 JSON 校验和 Mock 兜底

---

## 18. 后续迭代方向

1. 扩充菜品库（用户社区共建）
2. 接入真实营养数据库（如薄荷健康 API）
3. 增加用户反馈机制（推荐满意度评价）
4. 根据反馈动态调整推荐权重
5. 增加最近 7 天饮食趋势图可视化
6. 增加多用户登录系统
7. 接入真实外卖平台搜索链接
8. 增加语音输入饮食记录
9. 增加更严格的 JSON Schema 校验
10. 增加用户确认/修改时间的交互
11. 支持批量上传菜单图片，一次性入库多道菜品

---

## 19. AI 辅助编程提示词记录

### 19.1 需求分析提示词

> 请你作为产品经理，帮我把"基于多模态大模型的个性化饮食管理与外卖推荐系统"拆成 MVP 需求，要求包含目标用户、核心痛点、功能范围（含照片识别和价格区间）、不做的内容和验收标准。

### 19.2 数据库设计提示词

> 请你帮我设计一个 SQLite 数据库结构，包含 users、contacts、dishes、order_history、recommendation_records、notes_templates 六张表。dishes 表需要支持动态增长（通过 MLLM 照片分析入库），order_history 必须包含 occurred_at、time_assumption、recognized_foods 和价格信息。

### 19.3 多模态 Prompt 设计提示词

> 请你帮我设计一个千问 VL 多模态大模型 Prompt，用于从菜品照片中识别菜名、食材、营养信息和价格。要求模型只返回固定 JSON 格式，不输出其他文字。如果图片中有价格信息则识别，否则给出估算。

### 19.4 时间解析提示词

> 请你帮我设计一个饮食记录时间解析方案。要求大模型返回 occurred_at 和 time_assumption.resolved_occurred_at，且两者必须完全一致。如果用户只说"昨天晚上"，需结合当前时间解析出准确日期，并默认晚上为 19:30。

### 19.5 推荐算法提示词

> 请你帮我设计一个双层外卖推荐方案：第一层用规则打分预筛选 Top 10 候选菜品，第二层用千问大模型综合推理输出 Top 3 推荐。需要支持价格区间约束、忌口过滤、近期饮食去重和营养平衡。

### 19.6 测试方案提示词

> 请你为这个外卖推荐 MVP 设计最小 TDD 测试方案，包括一个成功路径、五个边界情况和三个失败场景，重点测试时间解析、照片识别、推荐算法、价格区间约束和备注生成。

---

## 20. 最终交付物清单

1. 项目源代码（前端 + 后端）
2. README.md（安装、运行、测试、Demo 步骤、Mock 说明）
3. docs/idea.md
4. docs/spec.md
5. docs/plan.md
6. docs/tasks.md
7. docs/prompts.md（关键提示词记录）
8. SQLite 预置菜品 JSON（init_dishes.json，30+ 道）
9. tests/ 测试代码（13 个测试文件，67 个用例）
12. 运行截图
13. Demo 截图
14. PPT
15. 课程报告
16. 小组分工和同行评分

---

## 21. 最小可交付标准

时间有限时，最低版本必须完成：

1. 用户偏好设置（含价格区间）
2. 记录一餐（至少支持文本输入模式）
3. 千问大模型或 Mock 模式解析时间、菜品和营养
4. **上传菜品照片 → MLLM 识别分析（至少 Mock 可走通）**
5. 保存带 occurred_at 的饮食历史到 SQLite
6. time_assumption.resolved_occurred_at 与 occurred_at 完全一致
7. 展示饮食历史
8. 分析最近 3 餐
9. 推荐下一餐（含价格区间约束）
10. 生成外卖备注
11. 保存推荐记录
12. README 说明运行方式
13. 至少 4 个自动化测试
14. 至少 1 条完整 Demo 链路

---

## 22. 一句话总结

本项目最终实现一个可运行、可验证、可展示的多模态外卖推荐 Agent。用户可以通过拍照上传或文字描述记录饮食，千问多模态大模型自动识别菜品和营养信息并动态丰富菜品库；当用户需要推荐下一餐时，系统读取近期饮食历史，结合用户画像、忌口、价格区间和健康目标，通过 LLM 智能推荐更合适的菜品，并自动生成可一键复制的下单备注，同时支持为亲友代点。
