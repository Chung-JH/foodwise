# 慧食 FoodWise —— Codex 分步实现提示词

## 使用说明
- 每个 Prompt 按 **Goal / Context / Constraints / Done when** 结构编写
- 复杂任务先 plan 再 coding（Prompt A 就是先计划）
- 每一步都要求 Codex 阅读尽可能多的文档，防止跑偏
- 按 A → B → C → ... → N 顺序执行，每步完成后验证再进入下一步
- 如遇到问题可回退到上一步修复

---

## Prompt A：先计划，不急着写代码

```
Goal:
为"慧食 FoodWise —— 基于多模态大模型的个性化饮食管理与外卖推荐系统"制定实施计划。

Context:
请先完整阅读以下文件：
@AGENTS.md
@docs/spec.md
@docs/plan.md
@docs/tasks.md
@FoodWise_Final_Plan.md

这是一个课程设计 MVP 项目，技术栈为 React + Tailwind（前端）、Python Flask + SQLite（后端，使用 Conda 虚拟环境 `conda create -n foodwise python=3.10`）、通义千问 VL + Qwen-Plus（大模型）。
要求范围清晰、实现可控、适合课堂 5 分钟演示。
项目有两个独立核心功能：
1. 记录一餐（文本/照片 → LLM 解析 → 存入数据库）
2. 推荐下一餐（历史+画像+预算 → 规则预筛选+LLM推理 → Top 3 推荐+备注）

Constraints:
- 先不要写代码
- 按里程碑 M1~M8 拆解
- 每个里程碑说明要改哪些文件、涉及哪些模块
- 每个里程碑给出验证方式（命令或手动步骤）
- 优先级按"先能演示核心链路，再补完整功能"排序
- 必须包含 Mock 模式设计（仅供开发调试，正式运行使用真实 API）
- 标出高风险点和建议先做的 3 个功能

Done when:
- 输出 M1~M8 实施计划
- 每个里程碑有文件清单和验证方式
- 标出高风险点（LLM 返回不稳定、前后端联调）
- 标出建议先做的 3 个功能
- 计划与 AGENTS.md 和 FoodWise_Final_Plan.md 保持一致
```

---

## Prompt B：项目初始化与目录结构

```
Goal:
初始化慧食 FoodWise 项目骨架，包括前端、后端、文档目录和配置文件。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md
@docs/plan.md
@FoodWise_Final_Plan.md（第 10 节技术栈、第 11 节目录结构）

项目目录结构应为：
foodwise/
├── frontend/          # React + Vite + Tailwind
├── backend/           # Python Flask
│   ├── app.py         # Flask 主入口
│   ├── api/           # API 路由
│   ├── lib/           # 业务逻辑
│   ├── data/          # SQLite DB + 预置 JSON
│   ├── uploads/       # 用户上传图片
│   ├── tests/         # pytest 测试
│   ├── config/        # LLM 配置（llm_config.json，gitignored）
│   └── requirements.txt
├── docs/              # SDD 文档
├── AGENTS.md
└── README.md

Constraints:
- 后端 Python 环境使用 Conda 管理：`conda create -n foodwise python=3.10 -y`
- 所有后端命令（pip install、python app.py、pytest）均须在 `conda activate foodwise` 后执行
- 前端使用 Vite + React 18 + Tailwind CSS + React Router DOM，需要 Node.js 18+
- 后端使用 Python Flask，入口为 backend/app.py
- 后端 app.py 启动时自动初始化 SQLite 数据库
- 创建 backend/config/llm_config.json（gitignored）包含：api_key、qwen_vl_model、qwen_text_model、use_mock_llm
- requirements.txt 包含：flask、flask-cors、python-dotenv、openai（或 dashscope SDK）、pytest
- 前端配置代理到后端 http://localhost:5000
- README.md 包含项目简介、conda 环境创建步骤、安装步骤、运行命令
- 所有文案为中文

Done when:
- `conda create -n foodwise python=3.10 -y` 成功创建环境
- `conda activate foodwise && pip install -r requirements.txt && python backend/app.py` 可启动
- 前端 `cd frontend && npm install && npm run dev` 可启动
- 后端 GET /api/health 返回 {"status": "ok"}
- 目录结构与 AGENTS.md 一致
- backend/config/llm_config.json 已创建（gitignored）
```

---

## Prompt C：SQLite 数据库建表与预置数据

