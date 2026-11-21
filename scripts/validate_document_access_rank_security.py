#!/usr/bin/env python3
"""Vérifie la frontière d'accès aux documents avant émission d'une URL.

Contrat statique avec mutations : le test dynamique du vrai handler est dans
scripts/test_document_access_rank_security.mjs. Aucun accès distant ni secret.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/functions/get-document-url/index.ts"
CONFIG = ROOT / "supabase/config.toml"

REQUIRED = {
    "niveaux explicitement définis":
        "const ranks:Record<string,number>={public:1,account:10,player:20,tester:30,admin:100};",
    "contrôle serveur dédié":
        "function documentAccessAllowed(accessLevel:unknown,userRank:number)",
    "type de niveau strict":
        "typeof accessLevel==='string'",
    "propriétés réellement déclarées":
        "Object.prototype.hasOwnProperty.call(ranks,accessLevel)",
    "rang fini":
        "Number.isFinite(userRank)",
    "comparaison de droits":
        "userRank>=ranks[accessLevel]",
    "refus avant réponse":
        "if(!documentAccessAllowed(doc.access_level,userRank))",
    "réponse sans URL":
        "return privateJson({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);",
    "projet actif":
        "doc.projects?.status!=='active'",
    "document approuvé":
        "doc.status!=='approved'",
    "authentification côté serveur":
        "optionalUser(req)",
    "rang côté serveur":
        "service.rpc('project_access_rank'",
    "lien externe après accès":
        "if(doc.external_url){",
    "lien statique uniquement lorsque document et projet sont publics":
        "if(doc.access_level!=='public'||doc.projects?.visibility!=='public'){",
    "lien signé après accès":
        "createSignedUrl(doc.storage_path,600)",
    "cache privé":
        "'Cache-Control':'private, no-store, max-age=0'",
}

def audit(source: str, config: str) -> list[str]:
    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f"Document : garde absent ou affaibli : {label}")

    old = "ranks[doc.access_level]||999"
    if old in source:
        errors.append("Ancien contrôle ACL vulnérable à Object.prototype interdit.")

    checks = [
        "const service=serviceClient(),user=await optionalUser(req);",
        "if(!documentAccessAllowed(doc.access_level,userRank))",
        "if(doc.external_url){",
        "if(doc.access_level!=='public'||doc.projects?.visibility!=='public'){",
        "createSignedUrl(doc.storage_path,600)",
    ]
    pos = [source.find(x) for x in checks]
    if min(pos) < 0 or pos != sorted(pos):
        errors.append("Ordre obligatoire : identité, rang autorisé, lien externe, signature.")

    if "[functions.get-document-url]\nverify_jwt = false" not in config:
        errors.append("Le contrat public JWT optionnel doit rester explicite.")

    if any(x in source for x in ("await req.json()", "await req.text()")):
        errors.append("Lecture du corps HTTP non bornée interdite.")
    if "readLimitedUtf8Body(req,MAX_REQUEST_BYTES)" not in source:
        errors.append("Limite des requêtes serveur supprimée.")
    return errors


def self_test(source: str, config: str) -> None:
    if errors := audit(source, config):
        raise AssertionError("La source saine est refusée : " + " | ".join(errors))

    mutations = {
        "propriété héritée autorisée":
            ("Object.prototype.hasOwnProperty.call(ranks,accessLevel)", "true"),
        "NaN autorisé":
            ("Number.isFinite(userRank)", "true"),
        "niveau non typé":
            ("typeof accessLevel==='string'", "true"),
        "comparaison supprimée":
            ("userRank>=ranks[accessLevel]", "true"),
        "contrôle serveur supprimé":
            ("if(!documentAccessAllowed(doc.access_level,userRank))", "if(false)"),
        "document privé accessible sans statut":
            ("doc.status!=='approved'", "false"),
        "projet inactif accepté":
            ("doc.projects?.status!=='active'", "false"),
        "signature avant autorisation":
            ("if(doc.external_url){", "if(false){"),
        "liens privés statiques acceptés":
            ("if(doc.access_level!=='public'||doc.projects?.visibility!=='public'){", "if(false){"),
        "projet privé seul accepté":
            ("if(doc.access_level!=='public'||doc.projects?.visibility!=='public'){", "if(doc.access_level!=='public'&&doc.projects?.visibility!=='public'){"),
        "lien signé trop long":
            ("createSignedUrl(doc.storage_path,600)", "createSignedUrl(doc.storage_path,3600)"),
        "cache privé retiré":
            ("'Cache-Control':'private, no-store, max-age=0'", "'Cache-Control':'public, max-age=3600'"),
        "ancien contrôle réintroduit":
            ("if(!documentAccessAllowed(doc.access_level,userRank))", "if(userRank<(ranks[doc.access_level]||999))"),
    }
    for label, (original, changed) in mutations.items():
        if source.count(original) != 1:
            raise AssertionError(f"Mutant non applicable : {label}")
        altered = source.replace(original, changed, 1)
        if not audit(altered, config):
            raise AssertionError(f"Mutation dangereuse non détectée : {label}")
    print(f"OK : {len(mutations)} mutations de régression ACL ont été rejetées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    source = EDGE.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    if args.self_test:
        self_test(source, config)
    errors = audit(source, config)
    if errors:
        for error in errors:
            print("ÉCHEC : " + error)
        return 1
    print("OK : niveaux exacts, propriétés propres, rangs finis et accès avant URLs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
