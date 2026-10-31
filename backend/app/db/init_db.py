"""Database schema initialization."""

from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 - Register all models with Base.metadata


def init_db() -> None:
    """Creates all database tables."""
    Base.metadata.create_all(bind=engine)
