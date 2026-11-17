#!/usr/bin/env python3
"""Bloque les portées ambiguës avant le RPC destructeur de contributions.

Validation du code réel et mutations négatives. Complément des scénarios Node
qui exécutent directement la vraie fonction Edge avec Supabase simulé.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/functions/revoke-my-contributions/index.ts"

REQUIRED = {
    "POST uniquement": "req.method !== 'POST'",
    "JWT vérifié": "await requiredUser(req)",
    "corps après auth": "await readBoundedJson(req)",
    "JSON limité": "readLimitedUtf8Body(req,MAX_REQUEST_BYTES)",
    "taille inchangée": "const MAX_REQUEST_BYTES=2048;",
    "propriété all propre": "const hasAll=Object.prototype.hasOwnProperty.call(body,'all');",
    "propriété session_id propre": "const hasSessionId=Object.prototype.hasOwnProperty.call(body,'session_id');",
    "liste blanche de champs": "Object.keys(body).some(key=>key!=='all'&&key!=='session_id')",
    "refus champs inconnus": "error:'Portée de révocation invalide.',code:'INVALID_SCOPE'",
    "all booléen": "if(hasAll && typeof body.all!=='boolean')",
    "suppression globale explicite": "const revokeAll=hasAll && body.all===true;",
    "session uniquement par propriété propre": "const sessionId=hasSessionId&&typeof body.session_id==='string'?body.session_id.trim():'';",
    "ambigu même si vide": "if(revokeAll && hasSessionId)",
    "code ambigu": "code:'AMBIGUOUS_SCOPE'",
    "UUID session requis": "if(!revokeAll && !UUID_RE.test(sessionId))",
    "UUID session privé": "code:'SESSION_REQUIRED'",
    "service après validation": "const service = serviceClient();",
    "RPC destructeur canonique": "service.rpc('revoke_sinjira_contributions'",
    "identité serveur": "p_user_id: user.id",
    "scope RPC exact": "p_session_id: revokeAll ? null : sessionId",
    "réponse non cacheable": "'Cache-Control':'private, no-store, max-age=0'",
    "erreur serveur expurgée": "console.error('[revoke-my-contributions]',{code:'REVOCATION_RPC_FAILED'});",
}
FORBIDDEN = (
    "if(revokeAll && sessionId)",
    "const revokeAll=Boolean(body.all)",
    "'all' in body",
    "p_user_id: body.user_id",
    "p_session_id: body.session_id || null",
    "await req.json()",
    "await req.text()",
    "console.error('[revoke-my-contributions]',error)",
)


def audit(source: str) -> list[str]:
    problems = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            problems.append("Révocation : garde absent ou affaibli : " + label)
    for marker in FORBIDDEN:
        if marker in source:
            problems.append("Révocation : accès dangereux : " + marker)
    auth = source.find("const user = await requiredUser(req);")
    body = source.find("const body = await readBoundedJson(req);")
    all_property = source.find("const hasAll=Object.prototype.hasOwnProperty.call(body,'all');")
    session_property = source.find("const hasSessionId=Object.prototype.hasOwnProperty.call(body,'session_id');")
    whitelist = source.find("if(Object.keys(body).some(")
    type_guard = source.find("if(hasAll && typeof body.all!=='boolean')")
    scope = source.find("const revokeAll=hasAll && body.all===true;")
    ambiguous = source.find("if(revokeAll && hasSessionId)")
    single = source.find("if(!revokeAll && !UUID_RE.test(sessionId))")
    service = source.find("const service = serviceClient();")
    rpc = source.find("service.rpc('revoke_sinjira_contributions'")
    if min(auth,body,all_property,session_property,whitelist,type_guard,scope,
           ambiguous,single,service,rpc) < 0 or not (
        auth < body < all_property < session_property < whitelist < type_guard
        < scope < ambiguous < single < service < rpc
    ):
        problems.append("Révocation : validation stricte et identité avant tout accès service_role/RPC")
    if source.count("service.rpc('revoke_sinjira_contributions'") != 1:
        problems.append("Révocation : un seul RPC destructeur doit exister")
    if source.count("if(revokeAll && hasSessionId)") != 1:
        problems.append("Révocation : refus d'ambiguïté obligatoire")
    return problems


def self_test(source: str) -> None:
    errors = audit(source)
    if errors:
        raise AssertionError("La source saine échoue : " + " ; ".join(errors))
    cases = [
        ("champs inconnus ignorés",
         "Object.keys(body).some(key=>key!=='all'&&key!=='session_id')",
         "Object.keys(body).some(key=>false)"),
        ("all hérité du prototype",
         "const hasAll=Object.prototype.hasOwnProperty.call(body,'all');",
         "const hasAll='all' in body;"),
        ("session héritée du prototype",
         "const hasSessionId=Object.prototype.hasOwnProperty.call(body,'session_id');",
         "const hasSessionId='session_id' in body;"),
        ("all coercé",
         "const revokeAll=hasAll && body.all===true;",
         "const revokeAll=Boolean(body.all);"),
        ("session coercée",
         "const sessionId=hasSessionId&&typeof body.session_id==='string'?body.session_id.trim():'';",
         "const sessionId=String(body.session_id||'');"),
        ("ambiguïté seulement si session non vide",
         "if(revokeAll && hasSessionId)",
         "if(revokeAll && sessionId)"),
        ("all non booléen toléré",
         "if(hasAll && typeof body.all!=='boolean')",
         "if(false)"),
        ("session invalide acceptée",
         "if(!revokeAll && !UUID_RE.test(sessionId))",
         "if(false)"),
        ("identité d'un autre usager",
         "p_user_id: user.id", "p_user_id: body.user_id"),
        ("portée globale implicite",
         "p_session_id: revokeAll ? null : sessionId",
         "p_session_id: null"),
        ("JSON sans limite",
         "readLimitedUtf8Body(req,MAX_REQUEST_BYTES)",
         "await req.text()"),
        ("JWT retiré",
         "const user = await requiredUser(req);",
         "const user = body.user_id;"),
        ("réponse publique",
         "'Cache-Control':'private, no-store, max-age=0'",
         "'Cache-Control':'public, max-age=300'"),
        ("méthode non restreinte",
         "req.method !== 'POST'", "false"),
    ]
    for label, old, new in cases:
        if source.count(old) != 1:
            raise AssertionError("Mutation mal formée : " + label + " count=" + str(source.count(old)))
        if not audit(source.replace(old,new,1)):
            raise AssertionError("Mutation indétectée : " + label)
    print(f"OK révocation explicite : {len(cases)} mutations dangereuses détectées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args = parser.parse_args()
    source = EDGE.read_text(encoding="utf-8")
    if args.self_test:
        self_test(source)
    errors = audit(source)
    if errors:
        for error in errors:
            print("ÉCHEC : " + error)
        return 1
    print("OK : aucune révocation globale sur scope ambigu, paramètres inconnus ou hérités.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
