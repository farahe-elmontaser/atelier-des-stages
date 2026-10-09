"""VRAIES offres de stage, depuis des sources PUBLIQUES et GRATUITES (sans cle).

Pourquoi ces sources ?
  Ce sont des API officielles, publiees exprès pour que d'autres sites affichent
  leurs offres. C'est legal, stable, et chaque offre a son VRAI lien.

  1. Greenhouse  : les pages carrieres de centaines d'entreprises (Stripe, Airbnb...)
                   https://boards-api.greenhouse.io/v1/boards/<entreprise>/jobs
  2. Lever       : idem pour d'autres entreprises (Spotify, Palantir, Mistral AI...)
                   https://api.lever.co/v0/postings/<entreprise>?mode=json
  3. The Muse    : site d'emploi avec un filtre officiel "Internship"
                   https://www.themuse.com/api/public/jobs?level=Internship
  4. Arbeitnow   : offres en Europe (beaucoup de stages / Werkstudent)
                   https://www.arbeitnow.com/api/job-board-api
  5. Remotive    : offres en teletravail
                   https://remotive.com/api/remote-jobs

On garde seulement les STAGES (mots-cles dans le titre ou type de contrat),
et on nettoie les descriptions HTML avec BeautifulSoup (partie B du cours).

Pour ajouter une entreprise : mettez son nom dans GREENHOUSE_ENTREPRISES ou
LEVER_ENTREPRISES (fichier .env). Le nom est celui de l'adresse de sa page carriere :
  boards.greenhouse.io/stripe  -> "stripe"      jobs.lever.co/spotify -> "spotify"

Tester toutes les sources :   python -m app.sources.verifier
"""
import re
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from ..config import (GREENHOUSE_ENTREPRISES, LEVER_ENTREPRISES, MUSE_PAGES,
                      ARBEITNOW_PAGES, REMOTIVE_ACTIF, MAX_PAR_SOURCE)
from ..models import Offer

ENTETES = {"User-Agent": "AtelierDesStagesBot/1.0 (projet etudiant Web Mining)"}

# Mots qui indiquent un stage (francais, anglais, allemand, espagnol)
MOTS_STAGE = re.compile(
    r"\b(intern|interns|internship|internships|stage|stagiaire|alternance|alternant|apprenti|apprentice|"
    r"apprenticeship|werkstudent|praktikum|praktikant|trainee|co-?op|pr[aá]cticas|becario|summer analyst|"
    r"graduate program|working student)\b", re.IGNORECASE)
FAUX_POSITIFS = re.compile(r"early[- ]stage|internal|international", re.IGNORECASE)


def est_un_stage(*textes):
    for t in textes:
        if t and MOTS_STAGE.search(FAUX_POSITIFS.sub(" ", t)):
            return True
    return False


def html_vers_texte(html, max_caracteres=3000):
    """Les API donnent la description en HTML : BeautifulSoup la transforme en texte."""
    if not html:
        return ""
    # Greenhouse donne du HTML "echappe" (&lt;p&gt;) : on le decode d'abord
    if "&lt;" in html:
        html = BeautifulSoup(html, "html.parser").get_text()
    texte = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", texte)[:max_caracteres]


def _get(url, **params):
    r = requests.get(url, params=params or None, headers=ENTETES, timeout=25)
    r.raise_for_status()
    time.sleep(0.5)                              # politesse : une petite pause
    return r.json()


def _joli_nom(slug):
    return slug.replace("-", " ").replace("_", " ").title()


# ---------------------------------------------------------------
# 1. Greenhouse (pages carrieres d'entreprises)
# ---------------------------------------------------------------
def source_greenhouse():
    offres = []
    for entreprise in GREENHOUSE_ENTREPRISES:
        try:
            data = _get(f"https://boards-api.greenhouse.io/v1/boards/{entreprise}/jobs", content="true")
        except Exception as e:
            print(f"    greenhouse/{entreprise} : ignore ({e.__class__.__name__})")
            continue
        n = 0
        for job in data.get("jobs", []):
            titre = job.get("title", "")
            if not est_un_stage(titre):
                continue
            offres.append(Offer(
                titre=titre,
                entreprise=_joli_nom(entreprise),
                ville=(job.get("location") or {}).get("name", ""),
                lien=job.get("absolute_url", ""),
                description=html_vers_texte(job.get("content", "")),
                source=f"Greenhouse · {_joli_nom(entreprise)}",
                date_publication=job.get("updated_at", ""),
            ))
            n += 1
        print(f"    greenhouse/{entreprise} : {n} stages sur {len(data.get('jobs', []))} offres")
    return offres[:MAX_PAR_SOURCE * 3]


