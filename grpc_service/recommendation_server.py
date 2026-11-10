"""gRPC-сервер рекомендаций для LofiFocus.

Использует общий engine/SessionLocal и репозитории, как основной API.
"""

from concurrent import futures

import grpc
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.repositories.FocusSessionRepo import FocusSessionRepo
from app.repositories.PlaylistRepo import PlaylistRepo
from app.repositories.TrackRepo import TrackRepo
from proto import recommendations_pb2, recommendations_pb2_grpc


class RecommendationService(recommendations_pb2_grpc.RecommendationServiceServicer):
    def __init__(self, db: Session) -> None:
        self.db = db
        self.sessions = FocusSessionRepo(db)
        self.playlists = PlaylistRepo(db)
        self.tracks = TrackRepo(db)

    def RecommendPlaylists(
        self,
        request: recommendations_pb2.PlaylistRecommendationRequest,
        context: grpc.ServicerContext,
    ) -> recommendations_pb2.PlaylistRecommendationResponse:
        limit = request.limit or 10

        # берём все сессии слушателя и считаем, какие плейлисты встречаются чаще
        sessions = self.sessions.list_by_listener(request.listener_id) if request.listener_id else self.sessions.list_active()

        score: dict[int, int] = {}
        for s in sessions:
            if request.mood_id and s.playlist.mood_id != request.mood_id:
                continue
            score[s.playlist_id] = score.get(s.playlist_id, 0) + 1

        # сортируем по счёту и ограничиваем
        sorted_ids = sorted(score.items(), key=lambda x: x[1], reverse=True)[:limit]

        response = recommendations_pb2.PlaylistRecommendationResponse()
        for playlist_id, s in sorted_ids:
            pl = self.playlists.read(playlist_id)
            if pl is None:
                continue
            response.playlists.add(playlist_id=pl.id, mood_id=pl.mood_id, score=s)
        return response

    def RecommendTracks(
        self,
        request: recommendations_pb2.TrackRecommendationRequest,
        context: grpc.ServicerContext,
    ) -> recommendations_pb2.TrackRecommendationResponse:
        limit = request.limit or 10

        sessions = self.sessions.list_by_listener(request.listener_id) if request.listener_id else self.sessions.list_active()

        score: dict[int, int] = {}
        for s in sessions:
            pl = s.playlist
            if request.mood_id and pl.mood_id != request.mood_id:
                continue
            for t in pl.tracks:
                score[t.id] = score.get(t.id, 0) + 1

        sorted_ids = sorted(score.items(), key=lambda x: x[1], reverse=True)[:limit]

        response = recommendations_pb2.TrackRecommendationResponse()
        for track_id, s in sorted_ids:
            t = self.tracks.read(track_id)
            if t is None:
                continue
            first_mood = t.moods[0].id if t.moods else 0
            response.tracks.add(track_id=t.id, mood_id=first_mood, score=s)
        return response


def serve(port: int = 50051) -> None:
    init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    db = SessionLocal()
    recommendations_pb2_grpc.add_RecommendationServiceServicer_to_server(
        RecommendationService(db), server,
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
