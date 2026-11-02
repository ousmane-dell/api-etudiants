"""Paramètres de l'application, lus une seule fois au démarrage.

Les variables PANNE_* servent à provoquer volontairement des anomalies
pour les expériences du mémoire. La valeur 0 désactive la panne.
"""
import os
from dataclasses import dataclass


@dataclass
class Parametres:
    url_bd: str = os.getenv("URL_BD", "sqlite:///./etudiants.db")
    version_app: str = os.getenv("VERSION_APP", "1.0.0")
    # --- Pannes injectables ---
    panne_latence_ms: int = int(os.getenv("PANNE_LATENCE_MS", "0"))            # délai ajouté à chaque requête
    panne_taux_erreurs: float = float(os.getenv("PANNE_TAUX_ERREURS", "0"))    # part des réponses en erreur 500 (0 à 1)
    panne_fuite_memoire_ko: int = int(os.getenv("PANNE_FUITE_MEMOIRE_KO", "0"))  # Ko gardés en mémoire à chaque requête
    panne_cpu_ms: int = int(os.getenv("PANNE_CPU_MS", "0"))                    # temps de calcul inutile par requête


parametres = Parametres()
