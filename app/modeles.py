from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base_de_donnees import Base


class Etudiant(Base):
    __tablename__ = "etudiants"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    filiere: Mapped[str] = mapped_column(String(100))
