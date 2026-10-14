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

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import config, get_db_url
from app.models.Base import Base

engine = create_engine(get_db_url(), echo=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_database() -> None:
    admin_engine = create_engine(get_db_url("postgres"), isolation_level="AUTOCOMMIT")
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


def init_db() -> None:
    create_database()
    Base.metadata.create_all(engine)