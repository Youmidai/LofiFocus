from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey

from app.models.User import User
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.Playlist import Playlist
    from app.models.Track import Track

class Administrator(User):
    __tablename__ = 'Administrator'
    id: Mapped[int] = mapped_column(ForeignKey('User.id'), primary_key=True)
    playlists: Mapped[List["Playlist"]] = relationship(back_populates="creator")
    tracks: Mapped[List["Track"]] = relationship(back_populates="added_by")
    __mapper_args__ = {"polymorphic_identity": "administrator"}
