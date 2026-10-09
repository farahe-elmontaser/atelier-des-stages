# Mettre L'Atelier des Stages en ligne sur un VPS

Architecture une fois en ligne :

```
Internet ──→ Nginx (port 80/443) ──┬──→ site React        (/var/www/atelier)
                                   └──→ /api → Uvicorn    (127.0.0.1:8000, 1 worker)
                                                  ├──→ SQLite  (/opt/atelier/backend/data)
                                                  └──→ Ollama  (127.0.0.1:11434)
```

- **Nginx** : la porte d'entrée. Il sert le site et transmet `/api` au backend (*reverse proxy*).
- **systemd** : démarre le backend tout seul et le relance s'il plante.
- Le backend et Ollama n'écoutent **qu'en local** : on ne peut pas les joindre directement depuis Internet.

Durée : environ **1 heure** la première fois.

---

## Étape 0 : envoyer la dernière version sur GitHub

Sur votre PC, dans VS Code, envoyez la dernière version (avec le dossier `deploy/`) :

```
git add .
git commit -m "Fichiers de deploiement"
git push
```

Le serveur téléchargera le code depuis GitHub. Le dépôt doit donc être **public**. S'il est privé, voir la section « Dépôt privé » en bas.

## Étape 1 : créer le serveur (VPS)

Choisissez **Ubuntu 22.04 ou 24.04**.

| Hébergeur | Machine conseillée | Remarque |
|---|---|---|
| **Oracle Cloud** (niveau « Always Free ») | Instance **Ampere A1** (ARM), le plus de RAM possible | Gratuit, mais il faut une carte bancaire pour la vérification. Les limites ont changé en 2026 : vérifiez-les. |
| Hetzner, OVH, DigitalOcean… | **4 Go de RAM minimum** si vous voulez Ollama | Quelques euros par mois |

**RAM et Ollama :** `llama3.2` (3B) demande environ 4 Go de RAM libre. Avec 2 Go, utilisez `llama3.2:1b` ou installez sans Ollama : le site marche alors avec la classification par mots-clés.

À la création :

1. Ajoutez une **clé SSH**. L'hébergeur vous laisse télécharger la clé privée (un fichier `.key` ou `.pem`). **Gardez-la précieusement** : c'est votre clé pour entrer sur le serveur.
2. Notez l'**adresse IP publique** du serveur (par exemple `132.145.20.10`).

### Spécial Oracle Cloud : ouvrir les ports 80 et 443

Oracle bloque tout par défaut, à **deux endroits** :

1. **Dans la console Oracle** : ouvrez votre instance, puis son **Subnet**, puis la **Security List**, puis **Add Ingress Rules**. Ajoutez deux règles :
   - Source `0.0.0.0/0`, protocole TCP, port de destination **80**
   - Source `0.0.0.0/0`, protocole TCP, port de destination **443**
2. **Dans la machine** : le script `install.sh` s'en occupe (règles `iptables`).

## Étape 2 : se connecter au serveur depuis Windows

Ouvrez **PowerShell** (SSH est inclus dans Windows 10 et 11) :

```
ssh -i C:\Users\farah\Downloads\ma-cle.key ubuntu@132.145.20.10
```

- Remplacez le chemin de la clé et l'IP par les vôtres.
- L'utilisateur est `ubuntu` sur Oracle et Ubuntu. Chez certains hébergeurs, c'est `root` : dans ce cas, créez d'abord un utilisateur (voir « Problèmes fréquents »).
- À la question « Are you sure you want to continue connecting? », tapez `yes`.

Si Windows refuse la clé (« UNPROTECTED PRIVATE KEY FILE »), tapez ceci dans PowerShell :
```
icacls C:\Users\farah\Downloads\ma-cle.key /inheritance:r /grant:r "$($env:USERNAME):(R)"
```

Vous êtes connectée quand la ligne commence par `ubuntu@...:~$`. Tout ce qui suit se tape **sur le serveur**.

## Étape 3 : lancer l'installation automatique

```
git clone https://github.com/farahe-elmontaser/stage-alert.git /tmp/atelier
bash /tmp/atelier/deploy/install.sh 132.145.20.10
```

