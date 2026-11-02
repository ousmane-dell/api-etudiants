import os

# Base SQLite en mémoire pour les tests : à définir avant d'importer l'application.
os.environ["URL_BD"] = "sqlite://"
