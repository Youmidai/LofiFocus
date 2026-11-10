"""Интеграционные тесты рекомендаций: FastAPI + реальный gRPC-сервер."""

from concurrent.futures import ThreadPoolExecutor
from typing import Iterator

import grpc
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.main import app
from app.core.security import hash_password
from app.models.Administrator import Administrator
from grpc_service.recommendation_server import RecommendationService
from proto import recommendations_pb2_grpc


@pytest.fixture
def api_db(engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(api_db) -> TestClient:
    app.dependency_overrides[get_db] = lambda: api_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client: TestClient, api_db: Session) -> str:
    api_db.add(Administrator(
        email="boss@mail.com", username="boss",
        password=hash_password("secret123"), type="administrator",
    ))
    api_db.commit()
    response = client.post("/login", data={"username": "boss", "password": "secret123"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def listener_token(client: TestClient) -> str:
    response = client.post("/register", json={
        "email": "fan@mail.com", "username": "fan", "password": "password123",
    })
    assert response.status_code == 201
    response = client.post("/login", data={"username": "fan", "password": "password123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_mood(client: TestClient, token: str, name: str) -> int:
    response = client.post("/moods", json={"name": name}, headers=auth(token))
    assert response.status_code == 201
    return response.json()["id"]


def create_track(client: TestClient, token: str, title: str, mood_ids: list[int]) -> int:
    response = client.post("/tracks", headers=auth(token), json={
        "title": title,
        "file_url": f"http://x/{title}",
        "duration_sec": 180,
        "bpm": 90,
        "mood_ids": mood_ids,
    })
    assert response.status_code == 201
    return response.json()["id"]


def create_playlist(client: TestClient, token: str, title: str, mood_id: int, track_ids: list[int]) -> int:
    response = client.post("/playlists", headers=auth(token), json={
        "title": title,
        "description": "",
        "mood_id": mood_id,
        "track_ids": track_ids,
    })
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def recommendation_server(api_db: Session) -> Iterator[None]:
    # поднимаем настоящий gRPC-сервер с той же сессией БД, что и API
    server = grpc.server(ThreadPoolExecutor(max_workers=5))
    recommendations_pb2_grpc.add_RecommendationServiceServicer_to_server(
        RecommendationService(api_db), server,
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    try:
        yield None
    finally:
        server.stop(None)


def test_recommend_playlists_integration(client: TestClient, admin_token: str, listener_token: str, recommendation_server):
    mood_id = create_mood(client, admin_token, "Focus")
    playlist_id = create_playlist(client, admin_token, "P", mood_id, [])

    started = client.post(
        "/sessions",
        headers=auth(listener_token),
        json={"playlist_id": playlist_id, "planned_duration_sec": 600},
    )
    assert started.status_code == 201

    response = client.get(
        f"/recommendations/playlists?mood_id={mood_id}",
        headers=auth(listener_token),
    )
    assert response.status_code == 200
    ids = [pl["id"] for pl in response.json()]
    assert playlist_id in ids


def test_recommend_tracks_integration(client: TestClient, admin_token: str, listener_token: str, recommendation_server):
    mood_id = create_mood(client, admin_token, "Focus")
    track_id = create_track(client, admin_token, "t1", [mood_id])
    playlist_id = create_playlist(client, admin_token, "P", mood_id, [track_id])

    started = client.post(
        "/sessions",
        headers=auth(listener_token),
        json={"playlist_id": playlist_id, "planned_duration_sec": 600},
    )
    assert started.status_code == 201

    response = client.get(
        f"/recommendations/tracks?mood_id={mood_id}",
        headers=auth(listener_token),
    )
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert track_id in ids
