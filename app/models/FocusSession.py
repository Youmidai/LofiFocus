from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey

from app.models.Base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.Listener import Listener
    from app.models.Playlist import Playlist


class FocusSession(Base):
    __tablename__ = 'FocusSession'
    id: Mapped[int] = mapped_column(primary_key=True)
    listener_id: Mapped[int] = mapped_column(ForeignKey('Listener.id', ondelete="CASCADE"))
    playlist_id: Mapped[int] = mapped_column(ForeignKey('Playlist.id', ondelete="CASCADE"))
    started_at: Mapped[datetime]
    ended_at: Mapped[datetime | None] = mapped_column(default=None)
    planned_duration_sec: Mapped[int]
    status: Mapped[str]
    listener: Mapped["Listener"] = relationship(back_populates="sessions")
    playlist: Mapped["Playlist"] = relationship(back_populates="sessions")
