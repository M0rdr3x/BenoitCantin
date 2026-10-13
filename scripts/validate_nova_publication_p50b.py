#!/usr/bin/env python3
"""Contrôle statique des pages de participation Projet Nova.

Ce contrôle ne vérifie ni les pratiques réelles de traitement, ni les droits
électoraux, ni l'absence de copies anciennes hors des pages désignées.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "projets" / "projet-nova"
PAGES = ("participer.html", "avis-legal.html", "recrutement.html", "confidentialite.html", "contact.html")
OLD_CLAIMS = (
    "qui contient le formulaire intégré de soutien et de préadhésion",
    "Soutenir Projet Nova et accéder au formulaire de recrutement.",
    "Les formulaires servent uniquement à communiquer avec le Projet Nova",
)


def validate(site_root: Path) -> list[str]:
    problems = []
    texts = {}
    for name in PAGES:
        path = site_root / name
        if not path.is_file():
            problems.append(f"Page absente : {name}")
            continue
        text = path.read_text("utf-8")
        texts[name] = text
        if re.search(r"<form\b", text, flags=re.IGNORECASE):
            problems.append(f"{name} : élément form actif à vérifier")
        if "formspree.io/f/" in text.lower() or "formsubmit.co/" in text.lower():
            problems.append(f"{name} : URL de collecte externe détectée")
        for phrase in OLD_CLAIMS:
            if phrase in text:
                problems.append(f"{name} : ancienne déclaration de formulaire actif")

    if "participer.html" in texts:
        text = texts["participer.html"]
        for phrase in ("contact volontaire", "formulaires externes", "suspendus", 'href="recrutement.html"', 'href="confidentialite.html"'):
            if phrase not in text:
                problems.append(f"participer.html : mention manquante — {phrase}")
        if "visionneuse.html?doc=formulaire-soutien" in text:
            problems.append("participer.html : ancien lien de soutien encore actif")

    if "avis-legal.html" in texts and "n’exploite actuellement pas de formulaire externe" not in texts["avis-legal.html"]:
        problems.append("avis-legal.html : suspension du formulaire non décrite")

    if "recrutement.html" in texts:
        text = texts["recrutement.html"]
        if "Aucun paiement" not in text:
            problems.append("recrutement.html : interdiction de paiement non indiquée")
        if "contact volontaire direct" not in text:
            problems.append("recrutement.html : contact volontaire non confirmé")

    if "confidentialite.html" in texts and "formulaires publics externes" not in texts["confidentialite.html"]:
        problems.append("confidentialite.html : suspension des formulaires absente")

    if "contact.html" in texts and "mailto:officiellenovaparti@gmail.com" not in texts["contact.html"]:
        problems.append("contact.html : canal public de contact manquant")
    return problems


def main() -> int:
    results = validate(ROOT)
    if results:
        for problem in results:
            print("ÉCHEC:", problem)
        return 1
    print("OK : cohérence statique de cinq pages publiques de Projet Nova.")
    print("Ce contrôle ne constitue ni homologation PRP, ni autorisation électorale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
