"""Lecture de la configuration depuis le fichier .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(nom, defaut="false"):
    return os.getenv(nom, defaut).strip().lower() in ("1", "true", "yes", "oui")


# Dossier ou l'application ecrit (base de donnees). Dans Docker : un volume.
STOCKAGE_DIR = Path(os.getenv("STOCKAGE_DIR", str(BASE_DIR / "data")))
DB_PATH = STOCKAGE_DIR / "offres.db"

DEMO_MODE = _bool("DEMO_MODE", "false")
INTERVALLE_MINUTES = int(os.getenv("INTERVALLE_MINUTES", "60"))

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_PAYS = [p.strip() for p in os.getenv("ADZUNA_PAYS", "fr").split(",") if p.strip()]
ADZUNA_MOTS_CLES = os.getenv("ADZUNA_MOTS_CLES", "stage")

FRANCE_TRAVAIL_CLIENT_ID = os.getenv("FRANCE_TRAVAIL_CLIENT_ID", "")
FRANCE_TRAVAIL_CLIENT_SECRET = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET", "")
FRANCE_TRAVAIL_MOTS_CLES = os.getenv("FRANCE_TRAVAIL_MOTS_CLES", "stage")

SCRAPING_ACTIF = _bool("SCRAPING_ACTIF", "false")   # site d'entrainement Fake Jobs (offres fictives)
SCRAPING_MAX_OFFRES = int(os.getenv("SCRAPING_MAX_OFFRES", "20"))
SCRAPING_PAUSE = float(os.getenv("SCRAPING_PAUSE", "1"))

# --- Vraies offres : API publiques sans cle (voir app/sources/offres_reelles.py) ---
def _liste(nom, defaut):
    return [x.strip() for x in os.getenv(nom, defaut).split(",") if x.strip()]

GREENHOUSE_ENTREPRISES = _liste("GREENHOUSE_ENTREPRISES",
    "stripe,airbnb,databricks,cloudflare,datadog,gitlab,figma,discord,robinhood,coinbase")
LEVER_ENTREPRISES = _liste("LEVER_ENTREPRISES", "spotify,palantir")
MUSE_PAGES = int(os.getenv("MUSE_PAGES", "0"))
ARBEITNOW_PAGES = int(os.getenv("ARBEITNOW_PAGES", "3"))
REMOTIVE_ACTIF = _bool("REMOTIVE_ACTIF", "true")
MAX_PAR_SOURCE = int(os.getenv("MAX_PAR_SOURCE", "60"))

JOB_BANK_CSV = BASE_DIR / os.getenv("JOB_BANK_CSV", "data/job_bank.csv")

# Securite
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")            # pour /api/refresh depuis une autre machine
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
URL_PUBLIQUE = os.getenv("URL_PUBLIQUE", "http://localhost:8000")   # pour le lien de desinscription

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
