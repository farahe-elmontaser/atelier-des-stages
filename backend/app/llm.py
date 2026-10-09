"""Classification des offres avec Ollama (LLM local, via son API REST).

Le LLM ne cherche PAS les offres (il inventerait) : il ANALYSE une offre reelle
que le scraping / les API lui donnent.
Si Ollama n'est pas lance, on utilise une classification simple par mots-cles.
"""
import json
import requests
from .config import OLLAMA_URL, OLLAMA_MODEL
from .matching import CATEGORIES

PROMPT = """Tu es un assistant qui analyse des offres de stage.

Offre :
Titre : {titre}
Entreprise : {entreprise}
Description : {description}

Choisis la categorie la plus adaptee dans cette liste EXACTE :
{categories}

Reponds UNIQUEMENT avec un objet JSON de ce format :
{{"categorie": "...", "competences": ["3 competences maximum"], "resume": "une phrase courte en francais"}}"""

MOTS_CLES = {
    "Machine Learning / Deep Learning": ["deep learning", "machine learning", "computer vision", "nlp", "pytorch", "tensorflow"],
    "Intelligence Artificielle": [" ia ", "intelligence artificielle", " ai ", "llm", "genai", "ia generative"],
    "Data Engineer": ["data engineer", "etl", "spark", "pipeline de donnees", "big data"],
    "Business Intelligence": ["business intelligence", "power bi", "tableau", " bi "],
    "Data Analyst": ["data analyst", "analyse de donnees", "analyste", "data"],
    "Cybersécurité": ["cyber", "securite", "soc", "pentest"],
    "Cloud / DevOps": ["devops", "cloud", "aws", "azure", "kubernetes", "docker"],
    "Réseaux & Télécoms": ["reseau", "telecom", "cisco", "network"],
    "Développement Mobile": ["mobile", "android", "ios", "flutter", "react native"],
    "Développement Web": ["web", "frontend", "front-end", "react", "angular", "javascript", "full stack", "fullstack"],
    "Logiciel / Backend": ["backend", "back-end", "java", "python", "developpeur", "developer", "logiciel", "software"],
    "Marketing / Communication": ["marketing", "communication", "community", "seo", "digital"],
    "Finance / Comptabilité": ["finance", "comptab", "audit", "controle de gestion"],
    "Commerce / Vente": ["commercial", "vente", "business developer", "sales"],
    "Ressources Humaines": ["rh", "ressources humaines", "recrutement", "talent"],
    "Génie Industriel": ["industriel", "logistique", "supply chain", "lean", "qualite"],
    "Génie Civil": ["genie civil", "btp", "construction", "batiment"],
    "Électronique / Électrique": ["electronique", "electrique", "embarque", "automatisme"],
    "Mécanique": ["mecanique", "cao", "solidworks", "catia"],
}


def _sans_accents(t):
    import unicodedata
    t = unicodedata.normalize("NFD", t.lower())
    return " " + "".join(c for c in t if unicodedata.category(c) != "Mn") + " "


def classer_par_mots_cles(titre, description):
    """Plan B si Ollama n'est pas disponible."""
    texte_titre = _sans_accents(titre)
    texte_complet = _sans_accents(titre + " " + description)
    for texte in (texte_titre, texte_complet):       # le titre est prioritaire
        for categorie, mots in MOTS_CLES.items():
            if any(m in texte for m in mots):
                return categorie
    return "Autre"


def analyser_offre(titre, entreprise, description):
    """Renvoie {"categorie", "competences", "resume", "methode"}."""
    prompt = PROMPT.format(titre=titre, entreprise=entreprise,
                           description=description[:2000],      # on limite la taille
                           categories=", ".join(CATEGORIES))
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "format": "json",                 # force une reponse JSON
            "stream": False,
            "options": {"temperature": 0},    # reponses stables
        }, timeout=120)
        r.raise_for_status()
        infos = json.loads(r.json()["response"])
        categorie = infos.get("categorie", "Autre")
        if categorie not in CATEGORIES:       # securite : le LLM peut inventer
            categorie = classer_par_mots_cles(titre, description)
        competences = [str(c) for c in infos.get("competences", [])][:3]
        return {"categorie": categorie, "competences": competences,
                "resume": str(infos.get("resume", ""))[:300], "methode": "llm"}
    except Exception as e:
        print(f"    (Ollama indisponible -> mots-cles) {type(e).__name__}")
        return {"categorie": classer_par_mots_cles(titre, description),
                "competences": [], "resume": description[:180], "methode": "mots-cles"}
