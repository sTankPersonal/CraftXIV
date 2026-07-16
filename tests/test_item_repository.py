from app.repositories.item_repository import ItemRepository


def test_cache_miss_fetches_full_tree_and_persists(app, fake_data_source):
    repository = ItemRepository(data_source=fake_data_source)

    item = repository.get_or_fetch(1)

    assert item.name == "Widget"
    assert item.is_leaf() is False
    assert sorted(fake_data_source.fetch_calls) == [1, 2, 3]

    component_ids = {component.component.game_id: component.quantity for component in item.components}
    assert component_ids == {2: 3, 3: 1}


def test_cache_hit_does_not_call_origin(app, fake_data_source):
    repository = ItemRepository(data_source=fake_data_source)

    repository.get_or_fetch(1)
    fake_data_source.fetch_calls.clear()
    repository.get_or_fetch(1)

    assert fake_data_source.fetch_calls == []


def test_shared_ingredient_is_fetched_only_once(app, fake_data_source):
    repository = ItemRepository(data_source=fake_data_source)

    repository.get_or_fetch(2)
    fake_data_source.fetch_calls.clear()
    repository.get_or_fetch(1)

    assert sorted(fake_data_source.fetch_calls) == [1, 3]
