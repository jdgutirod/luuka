from collections.abc import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db() -> Iterator[Session]:
    # Closing the session rolls back any open transaction and releases row locks
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
