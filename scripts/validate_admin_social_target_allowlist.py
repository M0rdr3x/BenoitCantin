#!/usr/bin/env python3
"""Sécurité des noms de tables de modération : contrat fail-closed.

Exécute des mutations négatives sans communiquer avec Supabase. Le test Node
exécute en plus les vraies fonctions TypeScript en sandbox isolée.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "supabase/functions/admin-social-v20/index.ts"

REQUIRED = {
    "authentification admin": "await requiredAdmin(req)",
    "garde de mappage": "function moderationTargetTable(network:unknown,targetType:unknown):[string,string]|null",
    "type réseau contrôlé": "typeof network!=='string'",
    "réseau propriété propre": "Object.prototype.hasOwnProperty.call(targetTables,network)",
    "type contenu contrôlé": "typeof targetType!=='string'",
    "type contenu propriété propre": "Object.prototype.hasOwnProperty.call(types,targetType)",
    "paire SQL exacte": "Array.isArray(pair)&&pair.length===2&&typeof pair[0]==='string'&&typeof pair[1]==='string'",
    "snapshot via table valide": "const pair=moderationTargetTable(r.network,r.target_type);",
    "snapshot absent sans requête": "if(!pair)return null;",
    "interdiction de sanction sur type inconnu":
        "if(action==='hide_content'&&!moderationTargetTable(r.network,r.target_type))throw new Error('CONTENT_TARGET_NOT_REVERSIBLE');",
    "identité source serveur": "const subject=await reportTargetUser(s,r);",
    "suspension sans sujet refusée":
        "if(action==='suspend_social'&&!subject)throw new Error('TARGET_USER_NOT_FOUND');",
    "motif de modération humain": "decision_source:'human_admin'",
    "réversibilité conservée": "if(action==='suspend_social'){",
    "journal fixe": "moderationLogCode(e)",
    "cache privé": "'Cache-Control':'private, no-store, max-age=0'",
}
FORBIDDEN = (
    "targetTables?.[r.network]?.[r.target_type]",
    "const pair=targetTables[r.network][r.target_type];",
    "if(!subject)throw new Error('TARGET_USER_NOT_FOUND');",
    "getPublicUrl(",
)

def validate(source: str) -> list[str]:
    errors = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append("Modération: garde manquant ou affaibli: " + label)
    for marker in FORBIDDEN:
        if marker in source:
            errors.append("Modération: opération risquée réintroduite: " + marker)
    if source.count("moderationTargetTable(r.network,r.target_type)") != 2:
        errors.append("Modération: cible validée exactement pour décision et snapshot.")
    # Le garde du type doit précéder toute lecture d'identité. En cas de suspension,
    # l'identité est vérifiée AVANT les écritures de sanctions.
    decision = source.find("async function createDecision(")
    guard = source.find("if(action==='hide_content'&&!moderationTargetTable(", decision)
    user = source.find("const subject=await reportTargetUser(s,r);", decision)
    subject = source.find("if(action==='suspend_social'&&!subject)", decision)
    evidence = source.find("const evidence=", decision)
    insert = source.find(".from('moderation_decisions').insert(row)", decision)
    if min(decision, guard, user, subject, evidence, insert) < 0 or not (
        decision < guard < user < subject < evidence < insert
    ):
        errors.append("Modération: identité/validation de cible après écriture ou ordre dangereux.")
    lookup = source.find("async function targetSnapshot(")
    pair = source.find("const pair=moderationTargetTable(", lookup)
    db_read = source.find("s.from(pair[0])", lookup)
    if min(lookup, pair, db_read) < 0 or not lookup < pair < db_read:
        errors.append("Modération: SQL ne doit pas précéder validation de table.")
    return errors


def self_test(source: str) -> None:
    if errors := validate(source):
        raise AssertionError("Le code sain est refusé: " + " / ".join(errors))
    mutations = {
        "réseau hérité autorisé": (
            "Object.prototype.hasOwnProperty.call(targetTables,network)", "true"
        ),
        "type hérité autorisé": (
            "Object.prototype.hasOwnProperty.call(types,targetType)", "true"
        ),
        "type réseau indéfini autorisé": ("typeof network!=='string'", "false"),
        "type de cible indéfini autorisé": ("typeof targetType!=='string'", "false"),
        "paire de SQL non validée": (
            "Array.isArray(pair)&&pair.length===2&&typeof pair[0]==='string'&&typeof pair[1]==='string'",
            "true",
        ),
        "snapshot SQL non validé": (
            "const pair=moderationTargetTable(r.network,r.target_type);",
            "const pair=targetTables?.[r.network]?.[r.target_type];",
        ),
        "garde d'action supprimé": (
            "if(action==='hide_content'&&!moderationTargetTable(r.network,r.target_type))",
            "if(false)",
        ),
        "suspension sans sujet permise": (
            "if(action==='suspend_social'&&!subject)throw new Error('TARGET_USER_NOT_FOUND');",
            "if(false)throw new Error('TARGET_USER_NOT_FOUND');",
        ),
        "auth admin supprimée": ("await requiredAdmin(req)", "await requiredUser(req)"),
        "cache public": (
            "'Cache-Control':'private, no-store, max-age=0'",
            "'Cache-Control':'public, max-age=3600'",
        ),
    }
    for label, (from_value, to_value) in mutations.items():
        if source.count(from_value) != 1:
            raise AssertionError(f"Mutation impossible {label}: {source.count(from_value)}")
        if not validate(source.replace(from_value, to_value, 1)):
            raise AssertionError("Mutation indétectée: " + label)
    print(f"OK: {len(mutations)} mutations dangereuses de sélection SQL bloquées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    source = SOURCE.read_text("utf-8")
    if args.self_test:
        self_test(source)
    errors = validate(source)
    if errors:
        print(f"ÉCHEC: {len(errors)} problèmes de cible de modération.")
        for error in errors:
            print("- " + error)
        return 1
    print("OK: réseaux/types propres, SQL sûr, aucune sanction sans identité et modération privée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
