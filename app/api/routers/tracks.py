from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import AdminDep, DbDep, MoodRepoDep, TrackRepoDep, get_current_admin, get_current_user, not_found
from app.api.schemas import TrackCreate, TrackOut, TrackUpdate
from app.models.Mood import Mood
from app.models.Track import Track
from app.repositories.MoodRepo import MoodRepo

router = APIRouter(prefix="/tracks", tags=["tracks"], dependencies=[Depends(get_current_user)])
admin_only = [Depends(get_current_admin)]


def load_moods(moods: MoodRepo, mood_ids: list[int]) -> list[Mood]:
    result = []
    for mood_id in dict.fromkeys(mood_ids):  # без дубликатов, порядок сохраняется
        mood = moods.read(mood_id)
        if mood is None:
            raise not_found(f"Mood {mood_id}")
        result.append(mood)
    return result


@router.get("", response_model=list[TrackOut])
def list_tracks(
    tracks: TrackRepoDep,
    mood_id: int | None = None,
    bpm_min: Annotated[int | None, Query(ge=0)] = None,
    bpm_max: Annotated[int | None, Query(ge=0)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Track]:
    return tracks.search(mood_id=mood_id, bpm_min=bpm_min, bpm_max=bpm_max, limit=limit, offset=offset)


@router.get("/{track_id}", response_model=TrackOut)
def get_track(track_id: int, tracks: TrackRepoDep) -> Track:
    track = tracks.read(track_id)
    if track is None:
        raise not_found("Track")
    return track


@router.post("", response_model=TrackOut, status_code=status.HTTP_201_CREATED)
def create_track(
    data: TrackCreate,
    admin: AdminDep,
    tracks: TrackRepoDep,
    moods: MoodRepoDep,
    db: DbDep,
) -> Track:
    track = tracks.create(
        title=data.title,
        file_url=data.file_url,
        duration_sec=data.duration_sec,
        bpm=data.bpm,
        added_by_id=admin.id,
        moods=load_moods(moods, data.mood_ids),
    )
    db.commit()
    return track


@router.patch("/{track_id}", response_model=TrackOut, dependencies=admin_only)
def update_track(
    track_id: int,
    data: TrackUpdate,
    tracks: TrackRepoDep,
    moods: MoodRepoDep,
    db: DbDep,
) -> Track:
    changes = data.model_dump(exclude_none=True)
    mood_ids = changes.pop("mood_ids", None)
    track = tracks.update(track_id, **changes)
    if track is None:
        raise not_found("Track")
    if mood_ids is not None:
        track.moods = load_moods(moods, mood_ids)
    db.commit()
    return track


@router.delete("/{track_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=admin_only)
def delete_track(track_id: int, tracks: TrackRepoDep, db: DbDep) -> None:
    if not tracks.delete(track_id):
        raise not_found("Track")
    db.commit()
