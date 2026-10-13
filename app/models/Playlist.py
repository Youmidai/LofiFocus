from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.models.Base import Base

if TYPE_CHECKING:
    from app.models.Administrator import Administrator
    from app.models.FocusSession import FocusSession
    from app.models.Track import Track

class Playlist(Base):
    __tablename__ = 'Playlist'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    mood_id: Mapped[int] = mapped_column(ForeignKey('Mood.id'))
    created_by: Mapped[int] = mapped_column(ForeignKey('Administrator.id'))
    tracks: Mapped[List["Track"]] = relationship(secondary="PlaylistTrack")
    creator: Mapped["Administrator"] = relationship(back_populates="playlists")
    sessions: Mapped[list["FocusSession"]] = relationship(back_populates="playlist")
