from sqlalchemy.engine import URL

config = {
    'db_name': 'lofidb',
    'admin_user': 'admin',
    'admin_password': 'admin123',
    'db_host': 'localhost',
    'sql_echo': False,
    # JWT
    'jwt_secret': 'dev-only-secret-change-me-in-production',
    'jwt_algorithm': 'HS256',
    'jwt_expire_minutes': 60,
}


def get_db_url(db_name: str | None = None) -> str:
    return URL.create(
        "postgresql+psycopg2",
        username=config["admin_user"],
        password=config["admin_password"],
        host=config["db_host"],
        database=db_name or config["db_name"],
    ).render_as_string(hide_password=False)