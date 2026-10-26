from app.core.security import hash_password, verify_password
from app.models.Listener import Listener
from app.models.User import User
from app.repositories.Exceptions import DuplicateError
from app.repositories.ListenerRepo import ListenerRepo
from app.repositories.UserRepo import UserRepository


class AuthService:
    """Регистрация и проверка учётных данных. HTTP здесь не используется."""

    def __init__(self, users: UserRepository, listeners: ListenerRepo) -> None:
        self.users = users
        self.listeners = listeners

    def register(self, email: str, username: str, password: str) -> Listener:
        email = email.lower()
        if self.users.find_by_email(email) is not None:
            raise DuplicateError("Email already registered")
        if self.users.find_by_username(username) is not None:
            raise DuplicateError("Username already taken")
        return self.listeners.create(
            email=email,
            username=username,
            password=hash_password(password),
            type="listener",
        )

    def authenticate(self, login: str, password: str) -> User | None:
        """login — username или email."""
        user = self.users.find_by_username(login) or self.users.find_by_email(login.lower())
        if user is None or not verify_password(password, user.password):
            return None
        return user
