# API des étudiants — application support du mémoire

API de gestion des étudiants (FastAPI + PostgreSQL), entièrement en français,
avec des métriques Prometheus et des pannes qu'on peut déclencher volontairement.

## Lancer l'application

Docker Desktop doit être ouvert. Dans PowerShell, depuis le dossier du projet :

```powershell
docker compose up -d --build
```

Puis ouvrir http://localhost:8000 (la documentation s'affiche, avec le bouton « Essayer »).

- Santé : http://localhost:8000/sante
- Base de données prête : http://localhost:8000/pret
- Métriques : http://localhost:8000/metriques

## Ajouter un étudiant

Le plus simple : dans la documentation, ouvrir `POST /etudiants`, cliquer sur « Essayer » puis « Exécuter ».
L'exemple est déjà rempli.

En PowerShell :

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/etudiants -ContentType application/json -Body '{"nom":"Diop","prenom":"Awa","email":"awa@ucad.sn","filiere":"RETEL"}'
Invoke-RestMethod http://localhost:8000/etudiants
```

## Lancer les tests (dans Docker, rien à installer)

```powershell
docker run --rm -v "${PWD}:/src" -w /src python:3.12-slim sh -c "pip install -q -r requirements-dev.txt && pytest -q"
```

## Déclencher des pannes

| Variable | Effet | Exemple |
|---|---|---|
| `PANNE_LATENCE_MS` | délai ajouté à chaque requête | `500` |
| `PANNE_TAUX_ERREURS` | part des réponses en erreur 500 (0 à 1) | `0.3` |
| `PANNE_FUITE_MEMOIRE_KO` | Ko gardés en mémoire à chaque requête | `512` |
| `PANNE_CPU_MS` | temps de calcul inutile par requête | `50` |
| `HOTE_BD` | serveur PostgreSQL (une fausse valeur simule une mauvaise config) | `bd-inexistante` |
| `VERSION_APP` | version affichée dans la métrique `info_application` | `1.1.0` |

```powershell
$env:PANNE_LATENCE_MS = "500"
docker compose up -d --force-recreate api
1..30 | ForEach-Object { Invoke-RestMethod http://localhost:8000/etudiants | Out-Null }
curl.exe -s http://localhost:8000/metriques | Select-String "duree_requetes_http_secondes_(sum|count)"
```

Retour à la normale :

```powershell
Remove-Item Env:PANNE_LATENCE_MS
docker compose up -d --force-recreate api
```

Les pannes touchent seulement `/etudiants`. `/sante`, `/pret` et `/metriques` restent sains.
`/sante` indique que l'application est vivante, `/pret` renvoie 503 si la base est injoignable.
