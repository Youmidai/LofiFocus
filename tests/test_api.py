"""Тесты REST API. Используют тестовую БД из conftest.py (фикстура `engine`).

Каждый тест выполняется в транзакции с SAVEPOINT и откатывается в конце,
поэтому commit() внутри обработчиков тестовую БД не засоряет.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.main import app
from app.core.security import hash_password
from app.models.Administrator import Administrator


@pytest.fixture
def api_db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(api_db):
    app.dependency_overrides[get_db] = lambda: api_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, api_db) -> str:
    api_db.add(Administrator(
        email="boss@mail.com", username="boss",
        password=hash_password("secret123"), type="administrator",
    ))
    api_db.commit()
    return login(client, "boss", "secret123")


@pytest.fixture
def listener_token(client) -> str:
    response = client.post("/register", json={
        "email": "fan@mail.com", "username": "fan", "password": "password123",
    })
    assert response.status_code == 201, response.text
    return login(client, "fan", "password123")


def create_mood(client, token, name) -> int:
    response = client.post("/moods", json={"name": name}, headers=auth(token))
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_track(client, token, title, mood_ids, bpm=90) -> int:
    response = client.post("/tracks", headers=auth(token), json={
        "title": title, "file_url": f"http://x/{title}",
        "duration_sec": 180, "bpm": bpm, "mood_ids": mood_ids,
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_playlist(client, token, title, mood_id, track_ids) -> int:
    response = client.post("/playlists", headers=auth(token), json={
        "title": title, "description": "d", "mood_id": mood_id, "track_ids": track_ids,
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


# ---------- регистрация и аутентификация ----------
def test_register_login_and_me(client):
    response = client.post("/register", json={
        "email": "Fan@Mail.com", "username": "fan", "password": "password123",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "listener"
    assert body["email"] == "fan@mail.com"
    assert "password" not in body

    token = login(client, "fan", "password123")
    me = client.get("/users/me", headers=auth(token))
    assert me.status_code == 200
    assert me.json()["username"] == "fan"

    # вход по email тоже работает
    assert login(client, "fan@mail.com", "password123")


def test_register_duplicate_and_validation(client):
    payload = {"email": "fan@mail.com", "username": "fan", "password": "password123"}
    assert client.post("/register", json=payload).status_code == 201
    assert client.post("/register", json=payload).status_code == 409

    short_password = {"email": "x@mail.com", "username": "xyz", "password": "123"}
    assert client.post("/register", json=short_password).status_code == 422


def test_login_wrong_password_and_bad_tokens(client, listener_token):
    wrong = client.post("/login", data={"username": "fan", "password": "nope-nope"})
    assert wrong.status_code == 401

    assert client.get("/users/me").status_code == 401
    assert client.get("/users/me", headers=auth("garbage")).status_code == 401
    assert client.get("/users/me", headers=auth(listener_token)).status_code == 200


# ---------- авторизация по ролям ----------
def test_listener_cannot_modify_catalog(client, listener_token):
    response = client.post("/moods", json={"name": "Chill"}, headers=auth(listener_token))
    assert response.status_code == 403


def test_admin_cannot_use_listener_endpoints(client, admin_token):
    assert client.get("/favourites", headers=auth(admin_token)).status_code == 403
    assert client.get("/sessions", headers=auth(admin_token)).status_code == 403


# ---------- CRUD ----------
def test_mood_crud(client, admin_token):
    mood_id = create_mood(client, admin_token, "Chill")
    assert client.post("/moods", json={"name": "Chill"}, headers=auth(admin_token)).status_code == 409

    renamed = client.put(f"/moods/{mood_id}", json={"name": "Calm"}, headers=auth(admin_token))
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Calm"

    assert client.delete(f"/moods/{mood_id}", headers=auth(admin_token)).status_code == 204
    assert client.get(f"/moods/{mood_id}", headers=auth(admin_token)).status_code == 404


def test_track_crud_and_filters(client, admin_token, listener_token):
    chill = create_mood(client, admin_token, "Chill")
    focus = create_mood(client, admin_token, "Focus")
    slow = create_track(client, admin_token, "slow", [chill], bpm=70)
    fast = create_track(client, admin_token, "fast", [chill, focus], bpm=120)

    # слушатель может читать
    by_mood = client.get(f"/tracks?mood_id={focus}", headers=auth(listener_token))
    assert [t["id"] for t in by_mood.json()] == [fast]

    by_bpm = client.get("/tracks?bpm_min=100", headers=auth(listener_token))
    assert [t["id"] for t in by_bpm.json()] == [fast]

    patched = client.patch(f"/tracks/{slow}", json={"title": "slower", "mood_ids": [focus]},
                           headers=auth(admin_token))
    assert patched.status_code == 200
    assert patched.json()["title"] == "slower"
    assert [m["id"] for m in patched.json()["moods"]] == [focus]

    assert client.post("/tracks", headers=auth(admin_token), json={
        "title": "t", "file_url": "u", "duration_sec": 1, "bpm": 1, "mood_ids": [99999],
    }).status_code == 404

    assert client.delete(f"/tracks/{fast}", headers=auth(admin_token)).status_code == 204
    assert client.get(f"/tracks/{fast}", headers=auth(admin_token)).status_code == 404


def test_playlist_crud_and_popular_track(client, admin_token):
    chill = create_mood(client, admin_token, "Chill")
    focus = create_mood(client, admin_token, "Focus")
    t1 = create_track(client, admin_token, "t1", [focus])
    t2 = create_track(client, admin_token, "t2", [focus])
    t3 = create_track(client, admin_token, "t3", [chill])

    create_playlist(client, admin_token, "F1", focus, [t1, t2])
    create_playlist(client, admin_token, "F2", focus, [t1, t3])
    chill_pl = create_playlist(client, admin_token, "C1", chill, [t3])

    popular = client.get(f"/moods/{focus}/popular-track", headers=auth(admin_token))
    assert popular.status_code == 200
    assert popular.json()["track"]["id"] == t1
    assert popular.json()["playlist_count"] == 2

    # у настроения без плейлистов популярного трека нет
    empty = create_mood(client, admin_token, "Empty")
    assert client.get(f"/moods/{empty}/popular-track", headers=auth(admin_token)).status_code == 404

    added = client.post(f"/playlists/{chill_pl}/tracks/{t1}", headers=auth(admin_token))
    assert added.status_code == 200
    assert sorted(t["id"] for t in added.json()["tracks"]) == sorted([t1, t3])

    removed = client.delete(f"/playlists/{chill_pl}/tracks/{t1}", headers=auth(admin_token))
    assert [t["id"] for t in removed.json()["tracks"]] == [t3]

    renamed = client.patch(f"/playlists/{chill_pl}", json={"title": "Chill++"}, headers=auth(admin_token))
    assert renamed.json()["title"] == "Chill++"

    assert client.delete(f"/playlists/{chill_pl}", headers=auth(admin_token)).status_code == 204
    assert client.get(f"/playlists/{chill_pl}", headers=auth(admin_token)).status_code == 404


# ---------- слушатель: избранное и фокус-сессии ----------
def test_favourites(client, admin_token, listener_token):
    mood = create_mood(client, admin_token, "Chill")
    track = create_track(client, admin_token, "t", [mood])

    assert client.put(f"/favourites/{track}", headers=auth(listener_token)).status_code == 204
    assert client.put(f"/favourites/{track}", headers=auth(listener_token)).status_code == 204  # идемпотентно
    favourites = client.get("/favourites", headers=auth(listener_token)).json()
    assert [t["id"] for t in favourites] == [track]

    assert client.delete(f"/favourites/{track}", headers=auth(listener_token)).status_code == 204
    assert client.get("/favourites", headers=auth(listener_token)).json() == []
    assert client.put("/favourites/99999", headers=auth(listener_token)).status_code == 404


def test_focus_session_lifecycle(client, admin_token, listener_token):
    mood = create_mood(client, admin_token, "Focus")
    playlist = create_playlist(client, admin_token, "P", mood, [])

    started = client.post("/sessions", headers=auth(listener_token),
                          json={"playlist_id": playlist, "planned_duration_sec": 1500})
    assert started.status_code == 201
    session_id = started.json()["id"]
    assert started.json()["status"] == "active"

    # вторая активная сессия запрещена
    again = client.post("/sessions", headers=auth(listener_token),
                        json={"playlist_id": playlist, "planned_duration_sec": 600})
    assert again.status_code == 409

    finished = client.post(f"/sessions/{session_id}/finish", headers=auth(listener_token))
    assert finished.status_code == 200
    assert finished.json()["status"] == "completed"
    assert finished.json()["ended_at"] is not None

    assert client.post(f"/sessions/{session_id}/finish", headers=auth(listener_token)).status_code == 409
    assert len(client.get("/sessions", headers=auth(listener_token)).json()) == 1


def test_session_of_another_listener_is_hidden(client, admin_token, listener_token):
    mood = create_mood(client, admin_token, "Focus")
    playlist = create_playlist(client, admin_token, "P", mood, [])
    session_id = client.post("/sessions", headers=auth(listener_token),
                             json={"playlist_id": playlist, "planned_duration_sec": 600}).json()["id"]

    client.post("/register", json={"email": "other@mail.com", "username": "other", "password": "password123"})
    other_token = login(client, "other", "password123")
    assert client.get(f"/sessions/{session_id}", headers=auth(other_token)).status_code == 404
