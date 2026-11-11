#!/usr/bin/env python3
"""Contrôle hors réseau de l'incrément de version de la seule fonction Edge Registre.

Source: tableaux Supabase CLI v2 « supabase functions list ». Aucune requête
autonome, aucun secret et aucune donnée utilisateur lue. Fail closed si le
format est inattendu. Version incrémentée != preuve de code identique.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SLUG = "submit-character-questionnaire"
COLUMNS = ("SLUG", "STATUS", "VERSION")


class DeploymentCheckError(ValueError):
    pass


def parse_list(source: str) -> dict[str, tuple[str, int]]:
    header: list[str] | None = None
    result: dict[str, tuple[str, int]] = {}
    for line in source.splitlines():
        if "|" not in line:
            continue
        cells = [piece.strip() for piece in line.strip().strip("|").split("|")]
        upper = [piece.upper() for piece in cells]
        if header is None:
            if all(name in upper for name in COLUMNS):
                if len(set(upper)) != len(upper):
                    raise DeploymentCheckError("En-têtes CLI dupliqués.")
                header = upper
            continue
        if not cells or all(set(cell) <= set("- ") for cell in cells):
            continue
        if len(cells) != len(header):
            raise DeploymentCheckError("Colonnes CLI incomplètes ou réordonnées.")
        slug = cells[header.index("SLUG")]
        if not slug:
            raise DeploymentCheckError("Slug vide.")
        if slug in result:
            raise DeploymentCheckError("Slug en double.")
        status = cells[header.index("STATUS")].upper()
        value = cells[header.index("VERSION")]
        if not value.isascii() or not value.isdigit():
            raise DeploymentCheckError("Version de fonction non numérique.")
        result[slug] = (status, int(value))
    if header is None:
        raise DeploymentCheckError("Table de versions Supabase CLI introuvable.")
    if SLUG not in result:
        raise DeploymentCheckError("Fonction Registre absente de l'inventaire.")
    return result


def verify(before: str, after: str) -> tuple[int, int]:
    prev = parse_list(before)[SLUG]
    next_version = parse_list(after)[SLUG]
    if prev[0] != "ACTIVE" or next_version[0] != "ACTIVE":
        raise DeploymentCheckError("Fonction Registre non ACTIVE avant ou après.")
    if next_version[1] <= prev[1]:
        raise DeploymentCheckError(
            f"Version Registre inchangée ou reculée : {prev[1]} -> {next_version[1]}"
        )
    return prev[1], next_version[1]


def self_test() -> None:
    def fixture(version: str = "17", *, slug: str = SLUG, status: str = "ACTIVE") -> str:
        return ("ID | NAME | SLUG | STATUS | VERSION | UPDATED_AT (UTC)\n"
                "----|------|------|--------|---------|-----------------\n"
                f"00000000 | Registre | {slug} | {status} | {version} | 2026-11-11\n"
                "11111111 | Exemple | other-function | ACTIVE | 4 | 2026-11-11\n")
    assert verify(fixture("17"), fixture("18")) == (17, 18)
    assert verify(fixture("8"), fixture("10")) == (8, 10)
    invalid = [
        ("aucun déploiement", fixture("17"), fixture("17")),
        ("version reculée", fixture("18"), fixture("17")),
        ("fonction désactivée", fixture("17"), fixture("18", status="REMOVED")),
        ("ancienne fonction désactivée", fixture("17", status="REMOVED"), fixture("18")),
        ("autre slug", fixture("17"), fixture("18", slug="another-slug")),
        ("doublon", fixture("17"), fixture("18") + "22222222 | Autre | submit-character-questionnaire | ACTIVE | 21 | aujourd'hui\n"),
        ("version arbitraire", fixture("17"), fixture("invalid")),
        ("version signe", fixture("17"), fixture("-1")),
        ("colonnes erronées", fixture("17"), "not a table"),
        ("ligne incomplète", fixture("17"), fixture("18").replace(" | 18 | ", " | ")),
    ]
    for name, before, after in invalid:
        try:
            verify(before, after)
        except DeploymentCheckError:
            continue
        raise AssertionError("Prévol devrait refuser: " + name)
    print(f"OK Edge Registre : {len(invalid)} cas trompeurs refusés, 2 versions valides.")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--before", type=Path)
    p.add_argument("--after", type=Path)
    a = p.parse_args()
    if a.self_test:
        self_test()
        return
    if not a.before or not a.after:
        p.error("Les inventaires --before et --after sont obligatoires.")
    before, after = verify(a.before.read_text("utf-8"), a.after.read_text("utf-8"))
    print(f"OK Registre Edge : version ACTIVE incrémentée {before} -> {after}.")
    print("Limite : la version ne prouve pas la parité du code ni un test HTTP AAL2.")


if __name__ == "__main__":
    main()
