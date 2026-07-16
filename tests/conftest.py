import pytest

from app.config import TestConfig
from app.datasources.base import DataSource
from app.extensions import db
from app.factory import AppFactory


class FakeDataSource(DataSource):
    """Records calls so tests can assert whether the origin was hit."""

    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload or {"value": "from-origin"}
        self.call_count = 0

    def fetch(self, key: str) -> dict:
        self.call_count += 1
        return dict(self.payload)


@pytest.fixture
def app():
    application = AppFactory(config_object=TestConfig).create_app()

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def fake_data_source():
    return FakeDataSource()
