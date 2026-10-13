from sqlalchemy import select

from app.models.Playlist import Playlist
from app.models.Track import Track
from app.repositories.BaseRepo import BaseRepo
from app.repositories.Exceptions import RepositoryError


class PlaylistRepo(BaseRepo[Playlist]):
    model = Playlist

    def list_by_creator(self, admin_id: int) -> list[Playlist]:
        return list(self.db.scalars(
            select(self.model).where(self.model.created_by == admin_id)
        ))

    def list_by_mood(self, mood_id: int) -> list[Playlist]:
        return list(self.db.scalars(
            select(self.model).where(self.model.mood_id == mood_id)
        ))

    def add_track(self, playlist_id: int, track_id: int) -> None:
        playlist = self.read(playlist_id)
        if playlist is None:
            raise RepositoryError(f"Playlist {playlist_id} not found")
        track = self.db.get(Track, track_id)
        if track is None:
            raise RepositoryError(f"Track {track_id} not found")
        if track not in playlist.tracks:
            playlist.tracks.append(track)
            self.db.flush()

    def remove_track(self, playlist_id: int, track_id: int) -> None:
        playlist = self.read(playlist_id)
        if playlist is None:
            raise RepositoryError(f"Playlist {playlist_id} not found")
        track = self.db.get(Track, track_id)
        if track is not None and track in playlist.tracks:
            playlist.tracks.remove(track)
            self.db.flush()