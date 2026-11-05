#!/usr/bin/env python3
"""Vérification du paquet *réel* de publication NOVA, sans réseau ni votes."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVA = Path("projets/projet-nova")
REQUIRED_FILES = (
    "index.html",
    "boussole-electorale.html",
    "sondage-citoyen.html",
    "sondages-a-valider.html",
    "assets/boussole-electorale.js",
    "assets/boussole-public-corpus.js",
    "assets/boussole-electorale.css",
    "assets/sondage-citoyen.js",
    "assets/sondage-public-corpus.js",
    "assets/sondage-citoyen.css",
    "assets/sondage-citoyen.svg",
    "data/boussole-electorale-v2.json",
    "data/sondage-citoyen-v1.json",
    "confidentialite.html",
    "sitemap.xml",
)
FORBIDDEN = ("supabase", "scripts", "tests", "docs", ".github", "mobile-native", ".env", "netlify.toml")


def check(published: Path) -> list[str]:
    errors: list[str] = []
    prefix = published / NOVA
    for path in REQUIRED_FILES:
        target = prefix / path
        if not target.is_file():
            errors.append(f"Fichier NOVA absent du paquet public : {NOVA / path}")
        elif target.is_symlink():
            errors.append(f"Symlink dans le paquet public : {NOVA / path}")
    for path in FORBIDDEN:
        if (published / path).exists():
            errors.append(f"Artefact privé ou de construction exposé : {path}")
    for config in ("_headers", "_redirects"):
        if not (published / config).is_file():
            errors.append(f"Configuration Netlify absente : {config}")
    if errors:
        return errors

    home = (prefix / "index.html").read_text(encoding="utf-8")
    poll_page = (prefix / "sondage-citoyen.html").read_text(encoding="utf-8")
    compass_page = (prefix / "boussole-electorale.html").read_text(encoding="utf-8")
    poll_js = (prefix / "assets" / "sondage-citoyen.js").read_text(encoding="utf-8")
    compass_js = (prefix / "assets" / "boussole-electorale.js").read_text(encoding="utf-8")
    poll = json.loads((prefix / "data" / "sondage-citoyen-v1.json").read_text(encoding="utf-8"))
    compass = json.loads((prefix / "data" / "boussole-electorale-v2.json").read_text(encoding="utf-8"))

    if home.count('src="assets/sondage-citoyen.svg"') < 2:
        errors.append("Le visuel spécifique au sondage doit apparaître dans les deux accès d'accueil")
    if home.count('src="../../assets/media/nova-boussole-electorale-v2.webp"') < 2:
        errors.append("Le visuel officiel de la boussole doit rester visible dans les deux accès d'accueil")
    import xml.etree.ElementTree as ET
    try:
        icon_root = ET.parse(prefix / "assets/sondage-citoyen.svg").getroot()
        if icon_root.tag != "{http://www.w3.org/2000/svg}svg":
            errors.append("Visuel sondage : le document n'est pas un SVG valide")
        for element in icon_root.iter():
            tag = element.tag.lower()
            if tag.endswith("}script") or tag.endswith("}foreignobject"):
                errors.append("Visuel sondage : contenu exécutable interdit")
            if any(str(key).lower().startswith("on") for key in element.attrib):
                errors.append("Visuel sondage : attribut d'événement interdit")
            if any("http:" in str(value) or "https:" in str(value) for value in element.attrib.values()):
                errors.append("Visuel sondage : ressource distante interdite")
    except ET.ParseError:
        errors.append("Visuel sondage : XML invalide")

    for route in ("sondage-citoyen.html", "boussole-electorale.html", "sondages-a-valider.html"):
        if not re.search(r'<a\b[^>]*href=["\']'+re.escape(route)+r'["\']', home):
            errors.append(f"Lien cliquable vers {route} absent de l’accueil publié")
    review_page = (prefix / "sondages-a-valider.html").read_text(encoding="utf-8")
    if 'href="sondages-a-valider.html"' not in poll_page:
        errors.append("Le sondage publié n’a pas de lien vers les questionnaires complets en révision")
    if len(re.findall(r'<li data-type="opinion" data-id="q[0-9]{2}">',review_page)) != 64:
        errors.append("Avant-projet 64 : questionnaire incomplet dans l’artefact public")
    if len(re.findall(r'<li data-type="consultation" data-id="q[0-9]{2}">',review_page)) != 40:
        errors.append("Avant-projet 40 : questionnaire incomplet dans l’artefact public")
    if '<meta name="robots" content="noindex,follow">' not in review_page:
        errors.append("Questionnaires candidats : noindex absent")
    if re.search(r'<\s*(?:form|input|button|script)\b', review_page, re.I):
        errors.append("Questionnaires candidats : composant interactif interdit")
    for rel in ("assets/sondage-citoyen.js", "assets/sondage-citoyen.css", "assets/sondage-public-corpus.js"):
        if rel not in poll_page:
            errors.append(f"Ressource du sondage non référencée : {rel}")
    for rel in ("assets/boussole-electorale.js", "assets/boussole-electorale.css", "assets/boussole-public-corpus.js"):
        if rel not in compass_page:
            errors.append(f"Ressource de la boussole non référencée : {rel}")

    if 'local.published===true' not in poll_js or '"nova-consultation-v1"' not in poll_js:
        errors.append("Sondage public : version ou fermeture explicite non vérifiables")
    if 'NOVA_POLL_APPROVED_VERSION' not in (
        ROOT / "supabase/functions/nova-civic-poll/index.ts"
    ).read_text(encoding="utf-8"):
        errors.append("Sondage public : verrou d’approbation serveur absent des sources")
    if not isinstance(poll.get("published"), bool) or len(poll.get("questions", [])) != 8:
        errors.append("Sondage public : corpus ou état de publication invalide")
    if "counts" in poll or "receipts" in poll:
        errors.append("Sondage public : agrégats ou données individuelles dans le corpus statique")
    if len(compass.get("questions", [])) != 64 or len(compass.get("axes", [])) != 16:
        errors.append("Boussole publique : corpus 64/16 incorrect")
    if 'bucket.primaryAnswered >= axisMinimumAnswered' not in compass_js:
        errors.append("Boussole publique : seuil minimum de réponses non appliqué")
    if "https://challenges.cloudflare.com" not in (published / "_headers").read_text(encoding="utf-8"):
        errors.append("CSP Netlify : origine Turnstile absente")
    if not (published / ".well-known/release.json").is_file():
        errors.append("Métadonnées de version de publication absentes")
    else:
        try:
            release = json.loads((published / ".well-known/release.json").read_text(encoding="utf-8"))
            if not re.fullmatch(r"[0-9a-f]{40}",str(release.get("source_sha",""))):
                errors.append("Version de publication : SHA Git de 40 caractères absent")
        except (ValueError, OSError):
            errors.append("Métadonnées de version de publication invalides")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default="_site")
    args = parser.parse_args()
    public = Path(args.directory).resolve()
    if not public.is_dir():
        raise SystemExit(f"Artefact NOVA non construit : {public}")
    problems = check(public)
    if problems:
        for item in problems:
            print("ERREUR publication NOVA :", item)
        raise SystemExit(1)
    print("OK publication NOVA : accès sondage/boussole depuis accueil, fichiers publics complets, corpus et sécurité.")
