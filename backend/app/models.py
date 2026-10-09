"""La classe Offer : le format commun a toutes les sources (centralisation)."""
import unicodedata


class Offer:
    def __init__(self, titre, entreprise, ville, lien, description="", source="", date_publication=""):
        self.titre = (titre or "").strip()
        self.entreprise = (entreprise or "Entreprise non precisee").strip()
        self.ville = (ville or "").strip()
        self.lien = (lien or "").strip()
        self.description = (description or "").strip()
        self.source = source
        self.date_publication = date_publication or ""
        # Remplis plus tard par le LLM
        self.categorie = None
        self.competences = []
        self.resume = ""

    def __repr__(self):
        return f"<Offer {self.titre} | {self.entreprise} | {self.ville} | {self.source}>"


def normaliser(texte):
    """minuscules, sans accents, sans espaces en trop"""
    texte = unicodedata.normalize("NFD", str(texte or "").lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return " ".join(texte.split())


def empreinte(o: Offer):
    """Identifiant unique d'une offre : titre + entreprise + ville (normalises)."""
    return f"{normaliser(o.titre)}|{normaliser(o.entreprise)}|{normaliser(o.ville)}"
