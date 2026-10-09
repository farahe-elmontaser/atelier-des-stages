"""Donnees ouvertes Job Bank (gouvernement du Canada).

1. Allez sur open.canada.ca et cherchez "Job Bank" (offres d'emploi).
2. Telechargez un fichier CSV et placez-le dans backend/data/job_bank.csv
3. Ouvrez le CSV et verifiez les noms des colonnes : si besoin, ajoutez-les
   dans le dictionnaire COLONNES ci-dessous.
Pas de cle, pas de scraping : on lit simplement le fichier.
"""
import pandas as pd
from ..config import JOB_BANK_CSV
from ..models import Offer

# Pour chaque champ, plusieurs noms de colonnes possibles (anglais / francais).
COLONNES = {
    "titre": ["Job Title", "job_title", "Titre du poste", "NOC Title", "Title", "titre"],
    "entreprise": ["Employer Name", "employer_name", "Nom de l'employeur", "Employer", "entreprise"],
    "ville": ["City", "city", "Ville", "Work Location", "Location", "ville"],
    "province": ["Province/Territory", "Province", "province"],
    "lien": ["Job Posting URL", "URL", "url", "Lien", "lien"],
    "description": ["Job Description", "Description", "description"],
    "date": ["First Posting Date", "Date Posted", "Date de publication", "date"],
    "id": ["Job Bank ID", "Job Posting ID", "ID", "id"],
}

MOTS_STAGE = ["stage", "stagiaire", "intern", "internship", "co-op", "coop", "student", "etudiant"]


def _lire_csv(chemin):
    """Les fichiers du gouvernement ne sont pas toujours en UTF-8 : on essaie plusieurs encodages."""
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return pd.read_csv(chemin, encoding=enc, sep=None, engine="python", dtype=str)
        except Exception:
            continue
    raise ValueError("Impossible de lire le CSV Job Bank")


def _colonne(df, champ):
    for nom in COLONNES[champ]:
        if nom in df.columns:
            return nom
    return None


def source_job_bank():
    if not JOB_BANK_CSV.exists():
        return []
    df = _lire_csv(JOB_BANK_CSV).fillna("")
    c = {champ: _colonne(df, champ) for champ in COLONNES}
    if not c["titre"]:
        raise ValueError(f"Colonne du titre introuvable. Colonnes du fichier : {list(df.columns)[:15]}")

    offres = []
    for _, ligne in df.iterrows():
        titre = ligne[c["titre"]]
        # On garde seulement les stages
        if not any(m in titre.lower() for m in MOTS_STAGE):
            continue
        ville = ligne[c["ville"]] if c["ville"] else ""
        if c["province"] and ligne[c["province"]]:
            ville = f"{ville}, {ligne[c['province']]}".strip(", ")
        lien = ligne[c["lien"]] if c["lien"] else ""
        if not lien and c["id"] and ligne[c["id"]]:
            lien = f"https://www.jobbank.gc.ca/jobsearch/jobposting/{ligne[c['id']]}"
        offres.append(Offer(
            titre=titre,
            entreprise=ligne[c["entreprise"]] if c["entreprise"] else "",
            ville=ville,
            lien=lien,
            description=ligne[c["description"]] if c["description"] else "",
            source="Job Bank",
            date_publication=ligne[c["date"]] if c["date"] else "",
        ))
    return offres
