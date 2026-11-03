import time

import pytest
from fastapi.testclient import TestClient

from app.base_de_donnees import Base, moteur
from app.config import parametres
from app.main import app

ETUDIANT = {"nom": "Diop", "prenom": "Awa", "email": "awa@ucad.sn", "filiere": "RETEL"}


@pytest.fixture(autouse=True)
def remise_a_zero():
    Base.metadata.drop_all(bind=moteur)
    Base.metadata.create_all(bind=moteur)
    yield
    parametres.panne_latence_ms = 0
    parametres.panne_taux_erreurs = 0.0
    parametres.panne_fuite_memoire_ko = 0
    parametres.panne_cpu_ms = 0


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_sante_et_pret(client):
    assert client.get("/sante").json()["statut"] == "ok"
    assert client.get("/pret").status_code == 200


def test_cycle_complet(client):
    cree = client.post("/etudiants", json=ETUDIANT)
    assert cree.status_code == 200
    id_etudiant = cree.json()["id"]

    assert client.get(f"/etudiants/{id_etudiant}").json()["email"] == ETUDIANT["email"]
    assert len(client.get("/etudiants").json()) == 1

    modifie = client.put(f"/etudiants/{id_etudiant}", json={**ETUDIANT, "filiere": "SIR"})
    assert modifie.json()["filiere"] == "SIR"

    assert client.delete(f"/etudiants/{id_etudiant}").status_code == 204
    assert client.get(f"/etudiants/{id_etudiant}").status_code == 404


def test_email_unique(client):
    assert client.post("/etudiants", json=ETUDIANT).status_code == 201
    reponse = client.post("/etudiants", json=ETUDIANT)
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == "Cet email est déjà utilisé"


def test_validation_en_francais(client):
    reponse = client.post("/etudiants", json={**ETUDIANT, "email": "invalide"})
    assert reponse.status_code == 422
    assert reponse.json()["detail"][0] == {"champ": "email", "message": "Format invalide"}


def test_champ_obligatoire_en_francais(client):
    reponse = client.post("/etudiants", json={})
    assert reponse.status_code == 422
    assert {e["message"] for e in reponse.json()["detail"]} == {"Champ obligatoire"}


def test_route_inconnue_en_francais(client):
    reponse = client.get("/n-importe-quoi")
    assert reponse.status_code == 404
    assert reponse.json()["detail"] == "Ressource introuvable"


def test_metriques_exposees(client):
    client.get("/etudiants")
    corps = client.get("/metriques").text
    assert "requetes_http_total" in corps
    assert 'chemin="/etudiants"' in corps
    assert "duree_requetes_http_secondes_bucket" in corps


def test_panne_taux_erreurs(client):
    parametres.panne_taux_erreurs = 1.0
    assert client.get("/etudiants").status_code == 500
    assert client.get("/sante").status_code == 200  # la supervision reste saine


def test_panne_latence(client):
    parametres.panne_latence_ms = 200
    debut = time.perf_counter()
    client.get("/etudiants")
    assert time.perf_counter() - debut >= 0.2


def test_documentation_en_francais(client):
    page = client.get("/docs")
    assert page.status_code == 200
    assert 'lang="fr"' in page.text
    assert "Essayer" in page.text


def test_exemple_court_dans_la_documentation(client):
    schema = client.get("/openapi.json").json()["components"]["schemas"]["EtudiantEntree"]
    assert schema["examples"][0]["email"] == "awa@ucad.sn"
