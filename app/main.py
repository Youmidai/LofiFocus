from datetime import datetime, UTC

from sqlalchemy import text

from app.db.session import SessionLocal, init_db
from app.repositories.UserRepo import UserRepository
from app.repositories.ListenerRepo import ListenerRepo
from app.repositories.AdministratorRepo import AdministratorRepo
from app.repositories.MoodRepo import MoodRepo
from app.repositories.TrackRepo import TrackRepo
from app.repositories.PlaylistRepo import PlaylistRepo
from app.repositories.FocusSessionRepo import FocusSessionRepo


TABLES = '"User", "Mood", "Track", "Playlist", "FocusSession"'


def cleanup(db):
    """Удаляет все данные, добавленные демонстрацией, и сбрасывает SERIAL."""
    db.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
    db.commit()


def main():
    init_db()
    db = SessionLocal()

    try:
        cleanup(db)
        print("=== БД очищена перед запуском ===\n")

        # 1. Создание пользователей
        print("=== Создание Listener и Administrator ===")
        listener_repo = ListenerRepo(db)
        admin_repo = AdministratorRepo(db)

        listener = listener_repo.create(
            email="listener@x.com", username="listener",
            password="hash", type="listener",
        )
        admin = admin_repo.create(
            email="admin@x.com", username="admin",
            password="hash", type="administrator",
        )
        db.commit()
        print(f"Listener: id={listener.id}, email={listener.email}")
        print(f"Administrator: id={admin.id}, email={admin.email}")

        # 2. Создание Mood
        print("\n=== Создание Mood ===")
        mood_repo = MoodRepo(db)
        chill = mood_repo.create(name="Chill")
        focus = mood_repo.create(name="Focus")
        db.commit()
        print(f"Moods: {chill.name}, {focus.name}")

        # 3. Создание Track с настроением
        print("\n=== Создание Track ===")
        track_repo = TrackRepo(db)
        track = track_repo.create(
            title="Lo-Fi Beat", file_url="http://x/1",
            duration_sec=180, bpm=90, added_by=admin,
        )
        track.moods.append(chill)
        db.commit()
        print(f"Track: {track.title}, moods={[m.name for m in track.moods]}")

        # 4. Создание Playlist с треками
        print("\n=== Создание Playlist ===")
        playlist_repo = PlaylistRepo(db)
        playlist = playlist_repo.create(
            title="My Playlist", description="Chill mix",
            mood_id=chill.id, created_by=admin.id,
        )
        playlist.tracks.append(track)
        db.commit()
        print(f"Playlist: {playlist.title}, tracks={[t.title for t in playlist.tracks]}")

        # 5. Добавление в избранное
        print("\n=== Добавление в избранное ===")
        listener.favourite_tracks.append(track)
        db.commit()
        print(f"Listener {listener.username} has {len(listener.favourite_tracks)} favourites")

        # 6. Поиск
        print("\n=== Поиск ===")
        found = track_repo.list_by_bpm_range(80, 100)
        print(f"Tracks with bpm 80-100: {[t.title for t in found]}")

        found = listener_repo.find_by_email("listener@x.com")
        print(f"Listener by email: {found.username if found else None}")

        # 7. FocusSession
        print("\n=== FocusSession ===")
        session_repo = FocusSessionRepo(db)
        fs = session_repo.create(
            listener=listener, playlist=playlist,
            started_at=datetime.now(UTC),
            planned_duration_sec=3600, status="active",
        )
        db.commit()
        print(f"Session: id={fs.id}, status={fs.status}")

        # 8. Обновление
        print("\n=== Update ===")
        updated = track_repo.update(track.id, title="Lo-Fi Beat (Remastered)")
        db.commit()
        print(f"Updated track: {updated.title}")

        # 9. Удаление через репозиторий (демонстрация Delete)
        print("\n=== Delete через репозиторий ===")
        assert track_repo.delete(track.id) is True
        db.commit()
        print(f"Track id={track.id} удалён (каскад на TrackMood/PlaylistTrack/Favourite)")

        session_before = session_repo.list_by_listener(listener.id)
        assert playlist_repo.delete(playlist.id) is True
        db.commit()
        session_after = session_repo.list_by_listener(listener.id)
        print(f"Playlist id={playlist.id} удалён")
        print(f"  FocusSession до: {len(session_before)}, после: {len(session_after)}")

        mood_repo.delete(chill.id)
        mood_repo.delete(focus.id)
        db.commit()
        print(f"Moods Chill/Focus удалены")

        print("\n=== Демонстрация завершена ===")

    except Exception as e:
        db.rollback()
        print(f"\n!!! Ошибка: {e}")
        raise
    finally:
        cleanup(db)
        db.close()
        print("\n=== БД очищена после запуска ===")


if __name__ == "__main__":
    main()