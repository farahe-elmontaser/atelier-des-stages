"""API REST (FastAPI) : la porte d'entree du frontend.

Lancement :  uvicorn app.main:app --reload
Test       :  http://localhost:8000/docs
"""
import hmac
import json
import re
import secrets
import threading
import time
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, Field

from .config import INTERVALLE_MINUTES, DEMO_MODE, ADMIN_TOKEN, CORS_ORIGINS
from .securite import limite_globale, limite_inscription, limite_evenements, ip_client, est_local
from . import usage
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
# CORS : seul NOTRE frontend a le droit d'appeler l'API depuis un navigateur
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Admin-Token"])


@app.middleware("http")
async def protections(request: Request, call_next):
    # 1) Limiteur de debit : trop de requetes depuis la meme IP -> 429
    if not limite_globale.autorise(ip_client(request)):
        return JSONResponse({"detail": "Trop de requêtes, réessayez dans une minute."}, status_code=429)
    # 2) Corps de requete trop gros -> refuse (protection memoire)
    if int(request.headers.get("content-length") or 0) > 10_000:
        return JSONResponse({"detail": "Requête trop volumineuse."}, status_code=413)
    reponse = await call_next(request)
    # 3) En-tetes de securite de base
    reponse.headers["X-Content-Type-Options"] = "nosniff"
    reponse.headers["X-Frame-Options"] = "DENY"
    return reponse


# ---------- Modeles de donnees recus du frontend (verifies automatiquement) ----------
# Une requete qui ne respecte pas ce format est refusee (erreur 422) avant d'arriver au code.
class Inscription(BaseModel):
    nom: str = Field("", max_length=80)
    email: str = Field(..., min_length=5, max_length=254)
    profil: str = Field(..., max_length=30)


class Evenement(BaseModel):
    type: str = Field(..., max_length=20)
    offre_id: int | None = None
    profil: str | None = Field(None, max_length=30)
    recherche: str | None = Field(None, max_length=100)
    session: str | None = Field(None, max_length=40)


def _offre(ligne):
    d = dict(ligne)
    d["competences"] = json.loads(d.get("competences") or "[]")
    return d


# ---------- Routes ----------
@app.get("/api/profils")
def lister_profils():
    return [{"id": cle, "label": p["label"], "categories": p["categories"]} for cle, p in PROFILS.items()]


@app.get("/api/offres")
def lister_offres(profil: str | None = Query(None, max_length=30),
                  q: str | None = Query(None, max_length=100),
                  source: str | None = Query(None, max_length=50)):
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
def inscription(data: Inscription, taches: BackgroundTasks, request: Request):
    if not limite_inscription.autorise(ip_client(request)):
        raise HTTPException(429, "Trop d'inscriptions depuis cette adresse. Réessayez plus tard.")
    email = data.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(400, "Adresse e-mail invalide")
    if data.profil not in PROFILS:
        raise HTTPException(400, "Profil inconnu")
    db = connexion()
    db.execute("""INSERT INTO utilisateurs (nom, email, profil, token) VALUES (?,?,?,?)
                  ON CONFLICT(email) DO UPDATE SET profil = excluded.profil, nom = excluded.nom""",
               (data.nom.strip(), email, data.profil, secrets.token_urlsafe(24)))
    db.commit()
    uid = db.execute("SELECT id FROM utilisateurs WHERE email = ?", (email,)).fetchone()["id"]
    db.close()

    def bienvenue():                      # envoie tout de suite les offres deja disponibles
        d = connexion()
        notifier_abonnes(d, uid)
        d.close()
    taches.add_task(bienvenue)
    return {"message": f"Inscription confirmée. Vous recevrez les offres « {PROFILS[data.profil]['label']} »."}


PAGE = """<html><body style="background:#f6f1eb;font-family:Georgia,serif;text-align:center;padding:80px 16px;color:#2b2622">
<h1 style="font-weight:400;letter-spacing:4px">L'ATELIER DES STAGES</h1><p style="font-family:Arial">{}</p></body></html>"""


@app.get("/api/desinscription", response_class=HTMLResponse)
def desinscription(token: str = Query(..., min_length=10, max_length=100)):
    """Lien envoye dans chaque e-mail. Le token secret empeche de desinscrire quelqu'un d'autre."""
    db = connexion()
    n = db.execute("DELETE FROM utilisateurs WHERE token = ?", (token,)).rowcount
    db.commit()
    db.close()
    if not n:
        return HTMLResponse(PAGE.format("Lien invalide ou déjà utilisé."), status_code=404)
    return PAGE.format("Vous êtes désinscrit. Vous ne recevrez plus d'e-mails.")


# ---------- WEB USAGE MINING ----------
@app.post("/api/evenements", status_code=204)
def evenement(e: Evenement, request: Request):
    """Le site envoie ici chaque action du visiteur (le "log" du web usage mining)."""
    if e.type not in usage.TYPES or e.type == "clic_email":
        raise HTTPException(400, "Type d'evenement inconnu")
    if limite_evenements.autorise(ip_client(request)):      # au-dela : ignore silencieusement
        usage.enregistrer(e.type, e.offre_id, e.profil, e.recherche, e.session, "site")
    return Response(status_code=204)


@app.get("/api/r/{offre_id}")
def redirection_email(offre_id: int):
    """Les liens des e-mails passent par ici : on compte le clic, puis on redirige vers l'offre."""
    db = connexion()
    ligne = db.execute("SELECT lien FROM offres WHERE id = ?", (offre_id,)).fetchone()
    db.close()
    if not ligne or not str(ligne["lien"] or "").startswith(("http://", "https://")):
        raise HTTPException(404, "Offre introuvable")
    usage.enregistrer("clic_email", offre_id, origine="email")
    return RedirectResponse(ligne["lien"], status_code=302)


@app.get("/api/usage")
def statistiques_usage():
    """Les patterns d'usage decouverts (offres populaires, associations...)."""
    return usage.analyser()


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


_dernier_refresh = {"t": 0.0}


@app.post("/api/refresh")
def relancer_maintenant(request: Request, x_admin_token: str = Header("")):
    """Relance le pipeline a la main (pratique pour la demo).
    Autorise seulement depuis cet ordinateur, ou avec le bon ADMIN_TOKEN,
    et au maximum une fois toutes les 30 secondes."""
    jeton_ok = bool(ADMIN_TOKEN) and hmac.compare_digest(x_admin_token, ADMIN_TOKEN)
    if not (est_local(request) or jeton_ok):
        raise HTTPException(403, "Action réservée à l'administrateur.")
    if time.monotonic() - _dernier_refresh["t"] < 30:
        raise HTTPException(429, "Une vérification vient d'être lancée, patientez 30 secondes.")
    _dernier_refresh["t"] = time.monotonic()
    return verifier_offres()
