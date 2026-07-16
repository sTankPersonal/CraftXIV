from app.repositories.resource_repository import ResourceRepository


def test_cache_miss_fetches_from_origin_and_persists(app, fake_data_source):
    repository = ResourceRepository(data_source=fake_data_source)

    result = repository.get("foo")

    assert result.from_cache is False
    assert result.resource.payload == fake_data_source.payload
    assert fake_data_source.call_count == 1


def test_cache_hit_does_not_call_origin(app, fake_data_source):
    repository = ResourceRepository(data_source=fake_data_source)

    repository.get("foo")
    result = repository.get("foo")

    assert result.from_cache is True
    assert fake_data_source.call_count == 1
