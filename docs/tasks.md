# docs/tasks.md

## T0 项目初始化
- [x] 创建项目目录结构（frontend/ backend/ docs/）
- [x] 创建 Conda 虚拟环境：`conda create -n foodwise python=3.10 -y`
- [x] 激活环境：`conda activate foodwise`
- [x] 初始化前端：`npm create vite@latest frontend -- --template react` + Tailwind CSS + React Router + recharts
- [x] 初始化后端：Flask + requirements.txt，在项目根目录执行 `pip install -r requirements.txt`
- [x] 创建 `backend/data/`、`backend/lib/`、`backend/api/`、`backend/tests/`、`backend/uploads/`、`backend/config/` 目录
- [x] 编写 AGENTS.md 和 docs/ 下的 SDD 文档

完成标准：
- `conda activate foodwise` 可正常激活
- 前端 `cd frontend && npm run dev` 可启动，显示首页
- 后端 `conda activate foodwise && cd backend && python app.py` 可启动，返回 health check
- 目录结构正确

## T1 数据库建表与初始化
- [x] 编写 `backend/lib/database.py`，实现 SQLite 建表（6 张表）
- [x] 编写 `backend/data/init_dishes.json`，预置 30-50 个常见外卖菜品（覆盖 9 个类别）
- [x] 实现数据库初始化函数（建表 + 导入预置菜品）
- [x] 实现 users 表 CRUD
- [x] 实现 dishes 表 CRUD
- [x] 实现 order_history 表 CRUD
- [x] 实现 contacts 表 CRUD
- [x] 编写 `backend/tests/test_database.py`

完成标准：
- 数据库文件 mealmate.db 可正常创建
- 预置菜品导入成功（覆盖盖饭类、粉面类、轻食类、快餐油炸类、麻辣类、汤粥类、家常菜类、面点类、饮料类）
- CRUD 操作正常
- `conda activate foodwise && pytest tests/test_database.py` 通过

## T2 时间解析与校验
- [x] 编写 `backend/lib/time_parser.py`
  - validate_meal_time()：校验 occurred_at 与 resolved_occurred_at 一致性
  - 校验 time_resolution 合法性
  - 校验 confidence 范围
  - 拒绝 unknown 类型
- [x] 编写 `backend/tests/test_time_parser.py`
  - 测试正常 inferred 时间
  - 测试 occurred_at 与 resolved_occurred_at 不一致 → 报错
  - 测试 unknown 类型 → 拒绝保存
  - 测试 confidence 越界 → 报错
  - 测试 explicit 时间正常通过

完成标准：
- 5+ 测试用例全部通过
- `conda activate foodwise && pytest tests/test_time_parser.py` 通过

## T3 千问 LLM API 封装
- [x] 编写 `backend/lib/llm.py`
  - call_qwen_text()：调用千问文本模型
  - call_qwen_vl()：调用千问 VL 多模态模型
  - parse_taste_text()：解析口味文本为结构化标签
  - parse_meal_record()：解析饮食记录（时间+菜品+营养）
  - analyze_dish_photo()：分析菜品照片
  - generate_recommendation()：生成推荐
  - generate_remark()：生成备注
  - 统一错误处理和 JSON 校验
- [x] 编写 `backend/lib/mock_llm.py`
  - 所有函数的 Mock 版本，返回与真实 API 完全一致的 JSON 结构
- [x] 创建 `backend/config/llm_config.json`（gitignored，包含 api_key、模型名、use_mock_llm）
- [x] 编写 `backend/tests/test_llm.py`
  - 测试 Mock 模式返回格式正确
  - 测试 JSON 校验逻辑

完成标准：
- `USE_MOCK_LLM=true` 时所有函数返回完整 JSON
- `USE_MOCK_LLM=false` 时能调通真实千问 API（至少文本模型）
- `conda activate foodwise && pytest tests/test_llm.py` 通过

