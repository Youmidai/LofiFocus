from sqlalchemy import select

from app.models.Mood import Mood
from app.repositories.BaseRepo import BaseRepo


class MoodRepo(BaseRepo[Mood]):
    model = Mood

    def find_by_name(self, name: str) -> Mood | None:
        return self.db.scalar(select(self.model).where(self.model.name == name))

    def list_by_name_pattern(self, pattern: str) -> list[Mood]:
        return list(self.db.scalars(
            select(self.model).where(self.model.name.ilike(f"%{pattern}%"))
        ))