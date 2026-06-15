import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from lib import log_meal
from lib.llm import LLMError


BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

log_meal_bp = Blueprint("log_meal", __name__, url_prefix="/api")


@log_meal_bp.post("/log-meal")
def create_text_meal():
    payload = request.get_json(silent=True) or {}
    try:
        result = log_meal.log_text_meal(payload.get("text"))
    except log_meal.MealLogError as exc:
        return jsonify({"error": str(exc)}), 400
    except LLMError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(result)


@log_meal_bp.post("/log-meal/photo")
def analyze_meal_photo():
    uploaded_file = request.files.get("image") or request.files.get("file")
    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({"error": "请上传图片文件"}), 400

    try:
        image_path = _save_upload(uploaded_file)
        result = log_meal.analyze_photo(image_path, request.form.get("price"))
    except log_meal.MealLogError as exc:
        return jsonify({"error": str(exc)}), 400
    except LLMError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(result)


@log_meal_bp.post("/log-meal/photo/save")
def save_meal_photo():
    payload = request.get_json(silent=True) or {}
    try:
        result = log_meal.save_photo_meal(
            payload.get("analysis") or {},
            occurred_at=payload.get("occurred_at"),
            user_price=payload.get("price"),
        )
    except log_meal.MealLogError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(result)


def _save_upload(uploaded_file):
    original_name = secure_filename(uploaded_file.filename)
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise log_meal.MealLogError("仅支持 jpg、jpeg、png、webp 图片")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    image_path = UPLOAD_DIR / filename
    uploaded_file.save(image_path)
    return image_path
