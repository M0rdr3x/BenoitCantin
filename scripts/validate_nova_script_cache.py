#!/usr/bin/env python3
"""Contrôle des versions de script sur les 42 pages HTML Projet Nova."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

NOVA = Path(__file__).resolve().parents[1] / "projets/projet-nova"
VERSION = "26.2.0"
EXPECTED_PAGE_COUNT = 42
EXPECTED_WITH_SCRIPT = 38
SCRIPT_RE = re.compile(r"script\.js\?v=([^\"'<>\s]+)")
EXPECTED_WITHOUT_SCRIPT = {
    "a-propos.html", "compte.html", "formulaire-soutien.html", "univers.html",
}


def validate_pages(pages: dict[str, str]) -> list[str]:
    issues: list[str] = []
    if len(pages) != EXPECTED_PAGE_COUNT:
        issues.append(f"{len(pages)} pages Nova contre {EXPECTED_PAGE_COUNT} attendues")
    found = 0
    without = set()
    for name, source in sorted(pages.items()):
        versions = SCRIPT_RE.findall(source)
        if not versions:
            without.add(name)
        elif len(versions) != 1:
            issues.append(f"{name}: {len(versions)} références au script (attendu 1)")
        else:
            found += 1
            if versions[0] != VERSION:
                issues.append(f"{name}: script.js?v={versions[0]} au lieu de {VERSION}")
    if found != EXPECTED_WITH_SCRIPT:
        issues.append(f"{found} pages avec script contre {EXPECTED_WITH_SCRIPT} attendues")
    if without != EXPECTED_WITHOUT_SCRIPT:
        issues.append(
            "Pages sans script modifiées: "
            + repr(sorted(without.symmetric_difference(EXPECTED_WITHOUT_SCRIPT)))
        )
    return issues


def self_test() -> list[str]:
    pages = {
        p.name: p.read_text(encoding="utf-8")
        for p in sorted(NOVA.glob("*.html"))
    }
    issues = []
    if validate_pages(pages):
        issues.append("La distribution de pages actuelle doit valider la cohérence")
    stale = dict(pages)
    stale["index.html"] = stale["index.html"].replace(
        "script.js?v=26.2.0", "script.js?v=19-integrated", 1
    )
    if not any("index.html" in x for x in validate_pages(stale)):
        issues.append("L'auto-test négatif n'a pas repéré un cache obsolète")
    missing = dict(pages)
    missing["boussole-electorale.html"] = missing["boussole-electorale.html"].replace(
        "script.js?v=26.2.0", "absent.js", 1
    )
    if not validate_pages(missing):
        issues.append("L'auto-test négatif n'a pas détecté le script manquant")
    return issues


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--self-test", action="store_true")
    options = args.parse_args()
    pages = {
        p.name: p.read_text(encoding="utf-8")
        for p in sorted(NOVA.glob("*.html"))
    }
    errors = self_test() if options.self_test else validate_pages(pages)
    for err in errors:
        print("ECHEC:", err)
    if errors:
        raise SystemExit(1)
    print("OK: 42 pages Projet Nova, 38 scripts versionnés 26.2.0, 4 exceptions.")
