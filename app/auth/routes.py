from flask import Blueprint, abort, current_app, flash, redirect, render_template, session, url_for
from flask.views import MethodView
from flask_login import login_required, login_user, logout_user

from app.auth.oauth_registry import oauth_registry
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


def _require_supported_provider(provider: str) -> None:
    if provider not in current_app.config["OAUTH_SUPPORTED_PROVIDERS"]:
        abort(404, description=f"Unsupported OAuth provider: {provider}")


class LoginPageView(MethodView):
    def get(self):
        return render_template(
            "login.html", providers=sorted(current_app.config["OAUTH_SUPPORTED_PROVIDERS"])
        )


class LoginView(MethodView):
    def get(self, provider: str):
        _require_supported_provider(provider)
        client = oauth_registry.get_client(provider)
        redirect_uri = url_for("auth.callback", provider=provider, _external=True)
        return client.authorize_redirect(redirect_uri)


class CallbackView(MethodView):
    def __init__(self) -> None:
        self._auth_service = AuthService(UserRepository())

    def get(self, provider: str):
        _require_supported_provider(provider)
        client = oauth_registry.get_client(provider)
        token = client.authorize_access_token()

        if provider == "google":
            profile = self._extract_google_profile(client, token)
        elif provider == "github":
            profile = self._extract_github_profile(client, token)

        user = self._auth_service.login_or_register(provider=provider, **profile)
        session.permanent = True
        login_user(user)
        flash(f"Welcome, {user.display_name}.", "success")
        return redirect(url_for("home.index"))

    @staticmethod
    def _extract_google_profile(client, token: dict) -> dict:
        userinfo = token.get("userinfo") or client.parse_id_token(token)
        return {
            "provider_user_id": userinfo["sub"],
            "display_name": userinfo.get("name") or userinfo.get("email") or "Google User",
        }

    @staticmethod
    def _extract_github_profile(client, token: dict) -> dict:
        profile = client.get(current_app.config["GITHUB_USER_PATH"], token=token).json()
        return {
            "provider_user_id": str(profile["id"]),
            "display_name": profile.get("name") or profile.get("login") or "GitHub User",
        }


class LogoutView(MethodView):
    decorators = [login_required]

    def post(self):
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("home.index"))


class AuthBlueprint:
    """Wraps blueprint construction and class-based view registration for OAuth login."""

    def __init__(self) -> None:
        self.blueprint = Blueprint("auth", __name__, url_prefix="/auth")
        self._register_views()

    def _register_views(self) -> None:
        self.blueprint.add_url_rule("/login", view_func=LoginPageView.as_view("login_page"))
        self.blueprint.add_url_rule(
            "/login/<string:provider>", view_func=LoginView.as_view("login")
        )
        self.blueprint.add_url_rule(
            "/callback/<string:provider>", view_func=CallbackView.as_view("callback")
        )
        self.blueprint.add_url_rule("/logout", view_func=LogoutView.as_view("logout"))
