import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import config
from app.models.Base import Base


TEST_DB_NAME = "lofidb_test"


def _admin_engine():
    return create_engine(
        f"postgresql://{config['admin_user']}:{config['admin_password']}"
        f"@{config['db_host']}/postgres?client_encoding=utf8",
        isolation_level="AUTOCOMMIT",
    )


def _terminate_connections(conn) -> None:
    conn.execute(
        text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = :name AND pid <> pg_backend_pid()"
        ),
        {"name": TEST_DB_NAME},
    )


def _create_test_db() -> None:
    admin_engine = _admin_engine()
    try:
        with admin_engine.connect() as conn:
            _terminate_connections(conn)
            conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    finally:
        admin_engine.dispose()


def _drop_test_db() -> None:
    admin_engine = _admin_engine()
    try:
        with admin_engine.connect() as conn:
            _terminate_connections(conn)
            conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def engine():
    _create_test_db()

    test_engine = create_engine(
        f"postgresql://{config['admin_user']}:{config['admin_password']}"
        f"@{config['db_host']}/{TEST_DB_NAME}?client_encoding=utf8",
    )
    Base.metadata.create_all(test_engine)

    yield test_engine

    test_engine.dispose()
    _drop_test_db()


@pytest.fixture
def db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()