"""Роутер рекомендаций, ходит в gRPC-сервис RecommendationService."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import ListenerDep, MoodRepoDep, PlaylistRepoDep, TrackRepoDep
from app.api.schemas import PlaylistOut, TrackOut
from app.models.Playlist import Playlist
from app.models.Track import Track
from grpc_service.recommendation_client import RecommendationClient


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _client() -> RecommendationClient:
    # простой клиент, на каждое обращение создаём канал
    return RecommendationClient()


@router.get("/playlists", response_model=list[PlaylistOut])
def recommend_playlists(
    listener: ListenerDep,
    moods: MoodRepoDep,
    playlists: PlaylistRepoDep,
    limit: Annotated[int, Query(gt=0, le=50)] = 10,
    mood_id: int | None = None,
    ) -> list[Playlist]:
    client = _client()
    resp = client.recommend_playlists(listener_id=listener.id, mood_id=mood_id, limit=limit)

    result: list[Playlist] = []
    for item in resp.playlists:
        playlist = playlists.read(item.playlist_id)
        if playlist is not None:
            if mood_id is not None and playlist.mood_id != mood_id:
                continue
            result.append(playlist)

    return result


@router.get("/tracks", response_model=list[TrackOut])
def recommend_tracks(
    listener: ListenerDep,
    tracks_repo: TrackRepoDep,
    limit: Annotated[int, Query(gt=0, le=50)] = 10,
    mood_id: int | None = None,
) -> list[Track]:
    client = _client()
    resp = client.recommend_tracks(listener_id=listener.id, mood_id=mood_id, limit=limit)

    result: list[Track] = []
    for item in resp.tracks:
        track = tracks_repo.read(item.track_id)
        if track is not None:
            if mood_id is not None and all(m.id != mood_id for m in track.moods):
                continue
            result.append(track)

    return result
