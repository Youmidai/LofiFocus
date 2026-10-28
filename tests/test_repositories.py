import pytest

from app.models.Administrator import Administrator
from app.models.Listener import Listener
from app.repositories.UserRepo import UserRepository
from app.repositories.ListenerRepo import ListenerRepo
from app.repositories.AdministratorRepo import AdministratorRepo
from app.repositories.MoodRepo import MoodRepo
from app.repositories.TrackRepo import TrackRepo
from app.repositories.PlaylistRepo import PlaylistRepo
from app.repositories.FocusSessionRepo import FocusSessionRepo
from app.repositories.Exceptions import DuplicateError, RepositoryError
from sqlalchemy import text


class TestUserRepository:
    def test_create(self, db):
        repo = UserRepository(db)
        user = repo.create(
            email="new@x.com", username="new", password="hash", type="user"
        )
        assert user.id is not None
        assert user.email == "new@x.com"

    def test_create_duplicate_email(self, db, seed):
        repo = UserRepository(db)
        with pytest.raises(DuplicateError):
            repo.create(
                email=seed["users"][0].email,
                username="another",
                password="hash",
                type="user",
            )

    def test_read(self, db, seed):
        repo = UserRepository(db)
        user = repo.read(seed["users"][0].id)
        assert user is not None
        assert user.id == seed["users"][0].id

    def test_read_all(self, db, seed):
        repo = UserRepository(db)
        users = repo.read_all()
        assert len(users) >= 5

    def test_update(self, db, seed):
        repo = UserRepository(db)
        updated = repo.update(seed["users"][0].id, username="changed")
        assert updated is not None
        assert updated.username == "changed"

    def test_delete(self, db, seed):
        repo = UserRepository(db)
        user_id = seed["users"][0].id
        assert repo.delete(user_id) is True
        assert repo.read(user_id) is None

    def test_find_by_email(self, db, seed):
        repo = UserRepository(db)
        found = repo.find_by_email(seed["users"][2].email)
        assert found is not None
        assert found.id == seed["users"][2].id

    def test_find_by_username(self, db, seed):
        repo = UserRepository(db)
        found = repo.find_by_username(seed["users"][3].username)
        assert found is not None
        assert found.id == seed["users"][3].id

    def test_list_by_type(self, db, seed):
        repo = UserRepository(db)
        listeners = repo.list_by_type("listener")
        assert all(u.type == "listener" for u in listeners)
        assert len(listeners) == 5


class TestListenerRepo:
    def test_create(self, db):
        repo = ListenerRepo(db)
        listener = repo.create(
            email="nl@x.com", username="nl", password="hash", type="listener"
        )
        assert listener.id is not None

    def test_find_by_email(self, db, seed):
        repo = ListenerRepo(db)
        found = repo.find_by_email(seed["listeners"][1].email)
        assert found is not None
        assert found.id == seed["listeners"][1].id

    def test_read(self, db, seed):
        repo = ListenerRepo(db)
        listener = repo.read(seed["listeners"][0].id)
        assert listener is not None
        assert listener.type == "listener"


class TestAdministratorRepo:
    def test_create(self, db):
        repo = AdministratorRepo(db)
        admin = repo.create(
            email="na@x.com", username="na", password="hash", type="administrator"
        )
        assert admin.id is not None

    def test_find_by_username(self, db, seed):
        repo = AdministratorRepo(db)
        found = repo.find_by_username(seed["admins"][2].username)
        assert found is not None
        assert found.id == seed["admins"][2].id

    def test_read(self, db, seed):
        repo = AdministratorRepo(db)
        admin = repo.read(seed["admins"][0].id)
        assert admin is not None
        assert admin.type == "administrator"


