from sqlalchemy import select

from app.models.Mood import Mood
from app.models.Track import Track
from app.repositories.BaseRepo import BaseRepo


class TrackRepo(BaseRepo[Track]):
    model = Track

    def list_by_bpm_range(self, lo: int, hi: int) -> list[Track]:
        return list(self.db.scalars(
            select(self.model).where(self.model.bpm.between(lo, hi))
        ))

    def list_by_mood(self, mood_id: int) -> list[Track]:
        return list(self.db.scalars(
            select(self.model).join(self.model.moods).where(Mood.id == mood_id)
        ))

    def list_by_administrator(self, admin_id: int) -> list[Track]:
        return list(self.db.scalars(
            select(self.model).where(self.model.added_by_id == admin_id)
        ))