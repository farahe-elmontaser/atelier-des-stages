#!/usr/bin/env bash
# Met le serveur a jour apres un "git push" depuis votre PC.
# Usage (sur le serveur) :  bash /opt/atelier/deploy/update.sh
set -euo pipefail
DOSSIER="/opt/atelier"

echo "=== Recuperation du nouveau code ==="
git -C "$DOSSIER" pull

echo "=== Bibliotheques Python ==="
"$DOSSIER/backend/venv/bin/pip" install -r "$DOSSIER/backend/requirements.txt"

echo "=== Reconstruction du site ==="
cd "$DOSSIER/frontend"
npm ci || npm install
npm run build
sudo rm -rf /var/www/atelier/*
sudo cp -r dist/* /var/www/atelier/

echo "=== Redemarrage du backend ==="
sudo systemctl restart atelier-backend
sleep 3
sudo systemctl --no-pager status atelier-backend | head -5
echo "Mise a jour terminee."
