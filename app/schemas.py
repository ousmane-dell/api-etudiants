from pydantic import BaseModel, ConfigDict, Field


class EtudiantEntree(BaseModel):
    """Données à fournir pour créer ou modifier un étudiant."""

    nom: str = Field(min_length=1, max_length=100, description="Nom de famille")
    prenom: str = Field(min_length=1, max_length=100, description="Prénom")
    email: str = Field(
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        max_length=255,
        description="Adresse email (unique)",
    )
    filiere: str = Field(min_length=1, max_length=100, description="Filière d'études")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"nom": "Diop", "prenom": "Awa", "email": "awa@ucad.sn", "filiere": "RETEL"}
            ]
        }
    )


class EtudiantSortie(EtudiantEntree):
    """Étudiant tel qu'il est renvoyé par l'API."""

    id: int = Field(description="Identifiant de l'étudiant")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {"id": 1, "nom": "Diop", "prenom": "Awa", "email": "awa@ucad.sn", "filiere": "RETEL"}
            ]
        },
    )
