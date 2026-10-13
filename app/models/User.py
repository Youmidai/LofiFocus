from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.Base import Base

class User(Base):
    __tablename__ = "User"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    type: Mapped[str] = mapped_column()
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "user",
    }