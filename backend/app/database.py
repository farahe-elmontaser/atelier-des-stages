"""Base de donnees SQLite : la memoire de l'application."""
import sqlite3
from .config import DB_PATH


def connexion():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


def creer_tables():
    """Etape 1 : creer les tables VIDES (les etageres)."""
    db = connexion()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS offres (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            empreinte        TEXT UNIQUE NOT NULL,   -- titre + entreprise + ville
            lien             TEXT,
            titre            TEXT,
            entreprise       TEXT,
            ville            TEXT,
            description      TEXT,
            source           TEXT,
            categorie        TEXT,
            competences      TEXT,                    -- liste JSON
            resume           TEXT,
            date_publication TEXT,
            date_ajout       TEXT DEFAULT CURRENT_TIMESTAMP,
            active           INTEGER DEFAULT 1        -- 1 = en ligne, 0 = disparue
        );

        CREATE TABLE IF NOT EXISTS utilisateurs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT,
            email       TEXT UNIQUE NOT NULL,
            profil      TEXT NOT NULL,
            date_ajout  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS envois (
            utilisateur_id INTEGER,
            offre_id       INTEGER,
            date_envoi     TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (utilisateur_id, offre_id)   -- jamais 2 fois la meme offre
        );
    """)
    db.commit()
    db.close()
