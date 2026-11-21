#!/usr/bin/env python3
"""Audit de l'URL signée documentaire, sans accès réseau ni secrets.

Les mutations négatives empêchent la suppression silencieuse des barrières
identité → accès → localisation → métadonnées Storage privées → signature.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/functions/get-document-url/index.ts"
GUARD = ROOT / "supabase/functions/_shared/private-document-storage.mjs"
CONFIG = ROOT / "supabase/config.toml"

REQUIRED_EDGE = {
    "authentification optionnelle contrôlée": "optionalUser(req)",
    "validation du statut approuvé": "doc.status!=='approved'",
    "validation du projet actif": "doc.projects?.status!=='active'",
    "rang projet côté serveur": "service.rpc('project_access_rank'",
    "refus des accès insuffisants": "if(!documentAccessAllowed(doc.access_level,userRank))",
    "niveau d'accès de type texte": "typeof accessLevel==='string'",
    "niveau d'accès explicitement déclaré": "Object.prototype.hasOwnProperty.call(ranks,accessLevel)",
    "rang RPC fini": "Number.isFinite(userRank)",
    "comparaison du rang réel": "userRank>=ranks[accessLevel]",
    "aucun lien externe avant contrôle d'accès": "if(doc.external_url){",
    "origine du site canonique": "const DOCUMENT_URL_BASE='https://www.benoitcantin.com';",
    "refus des URL de tiers, même HTTPS": "if(parsed.origin!==DOCUMENT_URL_BASE)return false;",
    "chemin Storage sécurisé": "privateDocumentLocationValid(doc.storage_bucket,doc.storage_path)",
    "lecture du bucket Supabase réel": "service.storage.getBucket(doc.storage_bucket)",
    "vérification de l'identité et du statut privé": "!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket)",
    "refus du bucket incertain": "if(bucketMetadataError||!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket))",
    "absence d'URL en cas de panne": "return privateJson({ok:false,error:'Stockage privé indisponible.'},503);",
    "journal d'erreur fixe du bucket": "console.error('[get-document-url]',{code:'DOCUMENT_PRIVATE_BUCKET_UNVERIFIED'});",
    "lien signé 600 secondes": "createSignedUrl(doc.storage_path,600)",
    "réponse signée 600 secondes": "expires_in:600",
    "cache privé": "'Cache-Control':'private, no-store, max-age=0'",
    "protection MIME": "'X-Content-Type-Options':'nosniff'",
    "referrer privé": "'Referrer-Policy':'no-referrer'",
}
REQUIRED_GUARD = {
    "format bucket strict": "/^[a-z0-9][a-z0-9._-]{0,62}$/",
    "objet chemin borné": "storagePath.length > 1024",
    "refus des traversées": "segment !== '.' && segment !== '..'",
    "refus du bucket public": "metadata.public === false",
    "identité exacte du bucket": "metadata.id === expectedBucketId",
}

def audit(edge: str, guard: str, config: str) -> list[str]:
    errors: list[str] = []
    for label, marker in REQUIRED_EDGE.items():
        if marker not in edge:
            errors.append("get-document-url : contrôle manquant : " + label)
    for label, marker in REQUIRED_GUARD.items():
        if marker not in guard:
            errors.append("garde de document Storage : contrôle manquant : " + label)

    for prohibited in (
        "getPublicUrl(", "console.error(bucketMetadataError)",
        "console.error(error)", "await req.json()", "await req.text()",
    ):
        if prohibited in edge:
            errors.append("Source documentaire interdit une primitive dangereuse : " + prohibited)
    if edge.count("createSignedUrl(") != 1 or edge.count("service.storage.getBucket(") != 1:
        errors.append("Exactement une vérification du bucket et une signature autorisées")
    if edge.count("return privateJson({ok:false,error:'Stockage privé indisponible.'},503);") != 2:
        errors.append("Les deux erreurs de configuration et de bucket doivent refuser la signature")

    gates = [
        "const service=serviceClient(),user=await optionalUser(req);",
        "if(!documentAccessAllowed(doc.access_level,userRank))",
        "if(doc.external_url){",
        "privateDocumentLocationValid(doc.storage_bucket,doc.storage_path)",
        "service.storage.getBucket(doc.storage_bucket)",
        "!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket)",
        "createSignedUrl(doc.storage_path,600)",
    ]
    positions = [edge.find(marker) for marker in gates]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        errors.append("Ordre des gardes obligatoire : identité → droits → destination → bucket privé → signature")

    if edge.count("console.error(") != 2:
        errors.append("Les journaux des documents doivent rester deux codes constants")
    if "[functions.get-document-url]\nverify_jwt = false" not in config:
        errors.append("Le contrat JWT optionnel explicite doit être conservé")
    if "export function privateDocumentLocationValid(" not in guard or \
            "export function isVerifiedPrivateDocumentBucket(" not in guard:
        errors.append("Les deux barrières Storage doivent rester dans le module exécuté")
    return errors

def self_test(edge: str, guard: str, config: str) -> int:
    if errors := audit(edge, guard, config):
        raise AssertionError("La version saine est rejetée : " + " ; ".join(errors))
    edge_mutations = {
        "décision du rang ignorée": ("if(!documentAccessAllowed(doc.access_level,userRank))", "if(false)"),
        "niveau prototypal accepté": ("Object.prototype.hasOwnProperty.call(ranks,accessLevel)", "true"),
        "rang NaN ou infini accepté": ("Number.isFinite(userRank)", "true"),
        "comparaison de rang contournée": ("userRank>=ranks[accessLevel]", "true"),
        "niveau typé supprimé": ("typeof accessLevel==='string'", "true"),
        "URL HTTPS de tiers permise": ("if(parsed.origin!==DOCUMENT_URL_BASE)return false;", "if(relative&&parsed.origin!==DOCUMENT_URL_BASE)return false;"),
        "statut ignoré": ("doc.status!=='approved'", "false"),
        "projet inactif accepté": ("doc.projects?.status!=='active'", "false"),
        "chemin non vérifié": ("privateDocumentLocationValid(doc.storage_bucket,doc.storage_path)", "true"),
        "bucket jamais consulté": ("service.storage.getBucket(doc.storage_bucket)", "Promise.resolve({data:{public:false}})"),
        "bucket public accepté": ("!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket)", "false"),
        "erreur bucket masquée": ("if(bucketMetadataError||!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket))", "if(false)"),
        "refus 503 désactivé": ("      return privateJson({ok:false,error:'Stockage privé indisponible.'},503);\n    }\n\n    const {data:signed,error:signedError}=", "      return privateJson({ok:true},200);\n    }\n\n    const {data:signed,error:signedError}="),
        "TTL élargi": ("createSignedUrl(doc.storage_path,600)", "createSignedUrl(doc.storage_path,3600)"),
        "lien public Storage": ("createSignedUrl(doc.storage_path,600)", "getPublicUrl(doc.storage_path)"),
        "log brut": ("console.error('[get-document-url]',{code:'DOCUMENT_PRIVATE_BUCKET_UNVERIFIED'});", "console.error(bucketMetadataError);"),
        "cache public": ("'Cache-Control':'private, no-store, max-age=0'", "'Cache-Control':'public, max-age=3600'"),
    }
    for label, (before, after) in edge_mutations.items():
        if edge.count(before) != 1:
            raise AssertionError("Mutation impossible : " + label)
        if not audit(edge.replace(before, after, 1), guard, config):
            raise AssertionError("Régression non détectée : " + label)

    guard_mutations = {
        "bucket public accepté": ("metadata.public === false", "metadata.public !== undefined"),
        "identité du bucket ignorée": ("metadata.id === expectedBucketId", "true"),
        "traversée autorisée": ("segment !== '.' && segment !== '..'", "true"),
        "chemin illimité": ("storagePath.length > 1024", "false"),
    }
    for label, (before, after) in guard_mutations.items():
        if guard.count(before) != 1:
            raise AssertionError("Mutation garde impossible : " + label)
        if not audit(edge, guard.replace(before, after, 1), config):
            raise AssertionError("Régression garde non détectée : " + label)

    bad_config = config.replace("[functions.get-document-url]\nverify_jwt = false",
                                "[functions.get-document-url]\nverify_jwt = true", 1)
    if bad_config == config or not audit(edge, guard, bad_config):
        raise AssertionError("Incohérence de la configuration JWT non détectée")
    total = len(edge_mutations) + len(guard_mutations) + 1
    print(f"OK : {total} affaiblissements documentaires volontairement injectés ont été rejetés")
    return total

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    edge = EDGE.read_text(encoding="utf-8")
    guard = GUARD.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    if args.self_test:
        self_test(edge, guard, config)
    errors = audit(edge, guard, config)
    if errors:
        for error in errors:
            print("ÉCHEC : " + error)
        return 1
    print("OK : accès documentaire validé avant toute signature, bucket réel non public et path sûr")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
