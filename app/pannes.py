"""Injection de pannes, appliquée uniquement aux routes /etudiants.

/sante, /pret et /metriques restent sains pour ne pas fausser la supervision.
"""
import asyncio
import random
import time

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from .config import parametres

_fuite: list[bytes] = []  # fuite mémoire volontaire : cette liste n'est jamais vidée


def _consommer_cpu(ms: int) -> None:
    fin = time.perf_counter() + ms / 1000
    while time.perf_counter() < fin:
        pass


async def injecter_pannes() -> None:
    if parametres.panne_latence_ms > 0:
        await asyncio.sleep(parametres.panne_latence_ms / 1000)
    if parametres.panne_cpu_ms > 0:
        await run_in_threadpool(_consommer_cpu, parametres.panne_cpu_ms)
    if parametres.panne_fuite_memoire_ko > 0:
        _fuite.append(b"x" * (parametres.panne_fuite_memoire_ko * 1024))  # octets vraiment écrits
    if parametres.panne_taux_erreurs > 0 and random.random() < parametres.panne_taux_erreurs:
        raise HTTPException(status_code=500, detail="Erreur injectée (PANNE_TAUX_ERREURS)")
