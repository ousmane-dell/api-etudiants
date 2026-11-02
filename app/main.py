import logging
import time
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import erreurs, modeles, pannes, schemas
from .base_de_donnees import Base, SessionLocale, moteur
from .config import parametres
from .docs_fr import page_documentation
from .metriques import DUREE, ERREURS_BD, INFO_APP, REQUETES

journal = logging.getLogger("api-etudiants")
CHEMINS_IGNORES = {"/", "/sante", "/pret", "/metriques", "/docs", "/openapi.json"}
tables_pretes = False


def initialiser_bd() -> bool:
    """Crée les tables. Ne plante pas si la BD est injoignable : /pret le signalera."""
    global tables_pretes
    try:
        Base.metadata.create_all(bind=moteur)
        tables_pretes = True
    except SQLAlchemyError as exc:
        ERREURS_BD.inc()
        journal.error("Base de données indisponible : %s", exc.__class__.__name__)
        tables_pretes = False
    return tables_pretes


@asynccontextmanager
async def lifespan(_: FastAPI):
    INFO_APP.labels(version=parametres.version_app).set(1)
    initialiser_bd()
    yield


app = FastAPI(
    title="API de gestion des étudiants",
    description="Application support du mémoire : chaîne CI/CD avec détection d'anomalies par IA.",
    version=parametres.version_app,
    lifespan=lifespan,
    docs_url=None,   # remplacée par notre page /docs en français
    redoc_url=None,
)


# ---------- Messages d'erreur en français ----------
@app.exception_handler(SQLAlchemyError)
async def gerer_erreur_bd(_: Request, __: SQLAlchemyError):
    ERREURS_BD.inc()
    return JSONResponse(status_code=500, content={"detail": "Erreur de base de données"})


@app.exception_handler(RequestValidationError)
async def gerer_erreur_validation(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": erreurs.traduire_erreurs_validation(exc.errors())},
    )


@app.exception_handler(StarletteHTTPException)
async def gerer_erreur_http(_: Request, exc: StarletteHTTPException):
    detail = erreurs.MESSAGES_HTTP.get(exc.detail, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=exc.headers)


# ---------- Mesure des requêtes (pour Prometheus) ----------
@app.middleware("http")
async def mesurer(request: Request, call_next):
    if request.url.path in CHEMINS_IGNORES:
        return await call_next(request)
    debut = time.perf_counter()
    statut = 500
    try:
        reponse = await call_next(request)
        statut = reponse.status_code
        return reponse
    finally:
        route = request.scope.get("route")
        chemin = route.path if route else "inconnu"  # modèle de route, pas l'URL réelle
        DUREE.labels(request.method, chemin).observe(time.perf_counter() - debut)
        REQUETES.labels(request.method, chemin, str(statut)).inc()


def obtenir_session():
    session = SessionLocale()
    try:
        yield session
    finally:
        session.close()


# ---------- Pages et supervision ----------
@app.get("/", include_in_schema=False)
def accueil():
    return RedirectResponse("/docs")


@app.get("/docs", include_in_schema=False)
def documentation():
    return HTMLResponse(page_documentation(app.title))


@app.get("/sante", tags=["Supervision"], summary="Vérifier que l'application tourne")
def verifier_sante():
    """Liveness : répond toujours 200 tant que l'application est vivante."""
    return {"statut": "ok", "version": parametres.version_app}


@app.get("/pret", tags=["Supervision"], summary="Vérifier que la base de données répond")
def verifier_pret():
    """Readiness : répond 503 si la base de données est injoignable."""
    ok = tables_pretes or initialiser_bd()
    if ok:
        try:
            with moteur.connect() as connexion:
                connexion.execute(text("SELECT 1"))
        except SQLAlchemyError:
            ok = False
    if not ok:
        return JSONResponse(status_code=503, content={"statut": "bd_indisponible"})
    return {"statut": "pret"}


@app.get("/metriques", tags=["Supervision"], summary="Métriques au format Prometheus")
def exposer_metriques():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------- API des étudiants ----------
routeur = APIRouter(
    prefix="/etudiants", tags=["Étudiants"], dependencies=[Depends(pannes.injecter_pannes)]
)


def valider_modification(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")


def trouver_etudiant(session: Session, id_etudiant: int) -> modeles.Etudiant:
    etudiant = session.get(modeles.Etudiant, id_etudiant)
    if etudiant is None:
        raise HTTPException(status_code=404, detail="Étudiant introuvable")
    return etudiant


@routeur.post(
    "",
    response_model=schemas.EtudiantSortie,
    status_code=201,
    summary="Ajouter un étudiant",
    response_description="L'étudiant qui vient d'être créé",
    responses={409: {"description": "Cet email est déjà utilisé"}},
)
def ajouter_etudiant(donnees: schemas.EtudiantEntree, session: Session = Depends(obtenir_session)):
    etudiant = modeles.Etudiant(**donnees.model_dump())
    session.add(etudiant)
    valider_modification(session)
    session.refresh(etudiant)
    return etudiant


@routeur.get(
    "",
    response_model=list[schemas.EtudiantSortie],
    summary="Lister les étudiants",
    response_description="La liste des étudiants",
)
def lister_etudiants(
    decalage: int = Query(0, ge=0, description="Nombre d'étudiants à sauter"),
    limite: int = Query(100, ge=1, le=500, description="Nombre maximum d'étudiants renvoyés"),
    session: Session = Depends(obtenir_session),
):
    requete = select(modeles.Etudiant).order_by(modeles.Etudiant.id).offset(decalage).limit(limite)
    return session.scalars(requete).all()


@routeur.get(
    "/{id_etudiant}",
    response_model=schemas.EtudiantSortie,
    summary="Consulter un étudiant",
    response_description="L'étudiant demandé",
    responses={404: {"description": "Étudiant introuvable"}},
)
def consulter_etudiant(
    id_etudiant: int = Path(description="Identifiant de l'étudiant"),
    session: Session = Depends(obtenir_session),
):
    return trouver_etudiant(session, id_etudiant)


@routeur.put(
    "/{id_etudiant}",
    response_model=schemas.EtudiantSortie,
    summary="Modifier un étudiant",
    response_description="L'étudiant après modification",
    responses={404: {"description": "Étudiant introuvable"}, 409: {"description": "Cet email est déjà utilisé"}},
)
def modifier_etudiant(
    donnees: schemas.EtudiantEntree,
    id_etudiant: int = Path(description="Identifiant de l'étudiant"),
    session: Session = Depends(obtenir_session),
):
    etudiant = trouver_etudiant(session, id_etudiant)
    for champ, valeur in donnees.model_dump().items():
        setattr(etudiant, champ, valeur)
    valider_modification(session)
    session.refresh(etudiant)
    return etudiant


@routeur.delete(
    "/{id_etudiant}",
    status_code=204,
    summary="Supprimer un étudiant",
    response_description="L'étudiant a été supprimé",
    responses={404: {"description": "Étudiant introuvable"}},
)
def supprimer_etudiant(
    id_etudiant: int = Path(description="Identifiant de l'étudiant"),
    session: Session = Depends(obtenir_session),
):
    session.delete(trouver_etudiant(session, id_etudiant))
    session.commit()


app.include_router(routeur)
