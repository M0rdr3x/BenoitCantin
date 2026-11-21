#!/usr/bin/env python3
"""Fail-closed contract for private SINJIRA novel downloads.

No JWT, external network, database or production credentials are used.
The contract supplements (rather than replaces) real entitlement tests.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/functions/get-novel-file-url/index.ts"
GUARD = ROOT / "supabase/functions/_shared/private-book-storage-guard.mjs"
CONFIG = ROOT / "supabase/config.toml"

REQUIRED = {
    "authentification": "const user=await requiredUser(req);",
    "requête JSON explicite": "if(!/^application",
    "lecteur à échéance absolue": "readLimitedUtf8BodyWithDeadline(req,MAX_REQUEST_BYTES,8000)",
    "code délai refusé": "if(message==='REQUEST_TIMEOUT')",
    "code MIME refusé": "if(message==='JSON_REQUIRED')",
    "slug chaîne stricte": "typeof body.slug==='string'",
    "POST seulement": "if(req.method!=='POST')",
    "état publié": "novel.status!=='published'",
    "droit propriétaire ou administrateur": "let entitled=Boolean(isOwner||isAdmin);",
    "vérification achat propriétaire": ".eq('user_id',user.id)",
    "vérification produit": ".eq('product_id',novel.product_id)",
    "rejet droit absent": "if(!entitled)return json(",
    "fichier activé": "if(!novel.file_ready)return json(",
    "chemin sûr": "privateBookLocationValid(novel.private_storage_bucket,novel.private_storage_path)",
    "lecture état bucket": "service.storage.getBucket(novel.private_storage_bucket)",
    "bucket privé exact": "!isVerifiedPrivateBucket(bucketMetadata,novel.private_storage_bucket)",
    "échec si bucket public": "return json({ok:false,error:'Stockage privé indisponible.'},503);",
    "journal fixe": "console.error('[get-novel-file-url]',{code:'NOVEL_PRIVATE_BUCKET_UNVERIFIED'});",
    "signature 600 secondes": "createSignedUrl(novel.private_storage_path,600",
    "expiration annoncée": "expires_in:600",
    "cache privé": "'Cache-Control':'private, no-store, max-age=0'",
    "anti sniff": "'X-Content-Type-Options':'nosniff'",
    "aucun référent": "'Referrer-Policy':'no-referrer'",
}
FORBIDDEN = ("getPublicUrl(", "console.error(error)", "console.error(bucketMetadataError)",
             "await reader.read()", "await reader.cancel(", "await req.text()", "await req.json()",
             "String(body?.slug")

def check_source(source: str, guard: str, config: str) -> list[str]:
    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append("Contrat lecture privée absent : " + label)
    for marker in FORBIDDEN:
        if marker in source:
            errors.append("Repli public ou journal brut interdit : " + marker)
    for marker in (
        "export function privateBookLocationValid(bucket, storagePath)",
        "export function isVerifiedPrivateBucket(metadata, expectedBucketId)",
        "metadata.public === false",
        "metadata.id === expectedBucketId",
    ):
        if marker not in guard:
            errors.append("Garde Storage privé absent : " + marker)
    stanza = config.split("[functions.get-novel-file-url]", 1)
    if len(stanza) != 2 or "verify_jwt = true" not in stanza[1].split("[functions.", 1)[0]:
        errors.append("La fonction roman doit exiger JWT côté Supabase.")
    auth_at = source.find("const user=await requiredUser(req);")
    entitled_at = source.find("if(!entitled)return json(")
    ready_at = source.find("if(!novel.file_ready)return json(")
    config_at = source.find("privateBookLocationValid(novel.private_storage_bucket,novel.private_storage_path)")
    bucket_at = source.find("service.storage.getBucket(novel.private_storage_bucket)")
    verify_at = source.find("!isVerifiedPrivateBucket(bucketMetadata,novel.private_storage_bucket)")
    sign_at = source.find("createSignedUrl(novel.private_storage_path,600")
    if not (0 <= auth_at < entitled_at < ready_at < config_at < bucket_at < verify_at < sign_at):
        errors.append("Ordre fail-closed obligatoire : JWT → droit → disponibilité → objet → bucket privé → signature.")
    if source.count("createSignedUrl(") != 1:
        errors.append("Une seule signature privée est autorisée.")
    if source.count("service.storage.getBucket(") != 1:
        errors.append("La vérification du bucket doit être unique et effective.")
    return errors

def self_test(source: str, guard: str, config: str) -> None:
    if errors := check_source(source, guard, config):
        raise AssertionError("Source saine rejetée : " + "; ".join(errors))
    mutations = {
        "auth supprimée": ("const user=await requiredUser(req);", "const user={id:'spoofed'};"),
        "délai lecture supprimé": ("readLimitedUtf8BodyWithDeadline(req,MAX_REQUEST_BYTES,8000)", "readLimitedUtf8Body(req,MAX_REQUEST_BYTES)"),
        "type du slug ignoré": ("typeof body.slug==='string'", "String(body.slug)"),
        "erreur d'attente supprimée": ("if(message==='REQUEST_TIMEOUT')", "if(false)"),
        "POST retiré": ("if(req.method!=='POST')", "if(false)"),
        "statut publié ignoré": ("novel.status!=='published'", "false"),
        "entitlement absent": ("if(!entitled)return json(", "if(false)return json("),
        "filtre utilisateur absent": (".eq('user_id',user.id)", ".eq('user_id','anonymous')"),
        "filtre produit absent": (".eq('product_id',novel.product_id)", ".eq('product_id','arbitrary')"),
        "fichier désactivé accepté": ("if(!novel.file_ready)return json(", "if(false)return json("),
        "chemin non validé": ("privateBookLocationValid(novel.private_storage_bucket,novel.private_storage_path)", "true"),
        "bucket non consulté": ("service.storage.getBucket(novel.private_storage_bucket)", "Promise.resolve({data:{public:false}})"),
        "bucket public accepté": ("!isVerifiedPrivateBucket(bucketMetadata,novel.private_storage_bucket)", "false"),
        "échec bucket silencieux": ("return json({ok:false,error:'Stockage privé indisponible.'},503);", "return json({ok:true},200);"),
        "cache partagé": ("'Cache-Control':'private, no-store, max-age=0'", "'Cache-Control':'public, max-age=3600'"),
        "durée portée à 24 heures": ("createSignedUrl(novel.private_storage_path,600", "createSignedUrl(novel.private_storage_path,86400"),
        "URL publique": ("createSignedUrl(novel.private_storage_path,600", "getPublicUrl(novel.private_storage_path"),
        "log erreur brute": ("console.error('[get-novel-file-url]',{code:'NOVEL_PRIVATE_BUCKET_UNVERIFIED'});", "console.error(bucketMetadataError);"),
    }
    for label, (old, new) in mutations.items():
        if source.count(old) != 1:
            raise AssertionError("Mutation non applicable : " + label)
        if not check_source(source.replace(old, new, 1), guard, config):
            raise AssertionError("Mutation non détectée : " + label)
    for label, new_guard in (
        ("bucket public autorisé", guard.replace("metadata.public === false", "metadata.public !== undefined", 1)),
        ("bucket id ignoré", guard.replace("metadata.id === expectedBucketId", "true", 1)),
    ):
        if new_guard == guard or not check_source(source, new_guard, config):
            raise AssertionError("Mutation garde non détectée : " + label)
    bad_config = config.replace("[functions.get-novel-file-url]\nverify_jwt = true",
                                "[functions.get-novel-file-url]\nverify_jwt = false", 1)
    if bad_config == config or not check_source(source, guard, bad_config):
        raise AssertionError("Désactivation JWT non détectée")
    print("OK : 21 mutations négatives refusées (droits, flux avec délai, bucket, JWT, TTL, cache et journal)")

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    source = EDGE.read_text("utf-8")
    guard = GUARD.read_text("utf-8")
    config = CONFIG.read_text("utf-8")
    if args.self_test:
        self_test(source, guard, config)
    errors = check_source(source, guard, config)
    for error in errors:
        print("ÉCHEC : " + error)
    if errors:
        return 1
    print("OK : accès au roman privé refusé si le bucket Storage ou le chemin ne sont pas prouvés sûrs")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
