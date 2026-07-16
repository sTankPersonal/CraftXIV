from flask import Blueprint, jsonify
from flask.views import MethodView
from sqlalchemy import text

from app.datasources.example import ExampleDataSource
from app.extensions import db
from app.repositories.resource_repository import ResourceRepository
from app.services.resource_service import ResourceService


class HealthView(MethodView):
    def get(self):
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok"})


class ResourceView(MethodView):
    def __init__(self) -> None:
        repository = ResourceRepository(data_source=ExampleDataSource())
        self._service = ResourceService(repository)

    def get(self, key: str):
        return jsonify(self._service.get_resource(key))


class ApiBlueprint:
    """Wraps blueprint construction and class-based view registration."""

    def __init__(self) -> None:
        self.blueprint = Blueprint("api", __name__)
        self._register_views()

    def _register_views(self) -> None:
        self.blueprint.add_url_rule(
            "/health", view_func=HealthView.as_view("health")
        )
        self.blueprint.add_url_rule(
            "/resources/<string:key>", view_func=ResourceView.as_view("resource")
        )
