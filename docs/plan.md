# docs/plan.md

## 1. 项目目标
完成一个基于多模态大模型的个性化饮食管理与外卖推荐系统 MVP：
- 从需求到 SDD 文档
- 从 SDD 到分步实现
- 使用 AI 辅助编程（Codex / Claude Code / Cursor）分步实现
- 集成千问多模态 + 文本大模型
- 用最小测试保证结果可验证

## 2. 技术选型

### 前端  
- React 18 + Vite
- Tailwind CSS
- React Router DOM
- 需要 Node.js 18+（可通过 conda 或官网安装）

### 后端
- Python 3.10+（通过 Conda 管理虚拟环境：`conda create -n foodwise python=3.10`）
- Flask（轻量 Web 框架）
- SQLite（单文件数据库）

### 大模型
- 通义千问 VL（Qwen-VL）：菜品照片识别、营养分析、价格识别
- 通义千问文本（Qwen-Plus）：饮食记录解析、推荐推理、备注生成、口味结构化
- 通过阿里云 DashScope API 调用

### 测试
- pytest（后端单元测试，在 conda 环境内运行）
- 手动验证清单

## 3. 选型理由
- Conda 管理 Python 环境，隔离依赖、跨平台一致性好
- React + Flask 前后端分离，各自独立开发，适合团队协作
- SQLite 单文件部署，无需额外数据库服务，适合 MVP
- 千问提供免费额度，适合教学项目
- Mock 模式（仅供开发调试）与真实 API 模式切换
- 双层推荐架构（规则 + LLM）既有确定性又有灵活性

## 4. 页面与路由设计

### 前端路由
- `/`：首页，项目介绍和功能入口
- `/profile`：用户偏好设置页
- `/log`：记录一餐（文本输入 + 照片上传）
- `/meals`：饮食历史页
- `/recommend`：推荐下一餐页
- `/contacts`：亲友档案管理页

### 后端 API
- `/api/profile`：用户画像 CRUD
- `/api/contacts`：亲友档案 CRUD
- `/api/log-meal`：文本记录饮食
- `/api/log-meal/photo`：照片分析（返回结果不保存）
- `/api/log-meal/photo/save`：保存确认的照片记录
- `/api/meals`：饮食历史查询
- `/api/meals/stats`：营养和消费统计
- `/api/meals/<meal_id>`：删除/更新记录
- `/api/recommend`：生成推荐
- `/api/recommend/records`：推荐历史
- `/api/recommend/confirm`：确认选择，保存到历史

## 5. 业务模块设计

### 5.1 用户画像模块
- 前端表单组件 Profile.jsx
- 后端 API `api/profile.py`
- LLM 口味文本解析 → taste_tags
- 数据库 CRUD `lib/database.py`

### 5.2 菜品照片识别模块
- 前端照片上传组件 PhotoUpload.jsx（集成在 LogMeal.jsx）
- 后端 API `api/log_meal.py`（`/api/log-meal/photo` 和 `/photo/save`）
- 千问 VL 调用 `lib/llm.py`
- 新菜品入库 dishes 表

### 5.3 饮食记录模块
- 前端 LogMeal.jsx（文本框 + 照片上传 + 解析结果 + 确认保存）
- 后端 API `api/log_meal.py`
- 千问文本模型调用 `lib/llm.py`
- 时间解析校验 `lib/time_parser.py`
- 写入 order_history 表

### 5.4 饮食历史模块
- 前端 MealHistory.jsx
- 后端 API `api/meals.py`
- 按 occurred_at 倒序查询

### 5.5 推荐引擎模块
- 前端 Recommend.jsx（价格区间选择器 + 推荐结果 + 备注编辑）
- 后端 API `api/recommend.py`
- 近期饮食分析 `lib/nutrition.py`
- 规则预筛选 `lib/recommender.py`
- LLM 综合推理 `lib/llm.py`

### 5.6 备注生成模块
- LLM 模式 + 规则兜底 `lib/remark.py`
- 每道推荐菜品生成独立备注（`generate_remarks_per_dish`）
- 备注编辑与复制功能内联在 Recommend.jsx（DishRemarksPanel）

### 5.7 亲友档案模块
- 前端 Contacts.jsx
- 后端 API `api/contacts.py`
- 切换后推荐基于对方画像

## 6. 核心数据流
1. 用户设置偏好 → LLM 解析口味 → 保存到 users 表
2. 用户上传照片 → 千问 VL 识别 → 结构化数据入 dishes 表
3. 用户输入饮食记录 → 千问文本模型解析时间和菜品 → 校验 → 入 order_history 表
4. 用户请求推荐 → 读取画像 + 历史 + 菜品库 → 规则预筛选 → LLM 推理 → 返回 Top 3
5. 推荐确认 → 生成备注 → 一键复制 → 保存推荐记录

## 7. 代码组织原则
- 前端页面只负责展示和交互
- 核心业务逻辑全部放在 `backend/lib/`
- API 路由处理放在 `backend/api/`
- 数据文件放在 `backend/data/`
- 测试优先覆盖 `backend/lib/` 中的函数
- LLM 调用统一封装在 `lib/llm.py`，Mock 在 `lib/mock_llm.py`
- 不在源代码中硬编码 API Key

## 8. 里程碑拆分

### M1：项目骨架与文档
- 初始化前端（React + Vite + Tailwind）和后端（Flask）
- 创建目录结构
- 编写 SDD 文档
- 首页静态页面

### M2：数据库与基础数据
- SQLite 建表（6 张表）
- 预置菜品 JSON（30-50 个）
- database.py CRUD 封装
- test_database.py

### M3：时间解析与 LLM 封装
- time_parser.py + test_time_parser.py
- llm.py（千问文本 + VL 封装）
- mock_llm.py
- test_llm.py

### M4：用户画像 + 记录一餐
- profile API + 前端页面
- log-meal API（文本 + 照片）+ 前端页面
- LLM 口味解析
- 时间校验和 JSON 校验

### M5：饮食历史 + 近期分析
- meals API + 前端页面
- nutrition.py + test_nutrition.py

### M6：推荐引擎 + 备注生成
- recommender.py + test_recommender.py
- remark.py + test_remark.py
- recommend API + 前端页面

### M7：亲友档案 + 联调
- contacts API + 前端页面
- 全链路联调
- Bug 修复

### M8：测试与收尾
- 完成所有测试
- README 完善
- prompts.md 记录

## 9. 风险与应对
- 风险：千问 API 不稳定或超出免费额度
  应对：实现 Mock 模式，所有功能均可在 Mock 下运行
- 风险：LLM 返回格式不稳定
  应对：JSON 校验 + 重试机制 + 规则兜底
- 风险：课堂时间有限
  应对：先确保文本记录 + 推荐链路跑通，照片识别可用 Mock 演示
- 风险：前后端联调问题
  应对：先各自开发测试，最后集成；后端提供完整 Mock 数据
- 风险：AI 一次改动过大
  应对：强制按里程碑逐步实现，每步都验证

## 10. 后续迭代方向
- 接入真实外卖平台搜索链接
- 扩充菜品库（用户社区共建）
- 增加用户反馈机制（推荐满意度评价）
- 增加 7 天饮食趋势可视化图表
- 增加多用户登录系统
- 接入真实营养数据库
- 支持语音输入
