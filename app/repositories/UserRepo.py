from sqlalchemy import select

from app.models.User import User
from app.repositories.BaseRepo import BaseRepo


class UserRepository(BaseRepo[User]):
    model = User

    def find_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(self.model).where(self.model.email == email))

    def find_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(self.model).where(self.model.username == username))

    def list_by_type(self, user_type: str) -> list[User]:
        return list(self.db.scalars(
            select(self.model).where(self.model.type == user_type)
        ))