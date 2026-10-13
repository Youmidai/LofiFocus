from sqlalchemy import func, select

from app.models.FocusSession import FocusSession
from app.repositories.BaseRepo import BaseRepo


class FocusSessionRepo(BaseRepo[FocusSession]):
    model = FocusSession

    def list_by_listener(self, listener_id: int) -> list[FocusSession]:
        return list(self.db.scalars(
            select(self.model).where(self.model.listener_id == listener_id)
        ))

    def list_by_status(self, status: str) -> list[FocusSession]:
        return list(self.db.scalars(
            select(self.model).where(self.model.status == status)
        ))

    def list_active(self) -> list[FocusSession]:
        return self.list_by_status("active")

    def count_for_listener(self, listener_id: int) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(self.model)
            .where(self.model.listener_id == listener_id)
        ) or 0