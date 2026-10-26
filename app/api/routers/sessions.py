from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbDep, ListenerDep, PlaylistRepoDep, SessionRepoDep, not_found
from app.api.schemas import FocusSessionCreate, FocusSessionOut
from app.models.FocusSession import FocusSession

# Фокус-сессии доступны только слушателям и только свои собственные.
router = APIRouter(prefix="/sessions", tags=["focus sessions"])


def _own_session(sessions: SessionRepoDep, listener: ListenerDep, session_id: int) -> FocusSession:
    session = sessions.read(session_id)
    if session is None or session.listener_id != listener.id:
        raise not_found("Session")
    return session


@router.post("", response_model=FocusSessionOut, status_code=status.HTTP_201_CREATED)
def start_session(
    data: FocusSessionCreate,
    listener: ListenerDep,
    sessions: SessionRepoDep,
    playlists: PlaylistRepoDep,
    db: DbDep,
) -> FocusSession:
    if playlists.read(data.playlist_id) is None:
        raise not_found("Playlist")
    if any(s.status == "active" for s in sessions.list_by_listener(listener.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have an active session")
    session = sessions.create(
        listener_id=listener.id,
        playlist_id=data.playlist_id,
        started_at=datetime.now(UTC),
        planned_duration_sec=data.planned_duration_sec,
        status="active",
    )
    db.commit()
    return session


@router.get("", response_model=list[FocusSessionOut])
def list_my_sessions(listener: ListenerDep, sessions: SessionRepoDep) -> list[FocusSession]:
    return sessions.list_by_listener(listener.id)


@router.get("/{session_id}", response_model=FocusSessionOut)
def get_my_session(session_id: int, listener: ListenerDep, sessions: SessionRepoDep) -> FocusSession:
    return _own_session(sessions, listener, session_id)


@router.post("/{session_id}/finish", response_model=FocusSessionOut)
def finish_session(
    session_id: int,
    listener: ListenerDep,
    sessions: SessionRepoDep,
    db: DbDep,
) -> FocusSession:
    session = _own_session(sessions, listener, session_id)
    if session.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT, "Session is not active")
    sessions.update(session.id, status="completed", ended_at=datetime.now(UTC))
    db.commit()
    return session
