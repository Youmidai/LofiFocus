import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import config
from app.models.Base import Base
from datetime import datetime, UTC

from app.models.User import User
from app.models.Listener import Listener
from app.models.Administrator import Administrator
from app.models.Mood import Mood
from app.models.Track import Track
from app.models.Playlist import Playlist
from app.models.FocusSession import FocusSession


TEST_DB_NAME = "lofidb_test"


def _admin_engine():
    return create_engine(
        f"postgresql://{config['admin_user']}:{config['admin_password']}"
        f"@{config['db_host']}/postgres?client_encoding=utf8",
        isolation_level="AUTOCOMMIT",
    )


def _terminate_connections(conn) -> None:
    conn.execute(
        text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = :name AND pid <> pg_backend_pid()"
        ),
        {"name": TEST_DB_NAME},
    )


def _create_test_db() -> None:
    admin_engine = _admin_engine()
    try:
        with admin_engine.connect() as conn:
            _terminate_connections(conn)
            conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    finally:
        admin_engine.dispose()


def _drop_test_db() -> None:
    admin_engine = _admin_engine()
    try:
        with admin_engine.connect() as conn:
            _terminate_connections(conn)
            conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def engine():
    _create_test_db()

    test_engine = create_engine(
        f"postgresql://{config['admin_user']}:{config['admin_password']}"
        f"@{config['db_host']}/{TEST_DB_NAME}?client_encoding=utf8",
    )
    Base.metadata.create_all(test_engine)

    yield test_engine

    test_engine.dispose()
    _drop_test_db()


@pytest.fixture
def db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def seed(db):
    """Создаёт 5 заглушек каждой сущности и возвращает их списки."""
    users = [
        User(email=f"user{i}@x.com", username=f"user{i}",
             password="hash", type="user")
        for i in range(5)
    ]
    listeners = [
        Listener(email=f"listener{i}@x.com", username=f"listener{i}",
                 password="hash", type="listener")
        for i in range(5)
    ]
    admins = [
        Administrator(email=f"admin{i}@x.com", username=f"admin{i}",
                      password="hash", type="administrator")
        for i in range(5)
    ]
    moods = [Mood(name=f"Mood{i}") for i in range(5)]

    db.add_all(users + listeners + admins + moods)
    db.flush()

    tracks = [
        Track(
            title=f"Track{i}",
            file_url=f"http://x/{i}",
            duration_sec=180 + i,
            bpm=90 + i * 10,
            added_by=admins[i % len(admins)],
        )
        for i in range(5)
    ]
    db.add_all(tracks)
    db.flush()

    for i, track in enumerate(tracks):
        track.moods.append(moods[i % len(moods)])

    playlists = [
        Playlist(
            title=f"Playlist{i}",
            description=f"Desc{i}",
            mood_id=moods[i % len(moods)].id,
            created_by=admins[i % len(admins)].id,
        )
        for i in range(5)
    ]
    db.add_all(playlists)
    db.flush()

    for i, playlist in enumerate(playlists):
        playlist.tracks.append(tracks[i % len(tracks)])
        playlist.tracks.append(tracks[(i + 1) % len(tracks)])

    for i, listener in enumerate(listeners):
        listener.favourite_tracks.append(tracks[i % len(tracks)])

    sessions = [
        FocusSession(
            listener_id=listeners[i % len(listeners)].id,
            playlist_id=playlists[i % len(playlists)].id,
            started_at=datetime.now(UTC),
            planned_duration_sec=3600,
            status="active" if i % 2 == 0 else "completed",
        )
        for i in range(5)
    ]
    db.add_all(sessions)
    db.flush()

    return {
        "users": users,
        "listeners": listeners,
        "admins": admins,
        "moods": moods,
        "tracks": tracks,
        "playlists": playlists,
        "sessions": sessions,
    }