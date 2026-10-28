"""Зависимости FastAPI (Dependency Injection): сессия БД, репозитории, сервисы, текущий пользователь."""

from collections.abc import Iterator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.Administrator import Administrator
from app.models.Listener import Listener
from app.models.User import User
from app.repositories.FocusSessionRepo import FocusSessionRepo
from app.repositories.ListenerRepo import ListenerRepo
from app.repositories.MoodRepo import MoodRepo
from app.repositories.PlaylistRepo import PlaylistRepo
from app.repositories.TrackRepo import TrackRepo
from app.repositories.UserRepo import UserRepository
from app.services.auth_service import AuthService

# tokenUrl нужен Swagger UI: кнопка Authorize отправляет форму на POST /login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def not_found(what: str) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"{what} not found")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ---------- БД ----------
def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # незакоммиченные изменения откатываются


DbDep = Annotated[Session, Depends(get_db)]


# ---------- Репозитории ----------
def get_user_repo(db: DbDep) -> UserRepository:
    return UserRepository(db)


def get_listener_repo(db: DbDep) -> ListenerRepo:
    return ListenerRepo(db)


def get_mood_repo(db: DbDep) -> MoodRepo:
    return MoodRepo(db)


def get_track_repo(db: DbDep) -> TrackRepo:
    return TrackRepo(db)


def get_playlist_repo(db: DbDep) -> PlaylistRepo:
    return PlaylistRepo(db)


def get_session_repo(db: DbDep) -> FocusSessionRepo:
    return FocusSessionRepo(db)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
ListenerRepoDep = Annotated[ListenerRepo, Depends(get_listener_repo)]
MoodRepoDep = Annotated[MoodRepo, Depends(get_mood_repo)]
TrackRepoDep = Annotated[TrackRepo, Depends(get_track_repo)]
PlaylistRepoDep = Annotated[PlaylistRepo, Depends(get_playlist_repo)]
SessionRepoDep = Annotated[FocusSessionRepo, Depends(get_session_repo)]


# ---------- Сервисы ----------
def get_auth_service(users: UserRepoDep, listeners: ListenerRepoDep) -> AuthService:
    return AuthService(users, listeners)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


# ---------- Аутентификация и авторизация ----------
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    users: UserRepoDep,
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise _unauthorized() from None
    user = users.read(user_id)
    if user is None:
        raise _unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_admin(user: CurrentUser) -> Administrator:
    if not isinstance(user, Administrator):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator role required")
    return user


def get_current_listener(user: CurrentUser) -> Listener:
    if not isinstance(user, Listener):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Listener role required")
    return user


AdminDep = Annotated[Administrator, Depends(get_current_admin)]
ListenerDep = Annotated[Listener, Depends(get_current_listener)]
