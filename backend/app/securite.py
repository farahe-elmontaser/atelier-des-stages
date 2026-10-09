"""Protections simples contre les abus (sans bibliotheque en plus).

Limiteur de debit ("rate limiting") : chaque adresse IP a droit a un nombre
maximum de requetes sur une periode. Au-dela -> erreur 429 "Trop de requetes".
Ainsi, un script qui envoie des milliers de requetes ne fait pas tomber le serveur.
"""
import ipaddress
import threading
import time
from collections import defaultdict, deque


class Limiteur:
    def __init__(self, max_requetes, periode_secondes):
        self.max = max_requetes
        self.periode = periode_secondes
        self.historique = defaultdict(deque)     # ip -> dates des dernieres requetes
        self.verrou = threading.Lock()

    def autorise(self, cle):
        maintenant = time.monotonic()
        with self.verrou:
            h = self.historique[cle]
            while h and maintenant - h[0] > self.periode:   # on oublie les vieilles requetes
                h.popleft()
            if len(h) >= self.max:
                return False
            h.append(maintenant)
            if len(self.historique) > 10_000:               # evite que la memoire grossisse sans fin
                self.historique.clear()
            return True


# Toutes les routes : 120 requetes par minute et par IP
limite_globale = Limiteur(120, 60)
# Evenements d'usage : 60 par minute et par IP (au-dela, ils sont ignores)
limite_evenements = Limiteur(60, 60)
# Inscription : 5 par 10 minutes et par IP (anti-spam)
limite_inscription = Limiteur(5, 600)


def ip_client(request):
    return request.client.host if request.client else "inconnu"


def est_local(request):
    """Vrai si la requete vient de cet ordinateur ou du reseau prive (ex. Docker sur votre PC).
    Sur un VPS derriere Nginx, la vraie IP publique du visiteur est utilisee -> faux."""
    ip = ip_client(request)
    if ip == "localhost":
        return True
    try:
        adresse = ipaddress.ip_address(ip)
        return adresse.is_loopback or adresse.is_private
    except ValueError:
        return False
