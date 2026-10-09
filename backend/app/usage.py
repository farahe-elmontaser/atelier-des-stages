"""WEB USAGE MINING : enregistrer ce que font les visiteurs, puis en tirer des patterns.

1. COLLECTE   : le site envoie un "evenement" a chaque action (POST /api/evenements)
                et les clics dans les e-mails passent par /api/r/{offre_id}.
                -> tout est stocke dans la table "evenements" (c'est notre log serveur).
2. ANALYSE    : des requetes SQL qui decouvrent des patterns :
                offres les plus vues, categories populaires, heures de visite,
                taux de clic, et ASSOCIATIONS ("ceux qui regardent X regardent aussi Y").

Vie privee : on ne stocke ni nom, ni e-mail, ni adresse IP. Seulement un
identifiant de session aleatoire, qui change a chaque visite.

Rapport dans le terminal :  python -m app.usage
"""
from collections import Counter
from itertools import combinations

from .database import connexion

TYPES = {"visite", "filtre_profil", "recherche", "vue_offre", "clic_origine", "inscription", "clic_email"}


def enregistrer(type_, offre_id=None, profil=None, recherche=None, session=None, origine="site"):
    if type_ not in TYPES:
        return
    db = connexion()
    categorie = None
    if offre_id is not None:
        ligne = db.execute("SELECT categorie FROM offres WHERE id = ?", (offre_id,)).fetchone()
        if not ligne:                      # offre inexistante : on n'enregistre rien
            db.close()
            return
        categorie = ligne["categorie"]
    db.execute("""INSERT INTO evenements (type, offre_id, categorie, profil, recherche, session, origine)
                  VALUES (?,?,?,?,?,?,?)""",
               (type_, offre_id, categorie, profil, (recherche or "").strip().lower() or None, session, origine))
    db.commit()
    db.close()


def analyser():
    """Renvoie les patterns d'usage decouverts (pour l'API et le rapport)."""
    db = connexion()
    q = lambda sql, *p: [dict(l) for l in db.execute(sql, p).fetchall()]

    par_type = {l["type"]: l["n"] for l in q("SELECT type, COUNT(*) AS n FROM evenements GROUP BY type")}
    sessions = db.execute("SELECT COUNT(DISTINCT session) FROM evenements WHERE session IS NOT NULL").fetchone()[0]

    offres_populaires = q("""
        SELECT o.id, o.titre, o.entreprise, o.categorie, COUNT(*) AS vues
        FROM evenements e JOIN offres o ON o.id = e.offre_id
        WHERE e.type = 'vue_offre'
        GROUP BY o.id ORDER BY vues DESC LIMIT 5""")

    categories_populaires = q("""
        SELECT categorie, COUNT(*) AS vues FROM evenements
        WHERE type = 'vue_offre' AND categorie IS NOT NULL
        GROUP BY categorie ORDER BY vues DESC LIMIT 5""")

    # Recherches : on ne montre que celles faites au moins 2 fois (pas de texte personnel isole)
    recherches = q("""
        SELECT recherche, COUNT(*) AS n FROM evenements
        WHERE type = 'recherche' AND recherche IS NOT NULL
        GROUP BY recherche HAVING n >= 2 ORDER BY n DESC LIMIT 5""")

    heures = q("""
        SELECT CAST(strftime('%H', date, 'localtime') AS INTEGER) AS heure, COUNT(*) AS n
        FROM evenements WHERE type = 'visite' GROUP BY heure ORDER BY heure""")

    # Taux de clic : sur 100 offres ouvertes, combien de fois va-t-on sur l'offre d'origine ?
    vues = par_type.get("vue_offre", 0)
    taux_clic = round(100 * par_type.get("clic_origine", 0) / vues, 1) if vues else 0

    # ASSOCIATIONS (comme "le pain et le fromage" du cours) :
    # pour chaque session, les categories regardees ; on compte les paires qui vont ensemble.
    paniers = {}
    for l in db.execute("""SELECT session, categorie FROM evenements
                           WHERE type = 'vue_offre' AND session IS NOT NULL AND categorie IS NOT NULL"""):
        paniers.setdefault(l["session"], set()).add(l["categorie"])
    paires = Counter()
    for cats in paniers.values():
        for a, b in combinations(sorted(cats), 2):
            paires[(a, b)] += 1
    nb_cat = Counter(c for cats in paniers.values() for c in cats)
    associations = []
    for (a, b), n in paires.most_common(5):
        if n < 2:
            continue
        # confiance : parmi les sessions qui ont vu A, quel % a aussi vu B ?
        associations.append({"a": a, "b": b, "sessions": n,
                             "confiance": round(100 * n / nb_cat[a]),
                             "confiance_inverse": round(100 * n / nb_cat[b])})
    db.close()
    return {
        "sessions": sessions,
        "evenements_par_type": par_type,
        "offres_populaires": offres_populaires,
        "categories_populaires": categories_populaires,
        "recherches_frequentes": recherches,
        "visites_par_heure": heures,
        "taux_clic_pourcent": taux_clic,
        "clics_email": par_type.get("clic_email", 0),
        "associations": associations,
    }


if __name__ == "__main__":
    r = analyser()
    print("\n=== RAPPORT DE WEB USAGE MINING ===\n")
    print(f"Sessions (visites) : {r['sessions']}")
    print("Evenements :", r["evenements_par_type"])
    print(f"Taux de clic vers l'offre d'origine : {r['taux_clic_pourcent']} %")
    print(f"Clics depuis les e-mails : {r['clics_email']}")
    print("\nOffres les plus consultees :")
    for o in r["offres_populaires"]:
        print(f"  {o['vues']:>3} vues  {o['titre']} ({o['entreprise']})")
    print("\nCategories les plus consultees :")
    for c in r["categories_populaires"]:
        print(f"  {c['vues']:>3}  {c['categorie']}")
    print("\nRecherches frequentes :")
    for x in r["recherches_frequentes"]:
        print(f"  {x['n']:>3}  {x['recherche']}")
    print("\nAssociations decouvertes (patterns) :")
    for a in r["associations"]:
        print(f"  {a['confiance']} % des visiteurs qui regardent « {a['a']} » regardent aussi « {a['b']} »"
              f"  ({a['sessions']} sessions)")
    if not r["associations"]:
        print("  (pas encore assez de donnees)")
