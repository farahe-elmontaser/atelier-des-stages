#!/usr/bin/env bash
# =====================================================================
#  Installation de L'Atelier des Stages sur un serveur Ubuntu (VPS)
#
#  Utilisation (sur le serveur, connecte en SSH) :
#     bash install.sh  VOTRE_DOMAINE_OU_IP
#  Exemples :
#     bash install.sh 132.145.20.10
#     bash install.sh atelier-stages.duckdns.org
#
#  Options (variables d'environnement) :
#     REPO=https://github.com/vous/votre-depot.git   (depot GitHub a installer)
#     OLLAMA=non        (ne pas installer Ollama : classification par mots-cles)
#     MODELE=llama3.2   (modele Ollama ; llama3.2:1b pour un petit serveur)
# =====================================================================
set -euo pipefail

DOMAINE="${1:-}"
REPO="${REPO:-https://github.com/farahe-elmontaser/stage-alert.git}"
OLLAMA="${OLLAMA:-oui}"
MODELE="${MODELE:-llama3.2}"
DOSSIER="/opt/atelier"
UTILISATEUR="$(whoami)"

if [ -z "$DOMAINE" ]; then
  echo "Usage : bash install.sh VOTRE_DOMAINE_OU_IP"; exit 1
fi
if [ "$UTILISATEUR" = "root" ]; then
  echo "Lancez ce script avec votre utilisateur normal (ex. ubuntu), pas root."; exit 1
fi

etape() { echo; echo "=== $* ==="; }

etape "1/9 Mise a jour du systeme et outils de base"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -y
sudo -E apt-get install -y python3 python3-venv python3-pip nginx git curl iptables-persistent

etape "2/9 Node.js 20 (pour construire le site React)"
if ! command -v node >/dev/null || [ "$(node -v | cut -d. -f1 | tr -d v)" -lt 18 ]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo -E apt-get install -y nodejs
fi
node -v

etape "3/9 Recuperation du code depuis GitHub"
sudo mkdir -p "$DOSSIER"
sudo chown "$UTILISATEUR":"$UTILISATEUR" "$DOSSIER"
if [ -d "$DOSSIER/.git" ]; then
  git -C "$DOSSIER" pull
else
  git clone "$REPO" "$DOSSIER"
fi

etape "4/9 Backend Python (environnement virtuel + bibliotheques)"
cd "$DOSSIER/backend"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

etape "5/9 Fichier de configuration .env"
if [ ! -f .env ]; then
  cp .env.example .env
  JETON="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
  sed -i "s|^URL_PUBLIQUE=.*|URL_PUBLIQUE=http://$DOMAINE|" .env
  sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=http://$DOMAINE,https://$DOMAINE|" .env
  sed -i "s|^ADMIN_TOKEN=.*|ADMIN_TOKEN=$JETON|" .env
  sed -i "s|^OLLAMA_MODEL=.*|OLLAMA_MODEL=$MODELE|" .env
  chmod 600 .env                       # seul votre utilisateur peut lire les secrets
  echo "  .env cree. ADMIN_TOKEN = $JETON  (gardez-le pour lancer /api/refresh)"
else
  echo "  .env existe deja : je ne le modifie pas."
fi

etape "6/9 Construction du site React"
cd "$DOSSIER/frontend"
npm ci || npm install
npm run build
sudo mkdir -p /var/www/atelier
sudo rm -rf /var/www/atelier/*
sudo cp -r dist/* /var/www/atelier/

etape "7/9 Ollama (LLM local)"
if [ "$OLLAMA" = "oui" ]; then
  if ! command -v ollama >/dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
  fi
  sudo systemctl enable --now ollama || true
  sleep 3
  ollama pull "$MODELE" || echo "  ATTENTION : telechargement du modele impossible (le site marchera avec les mots-cles)."
else
  echo "  Ollama non installe : classification par mots-cles."
fi

etape "8/9 Service systemd (le backend demarre tout seul et redemarre s'il plante)"
sed -e "s|__UTILISATEUR__|$UTILISATEUR|g" -e "s|__DOSSIER__|$DOSSIER|g" \
  "$DOSSIER/deploy/atelier-backend.service" | sudo tee /etc/systemd/system/atelier-backend.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable atelier-backend
sudo systemctl restart atelier-backend

etape "9/9 Nginx (porte d'entree) + pare-feu"
sed -e "s|__DOMAINE__|$DOMAINE|g" "$DOSSIER/deploy/nginx-atelier.conf" \
  | sudo tee /etc/nginx/sites-available/atelier >/dev/null
sudo ln -sf /etc/nginx/sites-available/atelier /etc/nginx/sites-enabled/atelier
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# Ouvrir les ports 80 (HTTP) et 443 (HTTPS) dans le pare-feu de la machine.
# (Indispensable sur Oracle Cloud, dont les images Ubuntu bloquent tout par defaut.)
for PORT in 80 443; do
  if ! sudo iptables -C INPUT -p tcp --dport "$PORT" -j ACCEPT 2>/dev/null; then
    sudo iptables -I INPUT 1 -p tcp --dport "$PORT" -j ACCEPT
  fi
done
sudo netfilter-persistent save || true

sleep 3
echo
echo "================================================================"
if curl -fs http://127.0.0.1/api/profils >/dev/null; then
  echo " Installation terminee !  Ouvrez :  http://$DOMAINE"
else
  echo " Installation terminee, mais l'API ne repond pas encore."
  echo " Regardez les journaux :  sudo journalctl -u atelier-backend -n 50"
fi
echo " Journaux du backend en direct :  sudo journalctl -u atelier-backend -f"
echo " Pour le HTTPS (avec un nom de domaine) :  bash $DOSSIER/deploy/https.sh $DOMAINE"
echo "================================================================"
