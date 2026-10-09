"""Source de DEMO : des offres d'exemple pour tester sans aucune cle d'API.

A chaque passage du scheduler, 3 offres de plus "apparaissent" et, a partir
du 3e passage, une offre "disparait" : parfait pour montrer la detection des nouvelles offres
et des offres supprimees pendant la soutenance.
"""
import json
from ..config import BASE_DIR
from ..models import Offer

FICHIER = BASE_DIR / "data" / "demo_offres.json"
COMPTEUR = BASE_DIR / "data" / ".demo_passage"


def source_demo():
    toutes = json.loads(FICHIER.read_text(encoding="utf-8"))

    passage = int(COMPTEUR.read_text()) if COMPTEUR.exists() else 0
    COMPTEUR.write_text(str(passage + 1))

    fin = min(len(toutes), 8 + passage * 3)        # 8 au debut, puis +3 a chaque passage
    visibles = toutes[:fin]
    if passage >= 2:                                # a partir du 3e passage, une offre disparait
        visibles.pop(1)

    return [Offer(d["titre"], d["entreprise"], d["ville"], d["lien"],
                  d["description"], d.get("source", "Demo"), d.get("date", ""))
            for d in visibles]
