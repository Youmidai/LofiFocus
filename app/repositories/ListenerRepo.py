from sqlalchemy import select

from app.models.Listener import Listener
from app.repositories.BaseRepo import BaseRepo


class ListenerRepo(BaseRepo[Listener]):
    model = Listener

    def find_by_email(self, email: str) -> Listener | None:
        return self.db.scalar(select(Listener).where(Listener.email == email))

    def find_by_username(self, username: str) -> Listener | None:
        return self.db.scalar(select(self.model).where(self.model.username == username))