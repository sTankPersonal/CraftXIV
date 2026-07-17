from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.datasources.garland_tools import GarlandToolsDataSource
from app.repositories.item_repository import ItemRepository
from app.repositories.list_repository import ListRepository
from app.services.item_service import ItemService
from app.services.list_service import ListService


class ItemViewBase(MethodView):
    decorators = [login_required]

    def __init__(self) -> None:
        data_source = GarlandToolsDataSource.from_app_config(current_app.config)
        self._item_repository = ItemRepository(data_source)
        self._service = ItemService(self._item_repository)


class ItemDetailView(ItemViewBase):
    def get(self, game_id: int):
        item = self._service.get_item(game_id)
        tree = self._service.get_tree(game_id)
        requirements = self._service.get_requirements(game_id, quantity=1)

        list_service = ListService(
            list_repository=ListRepository(),
            item_repository=self._item_repository,
            item_service=self._service,
        )
        user_lists = list_service.get_lists(current_user.id)

        return render_template(
            "item_detail.html",
            item=item,
            tree=tree,
            requirements=requirements["requirements"],
            quantity=1,
            user_lists=user_lists,
        )


class ItemRequirementsView(ItemViewBase):
    def get(self, game_id: int):
        quantity = request.args.get("quantity", 1, type=int)
        buy_ids = set(request.args.getlist("buy", type=int))
        requirements = self._service.get_requirements(game_id, quantity, buy_ids)
        return render_template(
            "_requirements.html", requirements=requirements["requirements"], quantity=quantity
        )


class ItemAddToListView(ItemViewBase):
    def post(self, game_id: int):
        list_id = request.form.get("list_id", type=int)
        quantity = request.form.get("quantity", 1, type=int)

        list_service = ListService(
            list_repository=ListRepository(),
            item_repository=self._item_repository,
            item_service=self._service,
        )
        result = list_service.add_item(list_id, current_user.id, game_id, quantity)
        if result is None:
            flash("Could not add item to that list.", "error")
        else:
            flash(f"Added {quantity}x {result['item']['name']} to your list.", "success")

        if request.form.get("source") == "search":
            query = request.form.get("q", "")
            return redirect(url_for("home.index", q=query) if query else url_for("home.index"))
        return redirect(url_for("items.detail", game_id=game_id))


class ItemBlueprint:
    """Wraps blueprint construction and class-based view registration for item pages."""

    def __init__(self) -> None:
        self.blueprint = Blueprint("items", __name__, url_prefix="/items")
        self._register_views()

    def _register_views(self) -> None:
        self.blueprint.add_url_rule("/<int:game_id>", view_func=ItemDetailView.as_view("detail"))
        self.blueprint.add_url_rule(
            "/<int:game_id>/requirements", view_func=ItemRequirementsView.as_view("requirements")
        )
        self.blueprint.add_url_rule(
            "/<int:game_id>/add-to-list", view_func=ItemAddToListView.as_view("add_to_list")
        )
