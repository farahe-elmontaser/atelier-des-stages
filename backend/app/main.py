"""API REST (FastAPI) : la porte d'entree du frontend.

Lancement :  uvicorn app.main:app --reload
Test       :  http://localhost:8000/docs
"""
import json
import re
import threading
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import INTERVALLE_MINUTES, DEMO_MODE
from .database import connexion, creer_tables
from .matching import PROFILS
from .pipeline import verifier_offres, notifier_abonnes, dernier_passage

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    creer_tables()                                                   # etape 1
    scheduler.add_job(verifier_offres, "interval", minutes=INTERVALLE_MINUTES, id="verif")
    scheduler.start()                                                # le reveil automatique
    threading.Thread(target=verifier_offres, daemon=True).start()    # un 1er passage tout de suite
    print(f"Scheduler lance : verification toutes les {INTERVALLE_MINUTES} min (demo={DEMO_MODE})")
    yield
    scheduler.shutdown()


app = FastAPI(title="L'Atelier des Stages - API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------- Modeles de donnees recus du frontend ----------
class Inscription(BaseModel):
    nom: str = ""
    email: str
    profil: str


def _offre(ligne):
    d = dict(ligne)
    d["competences"] = json.loads(d.get("competences") or "[]")
    return d


# ---------- Routes ----------
@app.get("/api/profils")
def lister_profils():
    return [{"id": cle, "label": p["label"], "categories": p["categories"]} for cle, p in PROFILS.items()]


@app.get("/api/offres")
def lister_offres(profil: str | None = None, q: str | None = None, source: str | None = None):
    sql, params = "SELECT * FROM offres WHERE active = 1", []
    if profil:
        if profil not in PROFILS:
            raise HTTPException(404, "Profil inconnu")
        cats = PROFILS[profil]["categories"]
        sql += f" AND categorie IN ({','.join('?' * len(cats))})"
        params += cats
    if q:
        sql += " AND (titre LIKE ? OR entreprise LIKE ? OR ville LIKE ? OR description LIKE ?)"
        params += [f"%{q}%"] * 4
    if source:
        sql += " AND source LIKE ?"
        params.append(f"{source}%")
    sql += " ORDER BY date_ajout DESC, id DESC LIMIT 200"
    db = connexion()
    lignes = db.execute(sql, params).fetchall()
    db.close()
    return [_offre(l) for l in lignes]


@app.get("/api/offres/{offre_id}")
def detail_offre(offre_id: int):
    db = connexion()
    ligne = db.execute("SELECT * FROM offres WHERE id = ?", (offre_id,)).fetchone()
    db.close()
    if not ligne:
        raise HTTPException(404, "Offre introuvable")
    return _offre(ligne)


@app.post("/api/inscription")
def inscription(data: Inscription, taches: BackgroundTasks):
    email = data.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(400, "Adresse e-mail invalide")
    if data.profil not in PROFILS:
        raise HTTPException(400, "Profil inconnu")
    db = connexion()
    db.execute("""INSERT INTO utilisateurs (nom, email, profil) VALUES (?,?,?)
                  ON CONFLICT(email) DO UPDATE SET profil = excluded.profil, nom = excluded.nom""",
               (data.nom.strip(), email, data.profil))
    db.commit()
    uid = db.execute("SELECT id FROM utilisateurs WHERE email = ?", (email,)).fetchone()["id"]
    db.close()

    def bienvenue():                      # envoie tout de suite les offres deja disponibles
        d = connexion()
        notifier_abonnes(d, uid)
        d.close()
    taches.add_task(bienvenue)
    return {"message": f"Inscription confirmée. Vous recevrez les offres « {PROFILS[data.profil]['label']} »."}


@app.delete("/api/desinscription/{email}")
def desinscription(email: str):
    db = connexion()
    n = db.execute("DELETE FROM utilisateurs WHERE email = ?", (email.strip().lower(),)).rowcount
    db.commit()
    db.close()
    if not n:
        raise HTTPException(404, "E-mail introuvable")
    return {"message": "Vous êtes désinscrit."}


@app.get("/api/stats")
def statistiques():
    db = connexion()
    r = {
        "offres_actives": db.execute("SELECT COUNT(*) FROM offres WHERE active = 1").fetchone()[0],
        "offres_total": db.execute("SELECT COUNT(*) FROM offres").fetchone()[0],
        "abonnes": db.execute("SELECT COUNT(*) FROM utilisateurs").fetchone()[0],
        "par_categorie": [dict(l) for l in db.execute(
            "SELECT categorie, COUNT(*) AS n FROM offres WHERE active = 1 GROUP BY categorie ORDER BY n DESC")],
        "par_source": [dict(l) for l in db.execute(
            "SELECT source, COUNT(*) AS n FROM offres WHERE active = 1 GROUP BY source ORDER BY n DESC")],
        "dernier_passage": dernier_passage,
        "intervalle_minutes": INTERVALLE_MINUTES,
    }
    db.close()
    return r


@app.post("/api/refresh")
def relancer_maintenant():
    """Relance le pipeline a la main (pratique pour la demo)."""
    return verifier_offres()
