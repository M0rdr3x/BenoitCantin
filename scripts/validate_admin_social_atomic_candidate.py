#!/usr/bin/env python3
"""Garde statique des contrats Edge de modération atomique.

Les tests PostgreSQL éphémères prouvent les transactions et leurs ACL.
Ce garde contrôle la route HTTP qui choisit les RPC sans aucun CRUD privé.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/candidate-edge/admin-social-v20/index.ts"
ACTIVE_EDGE = ROOT / "supabase/functions/admin-social-v20/index.ts"
LIMIT_RE = re.compile(r"\bMAX_REQUEST_BYTES\s*=\s*8_?192\s*;")

REQUIRED = {
    "POST uniquement": "req.method!=='POST'",
    "admin et AAL2": "const {user,service:s}=await requiredAdmin(req)",
    "Content-Type JSON": "contentType.startsWith('application/json')",
    "erreur média": "e?.message==='UNSUPPORTED_MEDIA_TYPE'",
    "lecture JSON bornée": "const b=await readLimitedJson(req)",
    "lecture du flux bornée": "readLimitedUtf8Body(req,MAX_REQUEST_BYTES)",
    "taille UTF8 réelle": "new TextEncoder().encode(raw).byteLength",
    "réponse privée": "'Cache-Control':'private, no-store, max-age=0'",
    "cache no-store secondaire": "'Pragma':'no-cache'",
    "nosniff": "'X-Content-Type-Options':'nosniff'",
    "no-referrer": "'Referrer-Policy':'no-referrer'",
    "journalisation allowlistée": "SAFE_LOG_CODES",
    "fallback log opaque": "return SAFE_LOG_CODES.has(code)?code:'MODERATION_BACKEND_FAILED'",
    "routage des sanctions vers RPC": "s.rpc('sinjira_admin_moderate_atomic'",
    "routage des appels vers RPC": "s.rpc('sinjira_admin_review_appeal_atomic'",
    "lecture des appels par RPC": "s.rpc('sinjira_admin_appeals_overview'",
    "jeton admin issu de requiredAdmin": "p_admin_id:adminId",
    "refus des erreurs SQL imprévues": "throw new Error('ATOMIC_MODERATION_FAILED')",
    "aucun détail de PostgREST dans la réponse": "if(error)atomicFailure(error)",
    "rapport clos refusé": "if(!r||r.status!=='open')throw new Error('REPORT_NOT_OPEN')",
    "snapshot Rencontres non authentifié refusé": "if(r.snapshot?.source==='dating')throw new Error('UNVERIFIED_DATING_PROVENANCE')",
    "durée entière strictement bornée": "typeof days!=='number'||!Number.isInteger(days)||days<1||days>365",
    "urgence strictement bornée": "if(!['standard','urgent_harm','illegal_content'].includes(urgency))",
    "révision humaine contrôlée": "reason.length<20||reason.length>4000",
    "révision d'appel autorisée": "if(a==='review_appeal')return privateJson(await reviewAppeal(s,user.id,b))",
    "clôture du rapport atomique": "await atomicModeration(s,user.id,b.report_id,'resolve_report')",
    "lecture sans accès CRUD privé": "appealOverview(s,user.id)",
    "réponses sanction réversibles": "reversible:true",
    "référence UUID vérifiée": "throw new Error('INVALID_MODERATION_REFERENCE')",
    "MFA indisponible bloque": "e?.message==='MFA_STATE_UNAVAILABLE'",
}

FORBIDDEN = {
    "json direct non borné": "await req.json()",
    "helper JSON cacheable": "return json(",
    "auth utilisateur au lieu d'admin": "requiredUser(req)",
    "client service créé avant authentification": "serviceClient()",
    "erreur brute retournée au client": "error:e?.message",
    "erreur brute journalisée": "console.error('[admin-social-v20]',e)",
    "message brut journalisé": "console.error('[admin-social-v20]',e?.message)",
    "lecture SQL privée directement par Edge": ".schema('private').from(",
    "INSERT direct de décision": ".from('moderation_decisions').insert(",
    "UPSERT direct de suspension": ".from('social_suspensions').upsert(",
    "UPDATE direct de rapport": ".from('social_reports').update(",
    "DELETE direct de suspension": ".from('social_suspensions').delete(",
    "limite de durée silencieusement corrigée": "Math.max(1,Math.min(Number(b.days||7),365))",
    "utilisation de la metadata utilisateur": "user_metadata",
}


def validate(path: Path) -> list[str]:
    try:
        src = path.read_text("utf-8", errors="strict")
    except OSError as err:
        return ["Module Edge illisible : " + str(err)]
    errors: list[str] = []
    for name, marker in REQUIRED.items():
        if marker not in src:
            errors.append("Contrat Edge absent : " + name)
    if not LIMIT_RE.search(src):
        errors.append("Taille HTTP 8192 octets exacte requise.")
    for name, marker in FORBIDDEN.items():
        if marker.lower() in src.lower():
            errors.append("Opération dangereuse interdite : " + name)

    auth = src.find("const {user,service:s}=await requiredAdmin(req)")
    media = src.find("requireJsonContentType(req)", auth)
    body = src.find("const b=await readLimitedJson(req)", auth)
    if min(auth, media, body) < 0 or not (auth < media < body):
        errors.append("JWT/admin/AAL2 doivent précéder Content-Type et lecture bornée.")

    log = src.find("console.error('[admin-social-v20]',moderationLogCode(e))")
    fallback = src.find("return SAFE_LOG_CODES.has(code)?code:'MODERATION_BACKEND_FAILED'")
    if min(log, fallback) < 0:
        errors.append("Journalisation brute sans allowlist interdite.")

    atomic_start = src.find("async function atomicModeration(")
    atomic_end = src.find("async function createDecision(", atomic_start)
    if atomic_start < 0 or atomic_end < 0:
        errors.append("Routage vers RPC atomique introuvable.")
    else:
        atomic = src[atomic_start:atomic_end]
        for name, marker in (
            ("RPC sanctions", "s.rpc('sinjira_admin_moderate_atomic'"),
            ("identité admin", "p_admin_id:adminId"),
            ("référence rapport", "p_report_id:reportId"),
            ("action SQL", "p_action:action"),
            ("échec atomique", "if(error)atomicFailure(error)"),
        ):
            if marker not in atomic:
                errors.append("AtomicModeration sans " + name)

    decision_start = src.find("async function createDecision(")
    decision_end = src.find("async function appealOverview(", decision_start)
    if decision_start < 0 or decision_end < 0:
        errors.append("Prévalidation de la décision introuvable.")
    else:
        decision = src[decision_start:decision_end]
        for marker in (
            "if(!r||r.status!=='open')",
            "typeof days!=='number'||!Number.isInteger(days)||days<1||days>365",
            "if(!['standard','urgent_harm','illegal_content'].includes(urgency))",
            "await atomicModeration(s,adminId,r.id,action,",
        ):
            if marker not in decision:
                errors.append("Prévalidation de sanction manquante : " + marker)

    if "CANDIDAT DE REVUE UNIQUEMENT" not in src:
        errors.append("Marqueur non-déployé absent du candidat Edge.")
    try:
        active = ACTIVE_EDGE.read_text("utf-8", errors="strict")
        for rpc in (
            "sinjira_admin_moderate_atomic",
            "sinjira_admin_review_appeal_atomic",
            "sinjira_admin_appeals_overview",
        ):
            if "s.rpc('" + rpc + "'" in active:
                errors.append("Fonction Edge active appelle une RPC encore candidate : " + rpc)
    except OSError:
        errors.append("Edge active indisponible pour comparaison.")
    if src.count("reversible:true") != 2:
        errors.append("Les deux sanctions doivent rester réversibles.")
    if src.count("privateJson(") < 13:
        errors.append("Toutes les réponses doivent conserver le cache privé.")
    if src.count("s.rpc('sinjira_admin_") != 3:
        errors.append("Les trois RPC SQL publiques, et seulement elles, doivent être utilisées.")
    return errors


def self_test() -> None:
    original = EDGE.read_text("utf-8", errors="strict")
    errors = validate(EDGE)
    if errors:
        raise AssertionError("Source sain invalide : " + "; ".join(errors))

    cases = {
        "lecture JSON directe": original.replace("const b=await readLimitedJson(req)",
            "const b=await req.json()", 1),
        "Content-Type retiré": original.replace("    requireJsonContentType(req);\n", "", 1),
        "Content-Type après lecture": original.replace(
            "    requireJsonContentType(req);\n    const b=await readLimitedJson(req);",
            "    const b=await readLimitedJson(req);\n    requireJsonContentType(req);", 1),
        "corps trop grand": original.replace("MAX_REQUEST_BYTES=8192;", "MAX_REQUEST_BYTES=81920;", 1),
        "no-store retiré": original.replace("'Cache-Control':'private, no-store, max-age=0'", "", 1),
        "admin retiré": original.replace("const {user,service:s}=await requiredAdmin(req)",
            "const user=await requiredUser(req),s=serviceClient()", 1),
        "erreur brute loguée": original.replace("console.error('[admin-social-v20]',moderationLogCode(e))",
            "console.error('[admin-social-v20]',e)", 1),
        "fallback log retiré": original.replace(
            "return SAFE_LOG_CODES.has(code)?code:'MODERATION_BACKEND_FAILED'",
            "return code", 1),
        "RPC sanction désactivée": original.replace(
            "s.rpc('sinjira_admin_moderate_atomic'",
            "s.rpc('unprotected_sanction_write'", 1),
        "RPC appel désactivée": original.replace(
            "s.rpc('sinjira_admin_review_appeal_atomic'",
            "s.rpc('unprotected_appeal_write'", 1),
        "RPC liste privée désactivée": original.replace(
            "s.rpc('sinjira_admin_appeals_overview'",
            "s.rpc('unprotected_appeal_list'", 1),
        "admin fourni par le client": original.replace("p_admin_id:adminId",
            "p_admin_id:payload.admin_id", 1),
        "référence rapport falsifiée": original.replace("p_report_id:reportId",
            "p_report_id:payload.report_id", 1),
        "erreur SQL brute": original.replace("if(error)atomicFailure(error)",
            "if(error)throw error", 1),
        "SQL validé seulement en UI": original.replace(
            "await atomicModeration(s,adminId,r.id,action,",
            "await s.from('moderation_decisions').insert(", 1),
        "rapport fermé autorisé": original.replace(
            "if(!r||r.status!=='open')throw new Error('REPORT_NOT_OPEN');", "", 1),
        "sanction Rencontres par snapshot forgé": original.replace(
            "if(r.snapshot?.source==='dating')throw new Error('UNVERIFIED_DATING_PROVENANCE');", "", 1),
        "durée laxiste": original.replace(
            "typeof days!=='number'||!Number.isInteger(days)||days<1||days>365",
            "typeof days!=='number'", 1),
        "urgence arbitraire": original.replace(
            "if(!['standard','urgent_harm','illegal_content'].includes(urgency))",
            "if(false)", 1),
        "clôture non atomique": original.replace(
            "await atomicModeration(s,user.id,b.report_id,'resolve_report')",
            "await s.from('social_reports').update({status:'resolved'})", 1),
        "lecture privée via REST": original.replace(
            "s.rpc('sinjira_admin_appeals_overview'",
            "s.schema('private').from('moderation_appeals')", 1),
        "appel humain supprimé": original.replace(
            "if(a==='review_appeal')return privateJson(await reviewAppeal(s,user.id,b))",
            "if(a==='review_appeal_disabled')return privateJson(await reviewAppeal(s,user.id,b))", 1),
        "sanction non réversible": original.replace("reversible:true", "reversible:false", 1),
    }
    with TemporaryDirectory() as td:
        tmp = Path(td) / "index.ts"
        for label, changed in cases.items():
            if changed == original:
                raise AssertionError("Mutation inopérante : " + label)
            tmp.write_text(changed, encoding="utf-8")
            if not validate(tmp):
                raise AssertionError("Mutation non détectée : " + label)
    print(f"OK contrat Edge atomique : {len(cases)} affaiblissements refusés.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Contrat de sécurité de modération atomique Edge.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(EDGE)
    if errors:
        print("ECHEC : " + "; ".join(errors))
        return 1
    print("OK Edge : JWT/AAL2 avant corps, requêtes bornées et trois RPC publiques réservées au serveur.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