```
Goal:
实现 SQLite 数据库建表脚本和预置菜品数据导入。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（第 8 节数据模型）
@docs/tasks.md（T1）
@FoodWise_Final_Plan.md（第 6 节数据库设计）

需要创建 6 张表：users、contacts、dishes、order_history、recommendation_records、notes_templates。
dishes 表需要通过 init_dishes.json 预置 30-50 个常见外卖菜品，覆盖 9 个类别：
盖饭类、粉面类、轻食类、快餐油炸类、麻辣类、汤粥类、家常菜类、面点类、饮料类。

Constraints:
- 实现 backend/lib/database.py：
  - init_db()：建表 + 导入预置数据
  - users 表 CRUD：get_user(), save_user()
  - contacts 表 CRUD：get_contacts(), add_contact(), update_contact(), delete_contact()
  - dishes 表 CRUD：get_dishes(), add_dish(), get_dish_by_name()
  - order_history 表 CRUD：add_meal(), get_meals(), get_recent_meals()
  - recommendation_records 表 CRUD：add_recommendation(), get_recommendations()
  - notes_templates 表 CRUD：add_note_template(), get_note_templates()
- 创建 backend/data/init_dishes.json，每道菜品包含完整字段：
  dish_id, name, category, ingredients, estimated_nutrition, levels, nutrition_tags, taste_tags, suitable_goals, remark_rules, price, price_source("preset"), confidence
- 每个类别至少 3-5 道菜，总计 30-50 道
- 先编写 backend/tests/test_database.py，再实现 database.py（TDD）
- 所有 JSON 字段用 TEXT 存储，读写时 json.dumps/json.loads

Done when:
- 在 conda 环境内运行：`conda activate foodwise && cd backend && pytest tests/test_database.py` 通过
- mealmate.db 文件可正常创建
- 预置菜品导入成功（可通过 get_dishes() 查询到 30+ 条记录）
- 6 张表均可正常读写
```

---

## Prompt D：时间解析与校验模块

```
Goal:
实现饮食记录时间解析与校验逻辑。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（FR-03 时间解析部分）
@docs/tasks.md（T2）
@FoodWise_Final_Plan.md（第 5 节时间解析设计）

时间校验是本项目的关键约束：
- occurred_at 必须是 ISO-8601 格式带时区
- occurred_at 必须与 time_assumption.resolved_occurred_at 完全一致
- time_resolution 只能是 explicit/inferred/defaulted/unknown
- unknown 类型不能直接保存
- confidence 必须在 0~1 之间

Constraints:
- 先编写 backend/tests/test_time_parser.py（至少 5 个测试用例）：
  1. 正常 inferred 时间通过校验
  2. occurred_at 与 resolved_occurred_at 不一致 → 抛出 ValueError
  3. time_resolution 为 unknown → 抛出 ValueError
  4. confidence 超出 0~1 范围 → 抛出 ValueError
  5. explicit 时间正常通过
- 再实现 backend/lib/time_parser.py：
  - validate_meal_time(meal_time: dict) → bool or raise ValueError
  - get_default_meal_time(meal_type: str) → str（返回默认时间如 "08:00"）
  - sort_meals_by_time(meals: list) → list（按 occurred_at 倒序）

Done when:
- `conda activate foodwise && pytest tests/test_time_parser.py` 全部通过（5+ 测试用例）
- 不一致的 occurred_at 被拦截
- unknown 类型被拒绝保存
- 函数签名与 FoodWise_Final_Plan.md 一致
```

---

## Prompt E：千问 LLM API 封装与 Mock 模式

