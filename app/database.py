from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_database_schema():
    """Add columns missing from older databases without replacing existing user data."""
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return

    columns = [col["name"] for col in inspector.get_columns("users")]
    if "full_access" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN full_access BOOLEAN NOT NULL DEFAULT FALSE"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
