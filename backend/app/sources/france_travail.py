"""API France Travail (offres d'emploi v2) : https://francetravail.io

1. Creez un compte sur francetravail.io, puis une application.
2. Abonnez l'application a l'API "Offres d'emploi".
3. Copiez client_id et client_secret dans le fichier .env.
Si l'API change, verifiez les URLs dans la documentation officielle.
"""
import requests
from ..config import FRANCE_TRAVAIL_CLIENT_ID, FRANCE_TRAVAIL_CLIENT_SECRET, FRANCE_TRAVAIL_MOTS_CLES
from ..models import Offer

URL_TOKEN = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
URL_OFFRES = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"


def _jeton():
    r = requests.post(
        URL_TOKEN,
        params={"realm": "/partenaire"},
        data={
            "grant_type": "client_credentials",
            "client_id": FRANCE_TRAVAIL_CLIENT_ID,
            "client_secret": FRANCE_TRAVAIL_CLIENT_SECRET,
            "scope": "api_offresdemploiv2 o2dsoffre",
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def source_france_travail():
    if not (FRANCE_TRAVAIL_CLIENT_ID and FRANCE_TRAVAIL_CLIENT_SECRET):
        return []
    r = requests.get(
        URL_OFFRES,
        headers={"Authorization": f"Bearer {_jeton()}", "Accept": "application/json"},
        params={"motsCles": FRANCE_TRAVAIL_MOTS_CLES, "range": "0-99"},
        timeout=20,
    )
    if r.status_code == 204:                      # aucun resultat
        return []
    r.raise_for_status()
    offres = []
    for job in r.json().get("resultats", []):
        lien = job.get("origineOffre", {}).get("urlOrigine") or \
            f"https://candidat.francetravail.fr/offres/recherche/detail/{job.get('id', '')}"
        offres.append(Offer(
            titre=job.get("intitule", ""),
            entreprise=job.get("entreprise", {}).get("nom", ""),
            ville=job.get("lieuTravail", {}).get("libelle", ""),
            lien=lien,
            description=job.get("description", ""),
            source="France Travail",
            date_publication=job.get("dateCreation", ""),
        ))
    return offres
