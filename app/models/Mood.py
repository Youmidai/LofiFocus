from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.Base import Base
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    from app.models.Track import Track


class Mood(Base):
    __tablename__ = "Mood"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)