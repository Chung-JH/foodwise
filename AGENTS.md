# AGENTS.md

## Project goal
Build an Agent-based MVP named "慧食 FoodWise —— 基于多模态大模型的个性化饮食管理与外卖推荐系统".
The app should support:
- User profile management (taste preferences, dietary restrictions, budget, health goals)
- Meal logging via natural language text input
- Meal logging via photo upload (Qwen-VL multimodal recognition)
- Meal history display with time parsing details
- Intelligent next-meal recommendation (rule scoring + LLM reasoning, grouped by 主食/饮品/点心)
- Per-dish auto-generated order remarks with copy function
- Contact (friend/family) profile management for ordering on behalf of others
- Nutrition and spending statistics

## Tech constraints
- Frontend: React + Tailwind CSS (Vite as build tool), requires Node.js 18+
- Backend: Python Flask, single `app.py` entry point
- Python environment: use `conda create -n foodwise python=3.10` to create virtual env, all backend commands run inside `conda activate foodwise`
- Database: SQLite, single file `backend/data/mealmate.db`
- LLM: 通义千问 (DashScope API) — Qwen-VL for image, Qwen-Plus for text
- API key: store in `backend/config/llm_config.json` (gitignored) or env vars, NEVER hardcode in source
- Keep the project in a single repository with `frontend/` and `backend/` top-level dirs
- Store preset dishes in `backend/data/init_dishes.json`
- Put all business logic in `backend/lib/`
- Put all API route handlers in `backend/api/`
- Prefer small diffs and simple code
- All UI text in Chinese (简体中文)
- Do not add heavy dependencies unless necessary
- Mock mode (`USE_MOCK_LLM=true`) available for development and testing only; production uses real API

## Workflow rules
- Read `docs/spec.md`, `docs/plan.md`, `docs/tasks.md`, and `AGENTS.md` before coding
- Read `FoodWise_Final_Plan.md` for detailed design when implementing any module
- For any non-trivial change, propose a short plan first
- Break work into milestones
- When changing business logic in `backend/lib/`, add or update tests in `backend/tests/`
- After each milestone, run `conda activate foodwise && pytest` to verify tests pass
- Two core features MUST be separate:
  - Feature 1: "记录一餐" (Log a meal) — text or photo → LLM parse → save to DB
  - Feature 2: "推荐下一餐" (Recommend next meal) — read history + profile + budget → LLM recommend
- `occurred_at` and `time_assumption.resolved_occurred_at` MUST always be identical
- All LLM responses MUST be validated JSON before saving to database

## Tech stack summary
| Layer | Technology |
|-------|-----------|
| Python Env | Conda (`conda create -n foodwise python=3.10`) |
| Frontend | React 18 + Tailwind CSS + Vite (Node.js 18+) |
| Backend | Python 3.10+ Flask |
| Multimodal LLM | Qwen-VL (via DashScope API) |
| Text LLM | Qwen-Plus (via DashScope API) |
| Database | SQLite 3 |
| Image storage | Local filesystem `backend/uploads/` |
| Testing | pytest |
| Dev tools | VS Code / Cursor / Claude Code / Codex |

## Database tables (6 tables)
1. `users` — user profiles with taste, budget, health goals
2. `contacts` — friend/family profiles
3. `dishes` — dish library (dynamically growing via MLLM photo analysis)
4. `order_history` — meal records with occurred_at, nutrition, price
5. `recommendation_records` — recommendation history
6. `notes_templates` — remark learning from user edits

## API endpoints
- `GET/POST /api/profile` — user profile CRUD
- `GET/POST/PUT/DELETE /api/contacts` — contact CRUD
- `POST /api/log-meal` — log meal via text
- `POST /api/log-meal/photo` — analyze photo (returns result without saving)
- `POST /api/log-meal/photo/save` — save confirmed photo meal record
- `GET /api/meals` — meal history (supports `?days=N&meal_type=X`)
- `GET /api/meals/stats` — nutrition & spending stats
- `DELETE /api/meals/<meal_id>` — delete meal record
- `PATCH /api/meals/<meal_id>` — update meal record
- `POST /api/recommend` — generate recommendation
- `GET /api/recommend/records` — recommendation history
- `POST /api/recommend/confirm` — confirm selection, save to order_history

## Frontend pages
- `/` — Home page with project intro and navigation
- `/profile` — User preference settings
- `/log` — Log a meal (text + photo upload)
- `/meals` — Meal history
- `/recommend` — Recommend next meal
- `/contacts` — Contact management

## Done when
- The relevant page works and displays correctly
- Backend API returns correct JSON
- Business logic in `lib/` has passing tests
- Mock mode returns data identical in structure to real API (used in automated tests only)
- `occurred_at` === `resolved_occurred_at` for all meal records
- LLM JSON responses are validated before DB write
- A manual verification path is provided
- The demo flow works: `/` → `/profile` → `/log` (photo+text) → `/meals` → `/recommend` → `/contacts`

## Do not
- Do not connect to real Meituan/Ele.me APIs
- Do not implement real payment or order placement
- Do not add user authentication/login in this MVP
- Do not deploy to cloud
- Do not do real-time menu crawling
- Do not provide medical-grade nutrition advice (mark as "仅供参考")
- Do not support multi-user concurrency
- Do not silently change route names, API paths, or database field names
- Do not hardcode the DashScope API key in source code; keep it in `backend/config/llm_config.json` (gitignored)
