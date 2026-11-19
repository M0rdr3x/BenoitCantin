#!/usr/bin/env python3
"""Fail-closed guard for process-argument-safe Supabase read-only GETs.

No tokens, network, SQL or user data are needed to validate the workflows.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "sinjira-v25-production-deploy.yml": "Télécharger l'historique V25 en lecture seule",
    "sinjira-v25-employment-production.yml": "Télécharger l'historique Emploi en lecture seule",
    "sinjira-v25-personal-ai-production-readiness.yml": "Télécharger l'historique distant en lecture seule",
}
EXPECTED_URL = "https://api.supabase.com/v1/projects/gpvivleexywljowcqkru/database/migrations"
PIPE = r"""printf 'Authorization: Bearer %s\n' "$SUPABASE_ACCESS_TOKEN" | curl -q """
FORMAT_GUARD = 'if [[ ! "$SUPABASE_ACCESS_TOKEN" =~ ^[-A-Za-z0-9._~+/=]+$ ]]; then'
TOKEN_ENV = '          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}'
CLI_COMMAND = re.compile(r"\bcurl\s+(?:-[^\s]*\s*)+", re.MULTILINE)


def download_step(source: str, name: str) -> str:
    header = "      - name: " + name + "\n"
    start = source.find(header)
    if start == -1 or source.count(header) != 1:
        return ""
    end = source.find("\n      - name:", start + len(header))
    return source[start:] if end == -1 else source[start:end]


def inspect(name: str, source: str) -> list[str]:
    errors: list[str] = []
    step = download_step(source, WORKFLOWS[name])
    if not step:
        return [name + ": étape GET approuvée manquante"]
    if source.count(EXPECTED_URL) != 1 or step.count(EXPECTED_URL) != 1:
        errors.append("URL de gestion Supabase doit apparaître une fois dans l'étape GET")
    if TOKEN_ENV not in step:
        errors.append("jeton non injecté via env d'étape")
    if step.count(PIPE) != 1 or source.count(PIPE) != 1:
        errors.append("l'en-tête Bearer doit être envoyé une fois par printf/pipe vers curl -q")
    if step.count(FORMAT_GUARD) != 1 or step.count("set -euo pipefail") != 1:
        errors.append("validation fail-closed du format token et pipefail requises")
    if step.count("--header @-") != 1:
        errors.append("curl doit charger l'en-tête Authorization depuis stdin")
    if "--header 'Accept: application/json'" not in step:
        errors.append("en-tête Accept JSON requis")
    if "--proto '=https'" not in step or "--request GET" not in step:
        errors.append("seule une lecture GET HTTPS explicite est autorisée")
    if len(re.findall(r"\bcurl\s+(?:-[^\s]*\s*)+", source)) != 1:
        errors.append("une seule commande curl est permise dans ce workflow")
    # No positional token expansion, accidental logging, curlrc or extra HTTP requests.
    if re.search(r'--header\s+["\x27]?Authorization\s*:\s*Bearer', source, re.I):
        errors.append("Authorization dans les arguments de curl interdit")
    if any(part in step for part in ("--location", "--proxy ", "--trace", "--verbose", "set -x", "curl --", "curl -K", "curl --config")):
        errors.append("redirection, proxy, trace ou curl sans -q interdits")
    if re.search(r'\b(?:echo|printf|cat|tee)\s+[^\n]*\$SUPABASE_ACCESS_TOKEN', step.replace(PIPE, "")):
        errors.append("affichage potentiel du jeton hors pipe approuvé")
    return [f"{name}: {message}" for message in errors]


def self_test(sources: dict[str, str]) -> None:
    total = 0
    for name, source in sources.items():
        if findings := inspect(name, source):
            raise AssertionError("référence invalide: " + "; ".join(findings))
        mutants = {
            "token dans argv": source.replace("--header @-", '--header "Authorization: Bearer $SUPABASE_ACCESS_TOKEN"', 1),
            "sans pipe": source.replace(PIPE, "curl -q ", 1),
            "curlrc": source.replace("curl -q ", "curl ", 1),
            "en-têtes non bornés": source.replace(FORMAT_GUARD, "if true; then", 1),
            "HTTP POST": source.replace("--request GET", "--request POST", 1),
            "HTTPS libre": source.replace("--proto '=https'", "--proto '=http,https'", 1),
            "redirection": source.replace("--header @-", "--location --header @-", 1),
            "traçage": source.replace("--header @-", "--trace-ascii - --header @-", 1),
            "header stdin retiré": source.replace("--header @-", "--header 'Accept: application/json'", 1),
            "endpoint détourné": source.replace(EXPECTED_URL, "https://example.invalid/migrations", 1),
        }
        for label, mutated in mutants.items():
            if mutated == source or not inspect(name, mutated):
                raise AssertionError(f"mutation non détectée: {name}: {label}")
            total += 1
    print(f"OK: {len(sources)} GET Supabase et {total} mutants adversariaux refusés.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    sources = {
        name: (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        for name in WORKFLOWS
    }
    if args.self_test:
        self_test(sources)
        return 0
    issues = [item for name, source in sources.items() for item in inspect(name, source)]
    for item in issues:
        print("ERREUR:", item)
    if issues:
        return 1
    print(f"OK: {len(sources)} GET Supabase sans Bearer dans argv ni .curlrc.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