```
Goal:
封装通义千问文本模型和多模态模型 API 调用，并实现完整的 Mock 模式。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md
@docs/tasks.md（T3）
@FoodWise_Final_Plan.md（第 7 节大模型 API 设计、第 8 节 Mock 模式设计）

千问 API 通过 DashScope 调用，API Key 从 backend/config/llm_config.json（gitignored）读取。
需要封装两类模型：
- 千问 VL（Qwen-VL）：图像理解，分析菜品照片
- 千问文本（Qwen-Plus）：饮食记录解析、推荐推理、备注生成、口味文本结构化

环境变量配置：
- DASHSCOPE_API_KEY：API 密钥
- QWEN_VL_MODEL：多模态模型名（默认 qwen-vl-plus）
- QWEN_TEXT_MODEL：文本模型名（默认 qwen-plus）
- USE_MOCK_LLM：是否使用 Mock 模式（true/false）

Constraints:
- 实现 backend/lib/llm.py：
  - _call_qwen_text(system_prompt, user_prompt) → dict：调用千问文本模型，返回 JSON
  - _call_qwen_vl(system_prompt, image_path_or_base64, user_prompt) → dict：调用千问 VL
  - parse_taste_text(taste_description) → list[str]：解析口味文本为标签
  - parse_meal_record(user_input, current_time) → dict：解析饮食记录
  - analyze_dish_photo(image_path) → dict：分析菜品照片
  - generate_recommendation(user_profile, recent_meals, recent_pattern, candidate_dishes, budget_range) → dict
  - generate_remark(user_profile, dishes, dish_category) → str
- 实现 backend/lib/mock_llm.py：
  - 所有函数的 Mock 版本
  - Mock 返回结果必须与真实 API 返回 JSON 结构完全一致
  - 包含 FoodWise_Final_Plan.md 第 8.3 节的 Mock 数据
- llm.py 根据 USE_MOCK_LLM 环境变量自动切换真实/Mock 模式
- System Prompt 和 User Prompt 模板按 FoodWise_Final_Plan.md 第 7.2~7.5 节编写
- 所有 LLM 返回结果必须经过 JSON 解析校验
- API 调用失败时抛出明确异常，不静默失败
- 编写 backend/tests/test_llm.py：
  - 测试 Mock 模式下各函数返回格式正确
  - 测试 JSON 校验逻辑（合法/非法输入）

Done when:
- USE_MOCK_LLM=true 时所有函数返回完整合法 JSON
- `conda activate foodwise && pytest tests/test_llm.py` 通过
- System Prompt 与 FoodWise_Final_Plan.md 一致
- `backend/config/llm_config.json`（gitignored）中 API Key 不硬编码在源代码中
```

---

## Prompt F：首页与前端页面骨架

```
Goal:
完成前端所有页面骨架和路由配置。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（第 7 节功能需求）
@docs/plan.md（第 4 节路由设计）
@docs/tasks.md（T4）
@FoodWise_Final_Plan.md（第 13 节页面设计）

项目前端使用 React + Tailwind CSS，共 6 个页面。

Constraints:
- 实现首页 Home.jsx：
  - 品牌名"慧食 / FoodWise"（英文 FoodWise，中文慧食）
  - 一句话介绍
  - 5 个功能入口按钮（设置偏好/记录一餐/查看历史/推荐下一餐/亲友档案）
  - 页面风格简洁美观，适合课堂展示
- 创建所有页面组件：
  - Profile.jsx（用户偏好设置）
  - LogMeal.jsx（记录一餐）
  - MealHistory.jsx（饮食历史，含 recharts 图表）
  - Recommend.jsx（推荐下一餐，按主食/饮品/点心分类）
  - Contacts.jsx（亲友档案）
- 配置 React Router DOM 路由（App.jsx），共 6 条路由
- 创建公共组件：
  - BrandLogo.jsx（品牌 Logo）
  - BudgetSlider.jsx（价格区间选择器）
  - PhotoUpload.jsx（照片上传）
- 所有页面文案为中文
- 页面设计参考 FoodWise_Final_Plan.md 第 13 节

Done when:
- 6 个路由可访问（/、/profile、/log、/meals、/recommend、/contacts）
- 首页展示品牌名、介绍和 5 个入口按钮
- 所有按钮跳转正确
- 页面风格统一，适合演示
```

---

## Prompt G：用户画像 API 与页面

