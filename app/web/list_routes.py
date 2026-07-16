from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.datasources.garland_tools import GarlandToolsDataSource
from app.repositories.item_repository import ItemRepository
from app.repositories.list_repository import ListRepository
from app.services.item_service import ItemService
from app.services.list_service import ListService


class ListViewBase(MethodView):
    decorators = [login_required]

    def __init__(self) -> None:
        data_source = GarlandToolsDataSource.from_app_config(current_app.config)
        item_repository = ItemRepository(data_source)
        self._service = ListService(
            list_repository=ListRepository(),
            item_repository=item_repository,
            item_service=ItemService(item_repository),
        )


class ListCollectionView(ListViewBase):
    def get(self):
        lists = self._service.get_lists(current_user.id)
        return render_template("lists.html", lists=lists)

    def post(self):
        name = request.form.get("name", "").strip()
        if name:
            self._service.create_list(current_user.id, name)
        else:
            flash("List name is required.", "error")
        return redirect(url_for("lists.collection"))


class ListDetailView(ListViewBase):
    def get(self, list_id: int):
        result = self._service.get_list(list_id, current_user.id)
        if result is None:
            abort(404)
        requirements = self._service.get_list_requirements(list_id, current_user.id)
        return render_template(
            "list_detail.html",
            crafting_list=result,
            items=result["items"],
            requirements=requirements["requirements"],
        )


class ListRenameView(ListViewBase):
    def post(self, list_id: int):
        name = request.form.get("name", "").strip()
        if name:
            result = self._service.rename_list(list_id, current_user.id, name)
            if result is None:
                abort(404)
        else:
            flash("List name is required.", "error")
        return redirect(url_for("lists.detail", list_id=list_id))


class ListDeleteView(ListViewBase):
    def post(self, list_id: int):
        if not self._service.delete_list(list_id, current_user.id):
            abort(404)
        return redirect(url_for("lists.collection"))


class ListItemsView(ListViewBase):
    def post(self, list_id: int):
        game_id = request.form.get("game_id", type=int)
        quantity = request.form.get("quantity", 1, type=int)
        result = self._service.add_item(list_id, current_user.id, game_id, quantity)
        if result is None:
            abort(404)
        return redirect(url_for("lists.detail", list_id=list_id))


class ListItemUpdateView(ListViewBase):
    def post(self, list_id: int, list_item_id: int):
        quantity = request.form.get("quantity", 1, type=int)
        result = self._service.update_item_quantity(list_id, current_user.id, list_item_id, quantity)
        if result is None:
            abort(404)
        return redirect(url_for("lists.detail", list_id=list_id))


class ListItemDeleteView(ListViewBase):
    def post(self, list_id: int, list_item_id: int):
        if not self._service.remove_item(list_id, current_user.id, list_item_id):
            abort(404)
        return redirect(url_for("lists.detail", list_id=list_id))


class ListBlueprint:
    """Wraps blueprint construction and class-based view registration for crafting list pages.

    All routes require login and are scoped to `current_user`.
    """

    def __init__(self) -> None:
        self.blueprint = Blueprint("lists", __name__, url_prefix="/lists")
        self._register_views()

    def _register_views(self) -> None:
        self.blueprint.add_url_rule("", view_func=ListCollectionView.as_view("collection"))
        self.blueprint.add_url_rule("/<int:list_id>", view_func=ListDetailView.as_view("detail"))
        self.blueprint.add_url_rule(
            "/<int:list_id>/rename", view_func=ListRenameView.as_view("rename")
        )
        self.blueprint.add_url_rule(
            "/<int:list_id>/delete", view_func=ListDeleteView.as_view("delete")
        )
        self.blueprint.add_url_rule(
            "/<int:list_id>/items", view_func=ListItemsView.as_view("items")
        )
        self.blueprint.add_url_rule(
            "/<int:list_id>/items/<int:list_item_id>/update",
            view_func=ListItemUpdateView.as_view("item_update"),
        )
        self.blueprint.add_url_rule(
            "/<int:list_id>/items/<int:list_item_id>/delete",
            view_func=ListItemDeleteView.as_view("item_delete"),
        )
