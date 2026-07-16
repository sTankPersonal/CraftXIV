from flask import Flask

from app.config import Config
from app.extensions import db, migrate


class AppFactory:
    """Builds and configures the Flask application instance."""

    def __init__(self, config_object: type[Config] = Config) -> None:
        self._config_object = config_object

    def create_app(self) -> Flask:
        app = Flask(__name__)
        app.config.from_object(self._config_object)

        self._init_extensions(app)
        self._register_blueprints(app)

        return app

    def _init_extensions(self, app: Flask) -> None:
        db.init_app(app)
        migrate.init_app(app, db)

    def _register_blueprints(self, app: Flask) -> None:
        from app.api.routes import ApiBlueprint

        app.register_blueprint(ApiBlueprint().blueprint)