```
Goal:
实现用户画像管理的后端 API 和前端页面。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（FR-01 用户画像管理）
@docs/tasks.md（T5）
@FoodWise_Final_Plan.md（第 4.1 节用户画像管理）

用户画像的核心设计：口味偏好由用户自由文本描述，千问 LLM 自动解析为结构化标签（taste_tags），而不是勾选预设标签。

Constraints:
- 实现 backend/api/profile.py：
  - GET /api/profile：返回当前用户画像（默认 user_id = "default_user"）
  - POST /api/profile：保存/更新用户画像
  - 保存时自动调用 LLM（或 Mock）解析 taste_description → taste_tags
- 前端实现 Profile.jsx 完整表单：
  - 姓名输入
  - 口味偏好自由文本输入（textarea）
  - LLM 解析后的标签展示（只读，来自后端返回的 taste_tags）
  - 忌口/过敏原输入（逗号分隔或标签式输入）
  - 健康目标选择（如 少油、高蛋白、低碳水、多蔬菜）
  - 默认预算设置（按早餐/午餐/晚餐分别设置 min-max）
  - 备注习惯输入（如 少油、不要香菜、米饭少一点）
  - 保存按钮 + 保存成功提示
- 在 app.py 中注册 profile 蓝图

Done when:
- GET /api/profile 返回正确的用户画像 JSON
- POST /api/profile 保存后再 GET 数据一致
- taste_description 保存后 taste_tags 被 LLM/Mock 自动填充
- 前端表单可正常编辑和保存
- 刷新页面后数据仍存在
```

---

## Prompt H：记录一餐功能（文本输入 + 照片上传）

```
Goal:
实现"记录一餐"的完整后端 API 和前端页面，支持文本输入和照片上传两种方式。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（FR-02 菜品照片识别、FR-03 自然语言饮食记录）
@docs/tasks.md（T7、T8）
@FoodWise_Final_Plan.md（第 4.2 节照片识别、第 4.3 节自然语言记录、第 5 节时间解析、第 7.2~7.4 节 Prompt 设计）

这是项目的核心功能之一。两个独立入口：
1. 文本输入 → 千问文本模型解析 → 校验 → 保存
2. 照片上传 → 千问 VL 分析 → 校验 → 保存

关键约束：occurred_at 必须与 resolved_occurred_at 完全一致。

Constraints:
- 实现 backend/api/log_meal.py：
  - POST /api/log-meal：接收 {"text": "昨天晚上吃了炸鸡汉堡套餐"}
    1. 读取当前时间 current_time
    2. 调用 LLM parse_meal_record()
    3. 调用 time_parser.validate_meal_time() 校验时间
    4. 校验 JSON 结构完整性
    5. 检查菜品是否已在 dishes 表，新菜品自动入库
    6. 生成 meal_id，写入 order_history 表
    7. 返回解析结果供前端展示
  - POST /api/log-meal/photo：接收图片文件
    1. 保存图片到 backend/uploads/
    2. 调用 LLM analyze_dish_photo()
    3. 校验 JSON
    4. 新菜品入库 dishes 表
    5. 返回分析结果
- 前端实现 LogMeal.jsx：
  - Tab 切换：文本记录 / 照片上传
  - 文本记录：自然语言输入框 + "解析"按钮
  - 照片上传：PhotoUpload 组件 + 图片预览 + "分析"按钮
  - 解析/分析结果展示区：
    - 用餐时间（可编辑确认）
    - 时间解析依据（time_assumption 展示）
    - 菜品列表 + 营养标签
    - 价格（照片模式下可手动补充）
  - "确认保存"按钮
  - time_resolution 为 unknown 时提示用户补充时间
- 在 app.py 中注册 log_meal 蓝图

Done when:
- 文本输入"昨天晚上吃了炸鸡汉堡套餐和可乐" → 正确解析时间、菜品、营养
- 照片上传 → 返回菜品名称、营养、价格（Mock 模式下预设结果）
- occurred_at === resolved_occurred_at（后端校验通过）
- 新菜品自动入库 dishes 表
- 数据保存到 order_history 表
- unknown 时间不直接保存
- Mock 模式下全流程可走通
```

---

## Prompt I：饮食历史页面与营养统计

```
Goal:
实现饮食历史展示和近期营养/消费统计功能。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（FR-04 饮食历史展示）
@docs/tasks.md（T9、T10）
@FoodWise_Final_Plan.md（第 4.8 节饮食历史与营养追踪）

饮食历史按 occurred_at 倒序展示。近期饮食分析是推荐引擎的重要输入。

Constraints:
- 实现 backend/api/meals.py：
  - GET /api/meals：返回饮食历史列表（支持 ?days=7 参数按时间范围筛选）
  - GET /api/meals/stats：返回近期营养和消费统计
- 先编写 backend/tests/test_nutrition.py：
  - 测试连续高油高热量 → 分析出"偏油、热量偏高"
  - 测试连续吃快餐 → 分析出"蔬菜偏少"
  - 测试无历史记录 → 返回默认空分析，不报错
- 再实现 backend/lib/nutrition.py：
  - analyze_recent_meals(meals: list) → dict
    返回 recent_pattern, prefer_next, avoid_next
  - 分析维度：油脂、热量、蔬菜、蛋白质、口味轻重、品类重复
- 前端实现 MealHistory.jsx：
  - 按 occurred_at 倒序展示饮食记录列表
  - 每条记录展示：用餐时间、餐次、菜品名称列表、营养标签、价格、时间解析依据
  - 顶部展示近期营养和消费统计摘要
- 在 app.py 中注册 meals 蓝图

Done when:
- GET /api/meals 返回按时间倒序排列的记录
- GET /api/meals/stats 返回正确的营养分析
- `conda activate foodwise && pytest tests/test_nutrition.py` 通过
- 前端历史页面信息完整
- 新增记录后刷新可见
```

