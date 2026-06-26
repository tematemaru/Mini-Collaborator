from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import Config

engine = create_engine(
    Config.DATABASE_URL,
    echo=Config.DEBUG,
    connect_args={"check_same_thread": False}  # для SQLite
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()