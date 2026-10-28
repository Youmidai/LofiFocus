from fastapi import APIRouter, Depends, status

from app.api.deps import (
    AdminDep,
    DbDep,
    MoodRepoDep,
    PlaylistRepoDep,
    TrackRepoDep,
    get_current_admin,
    get_current_user,
    not_found,
)
from app.api.schemas import PlaylistCreate, PlaylistOut, PlaylistUpdate
from app.models.Playlist import Playlist
from app.models.Track import Track
from app.repositories.TrackRepo import TrackRepo

router = APIRouter(prefix="/playlists", tags=["playlists"], dependencies=[Depends(get_current_user)])
admin_only = [Depends(get_current_admin)]


def load_tracks(tracks: TrackRepo, track_ids: list[int]) -> list[Track]:
    result = []
    for track_id in dict.fromkeys(track_ids):
        track = tracks.read(track_id)
        if track is None:
            raise not_found(f"Track {track_id}")
        result.append(track)
    return result


@router.get("", response_model=list[PlaylistOut])
def list_playlists(playlists: PlaylistRepoDep, mood_id: int | None = None) -> list[Playlist]:
    if mood_id is not None:
        return playlists.list_by_mood(mood_id)
    return playlists.read_all() or []


@router.get("/{playlist_id}", response_model=PlaylistOut)
def get_playlist(playlist_id: int, playlists: PlaylistRepoDep) -> Playlist:
    playlist = playlists.read(playlist_id)
    if playlist is None:
        raise not_found("Playlist")
    return playlist


@router.post("", response_model=PlaylistOut, status_code=status.HTTP_201_CREATED)
def create_playlist(
    data: PlaylistCreate,
    admin: AdminDep,
    playlists: PlaylistRepoDep,
    moods: MoodRepoDep,
    tracks: TrackRepoDep,
    db: DbDep,
) -> Playlist:
    if moods.read(data.mood_id) is None:
        raise not_found("Mood")
    playlist = playlists.create(
        title=data.title,
        description=data.description,
        mood_id=data.mood_id,
        created_by=admin.id,
        tracks=load_tracks(tracks, data.track_ids),
    )
    db.commit()
    return playlist


@router.patch("/{playlist_id}", response_model=PlaylistOut, dependencies=admin_only)
def update_playlist(
    playlist_id: int,
    data: PlaylistUpdate,
    playlists: PlaylistRepoDep,
    moods: MoodRepoDep,
    db: DbDep,
) -> Playlist:
    changes = data.model_dump(exclude_none=True)
    if "mood_id" in changes and moods.read(changes["mood_id"]) is None:
        raise not_found("Mood")
    playlist = playlists.update(playlist_id, **changes)
    if playlist is None:
        raise not_found("Playlist")
    db.commit()
    return playlist


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=admin_only)
def delete_playlist(playlist_id: int, playlists: PlaylistRepoDep, db: DbDep) -> None:
    if not playlists.delete(playlist_id):
        raise not_found("Playlist")
    db.commit()


@router.post("/{playlist_id}/tracks/{track_id}", response_model=PlaylistOut, dependencies=admin_only)
def add_track(
    playlist_id: int,
    track_id: int,
    playlists: PlaylistRepoDep,
    tracks: TrackRepoDep,
    db: DbDep,
) -> Playlist:
    playlist = playlists.read(playlist_id)
    if playlist is None:
        raise not_found("Playlist")
    if tracks.read(track_id) is None:
        raise not_found("Track")
    playlists.add_track(playlist_id, track_id)
    db.commit()
    return playlist


@router.delete("/{playlist_id}/tracks/{track_id}", response_model=PlaylistOut, dependencies=admin_only)
def remove_track(
    playlist_id: int,
    track_id: int,
    playlists: PlaylistRepoDep,
    db: DbDep,
) -> Playlist:
    playlist = playlists.read(playlist_id)
    if playlist is None:
        raise not_found("Playlist")
    playlists.remove_track(playlist_id, track_id)
    db.commit()
    return playlist
