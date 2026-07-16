from app.repositories.item_repository import ItemRepository
from app.services.item_service import ItemService


def _service(fake_data_source) -> ItemService:
    return ItemService(ItemRepository(data_source=fake_data_source))


def test_get_tree_nests_children_with_quantities(app, fake_data_source):
    service = _service(fake_data_source)

    tree = service.get_tree(1)

    assert tree["id"] == 1
    assert tree["quantity"] == 1
    children_by_id = {child["id"]: child for child in tree["children"]}
    assert children_by_id[2]["quantity"] == 3
    assert children_by_id[2]["children"] == []
    assert children_by_id[3]["quantity"] == 1


def test_get_requirements_flattens_leaves_and_scales_by_quantity(app, fake_data_source):
    service = _service(fake_data_source)

    result = service.get_requirements(1, quantity=2)

    requirements_by_id = {entry["id"]: entry["quantity"] for entry in result["requirements"]}
    assert requirements_by_id == {2: 6, 3: 2}


def test_search_returns_matching_names(app, fake_data_source):
    service = _service(fake_data_source)

    results = service.search("ore")

    assert results == [{"id": 2, "name": "Ore"}]