# ---------------------------------------------------------------
# 2. Lever (pages carrieres d'entreprises)
# ---------------------------------------------------------------
def source_lever():
    offres = []
    for entreprise in LEVER_ENTREPRISES:
        try:
            data = _get(f"https://api.lever.co/v0/postings/{entreprise}", mode="json")
        except Exception as e:
            print(f"    lever/{entreprise} : ignore ({e.__class__.__name__})")
            continue
        n = 0
        for job in data if isinstance(data, list) else []:
            titre = job.get("text", "")
            categories = job.get("categories") or {}
            if not est_un_stage(titre, categories.get("commitment", "")):
                continue
            date = job.get("createdAt")
            if isinstance(date, (int, float)):
                date = datetime.fromtimestamp(date / 1000, tz=timezone.utc).date().isoformat()
            offres.append(Offer(
                titre=titre,
                entreprise=_joli_nom(entreprise),
                ville=categories.get("location", ""),
                lien=job.get("hostedUrl", ""),
                description=(job.get("descriptionPlain") or html_vers_texte(job.get("description", "")))[:3000],
                source=f"Lever · {_joli_nom(entreprise)}",
                date_publication=date or "",
            ))
            n += 1
        print(f"    lever/{entreprise} : {n} stages sur {len(data) if isinstance(data, list) else 0} offres")
    return offres[:MAX_PAR_SOURCE * 3]


# ---------------------------------------------------------------
# 3. The Muse (filtre officiel "Internship")
# ---------------------------------------------------------------
def source_themuse():
    offres = []
    for page in range(1, MUSE_PAGES + 1):
        data = _get("https://www.themuse.com/api/public/jobs", level="Internship", page=page)
        for job in data.get("results", []):
            lieux = ", ".join(l.get("name", "") for l in job.get("locations", [])[:2])
            offres.append(Offer(
                titre=job.get("name", ""),
                entreprise=(job.get("company") or {}).get("name", ""),
                ville=lieux,
                lien=(job.get("refs") or {}).get("landing_page", ""),
                description=html_vers_texte(job.get("contents", "")),
                source="The Muse",
                date_publication=job.get("publication_date", ""),
            ))
        if page >= data.get("page_count", 0):
            break
    return offres[:MAX_PAR_SOURCE]


# ---------------------------------------------------------------
# 4. Arbeitnow (Europe)
# ---------------------------------------------------------------
def source_arbeitnow():
    offres = []
    for page in range(1, ARBEITNOW_PAGES + 1):
        data = _get("https://www.arbeitnow.com/api/job-board-api", page=page)
        for job in data.get("data", []):
            types = " ".join(job.get("job_types") or [])
            if not est_un_stage(job.get("title", ""), types):
                continue
            date = job.get("created_at")
            if isinstance(date, (int, float)):
                date = datetime.fromtimestamp(date, tz=timezone.utc).date().isoformat()
            offres.append(Offer(
                titre=job.get("title", ""),
                entreprise=job.get("company_name", ""),
                ville=job.get("location", "") + (" (télétravail)" if job.get("remote") else ""),
                lien=job.get("url", ""),
                description=html_vers_texte(job.get("description", "")),
                source="Arbeitnow",
                date_publication=date or "",
            ))
    return offres[:MAX_PAR_SOURCE]


# ---------------------------------------------------------------
# 5. Remotive (teletravail) - l'API demande de ne pas l'appeler trop souvent
# ---------------------------------------------------------------
_remotive_cache = {"t": 0.0, "offres": []}


def source_remotive():
    if not REMOTIVE_ACTIF:
        return []
    if time.time() - _remotive_cache["t"] < 6 * 3600:      # au maximum toutes les 6 heures
        return _remotive_cache["offres"]
    data = _get("https://remotive.com/api/remote-jobs", search="intern")
    offres = []
    for job in data.get("jobs", []):
        if not est_un_stage(job.get("title", ""), job.get("job_type", "")):
            continue
        offres.append(Offer(
            titre=job.get("title", ""),
            entreprise=job.get("company_name", ""),
            ville=job.get("candidate_required_location", "") + " (télétravail)",
            lien=job.get("url", ""),
            description=html_vers_texte(job.get("description", "")),
            source="Remotive",
            date_publication=job.get("publication_date", ""),
        ))
    _remotive_cache.update(t=time.time(), offres=offres[:MAX_PAR_SOURCE])
    return _remotive_cache["offres"]
