"""Простой gRPC-сервер рекомендаций для LofiFocus.

Сервер использует PostgreSQL через SQLAlchemy-модели и считает
"популярность" плейлистов/треков по статистике фокус-сессий.

В учебных целях сервер можно запускать отдельно от FastAPI.
"""

from concurrent import futures
from typing import Iterable

import grpc
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_db_url
from app.models.FocusSession import FocusSession
from app.models.Playlist import Playlist
from app.models.Track import Track
from app.models.Mood import Mood
from app.models.Base import Base

from proto import recommendations_pb2, recommendations_pb2_grpc


def _create_session() -> Session:
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker

  engine = create_engine(get_db_url(), echo=False)
  Base.metadata.create_all(engine)
  return sessionmaker(bind=engine)()


class RecommendationService(recommendations_pb2_grpc.RecommendationServiceServicer):
  """Реализация gRPC-интерфейса рекомендаций.

  Логика предельно простая:
  - для плейлистов считаем, сколько фокус-сессий запускалось с каждым
    плейлистом (по listener_id и/или mood_id);
  - для треков считаем количество сессий по плейлисту, умноженное на
    количество вхождений трека в плейлист.
  """

  def __init__(self, db: Session) -> None:
    self.db = db

  # ----- плейлисты -----
  def RecommendPlaylists(self, request: recommendations_pb2.PlaylistRecommendationRequest,
                         context: grpc.ServicerContext) -> recommendations_pb2.PlaylistRecommendationResponse:
    limit = request.limit or 10

    stmt = select(
      Playlist.id.label("playlist_id"),
      Playlist.mood_id.label("mood_id"),
      func.count(FocusSession.id).label("score"),
    ).join(FocusSession, FocusSession.playlist_id == Playlist.id)

    if request.listener_id:
      stmt = stmt.where(FocusSession.listener_id == request.listener_id)
    if request.mood_id:
      stmt = stmt.where(Playlist.mood_id == request.mood_id)

    stmt = stmt.group_by(Playlist.id).order_by(func.count(FocusSession.id).desc())
    stmt = stmt.limit(limit)

    rows: Iterable[tuple[int, int, int]] = self.db.execute(stmt)

    response = recommendations_pb2.PlaylistRecommendationResponse()
    for row in rows:
      response.playlists.add(
        playlist_id=row.playlist_id,
        mood_id=row.mood_id,
        score=row.score,
      )
    return response

  # ----- треки -----
  def RecommendTracks(self, request: recommendations_pb2.TrackRecommendationRequest,
                      context: grpc.ServicerContext) -> recommendations_pb2.TrackRecommendationResponse:
    limit = request.limit or 10

    from app.models.associations import playlist_track

    # Считаем число сессий на плейлист * присутствие трека в плейлисте.
    session_count = func.count(FocusSession.id).label("session_count")
    score_expr = session_count

    stmt = select(
      Track.id.label("track_id"),
      Mood.id.label("mood_id"),
      score_expr.label("score"),
    ).join(playlist_track, playlist_track.c.track_id == Track.id)
    stmt = stmt.join(Playlist, Playlist.id == playlist_track.c.playlist_id)
    stmt = stmt.join(FocusSession, FocusSession.playlist_id == Playlist.id)
    stmt = stmt.join(Mood, Mood.id == Playlist.mood_id)

    if request.listener_id:
      stmt = stmt.where(FocusSession.listener_id == request.listener_id)
    if request.mood_id:
      stmt = stmt.where(Mood.id == request.mood_id)

    stmt = stmt.group_by(Track.id, Mood.id).order_by(score_expr.desc()).limit(limit)

    rows: Iterable[tuple[int, int, int]] = self.db.execute(stmt)

    response = recommendations_pb2.TrackRecommendationResponse()
    for row in rows:
      response.tracks.add(
        track_id=row.track_id,
        mood_id=row.mood_id,
        score=row.score,
      )
    return response


def serve(port: int = 50051) -> None:
  """Запускает gRPC-сервер на указанном порту."""
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  db = _create_session()
  recommendations_pb2_grpc.add_RecommendationServiceServicer_to_server(
    RecommendationService(db), server,
  )
  server.add_insecure_port(f"[::]:{port}")
  server.start()
  server.wait_for_termination()


if __name__ == "__main__":
  serve()