---

## Prompt J：推荐打分算法（规则预筛选层）

```
Goal:
实现推荐引擎的第一层——规则预筛选算法。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（FR-05 智能推荐）
@docs/tasks.md（T11）
@FoodWise_Final_Plan.md（第 4.5 节智能推荐 Agent —— 第一层规则预筛选部分）

规则预筛选的目标是从菜品库中过滤和打分，输出 Top 10 候选菜品给 LLM 做最终推理。

打分规则（初始分 50）：
加分：预算内+15、口味匹配+10、健康目标匹配+20、近期偏油且少油+20、近期热量高且热量适中+15、近期蔬菜少且蔬菜多+15、蛋白质高+10
扣分：超预算-20、近期同类菜-15、近期偏油且油炸类-25、近期热量高且高热量-20、近期口味重且麻辣类-15
淘汰：含忌口食材直接淘汰

Constraints:
- 先编写 backend/tests/test_recommender.py：
  - 测试忌口过滤：菜品含 ["香菜"]，用户忌口 ["香菜"] → 淘汰
  - 测试预算约束：菜品 30 元，预算 [15,25] → 扣分
  - 测试口味偏好匹配：菜品 taste_tags 含 "微辣"，用户 taste_tags 含 "微辣" → 加分
  - 测试近期饮食补偿：近期偏油，菜品 fat_level="low" → 加分
  - 测试排序正确性：Top 10 按分数从高到低
- 再实现 backend/lib/recommender.py：
  - score_dish(dish, user_profile, recent_pattern, budget_range) → int
  - pre_filter(dishes, user_profile, recent_pattern, budget_range, recent_meals) → list[dict]
    返回 Top 10 候选菜品（含分数）
  - is_allergen_conflict(dish, avoid_ingredients) → bool

Done when:
- `conda activate foodwise && pytest tests/test_recommender.py` 全部通过
- 忌口食材被严格过滤
- 打分逻辑与 FoodWise_Final_Plan.md 一致
- 输出 Top 10 按分数排序
```

---

## Prompt K：备注生成模块

```
Goal:
实现智能备注生成功能，支持 LLM 生成和规则兜底两种模式。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（FR-06 智能备注生成）
@docs/tasks.md（T12）
@FoodWise_Final_Plan.md（第 4.6 节智能备注生成）

备注生成规则：
- LLM 模式：根据用户忌口 + 菜品类型 → 生成自然语言备注
- 规则兜底：remark_habits + remark_rules → 合并去重 → 按类别补充 → 加"谢谢。"
- 不同类别示例：
  盖饭类：少油，不要香菜，不要葱，米饭少一点，谢谢。
  粉面类：微辣，不要香菜，不要葱，汤少一点，谢谢。
  轻食类：酱料分开放，少油，不要香菜，谢谢。

Constraints:
- 先编写 backend/tests/test_remark.py：
  - 测试忌口包含：用户忌口 ["香菜","葱"] → 备注包含"不要香菜"和"不要葱"
  - 测试去重：remark_habits 和 remark_rules 有重复项 → 去重
  - 测试盖饭类适配：生成备注包含"米饭少一点"
  - 测试粉面类适配：生成备注包含"汤少一点"
  - 测试以"谢谢。"结尾
- 再实现 backend/lib/remark.py：
  - generate_remark(user_profile, dishes, use_llm=True) → str
  - _generate_remark_llm(user_profile, dishes) → str
  - _generate_remark_rule(user_profile, dishes) → str
  - LLM 不可用时自动降级到规则模式

Done when:
- `conda activate foodwise && pytest tests/test_remark.py` 全部通过
- LLM 模式和规则模式都能生成合理备注
- 备注包含所有忌口
- 不同菜品类别有不同备注适配
```

