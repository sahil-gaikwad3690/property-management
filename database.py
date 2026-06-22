"""Database setup — SQLite + SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./rental.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    """Tiny migration for the existing SQLite file.

    SQLAlchemy's create_all() only creates missing *tables*, not missing
    columns on tables that already exist. Add columns introduced after the
    DB was first created so old rental.db files keep working.
    """
    from sqlalchemy import inspect, text

    with engine.begin() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("users")}
        if "google_id" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR"))
