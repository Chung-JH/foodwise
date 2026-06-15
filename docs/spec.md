# docs/spec.md

## 1. 项目名称
慧食 FoodWise：基于多模态大模型的个性化饮食管理与外卖推荐系统

## 2. 一句话定义
用户通过拍照上传或自然语言记录饮食，千问多模态大模型自动识别菜品并分析营养，系统结合用户画像、预算、历史和营养目标，智能推荐下一餐外卖并按菜品自动生成个性化下单备注。

## 3. 背景问题
经常点外卖的大学生和上班族存在以下痛点：
1. 每天不知道吃什么，决策疲劳
2. 无意识重复吃高油高热量食物，缺乏营养感知
3. 每次下单都要手动输入相同的忌口备注
4. 帮亲友点餐时记不住对方口味和忌口
5. 预算与品质难平衡

## 4. 目标用户
- 用户 A：经常点外卖的大学生
- 用户 B：注重营养均衡的上班族 / 健身人群
- 用户 C：经常帮亲友代点外卖的人

## 5. MVP 目标
在一个代码仓库内完成可运行、可演示、可验证的 Web MVP，至少覆盖：
- 用户画像管理（含 LLM 解析口味文本）
- 菜品照片识别与营养分析（千问 VL）
- 自然语言饮食记录（千问文本模型）
- 饮食历史展示（含统计图表）
- 智能推荐下一餐（规则预筛选 + LLM 推理，按主食/饮品/点心分类，含价格区间约束）
- 按菜品生成专属备注与复制
- 亲友档案管理与代点
- Mock 模式（仅供开发调试）与真实 API 模式切换

## 6. 用户故事
- US-01：作为外卖用户，我希望设置口味偏好时只需自由描述，系统自动理解并结构化存储。
- US-02：作为外卖用户，我希望拍照上传菜品后，系统自动识别菜名、食材、营养信息和价格。
- US-03：作为外卖用户，我希望用自然语言输入"昨天晚上吃了炸鸡汉堡"，系统自动解析时间、菜品和营养。
- US-04：作为外卖用户，我希望查看近期饮食历史，了解自己的营养和消费趋势。
- US-05：作为外卖用户，我希望系统根据我的偏好、历史、预算和营养目标，推荐下一餐并说明理由。
- US-06：作为外卖用户，我希望系统自动生成下单备注，一键复制到外卖 App。
- US-07：作为帮亲友点餐的人，我希望创建亲友档案，切换后系统基于对方画像推荐。

## 7. 功能需求

### FR-01 用户画像管理
画像字段：姓名、口味偏好（自由文本 → LLM 解析为标签）、忌口/过敏原、健康目标、身体数据（可选）、默认预算（按餐次区分）、备注习惯。

验收标准：
- 口味文本保存后，taste_tags 由 LLM 自动填充
- 偏好保存后刷新页面仍存在
- 忌口列表在推荐时被严格过滤

### FR-02 菜品照片识别与营养分析
用户上传菜品照片或菜单截图，调用千问 VL 多模态模型识别。

MLLM 输出结构化信息：dish_name, ingredients, category, estimated_nutrition, levels, nutrition_tags, price, price_source, confidence, assumption。

价格处理：菜单截图识别价格 → 菜品实拍用户手动输入 → LLM 估算兜底。

验收标准：
- 上传菜品照片后返回结构化 JSON
- 新菜品自动入库 dishes 表
- 低置信度时提示用户确认
- Mock 模式下返回预设结果

### FR-03 自然语言饮食记录
用户输入如"昨天晚上吃了炸鸡汉堡套餐和可乐"，千问文本模型解析。

必须返回完整 meal_time 对象，含 occurred_at（ISO-8601）和 time_assumption。

时间解析规则：
- explicit：用户明确给出日期时间
- inferred：模糊时间（"昨天晚上"）→ 推断
- defaulted：没说时间 → 默认当前餐次
- unknown：无法判断 → 提示用户补充

验收标准：
- occurred_at 与 resolved_occurred_at 必须完全一致
- time_resolution 为 unknown 时不直接保存
- 解析结果展示后用户确认才保存
- Mock 模式下返回预设结果

### FR-04 饮食历史展示
按 occurred_at 倒序展示饮食记录，每条显示：用餐时间、菜品、营养标签、价格、时间解析依据。

验收标准：
- 记录按时间倒序排列
- 新增记录后刷新可见
- 每条记录信息完整

### FR-05 智能推荐下一餐
双层架构：规则预筛选 Top 10 → LLM 综合推理 Top 3。

推荐前可选/调整价格区间（滑动条 + 快捷档位）。

输出：推荐菜品列表（名称+价格+分数+理由+营养亮点）、组合总价、营养建议、健康提示。

