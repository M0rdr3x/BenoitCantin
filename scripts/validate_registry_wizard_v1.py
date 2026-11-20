#!/usr/bin/env python3
"""Registre SINJIRA : contrôle de la progression et des protections existantes.

Le parcours est une présentation uniquement; les règles de sécurité serveur,
le consentement et la validation du module métier restent inchangés.
"""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "projets/sinjira/registre/index.html"
JS = ROOT / "assets/js/sinjira-registry-wizard-v1.js"
CSS = ROOT / "assets/css/sinjira-registry-wizard-v1.css"


class RegistryHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fieldsets = 0
        self.labels = []
        self.ids = []
        self.names = []
        self.assets = []
        self.form_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "fieldset" and "v24-fieldset" in attrs.get("class", "").split():
            self.fieldsets += 1
        if tag == "form" and "data-character-form" in attrs:
            self.form_count += 1
        if tag == "label" and "for" in attrs:
            self.labels.append(attrs["for"])
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag in {"input", "select", "textarea"}:
            self.names.append((attrs.get("name"), attrs.get("id")))
        if tag in {"link", "script"}:
            self.assets.append(attrs.get("src") or attrs.get("href") or "")


def main():
    errors = []
    if not all(p.is_file() for p in (HTML, JS, CSS)):
        print("ECHEC : fichiers du parcours Registre manquants")
        return 1

    html = HTML.read_text("utf-8")
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    parser = RegistryHTML()
    parser.feed(html)

    if parser.fieldsets != 9 or parser.form_count != 1:
        errors.append("Le Registre doit conserver exactement neuf fieldsets et un formulaire")
    if len(parser.labels) < 25:
        errors.append("Associations explicites des 25 libellés manquantes")
    # Un id placé après le slash de fermeture d'un input crée du HTML
    # invalide et peut rendre le label inopérant selon le navigateur.
    if re.search(r"<input\b[^>]*\/\s+id=", html, re.I):
        errors.append("Attribut id mal placé après la fermeture de balise input")
    for label_id in parser.labels:
        if parser.ids.count(label_id) != 1:
            errors.append("Libellé sans identifiant de champ unique : " + label_id)
    for asset in (
        "sinjira-registry-wizard-v1.css?v=1.0.0",
        "sinjira-registry-wizard-v1.js?v=1.0.0",
        "sinjira-character-registry.js?v=24.5.10",
    ):
        if not any(asset in reference for reference in parser.assets):
            errors.append("Dépendance requise non chargée : " + asset)

    for marker in (
        'data-character-form', 'data-character-submit-status',
        'name="confirm_original" required', 'name="formspree_receipt_opt_in"',
        'type="submit" disabled', 'data-registry-login-actions',
        'AAL2', 'Ma sécurité',
    ):
        if marker not in html:
            errors.append("Garde-fou d’origine perdu : " + marker)

    for marker in (
        'steps.length !== 9', "consent.length !== 2", 'button[type="submit"]',
        'fieldset.hidden = i !== current', 'submit.hidden = !last',
        'form.addEventListener(\'invalid\'', 'form.addEventListener(\'submit\'',
        "event.preventDefault()", 'checkValidity()', 'reportValidity()',
        "10 * 1024 * 1024", "data-max-select", "prefers-reduced-motion",
    ):
        if marker not in js:
            errors.append("Contrôle de navigation manquant : " + marker)

    if re.search(r"\b(localStorage|sessionStorage|indexedDB|fetch\s*\(|sendBeacon|XMLHttpRequest)\b", js):
        errors.append("La progression ne doit pas enregistrer ou transmettre de réponse privée")
    if re.search(r"\b(form\.submit|requestSubmit)\s*\(", js):
        errors.append("Le script d'ergonomie ne doit jamais déclencher l'envoi lui-même")

    for marker in (
        '[hidden]', '.registry-wizard-header', '.registry-wizard-controls',
        '.registry-wizard-progress', 'min-height:50px',
        '@media(max-width:580px)', '@media(prefers-reduced-motion:reduce)',
    ):
        if marker not in css:
            errors.append("Affichage mobile/accessibilité manquant : " + marker)

    if errors:
        print(f"ECHEC Registre ergonomique : {len(errors)} erreur(s)")
        for err in errors:
            print("- " + err)
        return 1
    print("OK : neuf étapes, 25 libellés associés, consentements/AAL2 inchangés, sans persistance locale")
    return 0


if __name__ == "__main__":
    sys.exit(main())