class TestMoodRepo:
    def test_create(self, db):
        repo = MoodRepo(db)
        mood = repo.create(name="NewMood")
        assert mood.id is not None

    def test_create_duplicate(self, db, seed):
        repo = MoodRepo(db)
        with pytest.raises(DuplicateError):
            repo.create(name=seed["moods"][0].name)

    def test_find_by_name(self, db, seed):
        repo = MoodRepo(db)
        found = repo.find_by_name(seed["moods"][2].name)
        assert found is not None
        assert found.id == seed["moods"][2].id

    def test_list_by_name_pattern(self, db, seed):
        repo = MoodRepo(db)
        found = repo.list_by_name_pattern("Mood")
        assert len(found) == 5

    def test_read_all(self, db, seed):
        repo = MoodRepo(db)
        moods = repo.read_all()
        assert len(moods) == 5

    def test_update(self, db, seed):
        repo = MoodRepo(db)
        updated = repo.update(seed["moods"][0].id, name="Renamed")
        assert updated is not None
        assert updated.name == "Renamed"

    def test_delete(self, db, seed):
        repo = MoodRepo(db)
        mood_id = seed["moods"][0].id
        assert repo.delete(mood_id) is True
        assert repo.read(mood_id) is None


class TestTrackRepo:
    def test_create(self, db, seed):
        repo = TrackRepo(db)
        track = repo.create(
            title="NT", file_url="u", duration_sec=100, bpm=100,
            added_by=seed["admins"][0],
        )
        assert track.id is not None

    def test_read(self, db, seed):
        repo = TrackRepo(db)
        track = repo.read(seed["tracks"][0].id)
        assert track is not None
        assert track.title == seed["tracks"][0].title

    def test_read_all(self, db, seed):
        repo = TrackRepo(db)
        assert len(repo.read_all()) == 5

    def test_update(self, db, seed):
        repo = TrackRepo(db)
        updated = repo.update(seed["tracks"][0].id, title="Updated")
        assert updated is not None
        assert updated.title == "Updated"

    def test_delete(self, db, seed):
        repo = TrackRepo(db)
        track_id = seed["tracks"][0].id
        assert repo.delete(track_id) is True
        assert repo.read(track_id) is None

    def test_list_by_bpm_range(self, db, seed):
        repo = TrackRepo(db)
        tracks = repo.list_by_bpm_range(100, 120)
        assert all(100 <= t.bpm <= 120 for t in tracks)
        assert len(tracks) >= 1

    def test_list_by_mood(self, db, seed):
        repo = TrackRepo(db)
        mood_id = seed["moods"][0].id
        tracks = repo.list_by_mood(mood_id)
        assert all(seed["moods"][0] in t.moods for t in tracks)
        assert len(tracks) >= 1

    def test_list_by_administrator(self, db, seed):
        repo = TrackRepo(db)
        admin_id = seed["admins"][0].id
        tracks = repo.list_by_administrator(admin_id)
        assert all(t.added_by_id == admin_id for t in tracks)


class TestPlaylistRepo:
    def test_create(self, db, seed):
        repo = PlaylistRepo(db)
        pl = repo.create(
            title="NP", description="d",
            mood_id=seed["moods"][0].id, created_by=seed["admins"][0].id,
        )
        assert pl.id is not None

    def test_read(self, db, seed):
        repo = PlaylistRepo(db)
        pl = repo.read(seed["playlists"][0].id)
        assert pl is not None
        assert pl.title == seed["playlists"][0].title

    def test_read_all(self, db, seed):
        repo = PlaylistRepo(db)
        assert len(repo.read_all()) == 5

    def test_update(self, db, seed):
        repo = PlaylistRepo(db)
        updated = repo.update(seed["playlists"][0].id, title="Upd")
        assert updated is not None
        assert updated.title == "Upd"

    def test_delete(self, db, seed):
        repo = PlaylistRepo(db)
        pl_id = seed["playlists"][0].id
        assert repo.delete(pl_id) is True
        assert repo.read(pl_id) is None

    def test_list_by_creator(self, db, seed):
        repo = PlaylistRepo(db)
        admin_id = seed["admins"][0].id
        pls = repo.list_by_creator(admin_id)
        assert all(p.created_by == admin_id for p in pls)
        assert len(pls) >= 1

    def test_list_by_mood(self, db, seed):
        repo = PlaylistRepo(db)
        mood_id = seed["moods"][0].id
        pls = repo.list_by_mood(mood_id)
        assert all(p.mood_id == mood_id for p in pls)

    def test_add_track(self, db, seed):
        repo = PlaylistRepo(db)
        pl = seed["playlists"][0]
        new_track = seed["tracks"][4]
        before = len(pl.tracks)
        if new_track not in pl.tracks:
            repo.add_track(pl.id, new_track.id)
            assert len(pl.tracks) == before + 1

    def test_add_track_playlist_not_found(self, db, seed):
        repo = PlaylistRepo(db)
        with pytest.raises(RepositoryError, match="Playlist"):
            repo.add_track(99999, seed["tracks"][0].id)

    def test_add_track_track_not_found(self, db, seed):
        repo = PlaylistRepo(db)
        with pytest.raises(RepositoryError, match="Track"):
            repo.add_track(seed["playlists"][0].id, 99999)

    def test_remove_track(self, db, seed):
        repo = PlaylistRepo(db)
        pl = seed["playlists"][0]
        track = pl.tracks[0]
        repo.remove_track(pl.id, track.id)
        assert track not in pl.tracks


