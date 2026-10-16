from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    """Una sesión por petición. Cada servicio hace db.commit() cuando escribe."""
    with SessionLocal() as db:
        yield db