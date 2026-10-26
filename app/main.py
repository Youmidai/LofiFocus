"""Точка входа REST API.

Запуск для разработки:  uvicorn app.api.main:app --reload
Запуск на сервере:      gunicorn -c gunicorn.conf.py app.api.main:app
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app import models  # noqa: F401 — регистрирует все ORM-модели и таблицы связей
from app.api.routers import auth, favourites, moods, playlists, sessions, tracks
from app.repositories.Exceptions import DuplicateError, RepositoryError

app = FastAPI(
    title="LofiFocus API",
    version="0.2.0",
    description="REST API для сервиса LofiFocus: треки, плейлисты, настроения и фокус-сессии.",
)

for module in (auth, moods, tracks, playlists, favourites, sessions):
    app.include_router(module.router)


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(DuplicateError)
async def duplicate_handler(_: Request, exc: DuplicateError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=status.HTTP_409_CONFLICT)


@app.exception_handler(IntegrityError)
async def integrity_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        {"detail": "Operation violates a database constraint"},
        status_code=status.HTTP_409_CONFLICT,
    )


@app.exception_handler(RepositoryError)
async def repository_handler(_: Request, exc: RepositoryError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=status.HTTP_400_BAD_REQUEST)

