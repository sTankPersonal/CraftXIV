import os
from datetime import timedelta


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    assert value, f"Missing required environment variable: {name}"
    return value


class Config:
    SECRET_KEY = _require_env("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _require_env("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Users are logged out and must re-authenticate (re-syncing their display name from the
    # OAuth provider) after this long, regardless of activity.
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    OAUTH_SUPPORTED_PROVIDERS = frozenset(_require_env("OAUTH_SUPPORTED_PROVIDERS").split(","))

    GOOGLE_CLIENT_ID = _require_env("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = _require_env("GOOGLE_CLIENT_SECRET")
    GOOGLE_SERVER_METADATA_URL = _require_env("GOOGLE_SERVER_METADATA_URL")
    GOOGLE_OAUTH_SCOPE = _require_env("GOOGLE_OAUTH_SCOPE")

    GITHUB_CLIENT_ID = _require_env("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = _require_env("GITHUB_CLIENT_SECRET")
    GITHUB_API_BASE_URL = _require_env("GITHUB_API_BASE_URL")
    GITHUB_ACCESS_TOKEN_URL = _require_env("GITHUB_ACCESS_TOKEN_URL")
    GITHUB_AUTHORIZE_URL = _require_env("GITHUB_AUTHORIZE_URL")
    GITHUB_OAUTH_SCOPE = _require_env("GITHUB_OAUTH_SCOPE")
    GITHUB_USER_PATH = _require_env("GITHUB_USER_PATH")

    GARLAND_TOOLS_BASE_URL = _require_env("GARLAND_TOOLS_BASE_URL")
    GARLAND_TOOLS_SEARCH_PATH = _require_env("GARLAND_TOOLS_SEARCH_PATH")
    GARLAND_TOOLS_ITEM_PATH_TEMPLATE = _require_env("GARLAND_TOOLS_ITEM_PATH_TEMPLATE")
    GARLAND_TOOLS_NODE_PATH_TEMPLATE = _require_env("GARLAND_TOOLS_NODE_PATH_TEMPLATE")
    GARLAND_TOOLS_NPC_PATH_TEMPLATE = _require_env("GARLAND_TOOLS_NPC_PATH_TEMPLATE")
    GARLAND_TOOLS_CORE_DATA_PATH = _require_env("GARLAND_TOOLS_CORE_DATA_PATH")
    GARLAND_TOOLS_REQUEST_TIMEOUT = int(_require_env("GARLAND_TOOLS_REQUEST_TIMEOUT"))


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
