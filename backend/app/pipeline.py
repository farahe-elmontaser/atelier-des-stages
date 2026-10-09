"""Le pipeline complet, relance automatiquement par le scheduler.

 1. Collecte         (Job Bank CSV + Adzuna + France Travail [+ demo])
 2. Centralisation   (une seule liste d'objets Offer)
 3. Doublons         (titre + entreprise + ville)
 4. Deja en base ?   (comparaison par empreinte : nouvelles / supprimees)
 5. LLM              (categorie, competences, resume) -> seulement les nouvelles
 6. Stockage         (active = 1)
 7. Matching         (categorie -> profil -> abonnes)
 8. Notification     (un e-mail par abonne, jamais deux fois la meme offre)
"""
import json
import threading
from datetime import datetime

from .database import connexion
from .models import empreinte
from .sources import toutes_les_offres
from .llm import analyser_offre
from .matching import PROFILS
from .notifier import envoyer_email

_verrou = threading.Lock()
dernier_passage = {"date": None, "nouvelles": 0, "supprimees": 0, "emails": 0, "total_collecte": 0}


def supprimer_doublons(offres):
    vues, uniques = set(), []
    for o in offres:
        cle = empreinte(o)
        if cle and cle not in vues:
            vues.add(cle)
            uniques.append(o)
    return uniques


def verifier_offres():
    if not _verrou.acquire(blocking=False):          # deja en cours
        return dernier_passage
    try:
        print(f"\n=== Verification des offres : {datetime.now():%Y-%m-%d %H:%M:%S} ===")
        db = connexion()

        # 1 + 2. Collecte et centralisation (la PHOTO des sources)
        offres_site = toutes_les_offres()
        total = len(offres_site)

        # 3. Doublons
        offres_site = [o for o in offres_site if o.titre]
        offres_site = supprimer_doublons(offres_site)
        print(f"  {total} collectees -> {len(offres_site)} apres suppression des doublons")

        # 4. Comparaison avec la base
        cles_site = {empreinte(o): o for o in offres_site}
        lignes = db.execute("SELECT empreinte, source FROM offres WHERE active = 1").fetchall()
        cles_base = {l["empreinte"] for l in lignes}
        nouvelles = set(cles_site) - cles_base
        # On ne marque "supprimee" que si sa source a bien repondu cette fois-ci
        sources_ok = {o.source for o in offres_site}
        supprimees = {l["empreinte"] for l in lignes
                      if l["empreinte"] not in cles_site and l["source"] in sources_ok}

        # 5 + 6. LLM puis stockage, seulement pour les nouvelles
        for cle in nouvelles:
            o = cles_site[cle]
            infos = analyser_offre(o.titre, o.entreprise, o.description)
            print(f"  + NOUVELLE [{infos['categorie']}] ({infos['methode']}) {o.titre}")
            db.execute("""
                INSERT INTO offres (empreinte, lien, titre, entreprise, ville, description, source,
                                    categorie, competences, resume, date_publication, active)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,1)
                ON CONFLICT(empreinte) DO UPDATE SET active = 1, lien = excluded.lien
            """, (cle, o.lien, o.titre, o.entreprise, o.ville, o.description, o.source,
                                    infos["categorie"], json.dumps(infos["competences"], ensure_ascii=False),
                  infos["resume"], o.date_publication))
            db.commit()          # chaque offre apparait sur le site des qu'elle est classee
            

        for cle in supprimees:
            db.execute("UPDATE offres SET active = 0 WHERE empreinte = ?", (cle,))
            print(f"  - SUPPRIMEE {cle}")
        db.commit()

        # 7 + 8. Matching et notification
        emails = notifier_abonnes(db)
        db.close()

        dernier_passage.update(date=datetime.now().isoformat(timespec="seconds"),
                               nouvelles=len(nouvelles), supprimees=len(supprimees),
                               emails=emails, total_collecte=total)
        print(f"=== Fin : {len(nouvelles)} nouvelles, {len(supprimees)} supprimees, {emails} e-mails ===\n")
        return dernier_passage
    finally:
        _verrou.release()


def notifier_abonnes(db, utilisateur_id=None):
    """Pour chaque abonne : offres actives de son profil, jamais encore envoyees."""
    requete = "SELECT * FROM utilisateurs" + (" WHERE id = ?" if utilisateur_id else "")
    utilisateurs = db.execute(requete, (utilisateur_id,) if utilisateur_id else ()).fetchall()
    nb = 0
    for u in utilisateurs:
        categories = PROFILS.get(u["profil"], {}).get("categories", [])
        if not categories:
            continue
        marques = ",".join("?" * len(categories))
        offres = db.execute(f"""
            SELECT * FROM offres
            WHERE active = 1 AND categorie IN ({marques})
              AND id NOT IN (SELECT offre_id FROM envois WHERE utilisateur_id = ?)
            ORDER BY date_ajout DESC LIMIT 20
        """, (*categories, u["id"])).fetchall()
        if not offres:
            continue
        if envoyer_email(u["email"], u["nom"], [dict(o) for o in offres]):
            db.executemany("INSERT OR IGNORE INTO envois (utilisateur_id, offre_id) VALUES (?, ?)",
                           [(u["id"], o["id"]) for o in offres])
            db.commit()
            nb += 1
    return nb
