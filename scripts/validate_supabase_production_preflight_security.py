#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "supabase-production-preflight.yml"

SELF_TEST = "python scripts/test_supabase_production_preflight_security.py"
SELF_CHECK = "python scripts/validate_supabase_production_preflight_security.py"
EXPECTED_RUNNER = "    runs-on: ubuntu-24.04"
EXPECTED_PYTHON = "          python-version: '3.12.14'"
CONFIRMATION = "APPLY-SUPABASE-PRODUCTION"

PINNED_ACTIONS = {
    "actions/checkout": "d23441a48e516b6c34aea4fa41551a30e30af803",
    "actions/setup-python": "ece7cb06caefa5fff74198d8649806c4678c61a1",
    "supabase/setup-cli": "3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
}

REMOTE_JOB_GUARD = "    if: ${{ github.event_name == 'workflow_dispatch' }}"
APPLY_JOB_GUARD = (
    "    if: ${{ github.event_name == 'workflow_dispatch' && inputs.apply == true && "
    "inputs.confirmation == 'APPLY-SUPABASE-PRODUCTION' && github.ref == 'refs/heads/main' }}"
)
REMOTE_STEP_GUARD = "if: ${{ github.event_name == 'workflow_dispatch' && steps.auth.outputs.ready == 'true' }}"
APPLY_STEP_GUARD = "if: ${{ github.event_name == 'workflow_dispatch' && inputs.apply == true && steps.auth.outputs.ready == 'true' }}"

REMOTE_STEPS = (
    "Auditer l’inventaire Edge Functions de production",
    "Lier le projet de production dans le workspace protégé",
    "Exporter l'historique exact des migrations de production",
    "Publier l'historique distant comme artefact de prévol",
    "Auditer les fonctions SQL déjà en production",
    "Comparer l'historique des migrations",
    "Prévisualiser les migrations sans modifier la production",
)

APPLY_STEPS = (
    "Appliquer les migrations de production depuis le workspace protégé",
    "Auditer les fonctions SQL après migrations",
    "Garantir les secrets Edge Functions indispensables",
    "Déployer toutes les Edge Functions du workspace protégé",
    "Vérifier les Edge Functions déployées",
    "Vérifier l'historique et le dry-run après déploiement",
)

REMOTE_REQUIREMENTS = {
    "Détecter les secrets de connexion Supabase": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Auditer l’inventaire Edge Functions de production": ("SUPABASE_ACCESS_TOKEN",),
    "Lier le projet de production dans le workspace protégé": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Exporter l'historique exact des migrations de production": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Auditer les fonctions SQL déjà en production": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Comparer l'historique des migrations": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Prévisualiser les migrations sans modifier la production": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
}

APPLY_REQUIREMENTS = {
    "Détecter les secrets de connexion Supabase pour l'application": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Revalider la cible production après approbation": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Appliquer les migrations de production depuis le workspace protégé": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Auditer les fonctions SQL après migrations": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Garantir les secrets Edge Functions indispensables": ("SUPABASE_ACCESS_TOKEN", "OPTIONAL_RESEND_API_KEY"),
    "Déployer toutes les Edge Functions du workspace protégé": ("SUPABASE_ACCESS_TOKEN",),
    "Vérifier les Edge Functions déployées": ("SUPABASE_ACCESS_TOKEN",),
    "Vérifier l'historique et le dry-run après déploiement": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
}


def job_block(text: str, name: str) -> str:
    marker = f"  {name}:\n"
    start = text.find(marker)
    if start < 0:
        return ""
    following = re.search(r"(?m)^  [A-Za-z0-9_-]+:\n", text[start + len(marker):])
    if following is None:
        return text[start:]
    end = start + len(marker) + following.start()
    return text[start:end]


