from authlib.integrations.flask_client import OAuth
from flask import Flask


class OAuthRegistry:
    """Wraps Authlib's OAuth client registry and registers the Google/GitHub providers.

    Client id/secret are read by Authlib from `app.config["<NAME>_CLIENT_ID"/"_CLIENT_SECRET"]`;
    every other provider setting (endpoints, scopes) also comes from `app.config`, set by `Config`.
    """

    def __init__(self) -> None:
        self._oauth = OAuth()

    def init_app(self, app: Flask) -> None:
        self._oauth.init_app(app)
        self._oauth.register(
            name="google",
            server_metadata_url=app.config["GOOGLE_SERVER_METADATA_URL"],
            client_kwargs={"scope": app.config["GOOGLE_OAUTH_SCOPE"]},
        )
        self._oauth.register(
            name="github",
            api_base_url=app.config["GITHUB_API_BASE_URL"],
            access_token_url=app.config["GITHUB_ACCESS_TOKEN_URL"],
            authorize_url=app.config["GITHUB_AUTHORIZE_URL"],
            client_kwargs={"scope": app.config["GITHUB_OAUTH_SCOPE"]},
        )

    def get_client(self, provider: str):
        return getattr(self._oauth, provider)


oauth_registry = OAuthRegistry()
