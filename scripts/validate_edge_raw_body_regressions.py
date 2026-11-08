#!/usr/bin/env python3
"""Refuser toute nouvelle lecture HTTP entière dans une fonction Edge SINJIRA/NOVA.

Les dérogations historiques sont des DETTES à supprimer (issues de sécurité),
pas une preuve que les fonctions restantes sont sûres ou déployées.
Aucun endpoint ni donnée personnelle n'est appelé.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase" / "functions"
RAW_READ = re.compile(r"\bawait\s+req\s*\.\s*(?:text|json)\s*\(", re.I)
MAX_SOURCE_BYTES = 2 * 1024 * 1024

# Plafond historique : 1 lecture complète par fonction. Une correction peut
# ramener sa valeur à 0 sans devoir changer cette liste; jamais l'inverse.
# Le registre de production reste suivi dans les issues #702 et #713.
LEGACY_MAX = {
    "admin-analytics": 1,
    "admin-console": 1,
    "admin-license-codes": 1,
    "admin-reports": 1,
    "admin-sinjira-v18": 1,
    "admin-social-v20": 1,
    "delete-player-account": 1,
    "fracture-engine-gateway": 1,
    "life-story-export": 1,
    "redeem-license-code": 1,
    "revoke-my-contributions": 1,
    "security-context": 1,
    "send-player-sheet": 1,
    "submit-character-questionnaire": 1,
    "submit-fracture-endgame": 1,
    "submit-game-contribution": 1,
}


def inspect_one(slug: str, source: str) -> list[str]:
    amount = len(RAW_READ.findall(source))
    permitted = LEGACY_MAX.get(slug, 0)
    if amount > permitted:
        return [
            f"{slug}: lecture non bornée nouvelle ou multipliée "
            f"({amount} > plafond historique {permitted})"
        ]
    return []


def self_test() -> None:
    examples = (
        ("const x = await req.text();", 1),
        ("return await req.json()", 1),
        ("await  req . text ( )", 1),
        ("await req.text(); await req.json()", 2),
        ("return readLimitedUtf8Body(req, 1024)", 0),
        ("await reader.read()", 0),
    )
    for source, expected in examples:
        assert len(RAW_READ.findall(source)) == expected, "Détection brute incorrecte"
    assert inspect_one("new-private-function", "await req.text()")
    assert inspect_one("delete-player-account", "await req.text(); await req.json()")
    assert not inspect_one("delete-player-account", "await req.text()")
    assert not inspect_one("delete-player-account", "await readLimitedUtf8Body(req, 1024)")
    print("OK inventaire : 6 mutations et garde de non-régression pour les lectures HTTP entières.")


def validate() -> list[str]:
    errors: list[str] = []
    if not EDGE.is_dir() or EDGE.is_symlink():
        return ["Répertoire des fonctions Edge absent ou symbolique"]
    sources = sorted(EDGE.glob("*/index.ts"))
    if len(sources) < 25:
        return [f"Inventaire des fonctions Edge incomplet : {len(sources)}"]
    for path in sources:
        slug = path.parent.name
        if path.is_symlink() or path.parent.is_symlink():
            errors.append(f"{slug}: lien symbolique vers une source Edge interdit")
            continue
        if path.stat().st_size > MAX_SOURCE_BYTES:
            errors.append(f"{slug}: code source trop grand pour audit")
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeError, OSError):
            errors.append(f"{slug}: fichier source illisible en UTF-8")
            continue
        errors.extend(inspect_one(slug, text))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    if options.self_test:
        self_test()
        return 0
    errors = validate()
    for error in errors:
        print("ECHEC sécurité Edge : " + error)
    if errors:
        return 1
    print("OK : 25+ fonctions Edge analysées; aucune nouvelle lecture HTTP entière hors registre historique.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
