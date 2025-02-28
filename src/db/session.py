from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

# Créer le moteur de base de données
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

# Créer une session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dépendance qui fournit une session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()