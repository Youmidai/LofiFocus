from fastapi import APIRouter, status

from app.api.deps import DbDep, ListenerDep, TrackRepoDep, not_found
from app.api.schemas import TrackOut
from app.models.Track import Track

router = APIRouter(prefix="/favourites", tags=["favourites"])


@router.get("", response_model=list[TrackOut])
def list_favourites(listener: ListenerDep) -> list[Track]:
    return listener.favourite_tracks


@router.put("/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_favourite(track_id: int, listener: ListenerDep, tracks: TrackRepoDep, db: DbDep) -> None:
    """Идемпотентно: повторное добавление ничего не ломает."""
    track = tracks.read(track_id)
    if track is None:
        raise not_found("Track")
    if track not in listener.favourite_tracks:
        listener.favourite_tracks.append(track)
        db.commit()


@router.delete("/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favourite(track_id: int, listener: ListenerDep, tracks: TrackRepoDep, db: DbDep) -> None:
    track = tracks.read(track_id)
    if track is not None and track in listener.favourite_tracks:
        listener.favourite_tracks.remove(track)
        db.commit()
