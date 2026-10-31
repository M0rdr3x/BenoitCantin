#!/usr/bin/env python3
"""Contrôle bloquant de la RPC security-context avant tout déploiement Edge.

Ne lit que les métadonnées de pg_catalog avec une requête strictement SELECT.
Les valeurs du serveur et les secrets ne sont jamais reproduits dans les logs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "supabase/functions/security-context/index.ts"
WORKFLOW = ROOT / ".github/workflows/supabase-production-preflight.yml"
GATE_NAME = "Vérifier le contrat RPC security-context avant publication Edge"
EXPECTED_RPC = "service_security_evaluate_context_session"

QUERY = """SELECT EXISTS (
  SELECT 1
  FROM pg_catalog.pg_proc AS fn
  JOIN pg_catalog.pg_namespace AS ns ON ns.oid = fn.pronamespace
  WHERE fn.oid = pg_catalog.to_regprocedure(
    'public.service_security_evaluate_context_session(uuid,text,text,text,text,text,text,text,uuid)'
  )
    AND ns.nspname = 'public'
    AND fn.proname = 'service_security_evaluate_context_session'
    AND fn.prosecdef
    AND fn.prorettype = 'pg_catalog.jsonb'::pg_catalog.regtype
    AND pg_catalog.has_function_privilege('service_role', fn.oid, 'EXECUTE')
    AND NOT pg_catalog.has_function_privilege('anon', fn.oid, 'EXECUTE')
    AND NOT pg_catalog.has_function_privilege('authenticated', fn.oid, 'EXECUTE')
    AND fn.prosrc LIKE '%security_rebind_service_session%'
    AND fn.prosrc LIKE '%request_session_id%'
) AS security_context_rpc_ready"""


def validate_source(source: str) -> list[str]:
    errors = []
    imports = re.findall(r"""\bservice\.rpc\s*\(\s*['"]([^'"]+)['"]""", source)
    if imports != [EXPECTED_RPC]:
        errors.append("RPC de sécurité non approuvée, absente ou dupliquée")
    for marker in (
        "const sessionId = sessionIdFromVerifiedRequest(req);",
        "p_session_id: sessionId",
        "const user = await requiredUser(req);",
        "if (error) throw error;",
    ):
        if marker not in source:
            errors.append("Contrat de liaison de session/JWT incomplet")
            break
    return errors


def validate_result(data: object) -> list[str]:
    # Un seul booléen SQL True réel est accepté. Aucun repli permissif.
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        return ["Structure de réponse SQL distante non fiable"]
    if set(data[0]) != {"security_context_rpc_ready"}:
        return ["Colonne booléenne de sécurité inattendue"]
    if data[0]["security_context_rpc_ready"] is not True:
        return ["RPC de session absente ou protections SQL insuffisantes"]
    return []


def extract_step(text: str, name: str) -> str:
    marker = "      - name: " + name + "\n"
    start = text.find(marker)
    if start < 0:
        return ""
    end = text.find("\n      - name: ", start + len(marker))
    return text[start:] if end < 0 else text[start:end]


def validate_workflow(text: str) -> list[str]:
    errors = []
    step = extract_step(text, GATE_NAME)
    if not step:
        return ["Étape de vérification RPC absente"]
    positions = {
        "migrate": text.find("      - name: Appliquer les migrations de production depuis le workspace protégé"),
        "audit": text.find("      - name: Auditer les fonctions SQL après migrations"),
        "gate": text.find("      - name: " + GATE_NAME),
        "secrets": text.find("      - name: Garantir les secrets Edge Functions indispensables"),
        "deploy": text.find("      - name: Déployer toutes les Edge Functions du workspace protégé"),
    }
    if any(v < 0 for v in positions.values()) or not (
        positions["migrate"] < positions["audit"] < positions["gate"]
        < positions["secrets"] < positions["deploy"]
    ):
        errors.append("Ordre migration/audit/vérification/Edge non garanti")
    conditions = (
        "if: " + chr(36) + "{{ github.event_name == 'workflow_dispatch' && inputs.apply == true && steps.auth.outputs.ready == 'true' }}",
        "SUPABASE_ACCESS_TOKEN: " + chr(36) + "{{ secrets.SUPABASE_ACCESS_TOKEN }}",
        "set -euo pipefail",
        "scripts/validate_security_context_deployment_gate.py --check-source",
        "scripts/validate_security_context_deployment_gate.py --write-request",
        "scripts/validate_security_context_deployment_gate.py --check-response",
        "--proto '=https'",
        "--tlsv1.2",
        "--fail-with-body",
        "--data-binary",
        "/database/query/read-only",
    )
    for marker in conditions:
        if marker not in step:
            errors.append("Vérification RPC non fail-closed ou incomplète")
    if any(bad in step for bad in ("continue-on-error:", "|| true", "set +e")):
        errors.append("Erreur RPC ignorée : interdiction")
    if text.count("supabase functions deploy --project-ref") != 1:
        errors.append("Nombre de points de déploiement Edge inattendu")
    for marker in (
        "      - 'scripts/validate_security_context_deployment_gate.py'",
        "      - 'scripts/test_security_context_deployment_gate.py'",
    ):
        if text.count(marker) != 2:
            errors.append("Contrat RPC absent des déclencheurs PR et push")
    return errors


def validate_contract() -> list[str]:
    try:
        source = SOURCE.read_text("utf-8")
        workflow = WORKFLOW.read_text("utf-8")
    except (OSError, UnicodeError):
        return ["Sources de sécurité de production absentes"]
    return validate_source(source) + validate_workflow(workflow)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-source", type=Path)
    mode.add_argument("--check-response", type=Path)
    mode.add_argument("--write-request", type=Path)
    mode.add_argument("--check-contract", action="store_true")
    args = ap.parse_args()
    if args.write_request:
        args.write_request.write_text(json.dumps({"query": QUERY}) + "\n", "utf-8")
        print("PASS: requête de métadonnées SQL en lecture seule préparée")
        return 0
    if args.check_source:
        try:
            errors = validate_source(args.check_source.read_text("utf-8"))
        except (OSError, UnicodeError):
            errors = ["Code source Edge absent ou illisible"]
    elif args.check_response:
        try:
            payload = json.loads(args.check_response.read_text("utf-8"))
            errors = validate_result(payload)
        except (OSError, UnicodeError, ValueError):
            errors = ["Réponse SQL de sécurité distante illisible"]
    else:
        errors = validate_contract()
    if errors:
        for error in errors:
            print("NO_GO: " + error, file=sys.stderr)
        return 1
    print("PASS: contrat RPC session vérifié")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
