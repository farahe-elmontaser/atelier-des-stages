"""Lecture de la configuration depuis le fichier .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(nom, defaut="false"):
    return os.getenv(nom, defaut).strip().lower() in ("1", "true", "yes", "oui")


DB_PATH = BASE_DIR / "data" / "offres.db"

DEMO_MODE = _bool("DEMO_MODE", "true")
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

SCRAPING_ACTIF = _bool("SCRAPING_ACTIF", "true")
SCRAPING_MAX_OFFRES = int(os.getenv("SCRAPING_MAX_OFFRES", "20"))
SCRAPING_PAUSE = float(os.getenv("SCRAPING_PAUSE", "1"))

JOB_BANK_CSV = BASE_DIR / os.getenv("JOB_BANK_CSV", "data/job_bank.csv")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
