"""Envoi des e-mails aux abonnes.

Sans SMTP configure dans .env, l'e-mail est seulement affiche dans le terminal
(pratique pour tester). Avec Gmail : activez la validation en 2 etapes puis
creez un "mot de passe d'application" et mettez-le dans SMTP_PASSWORD.
"""
import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, URL_PUBLIQUE


def _lien_sur(url):
    """On n'accepte que des liens http(s) (pas de javascript:...)."""
    url = str(url or "")
    return html.escape(url, quote=True) if url.startswith(("http://", "https://")) else "#"


def _a_un_vrai_lien(o):
    return str(o.get("lien") or "").startswith(("http://", "https://"))


def _bouton(o):
    """Lien "Voir l'offre" (via /api/r/ pour compter le clic), seulement si l'offre a un vrai lien."""
    if not _a_un_vrai_lien(o):
        return '<span style="font:11px Arial;color:#9a8f85">Offre de démonstration (sans lien)</span>'
    url = _lien_sur(f"{URL_PUBLIQUE}/api/r/{o['id']}")
    return (f'<a href="{url}" style="font:11px Arial;letter-spacing:2px;'
            f'text-transform:uppercase;color:#2b2622">Voir l\'offre &rarr;</a>')


def _html(nom, offres, lien_desinscription):
    e = lambda t: html.escape(str(t or ""))          # le texte scrape ne peut pas injecter de HTML
    cartes = "".join(f"""
      <tr><td style="padding:22px 0;border-bottom:1px solid #e6ddd2">
        <div style="font:11px Arial;letter-spacing:2px;text-transform:uppercase;color:#E8601C">{e(o['categorie'])}</div>
        <div style="font:22px Georgia,serif;color:#2b2622;margin:6px 0">{e(o['titre'])}</div>
        <div style="font:13px Arial;color:#6f655c">{e(o['entreprise'])} &middot; {e(o['ville'])}</div>
        <div style="font:13px Arial;color:#4a423b;margin:10px 0">{e(o.get('resume'))}</div>
        {_bouton(o)}
      </td></tr>""" for o in offres)
    return f"""
    <div style="background:#f6f1eb;padding:40px 0">
      <table align="center" width="560" style="background:#fffdf9;padding:40px">
        <tr><td style="text-align:center;font:26px Georgia,serif;color:#2b2622;letter-spacing:4px">L'ATELIER DES STAGES</td></tr>
        <tr><td style="text-align:center;font:13px Arial;color:#6f655c;padding:14px 0 10px">
          Bonjour {e(nom)}, {len(offres)} nouvelle(s) offre(s) pour votre profil.</td></tr>
        {cartes}
        <tr><td style="text-align:center;font:11px Arial;color:#9a8f85;padding-top:26px">
          <a href="{_lien_sur(lien_desinscription)}" style="color:#9a8f85">Se désinscrire</a></td></tr>
      </table>
    </div>"""


def envoyer_email(email, nom, offres, token=""):
    lien_desinscription = f"{URL_PUBLIQUE}/api/desinscription?token={token}"
    sujet = f"{len(offres)} nouveau(x) stage(s) pour vous"
    if not (SMTP_USER and SMTP_PASSWORD):
        print(f"    [E-MAIL simule] -> {email} : {sujet}")
        for o in offres:
            print(f"        - {o['titre']} | {o['entreprise']} | {o['ville']}")
        print(f"        (lien de desinscription : {lien_desinscription})")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"] = f"L'Atelier des Stages <{SMTP_USER}>"
    msg["To"] = email
    texte = "\n".join(f"- {o['titre']} ({o['entreprise']}, {o['ville']})"
                      + (f" : {URL_PUBLIQUE}/api/r/{o['id']}" if _a_un_vrai_lien(o) else " (demo)")
                      for o in offres)
    texte += f"\n\nSe desinscrire : {lien_desinscription}"
    msg.attach(MIMEText(texte, "plain", "utf-8"))
    msg.attach(MIMEText(_html(nom, offres, lien_desinscription), "html", "utf-8"))
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
