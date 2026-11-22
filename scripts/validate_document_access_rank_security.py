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
    "rangs non-admin canoniques":
        "const CANONICAL_PROJECT_RANKS=new Set([0,1,10,20,30]);",
    "réponse admin explicite":
        "adminCheck.error!==null||typeof adminCheck.data!=='boolean'",
    "administrateur booléen strict":
        "if(adminCheck.data===true)userRank=100;",
    "erreur RPC rang et type":
        "rankCheck.error!==null||typeof rankCheck.data!=='number'",
    "rang integer sûr":
        "!Number.isSafeInteger(rankCheck.data)",
    "niveau RPC confirmé parmi les rangs canoniques":
        "!CANONICAL_PROJECT_RANKS.has(rankCheck.data)",
    "refus sans URL des RPC invalides":
        "return privateJson({ok:false,error:'Vérification des droits indisponible.'},503);",
    "lien externe après accès":
        "if(doc.external_url){",
    "lien statique uniquement lorsque document et projet sont publics":
        "if(doc.access_level!=='public'||doc.projects?.visibility!=='public'){",
    "chemin de Storage strict avant signature":
        "privateDocumentLocationValid(doc.storage_bucket,doc.storage_path)",
    "lecture du statut réel du bucket":
        "service.storage.getBucket(doc.storage_bucket)",
    "identité et statut privé du bucket":
        "!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket)",
    "refus d'erreur API Storage":
        "if(bucketMetadataError||!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket))",
    "erreur de stockage sans URL":
        "return privateJson({ok:false,error:'Stockage privé indisponible.'},503);",
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
        "const adminCheck=await service.rpc('is_sinjira_admin'",
        "if(adminCheck.data===true)userRank=100;",
        "const rankCheck=await service.rpc('project_access_rank'",
        "!CANONICAL_PROJECT_RANKS.has(rankCheck.data)",
        "if(!documentAccessAllowed(doc.access_level,userRank))",
        "if(doc.external_url){",
        "if(doc.access_level!=='public'||doc.projects?.visibility!=='public'){",
        "privateDocumentLocationValid(doc.storage_bucket,doc.storage_path)",
        "service.storage.getBucket(doc.storage_bucket)",
        "!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket)",
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
        "chemin de stockage non contrôlé":
            ("privateDocumentLocationValid(doc.storage_bucket,doc.storage_path)", "true"),
        "bucket non consulté":
            ("service.storage.getBucket(doc.storage_bucket)", "Promise.resolve({data:{public:false}})"),
        "bucket public admis":
            ("!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket)", "false"),
        "erreur de lecture bucket ignorée":
            ("if(bucketMetadataError||!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket))", "if(false)"),
        "lien signé trop long":
            ("createSignedUrl(doc.storage_path,600)", "createSignedUrl(doc.storage_path,3600)"),
        "cache privé retiré":
            ("'Cache-Control':'private, no-store, max-age=0'", "'Cache-Control':'public, max-age=3600'"),
        "erreur admin ignorée":
            ("adminCheck.error!==null", "false"),
        "type admin ignoré":
            ("typeof adminCheck.data!=='boolean'", "false"),
        "valeur admin truthy acceptée":
            ("if(adminCheck.data===true)userRank=100;", "if(adminCheck.data)userRank=100;"),
        "erreur rang ignorée":
            ("rankCheck.error!==null", "false"),
        "type rang ignoré":
            ("typeof rankCheck.data!=='number'", "false"),
        "rang fractionnaire accepté":
            ("!Number.isSafeInteger(rankCheck.data)", "false"),
        "rangs hors liste admis":
            ("!CANONICAL_PROJECT_RANKS.has(rankCheck.data)", "false"),
        "rangs admin non confirmés admis":
            ("const CANONICAL_PROJECT_RANKS=new Set([0,1,10,20,30]);", "const CANONICAL_PROJECT_RANKS=new Set([0,1,10,20,30,100]);"),
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