(Remplacez l'IP par celle de votre serveur.)

Le script fait tout en 9 étapes (environ 10 à 20 minutes, surtout pour télécharger le modèle Ollama) :

1. installation de Python, Nginx et Git ;
2. installation de Node.js 20 ;
3. récupération du code dans `/opt/atelier` ;
4. environnement Python et bibliothèques ;
5. création du `.env`, avec un `ADMIN_TOKEN` secret (**notez-le**) ;
6. construction du site React ;
7. installation d'Ollama et téléchargement du modèle ;
8. création du service systemd (démarrage automatique) ;
9. configuration de Nginx et ouverture du pare-feu.

Options possibles :
```
OLLAMA=non bash /tmp/atelier/deploy/install.sh 132.145.20.10          # sans LLM
MODELE=llama3.2:1b bash /tmp/atelier/deploy/install.sh 132.145.20.10  # petit modèle
```

Une fois terminé, ouvrez **http://132.145.20.10** dans votre navigateur. 🎉

## Étape 4 : configurer les clés (e-mails, API)

```
nano /opt/atelier/backend/.env
```

Remplissez `SMTP_USER`, `SMTP_PASSWORD`, et si vous les avez `ADZUNA_...` et `FRANCE_TRAVAIL_...`.
Pour enregistrer dans nano : **Ctrl+O**, **Entrée**, puis **Ctrl+X** pour quitter. Ensuite :

```
sudo systemctl restart atelier-backend
```

Si les e-mails n'arrivent pas, certains hébergeurs bloquent l'envoi SMTP. Regardez les journaux (commande plus bas). En cas de blocage, il faudra un service d'envoi par API comme Brevo.

## Étape 5 (optionnelle) : un nom de domaine et le HTTPS 🔒

Le HTTPS (le cadenas) nécessite un **nom de domaine**, pas une simple IP.

**Gratuit avec DuckDNS :**
1. Allez sur **duckdns.org** et connectez-vous avec Google ou GitHub.
2. Créez un sous-domaine, par exemple `atelier-stages`, puis mettez l'**IP de votre serveur** et cliquez sur *update ip*.
3. Vous obtenez `atelier-stages.duckdns.org`.

Ensuite, sur le serveur :
```
bash /opt/atelier/deploy/install.sh atelier-stages.duckdns.org
bash /opt/atelier/deploy/https.sh atelier-stages.duckdns.org
```

Votre site est maintenant en ligne sur **https://atelier-stages.duckdns.org**.

---

## Mettre à jour le site après une modification

1. Sur votre PC : `git add .`, puis `git commit -m "..."`, puis `git push`.
2. Sur le serveur :
   ```
   bash /opt/atelier/deploy/update.sh
   ```

## Commandes utiles (sur le serveur)

| Action | Commande |
|---|---|
| Voir le backend en direct (scraping, LLM, e-mails) | `sudo journalctl -u atelier-backend -f` (Ctrl+C pour quitter) |
| Les 50 dernières lignes du journal | `sudo journalctl -u atelier-backend -n 50` |
| État du backend | `sudo systemctl status atelier-backend` |
| Redémarrer le backend | `sudo systemctl restart atelier-backend` |
| Lancer une vérification maintenant | `curl -X POST -H "X-Admin-Token: VOTRE_ADMIN_TOKEN" http://127.0.0.1/api/refresh` |
| Modèles Ollama installés | `ollama list` |
| Mémoire libre | `free -h` |

Le bouton « Vérifier maintenant » du site est **réservé à l'administrateur** une fois en ligne. Les visiteurs voient « Action réservée à l'administrateur ». Le scheduler, lui, vérifie automatiquement toutes les heures.

## Problèmes fréquents

| Symptôme | Solution |
|---|---|
| Le site ne s'ouvre pas du tout | Ports 80/443 pas ouverts : vérifiez la **Security List** (Oracle) ou le pare-feu de l'hébergeur |
| « 502 Bad Gateway » | Le backend est arrêté : `sudo journalctl -u atelier-backend -n 50` pour voir l'erreur |
| Le site s'affiche mais 0 offre | Premier passage en cours (le LLM est lent) : attendez quelques minutes et suivez le journal |
| Tout est classé `(mots-cles)` | Ollama ne répond pas : `sudo systemctl status ollama`, et vérifiez la RAM avec `free -h` |
| Le serveur se connecte en `root` | Créez un utilisateur : `adduser farah`, puis `usermod -aG sudo farah`, `su - farah`, et relancez le script |
| Dépôt privé | Sur GitHub : **Settings > Developer settings > Personal access tokens**, créez un token, puis :<br>`REPO=https://VOTRE_TOKEN@github.com/farahe-elmontaser/stage-alert.git bash install.sh IP` |

## Sécurité du serveur : bonnes pratiques

- Ne partagez **jamais** la clé SSH ni le fichier `.env`.
- Mettez le système à jour de temps en temps : `sudo apt update && sudo apt upgrade -y`
- Le backend et Ollama n'écoutent qu'en local (`127.0.0.1`) : seul Nginx est exposé.
