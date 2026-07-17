from app.extensions import db
from app.models.user import User
from app.repositories.item_repository import ItemRepository
from app.repositories.list_repository import ListRepository
from app.services.item_service import ItemService
from app.services.list_service import ListService


def _make_user() -> User:
    user = User(provider="google", provider_user_id="abc123", display_name="Tester")
    db.session.add(user)
    db.session.commit()
    return user


def _service(fake_data_source) -> ListService:
    item_repository = ItemRepository(data_source=fake_data_source)
    return ListService(
        list_repository=ListRepository(),
        item_repository=item_repository,
        item_service=ItemService(item_repository),
    )


def test_create_and_get_list(app, fake_data_source):
    user = _make_user()
    service = _service(fake_data_source)

    created = service.create_list(user.id, "My List")
    fetched = service.get_list(created["id"], user.id)

    assert fetched["name"] == "My List"
    assert fetched["items"] == []


def test_get_list_scoped_to_owner(app, fake_data_source):
    owner = _make_user()
    other_user = User(provider="github", provider_user_id="xyz", display_name="Other")
    db.session.add(other_user)
    db.session.commit()
    service = _service(fake_data_source)

    created = service.create_list(owner.id, "My List")

    assert service.get_list(created["id"], other_user.id) is None


def test_add_item_and_aggregate_list_requirements(app, fake_data_source):
    user = _make_user()
    service = _service(fake_data_source)
    crafting_list = service.create_list(user.id, "My List")

    service.add_item(crafting_list["id"], user.id, game_id=1, quantity=2)

    result = service.get_list_requirements(crafting_list["id"], user.id)

    requirements_by_id = {entry["id"]: entry["quantity"] for entry in result["requirements"]}
    assert requirements_by_id == {2: 6, 3: 2}


def test_remove_item(app, fake_data_source):
    user = _make_user()
    service = _service(fake_data_source)
    crafting_list = service.create_list(user.id, "My List")
    list_item = service.add_item(crafting_list["id"], user.id, game_id=1, quantity=1)

    removed = service.remove_item(crafting_list["id"], user.id, list_item["id"])

    assert removed is True
    assert service.get_list(crafting_list["id"], user.id)["items"] == []
