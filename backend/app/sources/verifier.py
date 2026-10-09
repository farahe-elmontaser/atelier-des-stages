"""Teste chaque source une par une et affiche ce qu'elle trouve.

Lancement (dans le dossier backend, venv active) :
    python -m app.sources.verifier
"""
import time

from . import SOURCES

print("\n=== Verification des sources d'offres ===\n")
total = 0
for source in SOURCES:
    debut = time.time()
    try:
        offres = source()
    except Exception as e:
        print(f"[ERREUR] {source.__name__} : {e}\n")
        continue
    total += len(offres)
    print(f"[{len(offres):>3} offres] {source.__name__}  ({time.time() - debut:.1f} s)")
    for o in offres[:3]:
        print(f"      - {o.titre[:60]} | {o.entreprise} | {o.ville[:30]}")
        print(f"        {o.lien[:90]}")
    print()
print(f"TOTAL : {total} offres de stage trouvees.")