## T4 首页与前端骨架
- [x] 实现首页 Home.jsx：项目名称、简介、5 个功能入口按钮
- [x] 创建所有页面组件：Profile/LogMeal/MealHistory/Recommend/Contacts
- [x] 配置 React Router 路由（6 个路由）
- [x] 创建公共组件：BrandLogo/BudgetSlider/PhotoUpload/NutritionCard/RemarkEditor
- [x] 设置 Tailwind 主题色和基础样式

完成标准：
- 6 个路由可访问（/、/profile、/log、/meals、/recommend、/contacts）
- 首页展示项目介绍和入口按钮
- 点击按钮跳转正确

## T5 用户画像功能
- [x] 实现 `backend/api/profile.py`（GET/POST /api/profile）
- [x] 后端调用 LLM/Mock 解析 taste_description → taste_tags
- [x] 前端实现 Profile.jsx
  - 口味偏好自由文本输入
  - 忌口/过敏原标签输入
  - 默认预算设置（按餐次区分）
  - 健康目标设置
  - 备注习惯设置
  - 保存按钮

完成标准：
- 偏好保存后刷新仍存在（数据库持久化）
- taste_description 被 LLM 正确解析为 taste_tags
- Mock 模式下也能正常工作

## T6 亲友档案功能
- [x] 实现 `backend/api/contacts.py`（GET/POST/PUT/DELETE /api/contacts）
- [x] 前端实现 Contacts.jsx
  - 亲友列表展示
  - 新建/编辑/删除亲友档案
  - 口味、忌口、预算、健康目标表单

完成标准：
- 亲友 CRUD 功能完整
- 数据持久化到 contacts 表

## T7 记录一餐（文本输入）
- [x] 实现 `backend/api/log_meal.py`（POST /api/log-meal、/photo、/photo/save）
- [x] 后端调用 LLM 解析饮食记录文本
- [x] 后端校验 meal_time（调用 time_parser.py）
- [x] 后端校验 LLM 返回 JSON 格式
- [x] 新菜品自动入库 dishes 表
- [x] 写入 order_history 表
- [x] 前端实现 LogMeal.jsx 文本输入部分
  - 自然语言输入框
  - 解析结果展示（时间、菜品、营养标签）
  - 时间解析依据展示
  - 确认保存按钮

完成标准：
- 输入"昨天晚上吃了炸鸡汉堡套餐和可乐" → 正确解析时间、菜品、营养
- occurred_at === resolved_occurred_at
- 数据保存到 order_history
- Mock 模式下正常工作

## T8 记录一餐（照片上传）
- [x] 实现 `backend/api/log_meal.py`（POST /api/log-meal/photo）
- [x] 后端接收图片文件，保存到 uploads/
- [x] 后端调用千问 VL 分析照片
- [x] 后端校验 MLLM 返回 JSON
- [x] 新菜品入库 dishes 表
- [x] 前端实现 LogMeal.jsx 照片上传部分
  - PhotoUpload 组件
  - 图片预览
  - 分析结果展示
  - 用户可手动补充价格
  - 确认保存按钮

完成标准：
- 上传菜品照片 → 返回菜品名称、营养、价格
- 低置信度时提示用户
- Mock 模式下返回预设结果
- 新菜品入库 dishes 表

## T9 饮食历史页面
- [x] 实现 `backend/api/meals.py`（GET /api/meals、GET /api/meals/stats）
- [x] 前端实现 MealHistory.jsx
  - 按 occurred_at 倒序展示
  - 每条记录：用餐时间、菜品列表、营养标签、价格、时间解析依据
  - 近期营养和消费统计摘要

完成标准：
- 记录按时间倒序展示
- 信息完整
- 新增记录后刷新可见

## T10 近期饮食分析
- [x] 实现 `backend/lib/nutrition.py`
  - analyze_recent_meals()：分析最近 3 餐 / 最近 7 天
  - 生成 recent_pattern（偏油/热量偏高/蔬菜偏少/口味较重等）
  - 生成 prefer_next（下一餐建议偏向）
  - 生成 avoid_next（下一餐建议避免）
