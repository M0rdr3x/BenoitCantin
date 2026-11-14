#!/usr/bin/env python3
"""Fail closed if Netlify staging secrets escape their three approved steps.

Only inspects GitHub workflow source; no real credentials, deployment or network.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/deploy-netlify-staging.yml"
SECRETS = ("NETLIFY_AUTH_TOKEN", "NETLIFY_SITE_ID")
APPROVED_STEPS = (
    "Verrouiller ref, SHA, site et secrets",
    "Déployer le preview staging sans promotion",
    "Déployer le production-candidate sans promotion",
)
INSTALL_STEP = "Installer Netlify CLI sans identifiants"
CLI_BIN = '"$RUNNER_TEMP/netlify-cli-27.19.0/node_modules/.bin/netlify"'
OFFLINE_LINE = "          NPM_CONFIG_OFFLINE: 'true'"
STEP_LINE = re.compile(r"^      - name: ([^\n]+)$")
EXPRESSION = re.compile(r"\$\{\{\s*secrets\.(NETLIFY_AUTH_TOKEN|NETLIFY_SITE_ID)\s*\}\}")
ASSIGNMENT = re.compile(r"^\s*(NETLIFY_AUTH_TOKEN|NETLIFY_SITE_ID)\s*:")


def inspect(source: str) -> list[str]:
    errors: list[str] = []
    counts = {(step, secret): 0 for step in APPROVED_STEPS for secret in SECRETS}
    # Le lancement manuel de staging doit être impossible depuis une
    # branche de travail quelconque, même avec le bon expected_sha.
    branch_gates = re.findall(r"^    if:\s*(.*?)\s*$", source, re.MULTILINE)
    if branch_gates != ["github.ref == 'refs/heads/a1/web-release-transparency'"]:
        errors.append("la branche de staging doit être le seul ref explicitement approuvé")

    # GitHub configure GITHUB_REF_PROTECTED=true uniquement si ce ref est
    # soumis à une protection de branche / ruleset côté serveur. Aucune valeur
    # de secret ne doit être évaluée avant ce test fail-closed.
    if source.count("    environment: netlify-staging\n") != 1:
        errors.append("l'environnement netlify-staging doit être attaché au job")
    steps = re.findall(r"^      - name: ([^\n]+)$", source, re.MULTILINE)
    expected_first_step = "Refuser tout staging depuis une branche non protégée"
    if not steps or steps[0] != expected_first_step:
        errors.append("le contrôle de branche protégée doit être la toute première étape")
    gate_start = source.find("      - name: " + expected_first_step + "\n")
    gate_end = source.find("\n      - name:", gate_start + 1) if gate_start != -1 else -1
    gate_block = source[gate_start:gate_end] if gate_start >= 0 and gate_end > gate_start else ""
    expected_guard = 'if [ "${GITHUB_REF_PROTECTED:-false}" != "true" ]; then'
    if (
        gate_block.count(expected_guard) != 1
        or "          set -euo pipefail\n" not in gate_block
        or not re.search(r"(?m)^            exit 1\s*$", gate_block)
        or not re.search(r"(?m)^          fi\s*$", gate_block)
    ):
        errors.append("fail-closed GITHUB_REF_PROTECTED manquant ou affaibli")
    if source.count("GITHUB_REF_PROTECTED") != 1:
        errors.append("le contrôle de branche protégée doit être unique")
    if gate_start < 0 or gate_start > source.find("secrets.NETLIFY_AUTH_TOKEN"):
        errors.append("le contrôle de protection doit précéder tout accès aux secrets Netlify")

    # Les dépendances npm doivent être installées avant l'injection des secrets.
    # Le binaire local s'exécute ensuite sans lancer un gestionnaire de paquets.
    install_header = "      - name: " + INSTALL_STEP + "\n"
    audit_header = "      - name: Refuser les vulnérabilités graves Netlify avant tout secret\n"
    preflight_header = "      - name: Verrouiller ref, SHA, site et secrets\n"
    install_at = source.find(install_header)
    audit_at = source.find(audit_header)
    preflight_at = source.find(preflight_header)
    if (
        source.count(install_header) != 1
        or source.count(audit_header) != 1
        or not (0 <= install_at < audit_at < preflight_at)
    ):
        errors.append("installation et audit npm doivent précéder les secrets, dans cet ordre")
    install_block = source[install_at:audit_at] if 0 <= install_at < audit_at else ""
    audit_block = source[audit_at:preflight_at] if 0 <= audit_at < preflight_at else ""
    install_active = "\n".join(
        line for line in install_block.splitlines() if not line.lstrip().startswith("#")
    )
    required_install = (
        "          set -euo pipefail",
        '          cli_root="$RUNNER_TEMP/netlify-cli-27.19.0"',
        '          python3 scripts/validate_netlify_cli_lock.py',
        '          cp "$GITHUB_WORKSPACE/tools/netlify-cli/package.json" "$cli_root/package.json"',
        '          cp "$GITHUB_WORKSPACE/tools/netlify-cli/package-lock.json" "$cli_root/package-lock.json"',
        '          cd "$cli_root"',
        "          npm ci --ignore-scripts --no-audit --no-fund \\",
        '          : > "$cli_root/npm-user.conf"',
        '          : > "$cli_root/npm-global.conf"',
        '            --userconfig="$cli_root/npm-user.conf" --globalconfig="$cli_root/npm-global.conf" \\',
        "            --registry=https://registry.npmjs.org/",
        '          test -x "$cli_root/node_modules/.bin/netlify"',
        "manifest.version !== '27.19.0'",
        '          "$cli_root/node_modules/.bin/netlify" --version',
    )
    for marker in required_install:
        if install_active.count(marker) != 1:
            errors.append("installation Netlify sans secrets non conforme: " + marker)
    if "secrets." in install_active or re.search(r"(?m)^ *NETLIFY_(?:AUTH_TOKEN|SITE_ID):", install_active):
        errors.append("secrets injectés dans l'étape d'installation npm")
    # Le scan des avis publiés se produit lui aussi AVANT tout secret.
    audit_required = (
        "          set -euo pipefail",
        '          cli_root="$RUNNER_TEMP/netlify-cli-27.19.0"',
        "          audit_status=0",
        "          npm audit --json --omit=dev \\",
        "            --registry=https://registry.npmjs.org/ \\",
        '            > "$cli_root/netlify-audit.json" || audit_status=$?',
        '          python3 "$GITHUB_WORKSPACE/scripts/validate_netlify_cli_audit.py" \\',
        '            "$cli_root/netlify-audit.json" --exit-status "$audit_status"',
    )
    for item in audit_required:
        if audit_block.count(item) != 1:
            errors.append("audit npm pré-secret manquant ou affaibli : " + item)
    if (
        "secrets." in audit_block
        or re.search(r"(?m)^ *NETLIFY_(?:AUTH_TOKEN|SITE_ID):", audit_block)
        or "|| true" in audit_block
        or "continue-on-error: true" in source
    ):
        errors.append("audit npm doit être sans secrets et fail-closed")
    active_lines = [
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    ]
    npm_lines = [line for line in active_lines if re.search(r"(?<![\w-])npm\s+ci\b", line)]
    if len(npm_lines) != 1 or "npm ci --ignore-scripts --no-audit --no-fund" not in npm_lines[0]:
        errors.append("npm ci avec lockfile et scripts désactivés doit être unique")
    if any(re.search(r"(?<![\w-])(?:npx|npm\s+install|npm\s+exec|pnpm|yarn|corepack)\b", line) for line in active_lines):
        errors.append("installation ou gestionnaire de paquets dynamique interdit")

    for step_name in APPROVED_STEPS[1:]:
        header = "      - name: " + step_name + "\n"
        start = source.find(header)
        end = source.find("\n      - name:", start + len(header)) if start >= 0 else -1
        block = source[start:end] if start >= 0 and end > start else ""
        if block.count(OFFLINE_LINE) != 1 or block.count(CLI_BIN + " deploy") != 1:
            errors.append(step_name + ": binaire local et npm hors ligne obligatoires")
        if re.search(r"(?<![\w-])(?:npx|npm|pnpm|yarn|corepack)\s", block):
            errors.append(step_name + ": gestionnaire de paquets sous secrets interdit")

    # Netlify lit NETLIFY_AUTH_TOKEN et NETLIFY_SITE_ID depuis l'environnement.
    # Un jeton en argument --auth est visible dans les arguments des processus.
    cli_commands = re.findall(
        r'^\s*"\$RUNNER_TEMP/netlify-cli-27\.19\.0/node_modules/\.bin/netlify" deploy\b.*$',
        source, re.MULTILINE,
    )
    if len(cli_commands) != 2:
        errors.append("exactement deux déploiements Netlify draft attendus")
    for command in cli_commands:
        if re.search(r"--(?:auth|site|prod|prod-if-unlocked)\b", command):
            errors.append("arguments de credentials ou promotion live interdits dans netlify deploy")
        if "--no-build" not in command or "--json" not in command:
            errors.append("les déploiements staging doivent rester sans build externe et en JSON")

    # Un contrôle de non-vacuité local est le seul usage direct admissible
    # d'une valeur secrète dans le shell: aucun echo, argv, env-file ou log.
    shell_secret_lines = [
        line.strip() for line in source.splitlines()
        if re.search(r"\$(?:NETLIFY_AUTH_TOKEN|\{NETLIFY_AUTH_TOKEN\})", line)
        or re.search(r"\$(?:NETLIFY_SITE_ID|\{NETLIFY_SITE_ID\})", line)
    ]
    expected_check = 'if [ -z "$NETLIFY_AUTH_TOKEN" ] || [ -z "$NETLIFY_SITE_ID" ]; then'
    if shell_secret_lines != [expected_check]:
        errors.append("référence shell aux credentials hors du seul prévol de non-vacuité")
    current_step: str | None = None
    in_step_env = False
    for number, line in enumerate(source.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        step = STEP_LINE.fullmatch(line)
        if step:
            current_step = step.group(1)
            in_step_env = False
        elif line.strip():
            if indent < 6:
                current_step = None
                in_step_env = False
            elif indent == 8:
                in_step_env = line.strip() == "env:"
            elif indent == 6:
                current_step = None
                in_step_env = False
        references = EXPRESSION.findall(line)
        assignment = ASSIGNMENT.match(line)
        if not (references or assignment):
            continue
        if assignment:
            secret = assignment.group(1)
            expected = "          " + secret + ": ${{ secrets." + secret + " }}"
            safe = (
                current_step in APPROVED_STEPS
                and in_step_env
                and line.rstrip() == expected
                and len(references) == 1
                and references[0] == secret
            )
            if safe:
                counts[(current_step, secret)] += 1
            else:
                errors.append(f"ligne {number}: affectation {secret} hors de son env de step approuvé")
        elif references:
            errors.append(f"ligne {number}: interpolation de secret Netlify hors env approuvé")
    for (step, secret), count in counts.items():
        if count != 1:
            errors.append(f"{step}: {secret} doit apparaître exactement une fois (observé: {count})")
    for number, line in enumerate(source.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        if re.search(r"\bsecrets\s*\[\s*['\"](?:NETLIFY_AUTH_TOKEN|NETLIFY_SITE_ID)['\"]\s*\]", line):
            errors.append(f"ligne {number}: accès dynamique au secret Netlify interdit")
    return errors


def self_test(source: str) -> None:
    if errors := inspect(source):
        raise AssertionError("le workflow de référence ne respecte pas le contrat: " + "; ".join(errors))
    token = "          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}\n"
    site = "          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}\n"
    mutants = {
        "job-level exposure": source.replace(
            "    env:\n", "    env:\n      NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}\n", 1
        ),
        "setup-node exposure": source.replace(
            "      - name: Configurer Node\n",
            "      - name: Configurer Node\n        env:\n" + token, 1,
        ),
        "shell interpolation": source.replace(
            "          set -euo pipefail\n",
            "          echo '${{ secrets.NETLIFY_AUTH_TOKEN }}'\n          set -euo pipefail\n", 1,
        ),
        "replaced token binding": source.replace(
            token, "          NETLIFY_AUTH_TOKEN: ${{ inputs.token }}\n", 1
        ),
        "removed site binding": source.replace(site, "", 1),
        "token bracket lookup": source.replace(
            "          set -euo pipefail\n",
            "          echo '${{ secrets[\"NETLIFY_AUTH_TOKEN\"] }}'\n          set -euo pipefail\n", 1,
        ),
        "branch wildcard restored": source.replace(
            "    if: github.ref == 'refs/heads/a1/web-release-transparency'",
            "    if: startsWith(github.ref, 'refs/heads/a1/web-release-')", 1,
        ),
        "credential leaked via process args": source.replace(
            CLI_BIN + " deploy", CLI_BIN + ' deploy --auth "$NETLIFY_AUTH_TOKEN"', 1,
        ),
        "production promotion flag": source.replace(
            CLI_BIN + " deploy", CLI_BIN + " deploy --prod", 1,
        ),
        "shell secret echo": source.replace(
            "          set -euo pipefail\n",
            "          echo \"$NETLIFY_AUTH_TOKEN\"\n          set -euo pipefail\n", 1,
        ),
        "removed deployment": source.replace(
            CLI_BIN + " deploy", "false # deployment removed", 1,
        ),
        "installation retirée": source.replace(
            "      - name: " + INSTALL_STEP + "\n", "      - name: Installation non vérifiée\n", 1,
        ),
        "installation après les secrets": source.replace(
            "      - name: " + INSTALL_STEP + "\n", "      - name: CLI installée ailleurs\n", 1,
        ),
        "scripts npm autorisés": source.replace(
            "npm ci --ignore-scripts", "npm ci", 1,
        ),
        "lockfile non validé": source.replace(
            "python3 scripts/validate_netlify_cli_lock.py", "true # audit skipped", 1,
        ),
        "lockfile non copié": source.replace(
            'cp "$GITHUB_WORKSPACE/tools/netlify-cli/package-lock.json" "$cli_root/package-lock.json"',
            'echo "lockfile missing"', 1,
        ),
        "npm ci remplacé par install": source.replace(
            "npm ci --ignore-scripts", "npm install --ignore-scripts", 1,
        ),
        "smoke CLI supprimé": source.replace(
            '"$cli_root/node_modules/.bin/netlify" --version', "true # no CLI smoke", 1,
        ),
        "audit npm étape supprimée": source.replace(
            "      - name: Refuser les vulnérabilités graves Netlify avant tout secret",
            "      - name: Ne rien auditer", 1,
        ),
        "audit npm commande supprimée": source.replace(
            "npm audit --json --omit=dev", "echo audit skipped", 1,
        ),
        "audit npm parseur supprimé": source.replace(
            'python3 "$GITHUB_WORKSPACE/scripts/validate_netlify_cli_audit.py"',
            "true # audit bypassed", 1,
        ),
        "audit npm exit ignoré": source.replace(
            "|| audit_status=$?", "|| true", 1,
        ),
        "audit npm jeton injecté": source.replace(
            "      - name: Refuser les vulnérabilités graves Netlify avant tout secret\n",
            "      - name: Refuser les vulnérabilités graves Netlify avant tout secret\n"
            + "        env:\n"
            + "          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}\n", 1,
        ),
        "dépôt npm inconnu": source.replace(
            "--registry=https://registry.npmjs.org/", "--registry=https://example.invalid/", 1,
        ),
        "npmrc utilisateur accessible": source.replace(
            '--userconfig="$cli_root/npm-user.conf"', '--userconfig=$HOME/.npmrc', 1,
        ),
        "binaire CLI détourné": source.replace(
            CLI_BIN + " deploy", "netlify deploy", 1,
        ),
        "npm offline désactivé": source.replace(OFFLINE_LINE + "\n", "", 1),
        "npm avec secrets": source.replace(
            "      - name: " + INSTALL_STEP + "\n",
            "      - name: " + INSTALL_STEP + "\n        env:\n"
            + "          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}\n", 1,
        ),
        "npx pendant déploiement": source.replace(
            CLI_BIN + " deploy", "npx --yes netlify-cli@27.19.0 deploy", 1,
        ),
        "version binaire modifiée": source.replace(
            "manifest.version !== '27.19.0'", "manifest.version !== '999.0.0'", 1,
        ),
        "staging environment removed": source.replace(
            "    environment: netlify-staging\n", "", 1,
        ),
        "staging environment renamed": source.replace(
            "    environment: netlify-staging\n", "    environment: staging-unreviewed\n", 1,
        ),
        "protected-ref test removed": source.replace(
            'if [ "${GITHUB_REF_PROTECTED:-false}" != "true" ]; then',
            'if [ "false" != "true" ]; then', 1,
        ),
        "protected-ref check inverted": source.replace(
            'if [ "${GITHUB_REF_PROTECTED:-false}" != "true" ]; then',
            'if [ "${GITHUB_REF_PROTECTED:-false}" == "true" ]; then', 1,
        ),
        "protected-ref exit removed": source.replace(
            '            exit 1\n          fi\n\n      - name: Récupérer le dépôt',
            '            echo "CONTINUE"\n          fi\n\n      - name: Récupérer le dépôt', 1,
        ),
        "protected-ref check not first": source.replace(
            "      - name: Refuser tout staging depuis une branche non protégée\n",
            "      - name: Contrôle vide\n", 1,
        ),
    }
    for label, mutant in mutants.items():
        if mutant == source or not inspect(mutant):
            raise AssertionError(f"mutation non détectée: {label}")
    print(f"OK: contrat d'isolation et {len(mutants)} mutations adversariales vérifiées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    source = WORKFLOW.read_text(encoding="utf-8")
    if args.self_test:
        self_test(source)
        return 0
    errors = inspect(source)
    for error in errors:
        print("ERREUR:", error)
    if errors:
        return 1
    print("OK: jeton et identifiant Netlify limités aux trois étapes autorisées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
