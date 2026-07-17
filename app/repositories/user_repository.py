from sqlalchemy.orm import scoped_session

from app.extensions import db
from app.models.user import User


class UserRepository:
    """Persistence for User records, keyed by OAuth provider identity."""

    def __init__(self, session: scoped_session | None = None) -> None:
        self._session = session or db.session

    def get_by_id(self, user_id: str) -> User | None:
        return self._session.get(User, int(user_id))

    def get_or_create_from_oauth(self, provider: str, provider_user_id: str, display_name: str) -> User:
        existing = (
            self._session.query(User)
            .filter_by(provider=provider, provider_user_id=provider_user_id)
            .one_or_none()
        )
        if existing is not None:
            if existing.display_name != display_name:
                existing.display_name = display_name
                self._session.commit()
            return existing

        user = User(provider=provider, provider_user_id=provider_user_id, display_name=display_name)
        self._session.add(user)
        self._session.commit()
        return user
