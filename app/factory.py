from flask import Flask

from app.config import Config
from app.extensions import db, login_manager, migrate


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

        login_manager.init_app(app)
        login_manager.login_view = "auth.login_page"
        self._register_user_loader()

        from app.auth.oauth_registry import oauth_registry

        oauth_registry.init_app(app)

    def _register_user_loader(self) -> None:
        from app.repositories.user_repository import UserRepository

        login_manager.user_loader(UserRepository().get_by_id)

    def _register_blueprints(self, app: Flask) -> None:
        from app.api.health_routes import HealthBlueprint
        from app.auth.routes import AuthBlueprint
        from app.web.home_routes import HomeBlueprint
        from app.web.item_routes import ItemBlueprint
        from app.web.list_routes import ListBlueprint

        app.register_blueprint(HealthBlueprint().blueprint)
        app.register_blueprint(AuthBlueprint().blueprint)
        app.register_blueprint(HomeBlueprint().blueprint)
        app.register_blueprint(ItemBlueprint().blueprint)
        app.register_blueprint(ListBlueprint().blueprint)
