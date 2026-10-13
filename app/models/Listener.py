from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey

from app.models.User import User
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.FocusSession import FocusSession
    from app.models.Track import Track


class Listener(User):
    __tablename__ = 'Listener'
    id: Mapped[int] = mapped_column(ForeignKey('User.id'), primary_key=True)
    favourite_tracks: Mapped[List["Track"]] = relationship(secondary="Favourite")
    sessions: Mapped[list["FocusSession"]] = relationship(
        back_populates="listener",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    __mapper_args__ = {"polymorphic_identity": "listener"}