#!/usr/bin/env bash
# Active le HTTPS (cadenas) avec un certificat gratuit Let's Encrypt.
# Necessite un NOM DE DOMAINE qui pointe vers l'IP du serveur (pas une simple IP).
# Usage :  bash https.sh atelier-stages.duckdns.org
set -euo pipefail
DOMAINE="${1:?Usage : bash https.sh VOTRE_DOMAINE}"
DOSSIER="/opt/atelier"

sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d "$DOMAINE" --redirect --agree-tos --register-unsafely-without-email -n

# Les liens des e-mails (desinscription) passent en https
sed -i "s|^URL_PUBLIQUE=.*|URL_PUBLIQUE=https://$DOMAINE|" "$DOSSIER/backend/.env"
sudo systemctl restart atelier-backend
echo "HTTPS actif : https://$DOMAINE  (le certificat se renouvelle automatiquement)"
