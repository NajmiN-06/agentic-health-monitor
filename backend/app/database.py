from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session

BACKEND_DIR = Path(__file__).resolve().parent.parent
sqlite_url = f"sqlite:///{BACKEND_DIR / 'telemetry.db'}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    # Import models here so SQLModel inspects VitalsRecord before metadata creation
    from app.models import VitalsRecord  
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session