#!/usr/bin/env python3
"""Contrat fail-closed du prévol Supabase Auth en lecture seule, sans réseau."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/sinjira-auth-email-production-preflight.yml"
JOB = "    if: ${{ github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' && github.ref_protected == true }}\n"
REF = "          ref: ${{ github.sha }}\n"
SECRET = "          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n"
ACTION = "uses: actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd"
HEADERS = (
    "Confirmation explicite du mode lecture seule",
    "Refuser toute référence de production non protégée",
    "Checkout de main",
    "Vérifier l'empreinte exacte du checkout",
    "Vérifier Python 3.12 du runner Ubuntu 24.04",
    "Vérifier la protection GitHub et SHA live avant tout jeton",
    "Lire seulement la configuration Auth distante",
)
GUARD = 'test "${GITHUB_REF_PROTECTED:-}" = \x27true\x27'


def inspect(source: str) -> list[str]:
    errors: list[str] = []
    marker = "  production-inspection:\n"
    if source.count(marker) != 1:
        return ["Job production-inspection absent ou dupliqué"]
    local, remote = source.split(marker, 1)
    if source.count(JOB) != 1:
        errors.append("Condition workflow_dispatch/main protégée requise")
    if source.count("    environment: production\n") != 1:
        errors.append("Un environnement production est requis")
    if "    permissions:\n      contents: read\n" not in remote:
        errors.append("Jeton GitHub limité à contents: read")
    if source.count("  workflow_dispatch:\n") != 1:
        errors.append("Déclenchement manuel explicite requis")
    if "secrets." in local:
        errors.append("Secret interdit dans les tests PR")
    if source.count(SECRET) != 1 or source.count("secrets.SUPABASE_ACCESS_TOKEN") != 1:
        errors.append("Un unique jeton Supabase step-scoped est requis")
    if source.count("python3 scripts/preflight_sinjira_auth_email.py --remote") != 1:
        errors.append("Une seule inspection distante est autorisée")
    for bad in ("continue-on-error:", "persist-credentials: true", "--request PATCH",
                "--request POST", "--request PUT", "--request DELETE", "  pull_request_target:"):
        if bad in source:
            errors.append("Capacité dangereuse: " + bad)

    names = ["      - name: " + name + "\n" for name in HEADERS]
    positions = [remote.find(name) for name in names]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        errors.append("Étapes de contrôle manquantes ou mal ordonnées avant jeton")
        return errors
    if any(remote.count(name) != 1 for name in names):
        errors.append("Étape de contrôle production dupliquée")
    blocks = {
        name: remote[positions[i]:positions[i+1] if i+1 < len(names) else len(remote)]
        for i, name in enumerate(HEADERS)
    }
    if "PREFLIGHT-READ-ONLY" not in blocks[HEADERS[0]]:
        errors.append("Confirmation manuelle absente")
    if ("test \"$GITHUB_REF\" = 'refs/heads/main'" not in blocks[HEADERS[1]]
            or GUARD not in blocks[HEADERS[1]]):
        errors.append("Contrôle initial ref et branche protégée absent")
    if (REF not in blocks[HEADERS[2]]
            or "persist-credentials: false" not in blocks[HEADERS[2]]
            or "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803" not in blocks[HEADERS[2]]):
        errors.append("Checkout immuable et sans credentials obligatoire")
    if ('test "$(git rev-parse --verify HEAD)" = "$GITHUB_SHA"' not in blocks[HEADERS[3]]
            or GUARD not in blocks[HEADERS[3]]):
        errors.append("Vérification du SHA checkout et ref protégée absente")
    if "secrets." in "".join(blocks[name] for name in HEADERS[:-1]):
        errors.append("Jeton injecté avant vérification SHA live")
    live = blocks[HEADERS[5]]
    for required in (
        ACTION,
        "process.env.GITHUB_REF_PROTECTED !== 'true'",
        "github.rest.repos.getBranch({ owner, repo, branch: 'main' })",
        "branch.protected !== true",
        "branch.commit?.sha !== context.sha",
    ):
        if required not in live:
            errors.append("Contrôle live incomplet: " + required)
    if live.count("core.setFailed(") != 3 or "secrets." in live:
        errors.append("Contrôle live doit refuser trois erreurs sans accès au jeton")
    if (SECRET not in blocks[HEADERS[6]]
            or "run: python3 scripts/preflight_sinjira_auth_email.py --remote" not in blocks[HEADERS[6]]):
        errors.append("Lecture Auth et secret limités à la dernière étape")
    if remote.count("uses: actions/github-script@") != 1:
        errors.append("github-script épinglé et unique obligatoire")
    return errors


def self_test(source: str) -> None:
    assert not inspect(source), "Version initiale rejetée: " + "; ".join(inspect(source))
    mutants = {
        "job sans garde": source.replace(JOB, "    if: true\n", 1),
        "ref non protégée": source.replace("github.ref_protected == true", "true", 1),
        "environnement manquant": source.replace("    environment: production\n", "", 1),
        "checkout flottant": source.replace(REF, "          ref: main\n", 1),
        "preuve HEAD retirée": source.replace('test "$(git rev-parse --verify HEAD)" = "$GITHUB_SHA"', "true", 1),
        "ref initial détourné": source.replace("test \"$GITHUB_REF\" = 'refs/heads/main'", "true", 1),
        "protection initiale absente": source.replace(GUARD, "true", 1),
        "contrôle live retiré": source.replace("      - name: " + HEADERS[5] + "\n",
                                              "      - name: Contrôle retiré\n", 1),
        "action live flottante": source.replace(ACTION, "uses: actions/github-script@v8", 1),
        "protection live retirée": source.replace("branch.protected !== true", "false", 1),
        "SHA live retiré": source.replace("branch.commit?.sha !== context.sha", "false", 1),
        "ref live ignorée": source.replace("process.env.GITHUB_REF_PROTECTED !== 'true'", "false", 1),
        "sortie d'échec neutralisée": source.replace(
            "core.setFailed('Refus du prévol Auth : main a changé depuis la validation.')",
            "core.info('SHA ignoré')", 1),
        "secret ajouté à un test PR": source.replace(
            "      - name: Auto-tests sans accès production\n",
            "      - name: Auto-tests sans accès production\n        env:\n" + SECRET, 1),
        "secret ajouté à la confirmation": source.replace(
            "      - name: Confirmation explicite du mode lecture seule\n",
            "      - name: Confirmation explicite du mode lecture seule\n        env:\n" + SECRET, 1),
        "secret supprimé": source.replace(SECRET, "", 1),
        "inspection répétée": source.replace(
            "run: python3 scripts/preflight_sinjira_auth_email.py --remote",
            "run: python3 scripts/preflight_sinjira_auth_email.py --remote && "
            "python3 scripts/preflight_sinjira_auth_email.py --remote", 1),
        "masquage d'échec": source.replace(
            "    timeout-minutes: 5\n    permissions:",
            "    timeout-minutes: 5\n    continue-on-error: true\n    permissions:", 1),
    }
    for label, mutant in mutants.items():
        if mutant == source:
            raise AssertionError("Mutation sans effet: " + label)
        if not inspect(mutant):
            raise AssertionError("Mutation non rejetée: " + label)
    print(f"PASS: {len(mutants)} mutations dangereuses détectées sans secret ni réseau.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    source = WORKFLOW.read_text(encoding="utf-8")
    if args.self_test:
        self_test(source)
        return 0
    errors = inspect(source)
    if errors:
        for issue in errors:
            print("ERREUR:", issue)
        return 1
    print("PASS: prévol Auth protégé, SHA exact et secret borné à l'étape distante.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