def step_block(job: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = job.find(marker)
    if start < 0:
        return ""
    following = job.find("\n      - name: ", start + len(marker))
    return job[start:] if following < 0 else job[start:following]


def has_exact_line(block: str, line: str) -> bool:
    return line in block.splitlines()


def require_step_env(errors: list[str], job: str, name: str, required: tuple[str, ...]) -> None:
    block = step_block(job, name)
    if not block:
        errors.append(f"Étape distante obligatoire absente: {name}")
        return
    if "\n        env:\n" not in block:
        errors.append(f"L'étape distante n'a pas d'env local: {name}")
        return
    for key in required:
        if f"          {key}:" not in block:
            errors.append(f"Secret/env {key} non borné à l'étape: {name}")


def validate_text(text: str) -> list[str]:
    errors: list[str] = []

    if "permissions:\n  contents: read\n" not in text:
        errors.append("Le workflow doit conserver permissions.contents en lecture seule.")
    if "contents: write" in text:
        errors.append("Une permission contents: write est interdite dans le workflow production.")
    if "continue-on-error:" in text:
        errors.append("continue-on-error est interdit dans ce workflow production fail-closed.")
    if re.search(r"(^|\n)\s*set\s+-x(?:\s|$)", text):
        errors.append("set -x est interdit afin de réduire le risque d'exposition de secrets.")
    if "ubuntu-latest" in text:
        errors.append("ubuntu-latest est interdit pour ce workflow production sensible.")

    jobs = {
        name: job_block(text, name)
        for name in ("local-preflight", "remote-preflight", "apply-production")
    }
    for name, block in jobs.items():
        if not block:
            errors.append(f"Job de frontière obligatoire absent: {name}")

    if text.count(EXPECTED_RUNNER) != 3:
        errors.append("Les trois jobs doivent utiliser exactement ubuntu-24.04.")
    if text.count(EXPECTED_PYTHON) != 3:
        errors.append("Les trois jobs doivent figer Python exactement à 3.12.14.")
    if text.count("          persist-credentials: false") != 3:
        errors.append("Les trois checkouts doivent conserver persist-credentials: false.")

    uses = re.findall(r"(?m)^\s*-?\s*uses:\s+(\S+)", text)
    if not uses:
        errors.append("Aucune action réutilisable détectée.")
    allowed = {f"{action}@{sha}" for action, sha in PINNED_ACTIONS.items()}
    for target in uses:
        if target not in allowed:
            errors.append(f"Action réutilisable non approuvée ou non immuable: {target}")
    for action, sha in PINNED_ACTIONS.items():
        if f"uses: {action}@{sha}" not in text:
            errors.append(f"Action épinglée attendue absente: {action}@{sha}")

    for trigger_path in (
        "      - 'scripts/validate_supabase_production_preflight_security.py'",
        "      - 'scripts/test_supabase_production_preflight_security.py'",
        "      - '.github/workflows/supabase-production-preflight.yml'",
        "      - 'docs/SUPABASE_PRODUCTION_RUNBOOK.md'",
    ):
        if text.count(trigger_path) < 2:
            errors.append(f"Chemin critique absent des déclencheurs PR/push: {trigger_path.strip()}")

    if "      confirmation:" not in text or CONFIRMATION not in text or 'default: "PREFLIGHT_ONLY"' not in text:
        errors.append("L'entrée de confirmation textuelle production est absente ou incomplète.")
    if "group: supabase-production-${{ github.event_name == 'workflow_dispatch' && 'manual' || github.ref }}" not in text:
        errors.append("Les lancements manuels production doivent partager une concurrence sérialisée.")

    local = jobs["local-preflight"]
    if local:
        if "${{ secrets." in local:
            errors.append("Le prévol local ne doit référencer aucun secret production.")
        if re.search(r"(?m)^\s+supabase\s", local) or "&& supabase " in local:
            errors.append("Le prévol local ne doit exécuter aucune commande Supabase CLI.")
        if "environment:" in local:
            errors.append("Le prévol local ne doit pas dépendre de l'environment production.")
        setup_at = local.find(f"uses: actions/setup-python@{PINNED_ACTIONS['actions/setup-python']}")
        self_test_at = local.find(SELF_TEST)
        self_check_at = local.find(SELF_CHECK)
        validate_at = local.find("- name: Vérifier le dépôt Supabase")
        if min(setup_at, self_test_at, self_check_at, validate_at) < 0:
            errors.append("La chaîne locale Python → auto-test → contrat → validations est incomplète.")
        elif not setup_at < self_test_at < self_check_at < validate_at:
            errors.append("L'ordre doit rester Python → auto-test sécurité → contrat sécurité → validations Supabase.")
        for command in (
            "python scripts/validate_supabase.py",
            "python scripts/validate_edge_function_inventory.py",
            "python scripts/validate_social_rls_contract.py",
            "python scripts/validate_production_migration_ledger.py",
            "python scripts/build_supabase_production_workspace.py --output .prod-workspace/supabase",
        ):
            if command not in local:
                errors.append(f"Prévol local incomplet: {command}")

    remote = jobs["remote-preflight"]
    if remote:
        if not has_exact_line(remote, REMOTE_JOB_GUARD):
            errors.append("Le prévol distant doit être réservé au workflow_dispatch manuel au niveau exact du job.")
        if "environment: production" in remote:
            errors.append("Le prévol distant non mutant ne doit pas franchir la frontière d'application production.")
        intent = step_block(remote, "Vérifier l'intention manuelle")
        for marker in (
            '[ "${{ inputs.apply }}" = "true" ]',
            '[ "${{ github.ref }}" != "refs/heads/main" ]',
            f'[ "${{{{ inputs.confirmation }}}}" != "{CONFIRMATION}" ]',
            "exit 64",
            "exit 65",
        ):
            if marker not in intent:
                errors.append(f"Prévol distant sans verrou d'intention attendu: {marker}")
        for name in REMOTE_STEPS:
            block = step_block(remote, name)
            if not block:
                errors.append(f"Étape de prévol distant obligatoire absente: {name}")
            elif REMOTE_STEP_GUARD not in block:
                errors.append(f"Étape distante accessible hors lancement manuel authentifié: {name}")
        for name, required in REMOTE_REQUIREMENTS.items():
            require_step_env(errors, remote, name, required)
        if "supabase secrets set" in remote:
            errors.append("Le prévol distant ne doit jamais modifier les secrets Supabase.")
        if "supabase functions deploy" in remote:
            errors.append("Le prévol distant ne doit jamais déployer d'Edge Function.")
        write_push = '(cd .prod-workspace && supabase db push --linked --password "$SUPABASE_DB_PASSWORD")'
        if write_push in remote:
            errors.append("Le prévol distant ne doit jamais exécuter db push en écriture.")
        if '(cd .prod-workspace && supabase db push --linked --dry-run --password "$SUPABASE_DB_PASSWORD")' not in remote:
            errors.append("Le prévol distant doit conserver le dry-run borné au workspace protégé.")

    apply = jobs["apply-production"]
    if apply:
        if not has_exact_line(apply, APPLY_JOB_GUARD):
            errors.append("Le job d'application doit exiger workflow_dispatch + apply=true + confirmation + main au niveau exact du job.")
        if not has_exact_line(apply, "    environment: production"):
            errors.append("Le job d'application doit être attaché à l'environment GitHub production.")
        if not has_exact_line(apply, "    needs: [local-preflight, remote-preflight]"):
            errors.append("L'application doit dépendre des prévols local et distant.")
        if "python scripts/validate_production_migration_ledger.py" not in apply:
            errors.append("L'application doit revalider le ledger après la frontière d'environment.")
        if "python scripts/build_supabase_production_workspace.py --output .prod-workspace/supabase" not in apply:
            errors.append("L'application doit reconstruire le workspace protégé après la frontière d'environment.")

        approval = step_block(apply, "Revalider la cible production après approbation")
        for marker in (
            '(cd .prod-workspace && supabase link --project-ref "$PROJECT_ID" --password "$SUPABASE_DB_PASSWORD")',
            '(cd .prod-workspace && supabase db lint --linked --schema public --level error --fail-on error)',
            '(cd .prod-workspace && supabase migration list --linked --password "$SUPABASE_DB_PASSWORD")',
            '(cd .prod-workspace && supabase db push --linked --dry-run --password "$SUPABASE_DB_PASSWORD")',
        ):
            if marker not in approval:
                errors.append(f"Revalidation post-environment incomplète: {marker}")

        for name in APPLY_STEPS:
            block = step_block(apply, name)
            if not block:
                errors.append(f"Étape apply obligatoire absente: {name}")
            elif APPLY_STEP_GUARD not in block:
                errors.append(f"Étape apply sans garde workflow_dispatch + apply=true + auth: {name}")
        for name, required in APPLY_REQUIREMENTS.items():
            require_step_env(errors, apply, name, required)

        secret_step = step_block(apply, "Garantir les secrets Edge Functions indispensables")
        if "SUPABASE_DB_PASSWORD:" in secret_step:
            errors.append("Le mot de passe DB ne doit pas être exposé à l'étape des secrets Edge Functions.")
        apply_db = step_block(apply, "Appliquer les migrations de production depuis le workspace protégé")
        if '(cd .prod-workspace && supabase db push --linked --password "$SUPABASE_DB_PASSWORD")' not in apply_db:
            errors.append("Le db push production doit rester borné au workspace protégé dans le job d'application.")
        deploy = step_block(apply, "Déployer toutes les Edge Functions du workspace protégé")
        if '(cd .prod-workspace && supabase functions deploy --project-ref "$PROJECT_ID" --use-api)' not in deploy:
            errors.append("Le déploiement Edge Functions doit rester borné au workspace protégé dans le job d'application.")

    outside_apply = text.replace(apply, "", 1) if apply else text
    for marker, label in (
        ('supabase secrets set', "écriture de secrets"),
        ('(cd .prod-workspace && supabase db push --linked --password "$SUPABASE_DB_PASSWORD")', "db push en écriture"),
        ('supabase functions deploy', "déploiement Edge Functions"),
    ):
        if marker in outside_apply:
            errors.append(f"Primitive mutante hors job apply-production: {label}")

    for line in text.splitlines():
        if "${{ secrets." in line and not re.match(
            r"^ {10}(SUPABASE_ACCESS_TOKEN|SUPABASE_DB_PASSWORD|OPTIONAL_RESEND_API_KEY):", line
        ):
            errors.append(f"Référence de secret hors env d'étape autorisé: {line.strip()}")

    for marker in (
        "🟡 PRÉVOL PR",
        "🟡 PRÉVOL SEULEMENT",
        "aucun secret production exposé au run PR",
        "aucun secret production exposé au run push",
        "⛔ NON SYNCHRONISÉ",
        "🟡 PRÉVOL MANUEL SEULEMENT",
        "✅ APPLIQUÉ ET VÉRIFIÉ",
        "❌ ÉCHEC OU SYNCHRONISATION PARTIELLE",
    ):
        if marker not in text:
            errors.append(f"Résumé production sans frontière de confiance attendue: {marker}")

    for forbidden in ("--include-all", "supabase migration repair", "supabase db reset --linked"):
        if forbidden in text:
            errors.append(f"Primitive interdite dans le workflow production: {forbidden}")

    return errors


def main() -> int:
    if not WORKFLOW.is_file():
        print(f"Workflow introuvable: {WORKFLOW}")
        return 2
    errors = validate_text(WORKFLOW.read_text(encoding="utf-8"))
    if errors:
        print("Contrat sécurité préflight Supabase production: ÉCHEC")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Contrat sécurité préflight Supabase production: OK")
    print("- prévol local strictement sans secret ni Supabase CLI")
    print("- prévol distant manuel limité aux lectures, audits et dry-run")
    print("- application limitée à main + apply=true + confirmation textuelle")
    print("- job mutant isolé derrière environment: production")
    print("- cible, ledger et workspace revalidés après la frontière d'environnement")
    print("- actions immuables, runners/Python figés et secrets bornés aux étapes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
