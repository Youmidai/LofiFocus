from sqlalchemy import text

from app.models.Administrator import Administrator
from app.models.Listener import Listener
from app.models.Mood import Mood
from app.models.Track import Track


def _admin() -> Administrator:
    return Administrator(
        email="a@e.com",
        username="a",
        password="x",
        type="administrator",
    )


def test_cascade_track_mood(db):
    admin = _admin()
    mood = Mood(name="Chill")
    track = Track(
        title="S",
        file_url="u",
        duration_sec=1,
        bpm=1,
        added_by=admin,
    )
    track.moods.append(mood)
    db.add(track)
    db.flush()

    track_id = track.id
    db.delete(track)
    db.flush()

    rows = db.execute(
        text('SELECT * FROM "TrackMood" WHERE track_id = :id'),
        {"id": track_id},
    ).all()

    assert rows == []


def test_cascade_user_listener(db):
    listener = Listener(
        email="l@e.com",
        username="l",
        password="x",
        type="listener",
    )
    db.add(listener)
    db.flush()

    user_id = listener.id
    db.delete(listener)
    db.flush()

    rows = db.execute(
        text('SELECT * FROM "Listener" WHERE id = :id'),
        {"id": user_id},
    ).all()

    assert rows == []