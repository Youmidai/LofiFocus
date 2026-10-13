from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.Base import Base

if TYPE_CHECKING:
    from app.models.Administrator import Administrator
    from app.models.Mood import Mood


class Track(Base):
    __tablename__ = 'Track'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    file_url: Mapped[str]
    duration_sec: Mapped[int]
    bpm: Mapped[int]
    added_by_id: Mapped[int] = mapped_column(ForeignKey('Administrator.id'))
    added_by: Mapped["Administrator"] = relationship(back_populates="tracks")
    moods: Mapped[List["Mood"]] = relationship(secondary="TrackMood")