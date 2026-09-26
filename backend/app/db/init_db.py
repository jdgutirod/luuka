import app.models  # noqa: F401 (registers all models in Base.metadata)
from app.db.database import Base, engine

def init_db() -> None:
    # Creates missing tables only; it does not alter tables that already exist
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Tablas creadas")