---

## Prompt L：推荐页面集成（核心链路）

```
Goal:
实现推荐下一餐的完整后端 API 和前端页面，打通核心推荐链路。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（FR-05 智能推荐、FR-06 备注生成）
@docs/tasks.md（T13）
@FoodWise_Final_Plan.md（第 4.4 节价格区间、第 4.5 节推荐 Agent、第 7.5 节推荐 Prompt）

推荐链路：
用户设定价格区间 → 读取画像 → 读取历史 → 分析近期饮食 → 规则预筛选 Top 10 → LLM 综合推理 Top 3 → 生成备注 → 展示结果

Constraints:
- 实现 backend/api/recommend.py：
  - POST /api/recommend：
    接收 {"budget_range": [15, 25], "user_type": "self", "contact_id": null}
    内部流程：
    1. 读取用户画像（或亲友画像）
    2. 读取最近 3 餐饮食历史
    3. 调用 nutrition.analyze_recent_meals() 分析近期饮食
    4. 读取菜品库
    5. 调用 recommender.pre_filter() 规则预筛选 Top 10
    6. 调用 llm.generate_recommendation() LLM 推理 Top 3
    7. 调用 remark.generate_remark() 生成备注
    8. 保存推荐记录到 recommendation_records 表
    9. 返回推荐结果
  - GET /api/recommend/records：返回推荐历史
- 前端实现 Recommend.jsx：
  - "为谁点"下拉选择（自己 / 亲友列表）
  - BudgetSlider 价格区间选择器（预填用户默认值，可拖动调整）
  - "生成推荐"按钮
  - 最近 3 餐展示区
  - 近期饮食分析展示（如"近期偏油、热量偏高、蔬菜偏少"）
  - Top 3 推荐结果卡片：
    - 菜名、价格、推荐分数
    - 推荐理由
    - 营养亮点
  - 组合总价展示
  - 推荐结果按主食/饮品/点心分课型展示（勾选组合）
  - DishRemarksPanel（每道菜独立备注，可编辑 + 复制）
  - "换一批"按钮（排除当前推荐菜，重新生成）
  - "确认选择"按钮 → 调用 /api/recommend/confirm 保存
- 在 app.py 中注册 recommend 蓝图
- LLM 不可用时退化为纯规则模式（只返回规则预筛选 Top 3）

Done when:
- POST /api/recommend 返回完整推荐结果（Top 3 + 备注 + 分析）
- 推荐结果不含忌口食材
- 推荐菜品价格在设定区间内
- 切换亲友后推荐结果不同
- 一键复制功能可用
- Mock 模式下完整链路可走通
- 无饮食历史时仍可基于偏好推荐（不报错）
```

---

## Prompt M：亲友档案

```
Goal:
实现亲友档案管理 API 与页面。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md（FR-07 亲友档案）
@docs/tasks.md（T6）
@FoodWise_Final_Plan.md（第 4.7 节亲友档案、第 13.6 节亲友页面设计）

Demo 链路：设置偏好 → 上传菜品照片 → 记录一餐 → 查看历史 → 设定价格区间 → 推荐下一餐 → 勾选菜品 → 复制备注 → 切换亲友 → 再次推荐

Constraints:
- 实现 backend/api/contacts.py：
  - GET /api/contacts：获取亲友列表
  - POST /api/contacts：创建亲友档案
  - PUT /api/contacts/<contact_id>：更新亲友档案
  - DELETE /api/contacts/<contact_id>：删除亲友档案
- 前端实现 Contacts.jsx：
  - 亲友列表展示（姓名、口味摘要、忌口）
  - "新建亲友"按钮 → 展开表单（口味、忌口、预算、健康目标、备注习惯）
  - 编辑/删除功能
  - 预算按餐次分别设置（BudgetSlider）
- 在 app.py 中注册 contacts 蓝图

Done when:
- 亲友 CRUD 完整可用
- 切换亲友后 /api/recommend 推荐结果不同
- Mock 模式下可完整演示
```

---

## Prompt N：全链路联调、测试与文档收尾

