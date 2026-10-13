from sqlalchemy import select

from app.models.Administrator import Administrator
from app.repositories.BaseRepo import BaseRepo


class AdministratorRepo(BaseRepo[Administrator]):
    model = Administrator

    def find_by_email(self, email: str) -> Administrator | None:
        return self.db.scalar(select(self.model).where(self.model.email == email))

    def find_by_username(self, username: str) -> Administrator | None:
        return self.db.scalar(select(self.model).where(self.model.username == username))