#!/usr/bin/env python3
"""Garde-fou A1 : security-context reste minimal et refuse toute décision ambiguë."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/functions/security-context/index.ts"
WORKFLOW = ROOT / ".github/workflows/sinjira-security-context-response-v25.yml"


def validate(source: str, workflow: str) -> list[str]:
    errors: list[str] = []

    required_source = {
        "authentification requiredUser": "const user = await requiredUser(req);",
        "session JWT vérifiée": "const sessionId = sessionIdFromVerifiedRequest(req);",
        "RPC de décision serveur": "service_security_evaluate_context_session",
        "géolocalisation explicitement activée": "SINJIRA_TRUST_GEO_HEADERS",
        "réponse privée sans cache": "'Cache-Control': 'private, no-store, max-age=0'",
        "issues canoniques exactes": "const SECURITY_OUTCOMES = new Set(['allow', 'challenge', 'block']);",
        "projection typée fail-closed": "function publicSecurityResult(data: unknown): PublicSecurityResult | null",
        "absence de fallback implicite": "const outcome = typeof source.outcome === 'string' ? source.outcome.trim() : '';",
        "issue inconnue rejetée": "if (!SECURITY_OUTCOMES.has(outcome)) return null;",
        "UUID de défi normalisé": "const challengeId = typeof source.challenge_id === 'string' ? source.challenge_id.trim() : '';",
        "défi incomplet rejeté": "if (!challengeId || !UUID_RE.test(challengeId)) return null;",
        "défi public minimal": "return { outcome: 'challenge', challenge_id: challengeId };",
        "allow/block publics minimaux": "return { outcome: outcome as 'allow' | 'block' };",
        "projection calculée avant succès": "const publicSecurity = publicSecurityResult(data);",
        "projection obligatoire": "if (!publicSecurity) {",
        "réponse fail-closed générique": "return privateJson({ ok: false, error: 'Le contexte de sécurité est temporairement indisponible.' }, 503);",
        "projection utilisée sur HTTP": "security: publicSecurity",
        "objet complet conservé pour le push interne": "runSecurityPushBackground(service, user.id, data)",
    }
    for label, fragment in required_source.items():
        if fragment not in source:
            errors.append(f"Manquant: {label}.")

    forbidden_global = {
        "sérialisation brute du résultat RPC": "security: data",
        "spread brut du résultat RPC": "...data",
        "lecture IP X-Forwarded-For": "x-forwarded-for",
        "lecture IP Cloudflare": "cf-connecting-ip",
        "lecture IP X-Real-IP": "x-real-ip",
        "lecture IP True-Client-IP": "true-client-ip",
    }
    lowered = source.lower()
    for label, fragment in forbidden_global.items():
        if fragment.lower() in lowered:
            errors.append(f"Interdit: {label}.")

    helper_start = source.find("function publicSecurityResult(data: unknown)")
    if helper_start < 0:
        helper_start = source.find("function publicSecurityResult(data: unknown): PublicSecurityResult | null")
    helper_end = source.find("function sessionIdFromVerifiedRequest", helper_start)
    if helper_start < 0 or helper_end < 0:
        errors.append("Impossible d'isoler publicSecurityResult().")
    else:
        helper = source[helper_start:helper_end]
        forbidden_public_fields = (
            "risk_score",
            "risk_reasons",
            "country",
            "region",
            "city",
            "latitude",
            "longitude",
            "delete_after",
            "user_id",
            "device_key",
            "display_name",
            "platform",
        )
        for field in forbidden_public_fields:
            if field in helper:
                errors.append(f"Champ interne interdit dans la projection publique: {field}.")
        fallback_markers = (
            ": 'allow';",
            '|| \'allow\'',
            '?? \'allow\'',
            'return { outcome: \'allow\' }; // fallback',
        )
        for marker in fallback_markers:
            if marker in helper:
                errors.append("La projection contient un fallback implicite vers allow.")
                break

    projection_pos = source.find("const publicSecurity = publicSecurityResult(data);")
    reject_pos = source.find("if (!publicSecurity) {", projection_pos)
    push_pos = source.find("EdgeRuntime.waitUntil(runSecurityPushBackground(service, user.id, data));")
    success_pos = source.find("return privateJson({\n      ok: true")
    if min(projection_pos, reject_pos, push_pos, success_pos) < 0:
        errors.append("Impossible de vérifier l'ordre fail-closed de security-context.")
    elif not (projection_pos < reject_pos < push_pos < success_pos):
        errors.append("La décision publique doit être validée avant le push de fond et avant toute réponse de succès.")

    response_start = success_pos
    response_end = source.find("\n    });", response_start)
    if response_start < 0 or response_end < 0:
        errors.append("Impossible d'isoler la réponse HTTP de succès.")
    else:
        response = source[response_start:response_end]
        for field in ("risk_score", "risk_reasons", "country", "region", "city", "latitude", "longitude"):
            serialized_keys = (f"{field}:", f"'{field}':", f'"{field}":')
            if any(marker in response for marker in serialized_keys):
                errors.append(f"Champ interne exposé dans la réponse HTTP: {field}.")
        if "privacy:" in response:
            errors.append("La réponse publique contient encore le bloc documentaire privacy inutile au flux.")

    for line in source.splitlines():
        compact = line.strip()
        if compact.startswith("console.error") and (", error" in compact or " error)" in compact):
            errors.append("Le journal serveur sérialise encore l'objet d'erreur brut.")

    required_workflow = {
        "runner épinglé": "runs-on: ubuntu-24.04",
        "permissions lecture seule": "contents: read",
        "Python épinglé": "python-version: '3.12.14'",
        "auto-test": "python3 scripts/validate_security_context_response_v25.py --self-test",
        "validation": "python3 scripts/validate_security_context_response_v25.py",
    }
    for label, fragment in required_workflow.items():
        if fragment not in workflow:
            errors.append(f"Workflow manquant: {label}.")

    watched = (
        "supabase/functions/security-context/index.ts",
        "scripts/validate_security_context_response_v25.py",
        ".github/workflows/sinjira-security-context-response-v25.yml",
    )
    for path in watched:
        if workflow.count(path) < 2:
            errors.append(f"Le workflow doit surveiller {path} sur pull_request et push.")

    if "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803" not in workflow:
        errors.append("actions/checkout doit rester épinglé au SHA revu.")
    if "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1" not in workflow:
        errors.append("actions/setup-python doit rester épinglé au SHA revu.")

    return errors


def self_test(source: str, workflow: str) -> None:
    fail_closed_block = """    const publicSecurity = publicSecurityResult(data);\n    if (!publicSecurity) {\n      console.warn('[security-context] décision serveur invalide');\n      return privateJson({ ok: false, error: 'Le contexte de sécurité est temporairement indisponible.' }, 503);\n    }\n\n    EdgeRuntime.waitUntil(runSecurityPushBackground(service, user.id, data));"""
    reordered_block = """    EdgeRuntime.waitUntil(runSecurityPushBackground(service, user.id, data));\n\n    const publicSecurity = publicSecurityResult(data);\n    if (!publicSecurity) {\n      console.warn('[security-context] décision serveur invalide');\n      return privateJson({ ok: false, error: 'Le contexte de sécurité est temporairement indisponible.' }, 503);\n    }"""

    mutations: list[tuple[str, str, str]] = [
        ("réponse RPC brute", source.replace("security: publicSecurity", "security: data", 1), workflow),
        ("score de risque public", source.replace("return { outcome: outcome as 'allow' | 'block' };", "return { outcome: outcome as 'allow' | 'block', risk_score: source.risk_score } as any;", 1), workflow),
        ("raisons de risque publiques", source.replace("return { outcome: outcome as 'allow' | 'block' };", "return { outcome: outcome as 'allow' | 'block', risk_reasons: source.risk_reasons } as any;", 1), workflow),
        ("pays sérialisé dans la réponse", source.replace("geo_mode: geo.country ? 'trusted_coarse' : 'disabled'", "country: geo.country,\n      geo_mode: geo.country ? 'trusted_coarse' : 'disabled'", 1), workflow),
        ("IP brute", source.replace("const countryRaw = req.headers.get('cf-ipcountry') || '';", "const countryRaw = req.headers.get('cf-ipcountry') || '';\n  const ip = req.headers.get('x-forwarded-for');", 1), workflow),
        ("authentification retirée", source.replace("const user = await requiredUser(req);", "const user = { id: 'unsafe' };", 1), workflow),
        ("session vérifiée retirée", source.replace("const sessionId = sessionIdFromVerifiedRequest(req);", "const sessionId = 'unsafe';", 1), workflow),
        ("RPC retirée", source.replace("service_security_evaluate_context_session", "unsafe_context_rpc", 1), workflow),
        ("erreur brute journalisée", source.replace("console.error('[security-context] request failed', authRequired ? 'AUTH_REQUIRED' : 'UNEXPECTED');", "console.error('[security-context]', error);", 1), workflow),
        ("issue inconnue acceptée", source.replace("if (!SECURITY_OUTCOMES.has(outcome)) return null;", "if (!SECURITY_OUTCOMES.has(outcome)) return { outcome: 'allow' };", 1), workflow),
        ("RPC nulle transformée en allow", source.replace("const outcome = typeof source.outcome === 'string' ? source.outcome.trim() : '';", "const outcome = typeof source.outcome === 'string' ? source.outcome.trim() : 'allow';", 1), workflow),
        ("défi sans identifiant accepté", source.replace("if (!challengeId || !UUID_RE.test(challengeId)) return null;", "if (!challengeId) return { outcome: 'challenge', challenge_id: '00000000-0000-4000-8000-000000000000' };", 1), workflow),
        ("UUID de défi non vérifié", source.replace("if (!challengeId || !UUID_RE.test(challengeId)) return null;", "if (!challengeId) return null;", 1), workflow),
        ("allow retiré du contrat", source.replace("new Set(['allow', 'challenge', 'block'])", "new Set(['challenge', 'block'])", 1), workflow),
        ("block retiré du contrat", source.replace("new Set(['allow', 'challenge', 'block'])", "new Set(['allow', 'challenge'])", 1), workflow),
        ("validation fail-closed retirée", source.replace("if (!publicSecurity) {", "if (false) {", 1), workflow),
        ("503 fail-closed retiré", source.replace("}, 503);", "});", 1), workflow),
        ("push lancé avant validation", source.replace(fail_closed_block, reordered_block, 1), workflow),
        ("auto-test CI retiré", source, workflow.replace("python3 scripts/validate_security_context_response_v25.py --self-test", "echo self-test-retiré", 1)),
        ("chemin Edge retiré d'un trigger", source, workflow.replace("      - 'supabase/functions/security-context/index.ts'", "      - 'supabase/functions/security-context/index.disabled'", 1)),
    ]

    undetected: list[str] = []
    for name, mutated_source, mutated_workflow in mutations:
        if mutated_source == source and mutated_workflow == workflow:
            undetected.append(f"{name} (mutation non appliquée)")
            continue
        if not validate(mutated_source, mutated_workflow):
            undetected.append(name)
    if undetected:
        raise SystemExit("ÉCHEC auto-test, régressions non détectées: " + ", ".join(undetected))
    print(f"OK: {len(mutations)}/{len(mutations)} régressions security-context détectées")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    source = EDGE.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if args.self_test:
        self_test(source, workflow)
        return

    errors = validate(source, workflow)
    if errors:
        for error in errors:
            print(f"ERREUR: {error}")
        raise SystemExit(1)

    print("OK: security-context est minimal et fail-closed sur toute décision RPC ambiguë.")


if __name__ == "__main__":
    main()
