import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "data" / "mealmate.db"
INIT_DISHES_PATH = BASE_DIR / "data" / "init_dishes.json"


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        taste_description TEXT,
        taste_tags TEXT,
        avoid_ingredients TEXT,
        health_goals TEXT,
        body_data TEXT,
        default_budget TEXT,
        remark_habits TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS contacts (
        contact_id TEXT PRIMARY KEY,
        owner_user_id TEXT,
        name TEXT,
        taste_description TEXT,
        taste_tags TEXT,
        avoid_ingredients TEXT,
        health_goals TEXT,
        default_budget TEXT,
        remark_habits TEXT,
        created_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dishes (
        dish_id TEXT PRIMARY KEY,
        name TEXT UNIQUE,
        shop_name TEXT,
        category TEXT,
        ingredients TEXT,
        estimated_nutrition TEXT,
        levels TEXT,
        nutrition_tags TEXT,
        taste_tags TEXT,
        suitable_goals TEXT,
        remark_rules TEXT,
        price REAL,
        price_source TEXT,
        image_path TEXT,
        llm_analysis_raw TEXT,
        confidence REAL,
        created_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS order_history (
        meal_id TEXT PRIMARY KEY,
        user_id TEXT,
        user_type TEXT,
        occurred_at TEXT,
        created_at TEXT,
        meal_type TEXT,
        raw_input TEXT,
        input_type TEXT,
        time_resolution TEXT,
        time_assumption TEXT,
        recognized_foods TEXT,
        dish_ids TEXT,
        total_price REAL,
        total_nutrition TEXT,
        remark_used TEXT,
        budget_range_used TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS recommendation_records (
        rec_id TEXT PRIMARY KEY,
        user_id TEXT,
        created_at TEXT,
        based_on_meal_ids TEXT,
        recent_pattern TEXT,
        budget_range TEXT,
        recommendations TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notes_templates (
        template_id TEXT PRIMARY KEY,
        user_id TEXT,
        dish_category TEXT,
        generated_remark TEXT,
        user_edited_remark TEXT,
        created_at TEXT
    )
    """,
]


TABLE_COLUMNS = {
    "users": [
        "user_id",
        "name",
        "taste_description",
        "taste_tags",
        "avoid_ingredients",
        "health_goals",
        "body_data",
        "default_budget",
        "remark_habits",
        "created_at",
        "updated_at",
    ],
    "contacts": [
        "contact_id",
        "owner_user_id",
        "name",
        "taste_description",
        "taste_tags",
        "avoid_ingredients",
        "health_goals",
        "default_budget",
        "remark_habits",
        "created_at",
    ],
    "dishes": [
        "dish_id",
        "name",
        "shop_name",
        "category",
        "ingredients",
        "estimated_nutrition",
        "levels",
        "nutrition_tags",
        "taste_tags",
        "suitable_goals",
        "remark_rules",
        "price",
        "price_source",
        "image_path",
        "llm_analysis_raw",
        "confidence",
        "created_at",
    ],
    "order_history": [
        "meal_id",
        "user_id",
        "user_type",
        "occurred_at",
        "created_at",
        "meal_type",
        "raw_input",
        "input_type",
        "time_resolution",
        "time_assumption",
        "recognized_foods",
        "dish_ids",
        "total_price",
        "total_nutrition",
        "remark_used",
        "budget_range_used",
    ],
    "recommendation_records": [
        "rec_id",
        "user_id",
        "created_at",
        "based_on_meal_ids",
        "recent_pattern",
        "budget_range",
        "recommendations",
    ],
    "notes_templates": [
        "template_id",
        "user_id",
        "dish_category",
        "generated_remark",
        "user_edited_remark",
        "created_at",
    ],
}


JSON_FIELDS = {
    "users": {
        "taste_tags",
        "avoid_ingredients",
        "health_goals",
        "body_data",
        "default_budget",
        "remark_habits",
    },
    "contacts": {
        "taste_tags",
        "avoid_ingredients",
        "health_goals",
        "default_budget",
        "remark_habits",
    },
    "dishes": {
        "ingredients",
        "estimated_nutrition",
        "levels",
        "nutrition_tags",
        "taste_tags",
        "suitable_goals",
        "remark_rules",
        "llm_analysis_raw",
    },
    "order_history": {
        "time_assumption",
        "recognized_foods",
        "dish_ids",
        "total_nutrition",
        "budget_range_used",
    },
    "recommendation_records": {
        "based_on_meal_ids",
        "recent_pattern",
        "budget_range",
        "recommendations",
    },
    "notes_templates": set(),
}


PRIMARY_KEYS = {
    "users": "user_id",
    "contacts": "contact_id",
    "dishes": "dish_id",
    "order_history": "meal_id",
    "recommendation_records": "rec_id",
    "notes_templates": "template_id",
}


ID_PREFIXES = {
    "users": "user",
    "contacts": "contact",
    "dishes": "dish",
    "order_history": "meal",
    "recommendation_records": "rec",
    "notes_templates": "note",
}


def get_database_path():
    configured_path = os.getenv("MEALMATE_DB_PATH")
    return Path(configured_path) if configured_path else DEFAULT_DB_PATH


def _now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _new_id(table):
    return f"{ID_PREFIXES[table]}-{uuid.uuid4().hex}"


def _connect():
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    return conn


def _encode_value(table, field, value):
    if field in JSON_FIELDS[table] and value is not None:
        return json.dumps(value, ensure_ascii=False)
    return value


def _decode_value(table, field, value):
    if field in JSON_FIELDS[table]:
        if value in (None, ""):
            return None
        return json.loads(value)
    return value


def _decode_row(table, row):
    if row is None:
        return None
    return {
        field: _decode_value(table, field, row[field])
        for field in TABLE_COLUMNS[table]
        if field in row.keys()
    }


def _prepare_record(table, data):
    now = _now()
    record = {column: data.get(column) for column in TABLE_COLUMNS[table]}
    primary_key = PRIMARY_KEYS[table]
    record[primary_key] = record[primary_key] or _new_id(table)

    if "created_at" in record and not record["created_at"]:
        record["created_at"] = now
    if "updated_at" in record:
        record["updated_at"] = now

    return record


def _upsert(table, data):
    record = _prepare_record(table, data)
    columns = TABLE_COLUMNS[table]
    primary_key = PRIMARY_KEYS[table]
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)
    update_sql = ", ".join(
        f"{column}=excluded.{column}" for column in columns if column != primary_key
    )
    values = [_encode_value(table, column, record[column]) for column in columns]

    with _connect() as conn:
        conn.execute(
            f"""
            INSERT INTO {table} ({column_sql})
            VALUES ({placeholders})
            ON CONFLICT({primary_key}) DO UPDATE SET {update_sql}
            """,
            values,
        )
        conn.commit()

    return _get_by_id(table, record[primary_key])


def _get_by_id(table, item_id):
    primary_key = PRIMARY_KEYS[table]
    with _connect() as conn:
        row = conn.execute(
            f"SELECT * FROM {table} WHERE {primary_key} = ?", (item_id,)
        ).fetchone()
    return _decode_row(table, row)


def _query(table, sql, params=()):
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_decode_row(table, row) for row in rows]


def _load_preset_dishes():
    if not INIT_DISHES_PATH.exists():
        return []
    with INIT_DISHES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _import_preset_dishes():
    for dish in _load_preset_dishes():
        add_dish({**dish, "price_source": "preset"})


def init_db():
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.commit()

    _import_preset_dishes()
    return db_path


def init_database():
    return init_db()


def save_user(user):
    return _upsert("users", user)


def get_user(user_id="default_user"):
    return _get_by_id("users", user_id)


def add_contact(contact):
    return _upsert("contacts", contact)


def get_contacts(owner_user_id=None):
    if owner_user_id is None:
        return _query("contacts", "SELECT * FROM contacts ORDER BY created_at DESC")
    return _query(
        "contacts",
        "SELECT * FROM contacts WHERE owner_user_id = ? ORDER BY created_at DESC",
        (owner_user_id,),
    )


def get_contact(contact_id):
    return _get_by_id("contacts", contact_id)


def update_contact(contact_id, updates):
    existing = _get_by_id("contacts", contact_id)
    if existing is None:
        return None
    return _upsert("contacts", {**existing, **updates, "contact_id": contact_id})


def delete_contact(contact_id):
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM contacts WHERE contact_id = ?", (contact_id,))
        conn.commit()
    return cursor.rowcount > 0


def add_dish(dish):
    return _upsert("dishes", dish)


def get_dishes(category=None):
    if category is None:
        return _query("dishes", "SELECT * FROM dishes ORDER BY created_at DESC, name ASC")
    return _query(
        "dishes",
        "SELECT * FROM dishes WHERE category = ? ORDER BY created_at DESC, name ASC",
        (category,),
    )


def get_dish_by_name(name):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM dishes WHERE name = ?", (name,)).fetchone()
    return _decode_row("dishes", row)


def add_meal(meal):
    return _upsert("order_history", meal)


def get_meals(user_id=None):
    if user_id is None:
        return _query(
            "order_history",
            "SELECT * FROM order_history ORDER BY occurred_at DESC, created_at DESC",
        )
    return _query(
        "order_history",
        """
        SELECT * FROM order_history
        WHERE user_id = ?
        ORDER BY occurred_at DESC, created_at DESC
        """,
        (user_id,),
    )


def get_recent_meals(user_id=None, limit=3):
    meals = get_meals(user_id)
    return meals[:limit]


def get_recent_meals_by_type(user_id=None, meal_type=None, limit=3):
    meals = get_meals(user_id)
    if meal_type:
        meals = [m for m in meals if m.get("meal_type") == meal_type]
    return meals[:limit]


def delete_meal(meal_id):
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM order_history WHERE meal_id = ?", (meal_id,))
        conn.commit()
    return cursor.rowcount > 0


def update_meal(meal_id, updates):
    existing = _get_by_id("order_history", meal_id)
    if existing is None:
        return None
    return _upsert("order_history", {**existing, **updates, "meal_id": meal_id})


def add_recommendation(record):
    return _upsert("recommendation_records", record)


def get_recommendations(user_id=None):
    if user_id is None:
        return _query(
            "recommendation_records",
            "SELECT * FROM recommendation_records ORDER BY created_at DESC",
        )
    return _query(
        "recommendation_records",
        """
        SELECT * FROM recommendation_records
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    )


def add_note_template(template):
    return _upsert("notes_templates", template)


def get_note_templates(user_id=None, dish_category=None):
    clauses = []
    params = []
    if user_id is not None:
        clauses.append("user_id = ?")
        params.append(user_id)
    if dish_category is not None:
        clauses.append("dish_category = ?")
        params.append(dish_category)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return _query(
        "notes_templates",
        f"SELECT * FROM notes_templates {where_sql} ORDER BY created_at DESC",
        tuple(params),
    )
