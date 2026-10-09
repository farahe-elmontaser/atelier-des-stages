"""Centralisation : chaque source renvoie une liste d'objets Offer."""
from .demo import source_demo
from .scraping import source_scraping
from .job_bank import source_job_bank
from .adzuna import source_adzuna
from .france_travail import source_france_travail
from ..config import DEMO_MODE

SOURCES = [source_scraping, source_job_bank, source_adzuna, source_france_travail]
if DEMO_MODE:
    SOURCES.insert(0, source_demo)


def toutes_les_offres():
    resultat = []
    for source in SOURCES:
        try:
            offres = source()
            print(f"  [{source.__name__}] {len(offres)} offres")
            resultat += offres
        except Exception as e:  # une source en panne ne bloque pas les autres
            print(f"  [{source.__name__}] ERREUR : {e}")
    return resultat
