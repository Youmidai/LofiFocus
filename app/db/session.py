from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import config
from app.models.Base import Base

engine = create_engine(
    f"postgresql://{config['admin_user']}:{config['admin_password']}"
    f"@{config['db_host']}/{config['db_name']}",
    echo=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    admin_engine = create_engine(
        f"postgresql://{config['admin_user']}:{config['admin_password']}"
        f"@{config['db_host']}/postgres",
        isolation_level="AUTOCOMMIT",
    )
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": config["db_name"]},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{config["db_name"]}"'))
    finally:
        admin_engine.dispose()

    Base.metadata.create_all(engine)