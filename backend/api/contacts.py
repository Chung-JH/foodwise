from flask import Blueprint, jsonify, request

from lib import contacts
from lib.llm import LLMError


contacts_bp = Blueprint("contacts", __name__, url_prefix="/api")


@contacts_bp.get("/contacts")
def get_contacts():
    return jsonify({"contacts": contacts.list_contacts()})


@contacts_bp.post("/contacts")
def create_contact():
    payload = request.get_json(silent=True) or {}
    try:
        contact = contacts.create_contact(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LLMError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(contact), 201


@contacts_bp.put("/contacts/<contact_id>")
def update_contact(contact_id):
    payload = request.get_json(silent=True) or {}
    try:
        contact = contacts.update_contact(contact_id, payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LLMError as exc:
        return jsonify({"error": str(exc)}), 502
    if contact is None:
        return jsonify({"error": "亲友档案不存在"}), 404
    return jsonify(contact)


@contacts_bp.delete("/contacts/<contact_id>")
def delete_contact(contact_id):
    if not contacts.delete_contact(contact_id):
        return jsonify({"error": "亲友档案不存在"}), 404
    return jsonify({"deleted": True, "contact_id": contact_id})
