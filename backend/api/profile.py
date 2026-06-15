from flask import Blueprint, jsonify, request

from lib import profile as profile_service
from lib.llm import LLMError


profile_bp = Blueprint("profile", __name__, url_prefix="/api")


@profile_bp.get("/profile")
def get_profile():
    return jsonify(profile_service.get_profile())


@profile_bp.post("/profile")
def save_profile():
    payload = request.get_json(silent=True) or {}
    try:
        saved = profile_service.save_profile(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LLMError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(saved)
