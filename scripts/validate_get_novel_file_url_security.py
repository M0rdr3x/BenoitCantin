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
STREAM = ROOT / "supabase/functions/_shared/novel-request-bytes.mjs"

REQUIRED = {
    "limite d'octets": "const MAX_REQUEST_BYTES=2048;",
    "méthode POST": "if(req.method!=='POST')",
    "authentification": "const user=await requiredUser(req);",
    "JSON uniquement": "if(mediaType!=='application/json')throw new Error('UNSUPPORTED_MEDIA_TYPE');",
    "content-length entier": "!Number.isSafeInteger(Number(declaredLength))",
    "taille déclarée": "Number(declaredLength)>MAX_REQUEST_BYTES",
    "lecture bornée du flux": "const bytes=await collectNovelBodyBytes(req,MAX_REQUEST_BYTES);",
    "UTF-8 strict": "new TextDecoder('utf-8',{fatal:true}).decode(bytes)",
    "objet JSON seulement": "body===null||typeof body!=='object'||Array.isArray(body)",
    "slug strictement string": "typeof body?.slug==='string'?body.slug.trim():''",
    "erreur JSON 400": "if(message==='INVALID_JSON')return json({ok:false,error:'Corps JSON invalide.'},400);",
    "erreur taille 413": "if(message==='REQUEST_TOO_LARGE')return json({ok:false,error:'Requête trop volumineuse.'},413);",
    "erreur type 415": "if(message==='UNSUPPORTED_MEDIA_TYPE')return json({ok:false,error:'Type de contenu non autorisé.'},415);",
    "expiration et abandon 408": "if(message==='REQUEST_INTERRUPTED')return json({ok:false,error:'Lecture de la requête interrompue.'},408);",
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
STREAM_REQUIRED = {
    "délai global de huit secondes": "timeoutMs = 8_000",
    "délai plafonné": "timeoutMs > 30_000",
    "interruption par deadline": "const deadline = setTimeout(interrupt, timeoutMs);",
    "interruption sur abandon": "req.signal.addEventListener('abort', interrupt, {once:true});",
    "annulation asynchrone non bloquante": "void reader.cancel().catch(() => {});",
    "lecture par flux": "await reader.read();",
    "dépassement sans entier": "value.byteLength > maxBytes - total",
    "signal d'interruption": "if (interrupted || req.signal.aborted) throw new Error('REQUEST_INTERRUPTED');",
    "octets complets seulement": "const bytes = new Uint8Array(total);",
    "délai annulé": "clearTimeout(deadline);",
    "écouteur supprimé": "req.signal.removeEventListener('abort', interrupt);",
    "verrou libéré": "reader.releaseLock();",
    "statut taille conservé": "if (error instanceof Error && error.message === 'REQUEST_TOO_LARGE') throw error;",
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

def validate_text(source: str, config: str, stream: str) -> list[str]:
    errors = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f"Garde roman privé absent : {label}")
    for label, marker in STREAM_REQUIRED.items():
        if marker not in stream:
            errors.append(f"Protection du flux du roman absente : {label}")
    for marker in ("await reader.cancel()", "req.text()", "req.json()"):
        if marker in stream:
            errors.append("Primitive de lecture sans garanties dans le flux de roman")
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

def self_test(source: str, config: str, stream: str) -> None:
    problems = validate_text(source, config, stream)
    if problems:
        raise AssertionError("Source de référence invalide : " + " ; ".join(problems))
    mutations = {
        "auth supprimée": ("const user=await requiredUser(req);", "const user={id:'test'};"),
        "type JSON supprimé": ("if(mediaType!=='application/json')throw new Error('UNSUPPORTED_MEDIA_TYPE');", ""),
        "lecture du flux supprimée": ("const bytes=await collectNovelBodyBytes(req,MAX_REQUEST_BYTES);", "const bytes=new Uint8Array(0);"),
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
        if not validate_text(bad, config, stream):
            raise AssertionError(f"Mutation non détectée : {label}")
    stream_mutations = {
        "délai retiré": ("const deadline = setTimeout(interrupt, timeoutMs);", "const deadline = null;"),
        "interruption client retirée": ("req.signal.addEventListener('abort', interrupt, {once:true});", ""),
        "cancel bloquant": ("void reader.cancel().catch(() => {});", "await reader.cancel().catch(() => {});"),
        "limite réelle retirée": ("value.byteLength > maxBytes - total", "false"),
        "lecture directe non bornée": ("await reader.read();", "await req.text();"),
        "détection interruption supprimée": ("if (interrupted || req.signal.aborted) throw new Error('REQUEST_INTERRUPTED');", "if (false) throw new Error('REQUEST_INTERRUPTED');"),
        "deadline non nettoyée": ("clearTimeout(deadline);", ""),
        "écouteur non retiré": ("req.signal.removeEventListener('abort', interrupt);", ""),
        "statut taille perdu": ("if (error instanceof Error && error.message === 'REQUEST_TOO_LARGE') throw error;", ""),
    }
    for label, (old, new) in stream_mutations.items():
        if stream.count(old) != 1:
            raise AssertionError(f"Mutation du flux impossible : {label}")
        bad = stream.replace(old, new, 1)
        if not validate_text(source, config, bad):
            raise AssertionError(f"Régression du flux non détectée : {label}")
    bad_config = config.replace("[functions.get-novel-file-url]\nverify_jwt = true",
                                "[functions.get-novel-file-url]\nverify_jwt = false", 1)
    if bad_config == config or not validate_text(source, bad_config, stream):
        raise AssertionError("La désactivation JWT n'est pas détectée")
    print(f"OK : {len(mutations)+len(stream_mutations)+1} régressions de sécurité refusées")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    source = EDGE.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    stream = STREAM.read_text(encoding="utf-8")
    if args.self_test:
        self_test(source, config, stream)
    errors = validate_text(source, config, stream)
    for error in errors:
        print("ÉCHEC : " + error)
    if errors:
        return 1
    print("OK : roman privé, streaming avec timeout/abort, UTF-8 strict, JWT, droits et URL signée")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
