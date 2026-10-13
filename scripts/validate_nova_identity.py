#!/usr/bin/env python3
"""Garde-fou de dénomination du corpus PUBLIC ACTIF Projet Nova.

Le nom futur Parti Nova reste permis comme proposition CONDITIONNELLE.
Les archives historiques sont hors périmètre et ne sont jamais réécrites.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

TEXT_EXTENSIONS = {".html", ".htm", ".md", ".txt", ".json", ".js", ".css", ".csv", ".xml", ".yml", ".yaml"}
HISTORICAL_DIRS = {"archives", "historique", "historical", "legacy"}
OLD_ACRONYM = re.compile(r"(?<![A-Za-z\d])scq(?![A-Za-z\d])", re.IGNORECASE)
OLD_FULL_NAME = re.compile(r"souverainet[ée]\s+et\s+citoyennet[ée]\s+du\s+qu[ée]bec", re.IGNORECASE)


def scan_site(site_root: Path) -> list[str]:
    if not site_root.is_dir():
        return [f"Périmètre public actif introuvable : {site_root}"]
    findings: list[str] = []
    for path in sorted(site_root.rglob("*")):
        rel = path.relative_to(site_root)
        if HISTORICAL_DIRS.intersection(p.casefold() for p in rel.parts[:-1]):
            continue
        if not path.is_file():
            continue
        name_match = OLD_ACRONYM.search(rel.as_posix()) or OLD_FULL_NAME.search(rel.as_posix())
        if name_match:
            findings.append(f"Nom de fichier actif interdit : {rel.as_posix()}")
        if path.suffix.casefold() not in TEXT_EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"Texte non UTF-8 à contrôler : {rel.as_posix()}")
            continue
        for line_number, line in enumerate(content.splitlines(), 1):
            if OLD_ACRONYM.search(line) or OLD_FULL_NAME.search(line):
                findings.append(f"Ancienne dénomination dans {rel.as_posix()}:{line_number}")
                if len(findings) >= 100:
                    return findings
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Vérifie l'identité unique des documents publics actifs de Nova.")
    parser.add_argument("--site-root", type=Path, default=Path(__file__).resolve().parents[1] / "projets/projet-nova")
    args = parser.parse_args()
    issues = scan_site(args.site_root)
    if issues:
        print(f"ÉCHEC — {len(issues)} incohérence(s) d'identité dans les fichiers actifs :")
        for problem in issues:
            print(" -", problem)
        return 1
    print("OK — identité unique Projet Nova : aucune ancienne dénomination dans le périmètre textuel actif.")
    print("La qualification juridique et l'autorisation électorale ne sont pas vérifiées par ce programme.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