class TestFocusSessionRepo:
    def test_create(self, db, seed):
        from datetime import datetime, UTC
        repo = FocusSessionRepo(db)
        s = repo.create(
            listener_id=seed["listeners"][0].id,
            playlist_id=seed["playlists"][0].id,
            started_at=datetime.now(UTC),
            planned_duration_sec=1800,
            status="active",
        )
        assert s.id is not None

    def test_read(self, db, seed):
        repo = FocusSessionRepo(db)
        s = repo.read(seed["sessions"][0].id)
        assert s is not None

    def test_read_all(self, db, seed):
        repo = FocusSessionRepo(db)
        assert len(repo.read_all()) == 5

    def test_update(self, db, seed):
        repo = FocusSessionRepo(db)
        updated = repo.update(seed["sessions"][0].id, status="completed")
        assert updated is not None
        assert updated.status == "completed"

    def test_delete(self, db, seed):
        repo = FocusSessionRepo(db)
        sid = seed["sessions"][0].id
        assert repo.delete(sid) is True
        assert repo.read(sid) is None

    def test_list_by_listener(self, db, seed):
        repo = FocusSessionRepo(db)
        listener_id = seed["listeners"][0].id
        sessions = repo.list_by_listener(listener_id)
        assert all(s.listener_id == listener_id for s in sessions)
        assert len(sessions) >= 1

    def test_list_active(self, db, seed):
        repo = FocusSessionRepo(db)
        active = repo.list_active()
        assert all(s.status == "active" for s in active)

    def test_list_by_status(self, db, seed):
        repo = FocusSessionRepo(db)
        completed = repo.list_by_status("completed")
        assert all(s.status == "completed" for s in completed)

    def test_count_for_listener(self, db, seed):
        repo = FocusSessionRepo(db)
        listener_id = seed["listeners"][0].id
        count = repo.count_for_listener(listener_id)
        assert count >= 1


class TestM2MRelations:
    def test_playlist_tracks(self, db, seed):
        pl = seed["playlists"][0]
        assert len(pl.tracks) >= 1

    def test_track_moods(self, db, seed):
        track = seed["tracks"][0]
        assert len(track.moods) >= 1

    def test_listener_favourites(self, db, seed):
        listener = seed["listeners"][0]
        assert len(listener.favourite_tracks) >= 1

    def test_cascade_track_mood(self, db, seed):
        from sqlalchemy import text
        track = seed["tracks"][0]
        track_id = track.id
        db.delete(track)
        db.flush()
        rows = db.execute(
            text('SELECT * FROM "TrackMood" WHERE track_id = :id'),
            {"id": track_id},
        ).all()
        assert rows == []
    def test_playlist_creator(self, db, seed):
        """Playlist.creator ссылается на Administrator."""
        pl = seed["playlists"][0]
        assert pl.creator is not None
        assert pl.creator.id == pl.created_by
        assert pl.creator.type == "administrator"

    def test_playlist_mood(self, db, seed):
        """Playlist.mood ссылается на Mood."""
        pl = seed["playlists"][0]
        assert pl.mood is not None
        assert pl.mood.id == pl.mood_id

    def test_playlist_sessions(self, db, seed):
        """Playlist.sessions содержит FocusSession."""
        pl = seed["playlists"][0]
        assert len(pl.sessions) >= 1
        assert all(s.playlist_id == pl.id for s in pl.sessions)

    def test_track_added_by(self, db, seed):
        """Track.added_by ссылается на Administrator."""
        track = seed["tracks"][0]
        assert track.added_by is not None
        assert track.added_by.id == track.added_by_id
        assert track.added_by.type == "administrator"

    def test_administrator_playlists(self, db, seed):
        """Administrator.playlists содержит Playlist'ы."""
        admin = seed["admins"][0]
        assert len(admin.playlists) >= 1
        assert all(p.created_by == admin.id for p in admin.playlists)

    def test_administrator_tracks(self, db, seed):
        """Administrator.tracks содержит Track'и."""
        admin = seed["admins"][0]
        assert len(admin.tracks) >= 1
        assert all(t.added_by_id == admin.id for t in admin.tracks)

    def test_mood_playlists(self, db, seed):
        """Mood.playlists содержит Playlist'ы."""
        mood = seed["moods"][0]
        assert len(mood.playlists) >= 1
        assert all(p.mood_id == mood.id for p in mood.playlists)

    def test_listener_sessions(self, db, seed):
        """Listener.sessions содержит FocusSession."""
        listener = seed["listeners"][0]
        assert len(listener.sessions) >= 1
        assert all(s.listener_id == listener.id for s in listener.sessions)

    def test_focus_session_playlist(self, db, seed):
        """FocusSession.playlist ссылается на Playlist."""
        s = seed["sessions"][0]
        assert s.playlist is not None
        assert s.playlist.id == s.playlist_id


