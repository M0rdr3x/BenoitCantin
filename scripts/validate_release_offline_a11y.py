#!/usr/bin/env python3
"""Contrat de non-regression des surfaces publiques réconciliées avec main.

Vérifie sans navigateur que le secours hors ligne, le menu commun et le
formulaire personnel désactivé gardent leurs protections réelles.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_OFFLINE = (
    "/",
    "/projets/sinjira/",
    "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/communaute/",
    "/projets/sinjira/monde-parallele/",
    "/projets/sinjira/codex/",
    "/transparence-ia.html",
)


def validate_offline(html: str) -> list[str]:
    errors = []
    robots = re.search(
        r'<meta\s+name="robots"\s+content="([^"]+)"', html
    )
    tokens = {v.strip().lower() for v in (robots.group(1) if robots else "").split(",")}
    if not {"noindex", "nofollow", "noarchive"} <= tokens:
        errors.append("La page hors ligne exige noindex, nofollow et noarchive.")
    for marker in (
        'class="skip-link" href="#contenu"',
        '<main class="section" id="contenu">',
        'data-ai-transparency',
        'href="/transparence-ia.html"',
        'type="button" onclick="location.reload()"',
        'role="status" aria-live="polite"',
        "Les fonctions de compte, l’administration, les sauvegardes",
        "Aucune donnée privée n’est chargée depuis cette page.",
    ):
        if marker not in html:
            errors.append(f"Secours hors ligne incomplet : {marker}")
    for url in PUBLIC_OFFLINE:
        if f'href="{url}"' not in html:
            errors.append(f"Raccourci hors ligne absent : {url}")
    if re.search(r'(?:href|src|action)="(?:/compte/|/admin/|/Admin/|/app/|/supabase/)', html):
        errors.append("Une ressource authentifiée ne peut être servie par l'écran hors ligne.")
    return errors


def validate_public_consistency() -> list[str]:
    errors = []
    offline = (ROOT / "offline.html").read_text(encoding="utf-8")
    errors.extend(validate_offline(offline))
    for url in PUBLIC_OFFLINE:
        if url == "/":
            file = ROOT / "index.html"
        elif url.endswith("/"):
            file = ROOT / url.lstrip("/") / "index.html"
        else:
            file = ROOT / url.lstrip("/")
        if not file.is_file():
            errors.append(f"Destination publique non disponible : {url}")

    about = (ROOT / "a-propos.html").read_text(encoding="utf-8")
    for marker in (
        'aria-controls="navigation-principale"',
        'id="navigation-principale"',
        'data-sinjira-session-nav',
        'src="/assets/js/site.js?v=24.4.100"',
        'href="/transparence-ia.html"',
        'hreflang="fr-CA"',
    ):
        if marker not in about:
            errors.append(f"À propos : contrat menu/SEO/transparence manquant : {marker}")

    privacy = (ROOT / "gouvernance-vie-privee.html").read_text(encoding="utf-8")
    for marker in ('aria-controls="navigation-principale"', 'id="navigation-principale"', '/compte/vie-privee.html'):
        if marker not in privacy:
            errors.append(f"Gouvernance vie privée : contrat de main perdu : {marker}")

    contact = (ROOT / "contact.html").read_text(encoding="utf-8")
    for marker in (
        '<fieldset id="contact-personal-fields" disabled',
        "var PERSONAL_ENDPOINT=''",
        'href="/projets/projet-nova/contact.html"',
        'aria-controls="navigation-principale"',
    ):
        if marker not in contact:
            errors.append(f"Contact : séparation et désactivation non garanties : {marker}")
    return errors


def self_test() -> list[str]:
    from pathlib import Path

    sample = (ROOT / "offline.html").read_text(encoding="utf-8")
    errors = []
    if validate_offline(sample):
        errors.append("L'auto-test ne valide pas la page hors ligne actuelle.")
    altered = sample.replace("noindex,nofollow,noarchive", "index,follow", 1)
    if not validate_offline(altered):
        errors.append("Le test n'a pas rejeté une page indexable.")
    altered = sample.replace('type="button" onclick="location.reload()"', "", 1)
    if not validate_offline(altered):
        errors.append("Le test n'a pas rejeté la suppression du bouton de réessai.")
    altered = sample.replace('href="/projets/sinjira/romans/"', 'href="/compte/romans/"', 1)
    if not validate_offline(altered):
        errors.append("Le test n'a pas rejeté un raccourci de compte privé.")
    return errors


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    errors = self_test() if options.self_test else validate_public_consistency()
    for error in errors:
        print("ECHEC:", error)
    if errors:
        raise SystemExit(1)
    print("OK: secours public hors ligne, accessibilité, SEO, gouvernance et formulaire séparé.")
