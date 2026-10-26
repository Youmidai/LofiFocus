"""DTO: модели HTTP-запросов и ответов. Отделены от ORM-моделей из app/models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class UserOut(ORMModel):
    id: int
    email: str
    username: str
    type: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Mood ----------
class MoodIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class MoodOut(ORMModel):
    id: int
    name: str


# ---------- Track ----------
class TrackCreate(BaseModel):
    title: str = Field(min_length=1)
    file_url: str = Field(min_length=1)
    duration_sec: int = Field(gt=0)
    bpm: int = Field(gt=0)
    mood_ids: list[int] = []


class TrackUpdate(BaseModel):
    """Частичное обновление: переданные поля меняются, null/отсутствующие игнорируются."""

    title: str | None = Field(default=None, min_length=1)
    file_url: str | None = Field(default=None, min_length=1)
    duration_sec: int | None = Field(default=None, gt=0)
    bpm: int | None = Field(default=None, gt=0)
    mood_ids: list[int] | None = None


class TrackOut(ORMModel):
    id: int
    title: str
    file_url: str
    duration_sec: int
    bpm: int
    added_by_id: int
    moods: list[MoodOut]


class PopularTrackOut(BaseModel):
    track: TrackOut
    playlist_count: int


# ---------- Playlist ----------
class PlaylistCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    mood_id: int
    track_ids: list[int] = []


class PlaylistUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    mood_id: int | None = None


class PlaylistOut(ORMModel):
    id: int
    title: str
    description: str
    mood_id: int
    created_by: int
    tracks: list[TrackOut]


# ---------- FocusSession ----------
class FocusSessionCreate(BaseModel):
    playlist_id: int
    planned_duration_sec: int = Field(gt=0)


class FocusSessionOut(ORMModel):
    id: int
    listener_id: int
    playlist_id: int
    started_at: datetime
    ended_at: datetime | None
    planned_duration_sec: int
    status: str
