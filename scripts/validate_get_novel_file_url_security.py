#!/usr/bin/env python3
"""Frontière de lecture privée des romans : JWT, entrée JSON et entitlements.

Contrat statique et mutations négatives exécutées sans secrets et sans réseau.
Les essais E2E réels doivent être effectués en environnement de préproduction
avant toute publication de la fonction Edge.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/functions/get-novel-file-url/index.ts"
CONFIG = ROOT / "supabase/config.toml"

REQUIRED = {
    "limite d'octets": "const MAX_REQUEST_BYTES=2048;",
    "méthode POST": "if(req.method!=='POST')",
    "authentification": "const user=await requiredUser(req);",
    "JSON uniquement": "if(mediaType!=='application/json')throw new Error('UNSUPPORTED_MEDIA_TYPE');",
    "content-length entier": "!Number.isSafeInteger(Number(declaredLength))",
    "taille déclarée": "Number(declaredLength)>MAX_REQUEST_BYTES",
    "taille réelle du flux": "if(total>MAX_REQUEST_BYTES)",
    "UTF-8 strict": "new TextDecoder('utf-8',{fatal:true}).decode(bytes)",
    "objet JSON seulement": "body===null||typeof body!=='object'||Array.isArray(body)",
    "slug strictement string": "typeof body?.slug==='string'?body.slug.trim():''",
    "erreur JSON 400": "if(message==='INVALID_JSON')return json({ok:false,error:'Corps JSON invalide.'},400);",
    "erreur taille 413": "if(message==='REQUEST_TOO_LARGE')return json({ok:false,error:'Requête trop volumineuse.'},413);",
    "erreur type 415": "if(message==='UNSUPPORTED_MEDIA_TYPE')return json({ok:false,error:'Type de contenu non autorisé.'},415);",
    "URL privée 600 secondes": ".createSignedUrl(novel.private_storage_path,600",
    "expiration signée": "expires_in:600",
    "compte utilisateur": ".eq('user_id',user.id)",
    "produit acheté": ".eq('product_id',novel.product_id)",
    "état publié": "novel.status!=='published'",
    "droit de lecture": "if(!entitled)return json(",
    "cache privé": "'Cache-Control':'private, no-store, max-age=0'",
    "protection JSON": "'X-Content-Type-Options':'nosniff'",
    "referrer privé": "'Referrer-Policy':'no-referrer'",
    "erreur privée expurgée": "console.error('[get-novel-file-url]',{code:'NOVEL_ACCESS_FAILED'});",
}
FORBIDDEN = (
    "String(body?.slug||'').trim()",
    "new TextDecoder().decode(bytes)",
    "getPublicUrl(",
    "req.json(",
    "req.text(",
    "console.error(error)",
    "console.error('[get-novel-file-url]',error)",
)

def validate_text(source: str, config: str) -> list[str]:
    errors = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f"Garde roman privé absent : {label}")
    for marker in FORBIDDEN:
        if marker in source:
            errors.append("Primitive ou diagnostic dangereux interdit dans le roman privé")
    if config.count("[functions.get-novel-file-url]") != 1:
        errors.append("Stanza JWT du roman absente ou dupliquée")
    else:
        stanza = config.split("[functions.get-novel-file-url]", 1)[1].split("[functions.", 1)[0]
        if "verify_jwt = true" not in stanza or "verify_jwt = false" in stanza:
            errors.append("JWT de la fonction roman doit rester activé")
    auth = source.find("const user=await requiredUser(req);")
    parse = source.find("const body=await readBoundedJson(req);")
    rights = source.find("if(!entitled)return json(")
    signed = source.find(".createSignedUrl(novel.private_storage_path,600")
    if not (0 <= auth < parse < rights < signed):
        errors.append("Auth et validation des droits obligatoires avant création du lien signé")
    if source.count("console.error(") != 1:
        errors.append("Les journaux du roman doivent rester bornés à un code fixe")
    return errors

def self_test(source: str, config: str) -> None:
    problems = validate_text(source, config)
    if problems:
        raise AssertionError("Source de référence invalide : " + " ; ".join(problems))
    mutations = {
        "auth supprimée": ("const user=await requiredUser(req);", "const user={id:'test'};"),
        "type JSON supprimé": ("if(mediaType!=='application/json')throw new Error('UNSUPPORTED_MEDIA_TYPE');", ""),
        "taille de flux supprimée": ("if(total>MAX_REQUEST_BYTES)", "if(false)"),
        "UTF-8 permissif": ("new TextDecoder('utf-8',{fatal:true}).decode(bytes)", "new TextDecoder().decode(bytes)"),
        "tableau JSON accepté": ("body===null||typeof body!=='object'||Array.isArray(body)", "body===null||typeof body!=='object'"),
        "objet slug coerce": ("typeof body?.slug==='string'?body.slug.trim():''", "String(body?.slug||'').trim()"),
        "taille déclarée ignorée": ("Number(declaredLength)>MAX_REQUEST_BYTES", "false"),
        "droits ignorés": ("if(!entitled)return json(", "if(false)return json("),
        "entitlement utilisateur absent": (".eq('user_id',user.id)", ".eq('user_id','another-user')"),
        "entitlement produit absent": (".eq('product_id',novel.product_id)", ".eq('product_id','other')"),
        "lien public": (".createSignedUrl(novel.private_storage_path,600", ".getPublicUrl(novel.private_storage_path"),
        "URL signée trop longue": (".createSignedUrl(novel.private_storage_path,600", ".createSignedUrl(novel.private_storage_path,3600"),
        "cache privé enlevé": ("'Cache-Control':'private, no-store, max-age=0'", "'Cache-Control':'public, max-age=3600'"),
        "journaux bruts": ("console.error('[get-novel-file-url]',{code:'NOVEL_ACCESS_FAILED'});", "console.error(error);"),
    }
    for label, (old, new) in mutations.items():
        if source.count(old) != 1:
            raise AssertionError(f"Mutation impossible : {label}")
        bad = source.replace(old, new, 1)
        if not validate_text(bad, config):
            raise AssertionError(f"Mutation non détectée : {label}")
    bad_config = config.replace("[functions.get-novel-file-url]\nverify_jwt = true",
                                "[functions.get-novel-file-url]\nverify_jwt = false", 1)
    if bad_config == config or not validate_text(source, bad_config):
        raise AssertionError("La désactivation JWT n'est pas détectée")
    print(f"OK : {len(mutations)+1} régressions de sécurité refusées")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    source = EDGE.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    if args.self_test:
        self_test(source, config)
    errors = validate_text(source, config)
    for error in errors:
        print("ÉCHEC : " + error)
    if errors:
        return 1
    print("OK : roman privé, entrée bornée, JSON UTF-8 strict, JWT, droits et URL signée")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
