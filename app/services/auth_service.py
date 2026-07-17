from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """Business-logic layer that turns an OAuth provider profile into an application User."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def login_or_register(self, provider: str, provider_user_id: str, display_name: str) -> User:
        return self._user_repository.get_or_create_from_oauth(
            provider=provider,
            provider_user_id=provider_user_id,
            display_name=display_name,
        )
