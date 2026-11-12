from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


current_db_url = settings.database_url

def _create_engine_with_url(url: str):
    c_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    if url.startswith("sqlite"):
        return create_engine(url, connect_args=c_args, pool_pre_ping=True)
    else:
        return create_engine(
            url,
            connect_args=c_args,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=30,
            pool_recycle=3600
        )

try:
    engine = _create_engine_with_url(current_db_url)
    with engine.connect() as conn:
        pass
except Exception as e:
    import logging
    from config import BASE_DIR
    logging.getLogger("dragon.database").warning(f"Failed to connect to {current_db_url}, falling back to SQLite. Error: {e}")
    current_db_url = f"sqlite:///{BASE_DIR / 'dragon_s1.db'}"
    engine = _create_engine_with_url(current_db_url)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if current_db_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()




def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
