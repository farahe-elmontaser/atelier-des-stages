"""WEB SCRAPING avec requests + BeautifulSoup (partie B du cours).

Les 3 etapes du scraping :
  1. TELECHARGER la page HTML           -> requests
  2. ANALYSER le HTML (balises/classes) -> BeautifulSoup : find() / find_all()
  3. RANGER les infos                   -> objets Offer

On fait aussi du WEB STRUCTURE MINING : depuis la page "liste", on SUIT LE LIEN
de chaque offre (hyperlien) pour aller lire sa page "detail" (la description).

Regles respectees :
  - on lit robots.txt avant de visiter une page (urllib.robotparser)
  - on s'identifie avec un User-Agent
  - on fait une pause entre chaque requete (time.sleep)
  - si le site change son HTML, seule la fonction de ce site est a modifier

Test rapide (affiche les offres scrapees) :
    python -m app.sources.scraping
"""
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from ..config import SCRAPING_ACTIF, SCRAPING_MAX_OFFRES, SCRAPING_PAUSE
from ..models import Offer

USER_AGENT = "AtelierDesStagesBot/1.0 (projet etudiant Web Mining)"
_robots_cache = {}


# ---------------------------------------------------------------
# Outils communs a tous les sites
# ---------------------------------------------------------------
def autorise(url):
    """Lit le robots.txt du site et dit si on a le droit de visiter cette URL."""
    racine = "{0.scheme}://{0.netloc}".format(urlparse(url))
    if racine not in _robots_cache:
        rp = RobotFileParser()
        try:
            r = requests.get(racine + "/robots.txt", headers={"User-Agent": USER_AGENT}, timeout=15)
            # Pas de robots.txt (404) = tout est autorise
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except requests.RequestException:
            rp.parse([])
        _robots_cache[racine] = rp
    return _robots_cache[racine].can_fetch(USER_AGENT, url)


def telecharger(url):
    """Etape 1 : telecharger la page, puis etape 2 : la donner a BeautifulSoup."""
    if not autorise(url):
        raise PermissionError(f"robots.txt interdit : {url}")
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    r.raise_for_status()
    time.sleep(SCRAPING_PAUSE)                       # politesse envers le site
    return BeautifulSoup(r.text, "html.parser")


def texte(element):
    """Le texte d'une balise, ou "" si la balise n'existe pas."""
    return element.get_text(" ", strip=True) if element else ""


# ---------------------------------------------------------------
# Site 1 : Real Python "Fake Jobs" (site fait pour apprendre le scraping)
# ---------------------------------------------------------------
# Structure HTML d'une offre sur la page liste :
#   <div class="card-content">
#     <h2 class="title is-5">Senior Python Developer</h2>
#     <h3 class="subtitle is-6 company">Payne, Roberts and Davis</h3>
#     <p class="location">Stewartbury, AA</p>
#     <time datetime="2021-04-08">2021-04-08</time>
#     <a href="https://www.realpython.com">Learn</a>
#     <a href="https://realpython.github.io/fake-jobs/jobs/....html">Apply</a>
#   </div>
URL_FAKE_JOBS = "https://realpython.github.io/fake-jobs/"


def lire_detail_fake_jobs(url):
    """Structure mining : on suit le lien "Apply" pour lire la description."""
    soup = telecharger(url)
    contenu = soup.find("div", class_="content")
    paragraphe = contenu.find("p") if contenu else None
    return texte(paragraphe)


def scraper_fake_jobs():
    soup = telecharger(URL_FAKE_JOBS)
    cartes = soup.find_all("div", class_="card-content")       # find_all : TOUTES les offres

    offres = []
    for carte in cartes[:SCRAPING_MAX_OFFRES]:
        titre = texte(carte.find("h2", class_="title"))         # find : la PREMIERE balise
        entreprise = texte(carte.find("h3", class_="company"))
        ville = texte(carte.find("p", class_="location"))
        date = carte.find("time")
        date = date.get("datetime", texte(date)) if date else ""

        # Le lien "Apply" mene a la page detail de l'offre
        lien = ""
        for a in carte.find_all("a"):
            if texte(a).lower() == "apply":
                lien = urljoin(URL_FAKE_JOBS, a["href"])

        description = ""
        if lien:
            try:
                description = lire_detail_fake_jobs(lien)
            except Exception as e:
                print(f"    detail illisible ({e})")

        if titre:
            offres.append(Offer(titre, entreprise, ville, lien, description,
                                source="Scraping · Fake Jobs", date_publication=date))
    return offres


# ---------------------------------------------------------------
# Site 2 : MODELE a adapter a un vrai site d'offres
# ---------------------------------------------------------------
# 1. Choisissez un site dont le robots.txt AUTORISE la page des offres
#    et dont les conditions d'utilisation ne l'interdisent pas.
# 2. Clic droit > Inspecter : reperez la balise qui entoure UNE offre,
#    puis les balises du titre, de l'entreprise, de la ville et du lien.
# 3. Remplacez les noms ci-dessous, puis ajoutez la fonction dans SITES.
URL_MODELE = "https://www.exemple-site-de-stages.com/offres?page={page}"


def scraper_modele():
    offres = []
    for page in range(1, 3):                                    # pagination : pages 1 et 2
        soup = telecharger(URL_MODELE.format(page=page))
        for carte in soup.find_all("div", class_="offre"):      # <- a adapter
            lien_tag = carte.find("a")
            offres.append(Offer(
                titre=texte(carte.find("h2")),                  # <- a adapter
                entreprise=texte(carte.find("span", class_="entreprise")),
                ville=texte(carte.find("span", class_="ville")),
                lien=urljoin(URL_MODELE, lien_tag["href"]) if lien_tag else "",
                source="Scraping · Mon site",
            ))
    return offres


# ---------------------------------------------------------------
# Les sites actifs (ajoutez scraper_modele quand il est adapte)
# ---------------------------------------------------------------
SITES = [scraper_fake_jobs]


def source_scraping():
    if not SCRAPING_ACTIF:
        return []
    offres = []
    for site in SITES:
        try:
            resultat = site()
            print(f"    {site.__name__} : {len(resultat)} offres scrapees")
            offres += resultat
        except Exception as e:                    # un site en panne ne bloque pas les autres
            print(f"    {site.__name__} : ERREUR {e}")
    return offres


if __name__ == "__main__":
    for o in source_scraping():
        print(o, "|", o.description[:70])
