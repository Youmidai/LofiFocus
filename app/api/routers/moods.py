from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbDep, MoodRepoDep, TrackRepoDep, get_current_admin, get_current_user, not_found
from app.api.schemas import MoodIn, MoodOut, PopularTrackOut, TrackOut
from app.models.Mood import Mood

# Чтение — любому авторизованному пользователю, изменение — только администратору.
router = APIRouter(prefix="/moods", tags=["moods"], dependencies=[Depends(get_current_user)])
admin_only = [Depends(get_current_admin)]


@router.get("", response_model=list[MoodOut])
def list_moods(moods: MoodRepoDep) -> list[Mood]:
    return moods.read_all() or []


@router.get("/{mood_id}", response_model=MoodOut)
def get_mood(mood_id: int, moods: MoodRepoDep) -> Mood:
    mood = moods.read(mood_id)
    if mood is None:
        raise not_found("Mood")
    return mood


@router.post("", response_model=MoodOut, status_code=status.HTTP_201_CREATED, dependencies=admin_only)
def create_mood(data: MoodIn, moods: MoodRepoDep, db: DbDep) -> Mood:
    mood = moods.create(name=data.name)
    db.commit()
    return mood


@router.put("/{mood_id}", response_model=MoodOut, dependencies=admin_only)
def rename_mood(mood_id: int, data: MoodIn, moods: MoodRepoDep, db: DbDep) -> Mood:
    existing = moods.find_by_name(data.name)
    if existing is not None and existing.id != mood_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Mood with this name already exists")
    mood = moods.update(mood_id, name=data.name)
    if mood is None:
        raise not_found("Mood")
    db.commit()
    return mood


@router.delete("/{mood_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=admin_only)
def delete_mood(mood_id: int, moods: MoodRepoDep, db: DbDep) -> None:
    if not moods.delete(mood_id):
        raise not_found("Mood")
    db.commit()


@router.get("/{mood_id}/popular-track", response_model=PopularTrackOut)
def popular_track(mood_id: int, moods: MoodRepoDep, tracks: TrackRepoDep) -> PopularTrackOut:
    """Самый популярный трек среди плейлистов с данным настроением."""
    if moods.read(mood_id) is None:
        raise not_found("Mood")
    result = tracks.most_popular_by_playlist_mood(mood_id)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No tracks in playlists of this mood")
    track, count = result
    return PopularTrackOut(track=TrackOut.model_validate(track), playlist_count=count)
