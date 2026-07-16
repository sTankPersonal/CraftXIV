from flask import Blueprint, current_app, render_template, request
from flask.views import MethodView

from app.datasources.garland_tools import GarlandToolsDataSource
from app.repositories.item_repository import ItemRepository
from app.services.item_service import ItemService


class HomeView(MethodView):
    def get(self):
        return render_template("home.html")


class ItemSearchView(MethodView):
    def get(self):
        query = request.args.get("q", "").strip()
        results = []
        if query:
            data_source = GarlandToolsDataSource.from_app_config(current_app.config)
            service = ItemService(ItemRepository(data_source))
            results = service.search(query)
        return render_template("_search_results.html", results=results, query=query)


class HomeBlueprint:
    """Wraps blueprint construction and class-based view registration for the home/search page."""

    def __init__(self) -> None:
        self.blueprint = Blueprint("home", __name__)
        self._register_views()

    def _register_views(self) -> None:
        self.blueprint.add_url_rule("/", view_func=HomeView.as_view("index"))
        self.blueprint.add_url_rule("/items/search", view_func=ItemSearchView.as_view("item_search"))
