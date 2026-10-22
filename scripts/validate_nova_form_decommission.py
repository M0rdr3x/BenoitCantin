#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets" / "projet-nova"

ACTIVE_PUBLIC = (
    "contact.html",
    "recrutement.html",
    "propositions.html",
)

DOCS = (
    "ADMINISTRATION_FORMULAIRES.md",
    "FORMULAIRE_CONTACT.md",
)

PUBLIC_EMAIL = "officiellenovaparti@gmail.com"


def read(name: str) -> str:
    return (NOVA / name).read_text("utf-8", errors="strict")


def main() -> int:
    errors: list[str] = []

    for name in ACTIVE_PUBLIC:
        path = NOVA / name
        if not path.is_file():
            errors.append(f"Page publique Nova absente: {name}")
            continue
        html = read(name)
        if "<form" in html.lower():
            errors.append(f"{name}: formulaire HTML externe/actif détecté.")
        if "formspree.io/f/" in html.lower():
            errors.append(f"{name}: endpoint Formspree encore exposé.")
        if PUBLIC_EMAIL not in html:
            errors.append(f"{name}: canal public direct Projet Nova absent.")

    support = read("formulaire-soutien.html")
    for marker in ("noindex", "nofollow", "noarchive"):
        if marker not in support.lower():
            errors.append(f"formulaire-soutien.html: robots incomplet, {marker} absent.")
    target = "/projets/projet-nova/recrutement.html"
    if f'content="0; url={target}"' not in support:
        errors.append("formulaire-soutien.html: meta refresh exacte absente.")
    if f'href="{target}"' not in support:
        errors.append("formulaire-soutien.html: lien de secours exact absent.")
    if f"location.replace('{target}'+location.search+location.hash)" not in support:
        errors.append("formulaire-soutien.html: query/hash non conservés.")

    thanks = read("merci-formulaire.html")
    for marker in ("noindex", "nofollow", "noarchive"):
        if marker not in thanks.lower():
            errors.append(f"merci-formulaire.html: robots incomplet, {marker} absent.")
    for forbidden in (
        "formulaire de soutien et de préadhésion a été transmis",
        "formulaire transmis",
        "formspree.io/f/",
    ):
        if forbidden in thanks.lower():
            errors.append(f"merci-formulaire.html: ancien état trompeur encore présent: {forbidden}")
    for required in (
        "Cette confirmation n’est plus utilisée.",
        "elle ne confirme aucun envoi actuel",
        "recrutement.html",
        "contact.html",
    ):
        if required.lower() not in thanks.lower():
            errors.append(f"merci-formulaire.html: message de retrait incomplet: {required}")

    for name in DOCS:
        path = NOVA / name
        if not path.is_file():
            errors.append(f"Documentation formulaires Nova absente: {name}")
            continue
        text = read(name)
        if "formspree.io/f/" in text.lower():
            errors.append(f"{name}: ancien endpoint Formspree encore documenté.")
        if "kingtyrano@gmail.com" in text.lower():
            errors.append(f"{name}: adresse administrative privée historique encore documentée.")
        if PUBLIC_EMAIL not in text:
            errors.append(f"{name}: canal public actuel Projet Nova absent.")

    if errors:
        print(f"ECHEC retrait formulaires Nova: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK formulaires Projet Nova: aucun formulaire externe public actif, "
        "anciens parcours neutralisés et documentation alignée sur le contact direct."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
