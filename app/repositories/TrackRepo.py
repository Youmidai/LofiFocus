from sqlalchemy import func, select

from app.models.associations import playlist_track
from app.models.Mood import Mood
from app.models.Playlist import Playlist
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

    def search(
        self,
        mood_id: int | None = None,
        bpm_min: int | None = None,
        bpm_max: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Track]:
        stmt = select(self.model)
        if mood_id is not None:
            stmt = stmt.join(self.model.moods).where(Mood.id == mood_id)
        if bpm_min is not None:
            stmt = stmt.where(self.model.bpm >= bpm_min)
        if bpm_max is not None:
            stmt = stmt.where(self.model.bpm <= bpm_max)
        stmt = stmt.order_by(self.model.id).limit(limit).offset(offset)
        return list(self.db.scalars(stmt))

    def most_popular_by_playlist_mood(self, mood_id: int) -> tuple[Track, int] | None:
        playlist_ids = select(Playlist.id).where(Playlist.mood_id == mood_id)
        playlist_count = func.count(playlist_track.c.playlist_id).label("playlist_count")

        row = self.db.execute(
            select(playlist_track.c.track_id, playlist_count)
            .where(playlist_track.c.playlist_id.in_(playlist_ids))
            .group_by(playlist_track.c.track_id)
            .order_by(playlist_count.desc(), playlist_track.c.track_id)
            .limit(1)
        ).first()

        if row is None:
            return None
        track = self.read(row.track_id)
        if track is None:
            return None
        return track, row.playlist_count
