"""Base de donnees SQLite : la memoire de l'application."""
import sqlite3
from .config import DB_PATH


def connexion():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # timeout : si la base est occupee, on attend au lieu de planter
    db = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout = 15000")
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
            token       TEXT,                       -- secret pour le lien de desinscription
            date_ajout  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS envois (
            utilisateur_id INTEGER,
            offre_id       INTEGER,
            date_envoi     TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (utilisateur_id, offre_id)   -- jamais 2 fois la meme offre
        );

        -- WEB USAGE MINING : le "journal" (log) de ce que font les visiteurs
        CREATE TABLE IF NOT EXISTS evenements (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            type      TEXT NOT NULL,     -- visite, filtre_profil, recherche, vue_offre, clic_origine, inscription, clic_email
            offre_id  INTEGER,           -- l'offre concernee (si il y en a une)
            categorie TEXT,              -- categorie de l'offre (copiee pour l'analyse)
            profil    TEXT,              -- profil filtre sur le site
            recherche TEXT,              -- mots cherches
            session   TEXT,              -- identifiant ANONYME de la visite (pas de nom, pas d'IP)
            origine   TEXT,              -- "site" ou "email"
            date      TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_evenements_type ON evenements(type);
        CREATE INDEX IF NOT EXISTS idx_evenements_session ON evenements(session);
    """)
    # Mode WAL : plusieurs lectures en meme temps qu'une ecriture (plusieurs utilisateurs)
    db.execute("PRAGMA journal_mode = WAL")
    # Mise a jour d'une ancienne base : ajouter la colonne token si elle manque
    colonnes = [c["name"] for c in db.execute("PRAGMA table_info(utilisateurs)")]
    if "token" not in colonnes:
        db.execute("ALTER TABLE utilisateurs ADD COLUMN token TEXT")
    import secrets
    for (uid,) in db.execute("SELECT id FROM utilisateurs WHERE token IS NULL").fetchall():
        db.execute("UPDATE utilisateurs SET token = ? WHERE id = ?", (secrets.token_urlsafe(24), uid))
    # Les anciennes offres de demo avaient de faux liens (example.com) : on les retire
    db.execute("UPDATE offres SET lien = '' WHERE lien LIKE 'https://example.com/%'")
    db.commit()
    db.close()
