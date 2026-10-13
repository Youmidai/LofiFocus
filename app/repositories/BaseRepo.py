from typing import Generic, TypeVar, Type

from app.repositories.Exceptions import DuplicateError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.Base import Base

ModelT = TypeVar("ModelT", bound=Base)

class BaseRepo(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **kwargs) -> ModelT:
        obj = self.model(**kwargs)
        self.db.add(obj)
        try:
            self.db.flush()
        except IntegrityError as e:
            self.db.rollback()
            raise DuplicateError(f"{self.model.__name__} already exists") from e
        return obj

    def read(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def read_all(self) -> list[ModelT] | None:
        return list(self.db.scalars(select(self.model)))

    def update(self, id: int, **kwargs) -> ModelT | None:
        obj = self.read(id)
        if obj is None:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.db.flush()
        return obj

    def delete(self, id: int) -> bool:
        obj = self.read(id)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.flush()
        return True

