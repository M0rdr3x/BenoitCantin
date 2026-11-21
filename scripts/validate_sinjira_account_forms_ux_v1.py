#!/usr/bin/env python3
"""Contrat ergonomique des formulaires SINJIRA : sécurité et accessibilité.

Aucun accès aux comptes; lecture des quatre pages publiques versionnées.
Les noms, valeurs, droits et traitements des formulaires sont préservés.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "compte/connexion.html": 2,
    "compte/mot-de-passe-oublie.html": 1,
    "compte/reinitialiser-mot-de-passe.html": 2,
    "compte/inscription.html": 16,
    "compte/profil.html": 14,
    "compte/parametres.html": 2,
}
CSS = ROOT / "assets/css/sinjira-forms-ux-v1.css"
JS = ROOT / "assets/js/sinjira-password-visibility-v1.js"
FIELD = re.compile(
    r'<div class="field"><label\b([^>]*)>[^<]*</label><(input|select|textarea)\b([^>]*)>',
    re.I,
)
ATTRIBUTE = lambda key, attrs: (re.search(r'\b' + re.escape(key) + r'="([^"]+)"', attrs) or [None, None])[1]


def check_page(path, expected):
    errors = []
    text = (ROOT / path).read_text("utf-8")
    if 'data-sinjira-form-ux="v1"' not in text:
        errors.append(f"{path}: activation responsive absente")
    auth_nav = path in {
        "compte/connexion.html", "compte/inscription.html",
        "compte/mot-de-passe-oublie.html", "compte/reinitialiser-mot-de-passe.html",
    }
    css_version = "1.0.1" if auth_nav else "1.0.0"
    if f"/assets/css/sinjira-forms-ux-v1.css?v={css_version}" not in text:
        errors.append(f"{path}: style responsive manquant")
    if auth_nav and 'sinjira-auth-nav-v1.js?v=1.0.0' not in text:
        errors.append(f"{path}: commandes de navigation Auth absentes")
    found = list(FIELD.finditer(text))
    if len(found) != expected:
        errors.append(f"{path}: {len(found)} étiquettes de champs au lieu de {expected}")
    ids = re.findall(r'\bid="([^"]+)"', text)
    for match in found:
        label, _, field = match.groups()
        target = ATTRIBUTE("for", label)
        control = ATTRIBUTE("id", field)
        if not target or target != control or ids.count(control) != 1:
            errors.append(f"{path}: label non lié à un champ unique ({target}, {control})")
        if re.search(r'/\s+id=', field):
            errors.append(f"{path}: attribut id après fermeture de balise")
    if path.endswith("inscription.html"):
        open_details = text.index('data-optional-personal-info')
        required = text.index('data-signup-birth-date')
        guardian = text.index('data-guardian-code-wrap')
        origins = text.index('<h3>Originaire de</h3>')
        advice = text.index('SINJIRA™ ne demande pas votre adresse civique')
        if not required < guardian < open_details < origins < advice:
            errors.append("Inscription : âge, code parental ou résidence masqués")
        segment = text[open_details:text.index("</details>", open_details)]
        if re.search(r'\brequired\b', segment):
            errors.append("Inscription : le bloc facultatif masque un champ obligatoire")
        for marker in ('name="password"', 'name="password_confirm"',
                       'name="birth_date"', 'name="guardian_code"',
                       'name="formspree_receipt_opt_in"'):
            if marker not in text:
                errors.append(f"Inscription : champ de sécurité manquant {marker}")
    if path.endswith("profil.html"):
        if text.count('data-optional-private-profile') != 1:
            errors.append("Profil privé : section complémentaire manquante")
        if 'data-private-profile-form' not in text or 'data-private-profile-save' not in text:
            errors.append("Profil privé : contrat d'enregistrement cassé")
    if path.endswith("parametres.html"):
        for marker in ('data-privacy-settings-form', 'data-notification-settings-form',
                       'data-delete-account'):
            if marker not in text:
                errors.append("Paramètres : contrôle sensible manquant " + marker)
    if path.endswith(("connexion.html", "inscription.html", "reinitialiser-mot-de-passe.html")):
        if not re.search(r"sinjira-password-visibility-v1\.js\?v=1\.0\.[0-9]+", text):
            errors.append(path + ": assistance mot de passe manquante")
    return errors


def main():
    problems = []
    if not CSS.is_file() or not JS.is_file():
        print("ECHEC : styles ou script de saisie introuvables")
        return 1

    for path, expected in PAGES.items():
        problems.extend(check_page(path, expected))

    script = JS.read_text("utf-8")
    for marker in (
        "form[data-login-form], form[data-signup-form]", "input[type=\"password\"]",
        "button.type = 'button'", "button.dataset.passwordVisibility",
        "button.setAttribute('aria-controls'", "button.setAttribute('aria-pressed'",
        "document.addEventListener('visibilitychange'", "window.addEventListener('pagehide'",
        "form.addEventListener('submit', concealAll, true)",
        "document.addEventListener('DOMContentLoaded', initialize",
        "form[data-reset-form]",
    ):
        if marker not in script:
            problems.append("Affichage des mots de passe : protection manquante " + marker)
    if re.search(r'\b(localStorage|sessionStorage|indexedDB|fetch\s*\(|sendBeacon|XMLHttpRequest)\b', script):
        problems.append("Le script mot de passe ne doit enregistrer ou transmettre aucun secret")
    if re.search(r'\.value\b|console\.', script):
        problems.append("Le script mot de passe ne doit lire ou journaliser aucune valeur")
    css = CSS.read_text("utf-8")
    for marker in ('font-size:max(1rem,16px)', 'min-height:46px',
                   '.account-optional-details summary:focus-visible',
                   '@media(max-width:680px)', ':focus-visible'):
        if marker not in css:
            problems.append("Style de saisie mobile : protection manquante " + marker)

    if problems:
        print(f"ECHEC formulaires SINJIRA : {len(problems)} problème(s)")
        for problem in problems:
            print("- " + problem)
        return 1
    print("OK : 37 libellés liés, six formulaires, saisie 16 px et assistance sécurisée du mot de passe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
