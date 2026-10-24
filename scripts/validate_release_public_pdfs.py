#!/usr/bin/env python3
"""Vérifier la frontière de publication de chaque PDF du site statique.

Seul un document explicitement déclaré public peut être copié dans _site.
Des fichiers privés peuvent rester dans Git, jamais dans l'artefact public.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from build_netlify_public import (
    PUBLIC_APPROVED_PDFS,
    PUBLIC_ROOT_SUFFIXES,
    RUNTIME_WEB_SUFFIXES,
    ROOT,
    relative_path_allowed,
)

NEGATIVE_PATHS = (
    "roman_integral.pdf",
    "assets/pdf/rapport-interne.pdf",
    "compte/facture-personnelle.pdf",
    "admin/donnees-confidentielles.pdf",
    "projets/sinjira/romans/SINJIRA_Livre_01_INTEGRALE.pdf",
    "projets/sinjira/documents/SINJIRA_Livre_02_MASTER.pdf",
    "projets/sinjira/jeux/fracture-du-reseau-mere/documents/fiche-inedite.pdf",
    "projets/projet-nova/documents/proposition-privee.pdf",
    "projets/projet-nova/data/export-des-votes.pdf",
)


def validate() -> list[str]:
    errors: list[str] = []
    if len(PUBLIC_APPROVED_PDFS) != 20:
        errors.append("Inventaire public de PDF inattendu: 20 attendus (12 Nova, 8 SINJIRA)")
    if ".pdf" in PUBLIC_ROOT_SUFFIXES or ".pdf" in RUNTIME_WEB_SUFFIXES:
        errors.append("Publication implicite des PDF racine ou espace privé interdite")

    for rel in sorted(PUBLIC_APPROVED_PDFS):
        if not (ROOT / rel).is_file():
            errors.append(f"PDF déclaré public mais absent: {rel}")
        if not relative_path_allowed(rel):
            errors.append(f"PDF public validé non reconnu par le builder: {rel}")

    for filename in NEGATIVE_PATHS:
        rel = Path(filename)
        if relative_path_allowed(rel):
            errors.append(f"PDF non approuvé publié par défaut: {rel}")

    # Tous les PDF inconnus présents dans Git restent admissibles comme source
    # privée de travail, mais ne doivent jamais devenir un artefact Web.
    for source in ROOT.rglob("*.pdf"):
        rel = source.relative_to(ROOT)
        if any(part in {".git", "_site", ".venv", "node_modules"} for part in rel.parts):
            continue
        if rel not in PUBLIC_APPROVED_PDFS and relative_path_allowed(rel):
            errors.append(f"PDF non approuvé risquant une publication: {rel}")
    return errors


def self_test() -> list[str]:
    errors: list[str] = []
    approved = Path("projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf")
    forbidden = Path("projets/sinjira/romans/SINJIRA_Livre_01_INTEGRALE.pdf")
    if not relative_path_allowed(approved):
        errors.append("Auto-test: démo gratuite bloquée")
    if relative_path_allowed(forbidden):
        errors.append("Auto-test: intégrale privée publiée")
    if relative_path_allowed(Path("projets/projet-nova/documents/rapport-prive.pdf")):
        errors.append("Auto-test: nouvelle pièce Nova publiée sans approbation")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    errors = self_test() if options.self_test else validate()
    for error in errors:
        print("ECHEC:", error)
    if errors:
        raise SystemExit(1)
    print("OK : seuls les 20 PDF approuvés (Nova et SINJIRA) peuvent être publiés.")
