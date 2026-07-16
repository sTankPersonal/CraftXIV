from flask import Blueprint, jsonify
from flask.views import MethodView
from sqlalchemy import text

from app.extensions import db


class HealthView(MethodView):
    def get(self):
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok"})


class HealthBlueprint:
    """Wraps blueprint construction and class-based view registration."""

    def __init__(self) -> None:
        self.blueprint = Blueprint("health", __name__)
        self._register_views()

    def _register_views(self) -> None:
        self.blueprint.add_url_rule("/health", view_func=HealthView.as_view("health"))