- [x] 编写 `backend/tests/test_nutrition.py`
  - 测试连续高油高热量 → 分析出偏油
  - 测试蔬菜偏少 → 分析出蔬菜不足
  - 测试无历史 → 返回默认空分析

完成标准：
- 分析结果符合预期规则
- `conda activate foodwise && pytest tests/test_nutrition.py` 通过

## T11 推荐打分算法
- [x] 实现 `backend/lib/recommender.py`
  - score_dish()：单菜品打分（初始 50 分，加分/扣分/淘汰规则）
  - pre_filter()：规则预筛选 Top 10
  - 忌口直接淘汰
  - 预算加扣分
  - 近期饮食去重扣分
  - 营养补偿加分
  - 口味偏好匹配加分
- [x] 编写 `backend/tests/test_recommender.py`
  - 测试忌口过滤（含忌口食材 → 淘汰）
  - 测试预算约束（超预算 → 扣分）
  - 测试偏好匹配（符合口味 → 加分）
  - 测试排序正确性

完成标准：
- 忌口食材被严格过滤
- 打分逻辑正确
- `conda activate foodwise && pytest tests/test_recommender.py` 通过

## T12 备注生成
- [x] 实现 `backend/lib/remark.py`
  - generate_remarks_per_dish()：为每道推荐菜品生成独立备注列表
  - generate_remark()：生成合并备注（向后兼容）
  - LLM 模式优先，规则兜底，保证忌口强制出现
- [x] 编写 `backend/tests/test_remark.py`
  - 测试忌口包含
  - 测试去重
  - 测试不同菜品类别适配
  - 测试以"谢谢。"结尾

完成标准：
- 备注包含所有忌口
- 不同菜品类别有不同备注
- `conda activate foodwise && pytest tests/test_remark.py` 通过

## T13 推荐页面集成
- [x] 实现 `backend/api/recommend.py`（POST /api/recommend、GET /api/recommend/records、POST /api/recommend/confirm）
- [x] 推荐 API 内部流程：读取画像 → 读取历史 → 分析近期 → 预筛选 → LLM 推理 → 生成各菜品备注 → 返回结果
- [x] 前端实现 Recommend.jsx
  - 选择为谁点（自己 / 亲友下拉）
  - BudgetSlider 价格区间选择器（预填默认值）
  - 按主食/饮品/点心分课型展示推荐结果（勾选组合）
  - 近期饮食分析展示
  - 勾选菜品后显示营养合计与各菜品专属备注
  - DishRemarksPanel（按菜品可编辑 + 复制）
  - 确认选择 → 调用 /api/recommend/confirm 保存

完成标准：
- 完整推荐链路可运行
- 推荐结果不含忌口，按课型分类展示
- 价格在区间内（仅主食受预算约束）
- 备注按菜品独立生成，可编辑和复制

## T14 联调与验收
- [x] 全链路联调测试（Mock 模式 + 真实 API 模式）
- [x] 修复 Bug
- [x] 补充 test_app.py、test_contacts_api.py、test_log_meal_api.py 等集成测试

完成标准：
- Demo 链路流畅：设置偏好 → 上传照片 → 记录一餐 → 查看历史 → 设定价格 → 推荐 → 备注 → 切换亲友 → 再次推荐
- Mock 模式下可完整演示
- pytest tests/ -v 全部通过（13 个测试文件，67 个用例）

## T15 文档完善与交付
- [x] 完善 README.md（安装、运行、测试、Demo 步骤、Mock 说明）
- [x] 编写 docs/prompts.md（关键提示词记录）
- [x] 准备课堂 PPT
- [x] 整理手动验证清单

完成标准：
- README 可指导从零运行项目
- 提示词记录完整
- 可完成 5 分钟课堂演示
