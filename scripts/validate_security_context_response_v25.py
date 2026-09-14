#!/usr/bin/env python3
"""Garde-fou A1 : la réponse publique de security-context reste minimale."""

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
        "allowlist publique": "function publicSecurityResult(data: unknown)",
        "projection de l'issue": "const result: { outcome: string; challenge_id?: string } = { outcome };",
        "challenge limité au défi": "if (outcome === 'challenge'",
        "projection utilisée sur HTTP": "security: publicSecurityResult(data)",
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

    response_start = source.find("return privateJson({\n      ok: true")
    response_end = source.find("\n    });", response_start)
    if response_start < 0 or response_end < 0:
        errors.append("Impossible d'isoler la réponse HTTP de succès.")
    else:
        response = source[response_start:response_end]
        for field in ("risk_score", "risk_reasons", "country", "region", "city", "latitude", "longitude"):
            if field in response:
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
    mutations: list[tuple[str, str, str]] = [
        ("réponse RPC brute", source.replace("security: publicSecurityResult(data)", "security: data", 1), workflow),
        ("score de risque public", source.replace("const result: { outcome: string; challenge_id?: string } = { outcome };", "const result: any = { outcome, risk_score: source.risk_score };", 1), workflow),
        ("raisons de risque publiques", source.replace("const result: { outcome: string; challenge_id?: string } = { outcome };", "const result: any = { outcome, risk_reasons: source.risk_reasons };", 1), workflow),
        ("pays dans la projection", source.replace("const result: { outcome: string; challenge_id?: string } = { outcome };", "const result: any = { outcome, country: source.country };", 1), workflow),
        ("IP brute", source.replace("const countryRaw = req.headers.get('cf-ipcountry') || '';", "const countryRaw = req.headers.get('cf-ipcountry') || '';\n  const ip = req.headers.get('x-forwarded-for');", 1), workflow),
        ("authentification retirée", source.replace("const user = await requiredUser(req);", "const user = { id: 'unsafe' };", 1), workflow),
        ("session vérifiée retirée", source.replace("const sessionId = sessionIdFromVerifiedRequest(req);", "const sessionId = 'unsafe';", 1), workflow),
        ("RPC retirée", source.replace("service_security_evaluate_context_session", "unsafe_context_rpc", 1), workflow),
        ("erreur brute journalisée", source.replace("console.error('[security-context] request failed', authRequired ? 'AUTH_REQUIRED' : 'UNEXPECTED');", "console.error('[security-context]', error);", 1), workflow),
        ("allowlist contournée", source.replace("security: publicSecurityResult(data)", "security: { outcome: data?.outcome, ...data }", 1), workflow),
        ("auto-test CI retiré", source, workflow.replace("python3 scripts/validate_security_context_response_v25.py --self-test", "echo self-test-retiré", 1)),
        ("chemin Edge retiré d'un trigger", source, workflow.replace("      - 'supabase/functions/security-context/index.ts'", "      - 'supabase/functions/security-context/index.disabled'", 1)),
    ]

    undetected: list[str] = []
    for name, mutated_source, mutated_workflow in mutations:
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

    print("OK: security-context expose seulement outcome/challenge_id et geo_mode; le détail du risque reste serveur.")


if __name__ == "__main__":
    main()
