from flask import Blueprint, current_app, render_template, request
from flask.views import MethodView
from flask_login import current_user, login_required

from app.datasources.garland_tools import GarlandToolsDataSource
from app.repositories.item_repository import ItemRepository
from app.repositories.list_repository import ListRepository
from app.services.item_service import ItemService
from app.services.list_service import ListService


def _search(query: str) -> list[dict]:
    if not query:
        return []
    data_source = GarlandToolsDataSource.from_app_config(current_app.config)
    service = ItemService(ItemRepository(data_source))
    return service.search(query)


def _user_lists() -> list[dict]:
    data_source = GarlandToolsDataSource.from_app_config(current_app.config)
    item_repository = ItemRepository(data_source)
    list_service = ListService(
        list_repository=ListRepository(),
        item_repository=item_repository,
        item_service=ItemService(item_repository),
    )
    return list_service.get_lists(current_user.id)


class HomeView(MethodView):
    decorators = [login_required]

    def get(self):
        query = request.args.get("q", "").strip()
        return render_template(
            "home.html", query=query, results=_search(query), user_lists=_user_lists()
        )


class ItemSearchView(MethodView):
    decorators = [login_required]

    def get(self):
        query = request.args.get("q", "").strip()
        return render_template(
            "_search_results.html", results=_search(query), query=query, user_lists=_user_lists()
        )


class HomeBlueprint:
    """Wraps blueprint construction and class-based view registration for the home/search page."""

    def __init__(self) -> None:
        self.blueprint = Blueprint("home", __name__)
        self._register_views()

    def _register_views(self) -> None:
        self.blueprint.add_url_rule("/", view_func=HomeView.as_view("index"))
        self.blueprint.add_url_rule("/items/search", view_func=ItemSearchView.as_view("item_search"))
