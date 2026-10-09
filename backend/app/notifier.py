"""Envoi des e-mails aux abonnes.

Sans SMTP configure dans .env, l'e-mail est seulement affiche dans le terminal
(pratique pour tester). Avec Gmail : activez la validation en 2 etapes puis
creez un "mot de passe d'application" et mettez-le dans SMTP_PASSWORD.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD


def _html(nom, offres):
    cartes = "".join(f"""
      <tr><td style="padding:22px 0;border-bottom:1px solid #e6ddd2">
        <div style="font:11px Arial;letter-spacing:2px;text-transform:uppercase;color:#E8601C">{o['categorie']}</div>
        <div style="font:22px Georgia,serif;color:#2b2622;margin:6px 0">{o['titre']}</div>
        <div style="font:13px Arial;color:#6f655c">{o['entreprise']} &middot; {o['ville']}</div>
        <div style="font:13px Arial;color:#4a423b;margin:10px 0">{o.get('resume') or ''}</div>
        <a href="{o['lien']}" style="font:11px Arial;letter-spacing:2px;text-transform:uppercase;color:#2b2622">Voir l'offre &rarr;</a>
      </td></tr>""" for o in offres)
    return f"""
    <div style="background:#f6f1eb;padding:40px 0">
      <table align="center" width="560" style="background:#fffdf9;padding:40px">
        <tr><td style="text-align:center;font:26px Georgia,serif;color:#2b2622;letter-spacing:4px">L'ATELIER DES STAGES</td></tr>
        <tr><td style="text-align:center;font:13px Arial;color:#6f655c;padding:14px 0 10px">
          Bonjour {nom or ''}, {len(offres)} nouvelle(s) offre(s) pour votre profil.</td></tr>
        {cartes}
      </table>
    </div>"""


def envoyer_email(email, nom, offres):
    sujet = f"{len(offres)} nouveau(x) stage(s) pour vous"
    if not (SMTP_USER and SMTP_PASSWORD):
        print(f"    [E-MAIL simule] -> {email} : {sujet}")
        for o in offres:
            print(f"        - {o['titre']} | {o['entreprise']} | {o['ville']}")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"] = f"L'Atelier des Stages <{SMTP_USER}>"
    msg["To"] = email
    texte = "\n".join(f"- {o['titre']} ({o['entreprise']}, {o['ville']}) : {o['lien']}" for o in offres)
    msg.attach(MIMEText(texte, "plain", "utf-8"))
    msg.attach(MIMEText(_html(nom, offres), "html", "utf-8"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.send_message(msg)
        print(f"    [E-MAIL envoye] -> {email}")
        return True
    except Exception as e:
        print(f"    [E-MAIL ERREUR] {email} : {e}")
        return False
