from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from api.contacts import contacts_bp
from api.log_meal import log_meal_bp
from api.meals import meals_bp
from api.profile import profile_bp
from api.recommend import recommend_bp
from lib.database import init_database


def create_app():
    app = Flask(__name__)
    CORS(app)

    init_database()
    app.register_blueprint(contacts_bp)
    app.register_blueprint(log_meal_bp)
    app.register_blueprint(meals_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(recommend_bp)

    @app.get("/api/health")
    def health_check():
        return jsonify({"status": "ok"})

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)
