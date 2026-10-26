from datetime import datetime, UTC

from sqlalchemy import select

from app.models.Administrator import Administrator
from app.models.FocusSession import FocusSession
from app.models.Listener import Listener
from app.models.Mood import Mood
from app.models.Playlist import Playlist
from app.models.Track import Track
from app.models.User import User


def _admin(**overrides) -> Administrator:
    defaults = dict(
        email="admin@example.com",
        username="admin",
        password="hash",
        type="administrator",
    )
    return Administrator(**{**defaults, **overrides})


def _listener(**overrides) -> Listener:
    defaults = dict(
        email="listener@example.com",
        username="listener",
        password="hash",
        type="listener",
    )
    return Listener(**{**defaults, **overrides})


def test_create_user(db):
    user = User(
        email="u@example.com",
        username="u",
        password="hash",
        type="user",
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.flush()

    assert user.id is not None


def test_create_listener(db):
    listener = _listener()
    db.add(listener)
    db.flush()

    assert listener.id is not None
    assert listener.email == "listener@example.com"


def test_create_administrator(db):
    admin = _admin()
    db.add(admin)
    db.flush()

    assert admin.id is not None


def test_polymorphic_query(db):
    db.add(_listener())
    db.add(_admin())
    db.flush()

    users = db.scalars(select(User)).all()
    types = {type(u) for u in users}

    assert Listener in types
    assert Administrator in types


def test_track_mood_m2m(db):
    admin = _admin()
    mood = Mood(name="Chill")
    track = Track(
        title="Song",
        file_url="http://x",
        duration_sec=180,
        bpm=90,
        added_by=admin,
    )
    track.moods.append(mood)
    db.add(track)
    db.flush()

    assert mood in track.moods


def test_playlist_track_m2m(db):
    admin = _admin()
    mood = Mood(name="Focus")

    db.add(admin)
    db.add(mood)
    db.flush()

    track = Track(
        title="S",
        file_url="u",
        duration_sec=1,
        bpm=1,
        added_by=admin,
    )
    playlist = Playlist(
        title="P",
        description="d",
        mood_id=mood.id,
        created_by=admin.id,
    )
    playlist.tracks.append(track)
    db.add(playlist)
    db.flush()

    assert track in playlist.tracks


def test_favourite_m2m(db):
    listener = _listener()
    admin = _admin()
    track = Track(
        title="S",
        file_url="u",
        duration_sec=1,
        bpm=1,
        added_by=admin,
    )
    listener.favourite_tracks.append(track)
    db.add(listener)
    db.flush()

    assert track in listener.favourite_tracks


def test_focus_session(db):
    listener = _listener()
    admin = _admin()
    mood = Mood(name="Focus")
    db.add_all([listener, admin, mood])
    db.flush()                    # ← даём им id

    playlist = Playlist(
        title="P", description="d",
        mood_id=mood.id,
        created_by=admin.id,
    )
    session = FocusSession(
        listener=listener,
        playlist=playlist,
        started_at=datetime.now(UTC),
        planned_duration_sec=3600,
        status="active",
    )
    db.add(session)
    db.flush()

    assert session.id is not None
    assert session.listener == listener

