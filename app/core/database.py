from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True
)

LocalSession = sessionmaker(
    bind=engine
)

def get_db():
    with LocalSession() as session:
        yield session

class Base(DeclarativeBase):
    pass

