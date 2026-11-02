from prometheus_client import Counter, Gauge, Histogram

REQUETES = Counter(
    "requetes_http_total", "Nombre de requêtes HTTP", ["methode", "chemin", "statut"]
)
DUREE = Histogram(
    "duree_requetes_http_secondes",
    "Durée des requêtes HTTP en secondes",
    ["methode", "chemin"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
ERREURS_BD = Counter("erreurs_bd_total", "Nombre d'erreurs de base de données")
INFO_APP = Gauge("info_application", "Version de l'application déployée", ["version"])
