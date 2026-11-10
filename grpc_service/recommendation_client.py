"""Минимальный gRPC-клиент для RecommendationService."""

from dataclasses import dataclass

import grpc

from proto import recommendations_pb2, recommendations_pb2_grpc


@dataclass
class RecommendationClientConfig:
    host: str = "localhost"
    port: int = 50051

    @property
    def target(self) -> str:
        return f"{self.host}:{self.port}"


class RecommendationClient:
    def __init__(self, config: RecommendationClientConfig | None = None) -> None:
        self._config = config or RecommendationClientConfig()
        self._channel = grpc.insecure_channel(self._config.target)
        self._stub = recommendations_pb2_grpc.RecommendationServiceStub(self._channel)

    def recommend_playlists(self, listener_id: int | None, mood_id: int | None, limit: int = 10):
        request = recommendations_pb2.PlaylistRecommendationRequest(
            listener_id=listener_id or 0,
            mood_id=mood_id or 0,
            limit=limit,
        )
        return self._stub.RecommendPlaylists(request)

    def recommend_tracks(self, listener_id: int | None, mood_id: int | None, limit: int = 10):
        request = recommendations_pb2.TrackRecommendationRequest(
            listener_id=listener_id or 0,
            mood_id=mood_id or 0,
            limit=limit,
        )
        return self._stub.RecommendTracks(request)
