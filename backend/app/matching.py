"""Profils (ce que choisit l'utilisateur) et categories (ce que donne le LLM)."""

PROFILS = {
    "data-ia": {
        "label": "Informatique · Data · IA",
        "categories": ["Data Analyst", "Data Engineer", "Business Intelligence",
                       "Intelligence Artificielle", "Machine Learning / Deep Learning"],
    },
    "dev": {
        "label": "Développement logiciel",
        "categories": ["Développement Web", "Développement Mobile", "Logiciel / Backend"],
    },
    "reseaux": {
        "label": "Réseaux · Cybersécurité · Cloud",
        "categories": ["Réseaux & Télécoms", "Cybersécurité", "Cloud / DevOps"],
    },
    "business": {
        "label": "Marketing · Finance · Commerce",
        "categories": ["Marketing / Communication", "Finance / Comptabilité",
                       "Commerce / Vente", "Ressources Humaines"],
    },
    "ingenierie": {
        "label": "Ingénierie & Industrie",
        "categories": ["Génie Industriel", "Génie Civil", "Électronique / Électrique", "Mécanique"],
    },
}

CATEGORIES = [c for p in PROFILS.values() for c in p["categories"]] + ["Autre"]


def profils_de_la_categorie(categorie):
    """Quels profils contiennent cette categorie ?"""
    return [cle for cle, p in PROFILS.items() if categorie in p["categories"]]
