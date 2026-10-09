"""API Adzuna : https://developer.adzuna.com (cle gratuite : app_id + app_key)."""
import time
import requests
from ..config import ADZUNA_APP_ID, ADZUNA_APP_KEY, ADZUNA_PAYS, ADZUNA_MOTS_CLES
from ..models import Offer


def source_adzuna():
    if not (ADZUNA_APP_ID and ADZUNA_APP_KEY):
        return []
    offres = []
    for pays in ADZUNA_PAYS:                      # ex. fr, ca, za
        url = f"https://api.adzuna.com/v1/api/jobs/{pays}/search/1"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": ADZUNA_MOTS_CLES,
            "results_per_page": 50,
            "sort_by": "date",
        }
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        for job in r.json().get("results", []):
            offres.append(Offer(
                titre=job.get("title", ""),
                entreprise=job.get("company", {}).get("display_name", ""),
                ville=job.get("location", {}).get("display_name", ""),
                lien=job.get("redirect_url", ""),
                description=job.get("description", ""),
                source=f"Adzuna ({pays})",
                date_publication=job.get("created", ""),
            ))
        time.sleep(1)                              # politesse : une pause entre les pays
    return offres
