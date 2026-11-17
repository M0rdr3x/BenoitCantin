#!/usr/bin/env python3
"""Contrat fail-closed des dictionnaires statistiques Edge administrateurs.

Le test Node exécute les blocs d'agrégation des deux fichiers TS réels.
Ce contrat protège contre une réintroduction silencieuse de prototypes hérités.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = ROOT / "supabase/functions/admin-analytics/index.ts"
CONSOLE = ROOT / "supabase/functions/admin-console/index.ts"

REQUIRED_ANALYTICS = {
    "authentification administrateur AAL2": "requiredAdmin(req)",
    "source de données serveur": ".from('internal_gameplay_contributions')",
    "résultats sans prototype": "const results: Record<string, number> = Object.create(null);",
    "difficultés sans prototype": "const difficulty: Record<string, number> = Object.create(null);",
    "cartes sans prototype": "const cardCounts: Record<string, number> = Object.create(null);",
    "compte réel": "map[normalized] = (map[normalized] || 0) + 1;",
    "cache privé": "'Cache-Control': 'private, no-store, max-age=0'",
}
REQUIRED_CONSOLE = {
    "authentification administrateur AAL2": "requiredAdmin(req)",
    "source de données serveur": "service.from('internal_gameplay_contributions')",
    "index des jeux sans prototype": "const byGame:any=Object.create(null);",
    "index des difficultés sans prototype": "difficulty:Object.create(null)};",
    "synthèse sans valeurs brutes": "return privateJson({ok:true,analytics:byGame});",
    "cache privé": "'Cache-Control':'private, no-store, max-age=0'",
}


def audit(analytics: str, console: str) -> list[str]:
    errors: list[str] = []
    for label, value in REQUIRED_ANALYTICS.items():
        if value not in analytics:
            errors.append("admin-analytics: garde absent " + label)
    for label, value in REQUIRED_CONSOLE.items():
        if value not in console:
            errors.append("admin-console: garde absent " + label)

    if "const results: Record<string, number> = {};" in analytics or \
            "const difficulty: Record<string, number> = {};" in analytics or \
            "const cardCounts: Record<string, number> = {};" in analytics:
        errors.append("admin-analytics: agrégat vulnérable avec prototype ordinaire")
    if "const byGame:any={};" in console or "difficulty:{}};" in console:
        errors.append("admin-console: agrégat vulnérable avec prototype ordinaire")

    for slug, source, agg_marker, auth_marker in [
        ("admin-analytics", analytics, "const results: Record<string, number>", "await requiredAdmin(req)"),
        ("admin-console", console, "const byGame:any=", "await requiredAdmin(req)"),
    ]:
        auth_index = source.find(auth_marker)
        agg_index = source.find(agg_marker)
        response_index = source.find("return privateJson({", agg_index)
        if auth_index < 0 or agg_index < 0 or response_index < 0 or \
                not auth_index < agg_index < response_index:
            errors.append(slug + ": authentification avant agrégat et réponse obligatoire")
    if analytics.count("Object.create(null)") != 3:
        errors.append("admin-analytics: exactement trois agrégats typés sans prototype")
    # Les autres fonctionnalités admin-console ne sont pas modifiées.
    if console.count("Object.create(null)") != 2:
        errors.append("admin-console: exactement deux agrégats sans prototype")
    return errors


def self_test(analytics: str, console: str) -> None:
    if errs := audit(analytics, console):
        raise AssertionError("Code sain refusé: " + " | ".join(errs))

    mutations = [
        ("résultats hérités", "analytics",
         "const results: Record<string, number> = Object.create(null);",
         "const results: Record<string, number> = {};"),
        ("difficultés héritées", "analytics",
         "const difficulty: Record<string, number> = Object.create(null);",
         "const difficulty: Record<string, number> = {};"),
        ("cartes héritées", "analytics",
         "const cardCounts: Record<string, number> = Object.create(null);",
         "const cardCounts: Record<string, number> = {};"),
        ("jeu __proto__ hérité", "console",
         "const byGame:any=Object.create(null);",
         "const byGame:any={};"),
        ("difficulté __proto__ héritée", "console",
         "difficulty:Object.create(null)};",
         "difficulty:{}};"),
        ("auth requise supprimée", "analytics", "requiredAdmin(req)", "requiredUser(req)"),
        ("auth admin supprimée", "console", "requiredAdmin(req)", "requiredUser(req)"),
        ("cache Analytics public", "analytics",
         "'Cache-Control': 'private, no-store, max-age=0'",
         "'Cache-Control': 'public, max-age=3600'"),
        ("cache Console public", "console",
         "'Cache-Control':'private, no-store, max-age=0'",
         "'Cache-Control':'public, max-age=3600'"),
    ]
    for label, part, original, bad in mutations:
        source = analytics if part == "analytics" else console
        if source.count(original) != 1:
            raise AssertionError(f"Mutation {label} impossible: {source.count(original)} marqueurs")
        altered = source.replace(original, bad, 1)
        a = altered if part == "analytics" else analytics
        c = altered if part == "console" else console
        if not audit(a, c):
            raise AssertionError(f"Mutation non détectée: {label}")
    print(f"OK: {len(mutations)} mutations de prototype/auth/cache détectées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    analytics = ANALYTICS.read_text("utf-8")
    console = CONSOLE.read_text("utf-8")
    if args.self_test:
        self_test(analytics, console)
    errors = audit(analytics, console)
    if errors:
        print(f"ÉCHEC: {len(errors)} problème(s) de prototype statistique.")
        for error in errors:
            print("- " + error)
        return 1
    print("OK: agrégations administrateur sans prototype, auth AAL2 et cache privé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