验收标准：
- 推荐结果不包含用户忌口食材
- 推荐菜品价格在设定区间内
- 推荐理由结合用户画像和近期饮食
- 无饮食历史时仍可基于偏好推荐
- LLM 不可用时退化为纯规则模式

### FR-06 智能备注生成
每道推荐菜品独立生成专属备注（`remarks` 列表）。
LLM 模式（优先）：根据画像忌口 + 具体菜品类型生成自然语言备注。
规则兜底：拼接 remark_habits + remark_rules → 去重 → 加"谢谢。"

验收标准：
- 每道菜有独立备注，包含该菜品的忌口项
- 备注根据菜品类别适配（如粉面类加"汤少一点"）
- 用户可按菜品编辑备注后复制
- 忌口食材强制出现在 LLM 生成的备注中

### FR-07 亲友档案管理
用户可创建/编辑/删除亲友档案，含口味、忌口、预算、健康目标。

切换"帮谁点"后推荐和备注基于对方画像。

验收标准：
- 亲友档案 CRUD 功能完整
- 切换亲友后推荐结果不同
- 价格区间自动切换

## 8. 数据模型

### users 表
```
user_id: TEXT PRIMARY KEY
name: TEXT
taste_description: TEXT
taste_tags: TEXT (JSON array)
avoid_ingredients: TEXT (JSON array)
health_goals: TEXT (JSON array)
body_data: TEXT (JSON, optional)
default_budget: TEXT (JSON {breakfast:[min,max], lunch:[min,max], dinner:[min,max]})
remark_habits: TEXT (JSON array)
created_at: TEXT (ISO-8601)
updated_at: TEXT (ISO-8601)
```

### contacts 表
```
contact_id: TEXT PRIMARY KEY
owner_user_id: TEXT FK→users
name: TEXT
taste_description: TEXT
taste_tags: TEXT (JSON)
avoid_ingredients: TEXT (JSON)
health_goals: TEXT (JSON)
default_budget: TEXT (JSON)
remark_habits: TEXT (JSON)
created_at: TEXT
```

### dishes 表
```
dish_id: TEXT PRIMARY KEY
name: TEXT
shop_name: TEXT (optional)
category: TEXT (盖饭类/粉面类/轻食类/快餐油炸类/麻辣类/汤粥类/家常菜类/面点类/饮料类)
ingredients: TEXT (JSON array)
estimated_nutrition: TEXT (JSON {calories_kcal, protein_g, fat_g, carbs_g, sodium_mg})
levels: TEXT (JSON {calorie_level, protein_level, fat_level, carbs_level, sodium_level, vegetable_level})
nutrition_tags: TEXT (JSON array)
taste_tags: TEXT (JSON array)
suitable_goals: TEXT (JSON array)
remark_rules: TEXT (JSON array)
price: REAL
price_source: TEXT (image_recognized/user_input/llm_estimated/preset)
image_path: TEXT (optional)
llm_analysis_raw: TEXT (optional)
confidence: REAL
created_at: TEXT
```

### order_history 表
```
meal_id: TEXT PRIMARY KEY
user_id: TEXT
user_type: TEXT (self/contact)
occurred_at: TEXT (ISO-8601, MUST equal resolved_occurred_at)
created_at: TEXT
meal_type: TEXT (breakfast/lunch/dinner/snack)
raw_input: TEXT
input_type: TEXT (text/photo)
time_resolution: TEXT (explicit/inferred/defaulted)
time_assumption: TEXT (JSON)
recognized_foods: TEXT (JSON array)
dish_ids: TEXT (JSON array)
total_price: REAL
total_nutrition: TEXT (JSON)
remark_used: TEXT
budget_range_used: TEXT (JSON)
```

### recommendation_records 表
```
rec_id: TEXT PRIMARY KEY
user_id: TEXT
created_at: TEXT
based_on_meal_ids: TEXT (JSON array)
recent_pattern: TEXT (JSON)
budget_range: TEXT (JSON)
recommendations: TEXT (JSON array)
```

### notes_templates 表
```
template_id: TEXT PRIMARY KEY
user_id: TEXT
dish_category: TEXT
generated_remark: TEXT
user_edited_remark: TEXT
created_at: TEXT
```

## 9. 非功能要求
- 页面文案为中文
- 界面简洁美观，适合课堂演示
- 代码结构清晰，前后端分离
- 业务逻辑放入 `backend/lib/`，便于测试
- Mock 模式仅供开发调试，正式运行使用真实 API
- LLM 返回必须经过 JSON 校验才能入库
- 营养数据标注"仅供参考，不构成医学建议"

## 10. 范围外
- 真实外卖平台 API 接入
- 真实下单和支付
- 用户登录/注册/认证
- 云端部署
- 实时菜单爬取
- 医学级营养建议
- 多用户并发
- 复杂价格走势分析
- 复杂机器学习推荐模型