class TestCascade:
    def test_delete_user_cascades_listener(self, db, seed):
        from sqlalchemy import text
        listener = seed["listeners"][0]
        listener_id = listener.id
        db.delete(listener)
        db.flush()
        rows = db.execute(
            text('SELECT * FROM "Listener" WHERE id = :id'),
            {"id": listener_id},
        ).all()
        assert rows == []

def test_listener_creates_user_row(db):
    """При создании Listener появляется строка и в User, и в Listener."""
    listener = Listener(
        email="l@x.com",
        username="l",
        password="hash",
        type="listener",
    )
    db.add(listener)
    db.flush()

    listener_id = listener.id

    user_row = db.execute(
        text('SELECT id, email, username, type FROM "User" WHERE id = :id'),
        {"id": listener_id},
    ).fetchone()

    listener_row = db.execute(
        text('SELECT id FROM "Listener" WHERE id = :id'),
        {"id": listener_id},
    ).fetchone()

    assert user_row is not None
    assert user_row.email == "l@x.com"
    assert user_row.username == "l"
    assert user_row.type == "listener"

    assert listener_row is not None
    assert user_row.id == listener_row.id


def test_administrator_creates_user_row(db):
    """При создании Administrator появляется строка и в User, и в Administrator."""
    admin = Administrator(
        email="a@x.com",
        username="a",
        password="hash",
        type="administrator",
    )
    db.add(admin)
    db.flush()

    admin_id = admin.id

    user_row = db.execute(
        text('SELECT id, email, username, type FROM "User" WHERE id = :id'),
        {"id": admin_id},
    ).fetchone()

    admin_row = db.execute(
        text('SELECT id FROM "Administrator" WHERE id = :id'),
        {"id": admin_id},
    ).fetchone()

    assert user_row is not None
    assert user_row.email == "a@x.com"
    assert user_row.username == "a"
    assert user_row.type == "administrator"

    assert admin_row is not None
    assert user_row.id == admin_row.id


def test_listener_does_not_create_administrator_row(db):
    """Listener не создаёт строку в Administrator — только в Listener."""
    listener = Listener(
        email="l2@x.com",
        username="l2",
        password="hash",
        type="listener",
    )
    db.add(listener)
    db.flush()

    admin_row = db.execute(
        text('SELECT id FROM "Administrator" WHERE id = :id'),
        {"id": listener.id},
    ).fetchone()

    assert admin_row is None

    listener_row = db.execute(
        text('SELECT id FROM "Listener" WHERE id = :id'),
        {"id": listener.id},
    ).fetchone()

    assert listener_row is not None


def test_user_row_count_after_creating_listener(db):
    """После создания Listener в User ровно одна новая строка."""
    before = db.execute(text('SELECT COUNT(*) FROM "User"')).scalar()

    listener = Listener(
        email="l3@x.com",
        username="l3",
        password="hash",
        type="listener",
    )
    db.add(listener)
    db.flush()

    after = db.execute(text('SELECT COUNT(*) FROM "User"')).scalar()

    assert after == before + 1