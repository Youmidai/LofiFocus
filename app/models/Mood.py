from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.Base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
if TYPE_CHECKING:
    from app.models.Playlist import Playlist

class Mood(Base):
    __tablename__ = "Mood"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    playlists: Mapped[list["Playlist"]] = relationship(
        back_populates="mood",
        cascade="all, delete-orphan",
    )