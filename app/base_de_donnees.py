from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import parametres

url = parametres.url_bd

if url.startswith("sqlite"):
    options = {"connect_args": {"check_same_thread": False}}
    if url in ("sqlite://", "sqlite:///:memory:"):
        options["poolclass"] = StaticPool  # base en mémoire partagée (pour les tests)
else:
    # Délai court : une mauvaise config de la BD doit échouer vite et se voir.
    options = {"connect_args": {"connect_timeout": 3}, "pool_pre_ping": True}

moteur = create_engine(url, **options)
SessionLocale = sessionmaker(bind=moteur, autoflush=False)


class Base(DeclarativeBase):
    pass