```
Goal:
完成全链路联调测试、补充自动化测试、完善文档和 README。

Context:
请完整阅读以下文件：
@AGENTS.md
@docs/spec.md
@docs/plan.md
@docs/tasks.md（T15）
@FoodWise_Final_Plan.md（第 14 节测试方案、第 15 节开发阶段、第 20 节交付物清单、第 21 节最小可交付标准）

核心成功路径测试：
- 用户偏好：微辣，不吃香菜不吃葱，午餐预算 15-30 元，目标少油高蛋白
- 饮食历史：昨天中午黄焖鸡米饭 + 昨天晚上炸鸡汉堡 + 今天中午麻辣烫
- 预算：15-25 元
- 预期：推荐清淡高蛋白少油菜品，不含香菜葱，备注"少油，不要香菜，不要葱…谢谢"

Constraints:
- 全链路联调测试（Mock 模式 + 真实 API 模式）：
  1. 设置偏好 → 保存成功
  2. 文本记录"昨天晚上吃了炸鸡汉堡套餐和可乐" → 解析正确
  3. 查看历史 → 记录按时间倒序
  4. 推荐下一餐 → 结果合理
  5. 一键复制备注 → 可用
  6. 切换亲友 → 推荐结果不同
- 确保所有测试文件全部通过（13 个文件，67 个用例）：
  - test_app.py、test_full_demo_flow.py
  - test_database.py、test_time_parser.py、test_llm.py
  - test_nutrition.py、test_recommender.py、test_remark.py
  - test_contacts_api.py、test_log_meal_api.py、test_meals_api.py
  - test_profile_api.py、test_recommend_api.py
- 完善 README.md：
  - 项目简介
  - 技术栈
  - 前置依赖（Conda、Node.js）
  - Conda 环境创建步骤（`conda create -n foodwise python=3.10 -y`）
  - 安装步骤（`conda activate foodwise && pip install -r requirements.txt` + `npm install`）
  - 环境变量配置（.env 说明）
  - 运行命令（`conda activate foodwise && python app.py` + `npm run dev`）
  - Mock 模式说明
  - 测试命令（`conda activate foodwise && pytest tests/ -v`）
  - Demo 操作步骤（1~9 步）
  - 项目局限说明
- 编写 docs/prompts.md：
  - 记录所有关键 LLM System Prompt 和 User Prompt 模板
  - 记录使用 Codex/AI 辅助编程的关键提示词
- 修复联调中发现的 Bug

Done when:
- `conda activate foodwise && cd backend && pytest tests/ -v` 全部通过（13 个测试文件，67 个用例）
- Mock 模式下完整 Demo 链路流畅
- README.md 可指导从零运行项目（包含 conda 环境创建步骤）
- docs/prompts.md 包含所有关键提示词
- 满足 FoodWise_Final_Plan.md 第 21 节最小可交付标准（14 项全部达成）
```

---

## 附录：各 Prompt 依赖关系

```
A（计划）
 ↓
B（项目骨架）
 ↓
C（数据库+预置数据）
 ↓
D（时间解析）──→ E（LLM 封装+Mock）
                    ↓
                F（前端骨架）
                    ↓
                G（用户画像）
                    ↓
                H（记录一餐：文本+照片）
                    ↓
                I（饮食历史+营养分析）
                    ↓
                J（推荐打分算法）──→ K（备注生成）
                                        ↓
                                    L（推荐页面集成）
                                        ↓
                                    M（亲友+Demo）
                                        ↓
                                    N（联调+测试+文档）
```

## 附录：紧急裁剪方案（时间不足时）

如果时间紧张，按以下优先级裁剪：

**必须完成（最小可交付）：**
- Prompt B（项目骨架）
- Prompt C（数据库）
- Prompt E（LLM + Mock）
- Prompt F（前端骨架）
- Prompt G（用户画像）
- Prompt H 的文本部分（记录一餐 - 文本输入）
- Prompt I（饮食历史）
- Prompt J（推荐算法）
- Prompt L（推荐页面 - 简化版）

**可以降级：**
- Prompt H 照片上传部分 → 只用 Mock 数据展示
- Prompt K 备注生成 → 只用规则兜底模式
- Prompt M 亲友档案 → 只做后端 API，前端简化
- Prompt D 时间解析 → 简化校验规则

**可以跳过：**
- Prompt M 中的 Demo 页面 → 直接在推荐页面演示
- Prompt N 中的 test_report.md → 口头说明测试结果
