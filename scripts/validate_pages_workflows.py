#!/usr/bin/env python3
"""Empêche une publication Pages accidentelle par une régression du workflow manuel."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".github/workflows/deploy-pages-controlled.yml"
CHECKOUT_SHA = "d23441a48e516b6c34aea4fa41551a30e30af803"
JEKYLL_SHA = "44a6e6beabd48582f863aeeb6cb2151cc1716697"
UPLOAD_SHA = "98ef48e41587a300b82de4cf298aa98b57b2faae"
# Action officiellement inspectée au SHA : inputs.include-hidden-files déclaré
# et archive tar conditionnelle. Ancien SHA de 2024 IGNORAIT ce paramètre.
LEGACY_UPLOAD_SHA = "56afc609e74202658d3ffba0e8f6dda462b719fa"
DEPLOY_SHA = "368f82528645a54fb793d4d04e342629a3f51346"
JEKYLL_AUDIT_PATH = ROOT / ".github/workflows/audit-pages-jekyll.yml"



def validate_jekyll_ci(source: str) -> list[str]:
    """Prouver que l'audit Jekyll est réellement lancé sur TOUTES les PR.

    Les exclusions de source Jekyll sont sans effet lorsque le job n'est pas
    déclenché. Une liste paths omet facilement un nouveau HTML, une image ou
    une ressource critique; un required check peut aussi manquer entièrement.
    """
    errors: list[str] = []
    active = "\n".join(
        line for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ) + "\n"
    head, sep, jobs = active.partition("\njobs:\n")
    if not sep or active.count("\njobs:\n") != 1:
        return ["Structure YAML de jobs invalide"]
    for token, description in (
        ("on:\n  pull_request:\n    branches: [main]\n",
         "La preuve Jekyll doit couvrir toutes les PR vers main"),
        ("    types: [opened, synchronize, reopened, ready_for_review]\n",
         "Les mises à jour et passages ready_for_review doivent relancer Jekyll"),
        ("  workflow_dispatch:\n",
         "L'audit manuel Jekyll doit rester disponible"),
        ("permissions:\n  contents: read\n",
         "L'audit doit avoir uniquement l'accès en lecture"),
    ):
        if head.count(token) != 1:
            errors.append(description)
    if re.search(r"(?m)^\s+paths(?:-ignore)?:", head):
        errors.append("Interdiction des filtres paths/paths-ignore sur l'audit de sécurité")
    if re.search(r"(?m)^  (?:push|schedule|workflow_run|repository_dispatch):", head):
        errors.append("Déclencheurs inattendus pour la preuve Jekyll sans publication")
    if re.search(r"(?m)^  (?:contents|pages|id-token|actions): write", head):
        errors.append("Permissions d'écriture interdites dans l'audit")
    job_names = re.findall(r"(?m)^  ([a-z][a-z0-9-]*):\s*$", jobs)
    if job_names != ["jekyll-proof"]:
        errors.append("Un seul job jekyll-proof est autorisé, sans publication")
        return errors
    if jobs.count("    name: Construire puis auditer Pages sans déployer\n") != 1:
        errors.append("Nom stable du required check Jekyll modifié")
    if "    runs-on: ubuntu-24.04\n" not in jobs:
        errors.append("Le runner Jekyll doit rester figé")
    if "    timeout-minutes: 20\n" not in jobs:
        errors.append("Budget Jekyll de 20 minutes absent")
    if re.search(r"(?m)^    (?:if|permissions|continue-on-error|strategy):", jobs):
        errors.append("Job Jekyll conditionnel, avec permissions supplémentaires ou erreurs ignorées")
    if re.search(r"(?m)^        (?:if|continue-on-error):", jobs):
        errors.append("Une étape du contrôle Jekyll pourrait être sautée")
    for token, description in (
        ("uses: actions/jekyll-build-pages@44a6e6beabd48582f863aeeb6cb2151cc1716697",
         "Compilation Jekyll réelle avec action épinglée"),
        ("destination: ./_site", "Destination _site isolée"),
        ("python3 scripts/audit_pages_jekyll.py --self-test",
         "Autotests des exclusions de source"),
        ("python3 scripts/audit_pages_jekyll.py --source . --built _site",
         "Audit réel de l'artefact Jekyll"),
        ("python3 scripts/audit_pages_secrets.py --built _site",
         "Analyse des secrets dans le build"),
        ("python3 scripts/validate_pages_workflows.py --self-test",
         "Autotests de la chaîne Pages"),
        ("python3 scripts/validate_pages_workflows.py",
         "Garde de publication et d'audit Jekyll"),
    ):
        if token not in jobs:
            errors.append("Étape Jekyll absente : " + description)
    for command, times in (
        ("python3 scripts/audit_pages_jekyll.py --source . --built _site", 2),
        ("python3 scripts/audit_pages_secrets.py --built _site", 2),
    ):
        if jobs.count(command) != times:
            errors.append(
                "Audits Jekyll de source et secrets requis avant et après le reçu : " + command
            )
    for command in (
        "          python3 scripts/validate_pages_workflows.py --self-test\n",
        "          python3 scripts/validate_pages_workflows.py\n",
    ):
        if jobs.count(command) != 1:
            errors.append(
                "Autotest et garde de publication Pages exécutables requis : " + command.strip()
            )
    if jobs.count("uses: actions/jekyll-build-pages@") != 1:
        errors.append("La compilation Jekyll doit être exécutée une seule fois")
    if jobs.count("persist-credentials: false") != 1:
        errors.append("Checkout Jekyll sans persistance des identifiants requis")
    if re.search(r"(?m)^        uses: actions/checkout@(?!d23441a48e516b6c34aea4fa41551a30e30af803)", jobs):
        errors.append("Checkout Jekyll non épinglé au SHA contrôlé")
    for forbidden in ("upload-pages-artifact@", "deploy-pages@", "pages: write",
                      "id-token: write", "continue-on-error: true", "|| true"):
        if forbidden in active:
            errors.append("Publication ou contournement interdit dans l'audit : " + forbidden)
    return errors


def self_test_jekyll_ci() -> None:
    source = JEKYLL_AUDIT_PATH.read_text("utf-8")
    assert not validate_jekyll_ci(source), validate_jekyll_ci(source)
    mutations = {
        "paths seulement CSS": (
            "    types: [opened, synchronize, reopened, ready_for_review]\n",
            "    types: [opened, synchronize, reopened, ready_for_review]\n"
            "    paths:\n      - 'assets/css/**'\n",
        ),
        "paths-ignore excluant les images": (
            "    types: [opened, synchronize, reopened, ready_for_review]\n",
            "    types: [opened, synchronize, reopened, ready_for_review]\n"
            "    paths-ignore:\n      - 'assets/media/**'\n",
        ),
        "PR supprimée": ("  pull_request:\n", "  pull_request_disabled:\n"),
        "branche de revue détournée": ("    branches: [main]\n",
                                     "    branches: [not-main]\n"),
        "synchronize désactivé": (
            "opened, synchronize, reopened, ready_for_review",
            "opened, reopened, ready_for_review",
        ),
        "run manuel retiré": ("  workflow_dispatch:\n", ""),
        "job Jekyll désactivé": ("  jekyll-proof:\n",
                                "  jekyll-proof:\n    if: false\n"),
        "required check renommé": (
            "    name: Construire puis auditer Pages sans déployer\n",
            "    name: Construire un aperçu facultatif\n",
        ),
        "erreurs ignorées": ("    timeout-minutes: 20\n",
                             "    timeout-minutes: 20\n    continue-on-error: true\n"),
        "publication ajoutée": ("  jekyll-proof:\n",
                               "  deploy:\n    runs-on: ubuntu-24.04\n  jekyll-proof:\n"),
        "artefact root téléversé": (
            "          destination: ./_site\n",
            "          destination: ./_site\n"
            "      - name: Envoyer le dépôt entier\n"
            "        uses: actions/upload-pages-artifact@v3\n",
        ),
        "permissions accrues": ("  contents: read\n",
                                 "  contents: write\n"),
        "audit des secrets retiré": (
            "python3 scripts/audit_pages_secrets.py --built _site",
            "echo SECRETS_NON_TESTES",
        ),
        "audit de source retiré": (
            "python3 scripts/audit_pages_jekyll.py --source . --built _site",
            "echo FUITES_NON_TESTEES",
        ),
        "compilation Jekyll retirée": (
            "actions/jekyll-build-pages@44a6e6beabd48582f863aeeb6cb2151cc1716697",
            "actions/jekyll-build-pages@v1",
        ),
        "contrat Pages retiré": (
            "          python3 scripts/validate_pages_workflows.py\n",
            "          echo GARDE_PAGES_IGNOREE\n",
        ),
        "autotests de publication Pages retirés": (
            "          python3 scripts/validate_pages_workflows.py --self-test\n",
            "          echo AUTOTESTS_PAGES_IGNORES\n",
        ),
    }
    for label, (old, replacement) in mutations.items():
        if old not in source:
            raise AssertionError("Mutation Jekyll inapplicable : " + label)
        candidate = source.replace(old, replacement, 1)
        if not validate_jekyll_ci(candidate):
            raise AssertionError("Régression Jekyll non détectée : " + label)
    print(f"OK audit Jekyll universel : {len(mutations)} mutations de déclenchement/publication refusées")


def job_steps(workflow: str, name: str) -> list[tuple[str, str]]:
    """Extraire des étapes YAML du job, sans installer de parseur externe.

    Contrat volontairement strict : toute modification d'indentation ou
    de structure du workflow doit être revue avant la publication.
    """
    jobs = list(re.finditer(r"(?m)^  ([a-z][a-z0-9-]*):\s*$", workflow))
    match = next((i for i, m in enumerate(jobs) if m.group(1) == name), None)
    if match is None:
        return []
    start = jobs[match].end()
    end = jobs[match + 1].start() if match + 1 < len(jobs) else len(workflow)
    body = workflow[start:end]
    headers = list(re.finditer(r"(?m)^      - name: ([^\n]+)$", body))
    return [
        (m.group(1).strip(), body[m.end():headers[i + 1].start()
                                  if i + 1 < len(headers) else len(body)])
        for i, m in enumerate(headers)
    ]


def active_audit_commands(step: str) -> set[str]:
    """Ne compter que les commandes Python/Node actives, jamais echo ou commentaires.

    Une mention textuelle d'un audit dans une annotation YAML, un echo ou
    une commande commentée ne doit jamais satisfaire le garde.
    """
    results: set[str] = set()
    lines = step.splitlines()
    for i, line in enumerate(lines):
        match = re.fullmatch(r"        run: (.+)", line)
        if not match:
            continue
        value = match.group(1).strip()
        if value.startswith(("python3 ", "node --test ")):
            results.add(value)
        elif value in {"|", "|-"}:
            for candidate in lines[i + 1:]:
                if candidate.strip() and not candidate.startswith("          "):
                    break
                if candidate.startswith("          "):
                    command = candidate[10:].strip()
                    if command.startswith(("python3 ", "node --test ")):
                        results.add(command)
    return results


def executable_guards(workflow: str) -> list[str]:
    """Lier les contrôles au vrai job et à l'étape précédant l'upload."""
    issues: list[str] = []
    artifact = job_steps(workflow, "artifact")
    deploy = job_steps(workflow, "deploy")
    verify = job_steps(workflow, "verify-live")
    names = [name for name, _ in artifact]
    compile_step = "Construire Jekyll — pas la racine technique du dépôt"
    before = "Marquer le build avec le SHA et l'identifiant du workflow"
    audit_name = "Refuser toute fuite de code et toute perte de route"
    after = "Téléverser uniquement l’artefact vérifié, et seulement en mode PUBLISH"
    if not (names.count(compile_step) == names.count(before) ==
            names.count(audit_name) == names.count(after) == 1
            and names.index(compile_step) < names.index(before)
            < names.index(audit_name) < names.index(after)):
        return ["Ordre compilation -> reçu -> audits finaux -> upload non prouvé"]
    build_step = next(body for name, body in artifact if name == audit_name)
    live_step = next((body for name, body in verify
                      if name.startswith("Attendre le reçu SHA/run réel")), "")
    integrity_step = next((body for name, body in verify
                           if name.startswith("Confirmer les octets CDN")), "")
    build_commands = active_audit_commands(build_step)
    live_commands = active_audit_commands(live_step)
    integrity_commands = active_audit_commands(integrity_step)
    required_build = (
        "python3 scripts/audit_pages_jekyll.py --source . --built _site",
        "python3 scripts/validate_sinjira_public_links.py --check",
        "python3 scripts/validate_sinjira_catalogues_metadata.py --built _site",
        "node --test tests/test_sinjira_library_access.cjs",
        "node --test tests/test_document_url_authorization.cjs",
        "node --test tests/test_novel_file_authorization.cjs",
        "python3 scripts/validate_get_private_book_url_security.py",
        "node --test tests/test_private_book_authorization.cjs",
        "python3 scripts/validate_boussole_home_visual.py --built _site",
        "python3 scripts/audit_public_documents.py --source . --built _site",
        'python3 scripts/audit_public_json.py --source . --built _site --release-sha "$GITHUB_SHA" --release-run-id "$GITHUB_RUN_ID"',
        "python3 scripts/audit_public_csv.py --source . --built _site",
        'python3 scripts/audit_public_surface.py --source . --built _site --release-sha "$GITHUB_SHA" --release-run-id "$GITHUB_RUN_ID"',
        "python3 scripts/audit_pwa_precache.py --source . --built _site",
        'python3 scripts/pages_release_proof.py --verify _site --sha "$GITHUB_SHA" --run-id "$GITHUB_RUN_ID"',
        'python3 scripts/verify_pages_tar_archive.py --built _site --sha "$GITHUB_SHA" --run-id "$GITHUB_RUN_ID"',
        "python3 scripts/audit_pages_secrets.py --built _site",
    )
    for command in required_build:
        if command not in build_commands:
            issues.append("Audit final absent ou non exécutable : " + command.split()[1])
    required_live = (
        'python3 scripts/verify_pages_live.py --check --release-sha "$GITHUB_SHA" --release-run-id "$GITHUB_RUN_ID" --await-release',
    )
    required_integrity = (
        'python3 scripts/verify_pages_integrity.py --check --expected-sha "$GITHUB_SHA"',
    )
    for command in required_live:
        if command not in live_commands:
            issues.append("Vérification HTTP non exécutable dans le job live")
    for command in required_integrity:
        if command not in integrity_commands:
            issues.append("Contrôle CDN non exécutable dans le job live")
    for job_name, steps, prefix in (
        ("artifact", artifact, "Attester Pages ET la fraîcheur"),
        ("deploy", deploy, "Revérifier Pages et HEAD main"),
    ):
        match = [body for name, body in steps if name.startswith(prefix)]
        if (len(match) != 1 or
                "python3 scripts/attest_pages_production.py --check"
                not in active_audit_commands(match[0])):
            issues.append("Attestation Pages non exécutable dans le job " + job_name)
    return issues


def validate(workflow: str) -> list[str]:
    errors: list[str] = []
    def need(ok: bool, name: str) -> None:
        if not ok:
            errors.append(name)
    need(workflow.startswith("name: Pages — déploiement isolé explicitement approuvé\n"),
         "Identité du workflow modifiée")
    # YAML autorise parfois des clés dupliquées selon le parseur. Une deuxième
    # définition de job ne doit pas pouvoir remplacer silencieusement la bonne.
    jobs_marker = "\njobs:\n"
    need(workflow.count(jobs_marker) == 1, "Bloc jobs YAML absent ou dupliqué")
    jobs = workflow.split(jobs_marker, 1)[-1]
    names_in_yaml = re.findall(r"(?m)^  ([a-z][a-z0-9-]*):\s*$", jobs)
    need(names_in_yaml == ["artifact", "deploy", "verify-live"],
         "Jobs Pages inattendus, dupliqués ou dans un ordre non autorisé")
    need("on:\n  workflow_dispatch:\n" in workflow,
         "Déclenchement exclusivement manuel absent")
    need(not re.search(r"(?m)^  (?:push|pull_request|schedule|repository_dispatch|workflow_run):", workflow),
         "Publication automatique interdite")
    need("permissions:\n  contents: read\n" in workflow,
         "Permissions lecture seule globales manquantes")
    need("group: pages-production-controlled" in workflow,
         "Exclusion mutuelle des déploiements manquante")
    need("cancel-in-progress: false" in workflow,
         "Interruption d'un déploiement en cours interdite")
    need("test \"$EXPECTED_SHA\" = \"$GITHUB_SHA\"" in workflow,
         "Vérification SHA exact manquante")
    need("test \"$(git rev-parse HEAD)\" = \"$EXPECTED_SHA\"" in workflow,
         "Révision Git locale non vérifiée")
    need('test "$SOURCE" = "ACTIONS_ONLY"' in workflow,
         "Confirmation manuelle du mode Actions requise")
    need('test "$MODE" = "DRY_RUN" || test "$MODE" = "PUBLISH"' in workflow,
         "Choix des modes DRY_RUN/PUBLISH manquant")
    need("github.ref == 'refs/heads/main'" in workflow,
         "Publication limitée à main")
    need("inputs.mode == 'PUBLISH' && inputs.confirm_actions_source == 'ACTIONS_ONLY'" in workflow,
         "Publication non conditionnée au double consentement")
    need(f"uses: actions/upload-pages-artifact@{LEGACY_UPLOAD_SHA}" not in workflow,
         "Action Pages 2024 incompatible avec include-hidden-files interdite")
    need(workflow.count(f"uses: actions/checkout@{CHECKOUT_SHA}") == 3,
         "Checkout non épinglé ou nombre d'étapes modifié")
    need(workflow.count("persist-credentials: false") == 3,
         "Credentials checkout persistés")
    for tool, sha in {
        "actions/jekyll-build-pages": JEKYLL_SHA,
        "actions/upload-pages-artifact": UPLOAD_SHA,
        "actions/deploy-pages": DEPLOY_SHA,
    }.items():
        need(workflow.count(f"uses: {tool}@{sha}") == 1,
             f"Action non épinglée ou manquante: {tool}")
    uses = re.findall(r"(?m)^\s*uses:\s+(\S+)\s*$", workflow)
    need(len(uses) == 8, "Nombre d'actions externes inattendu")
    need(all(re.search(r"@[0-9a-f]{40}$", u) for u in uses),
         "Action non immuable détectée")
    need('      - name: Tracer l\'origine du publish' in workflow,
         "Etape de traçabilité du publish manquante")
    need("printf '%s\\n' '- Répertoire upload-pages-artifact : _site" in workflow,
         "Résumé de publication doit utiliser printf et non des backticks")
    need(workflow.count("path: _site") == 1,
         "L'artefact Pages doit être téléversé depuis _site exactement")
    need(workflow.count("include-hidden-files: 'true'") == 1,
         "Les fichiers approuvés .well-known doivent être inclus dans l'artefact Pages")
    upload_start = "      - name: Téléverser uniquement l’artefact vérifié, et seulement en mode PUBLISH\n"
    upload_end = "      - name: Tracer l'origine du publish\n"
    upload_block = (workflow.split(upload_start, 1)[1].split(upload_end, 1)[0]
                    if workflow.count(upload_start) == 1 and workflow.count(upload_end) == 1
                    else "")
    need(bool(upload_block), "Étape d'upload Pages introuvable ou dupliquée")
    need("        if: ${{ inputs.mode == 'PUBLISH' && inputs.confirm_actions_source == 'ACTIONS_ONLY' }}" in upload_block,
         "DRY_RUN ne doit jamais téléverser d'artefact Pages")
    need("uses: actions/upload-pages-artifact@" in upload_block,
         "Action de téléversement non associée à la condition PUBLISH")
    need("include-hidden-files: 'true'" in upload_block and "path: _site" in upload_block,
         "L'upload conditionnel doit conserver _site et .well-known")

    need(re.search(r"(?m)^\s+path:\s*\.\s*$", workflow) is None,
         "Téléversement de la racine du dépôt interdit")
    need("python3 scripts/audit_pages_jekyll.py --source . --built _site" in workflow,
         "Audit réel de l'artefact absent")
    need("python3 scripts/audit_public_documents.py --self-test" in workflow,
         "Autotests de documents publics absents")
    need("python3 scripts/audit_public_documents.py --source ." in workflow,
         "Contrôle des fichiers sources publics manquant")
    need("python3 scripts/audit_public_documents.py --source . --built _site" in workflow,
         "Contrôle PDF final avant publication manquant")
    need("python3 scripts/audit_public_json.py --self-test" in workflow,
         "Autotests JSON publics manquants")
    need("python3 scripts/audit_public_json.py --source ." in workflow,
         "Contrôle des sources JSON publics manquant")
    need("python3 scripts/audit_public_json.py --source . --built _site" in workflow,
         "Audit des données JSON publiées manquant")
    need("python3 scripts/audit_public_csv.py --self-test" in workflow,
         "Autotests CSV publics manquants")
    need("python3 scripts/audit_public_csv.py --source ." in workflow,
         "Contrôle des sources CSV publics manquant")
    need("python3 scripts/audit_public_csv.py --source . --built _site" in workflow,
         "Audit des données CSV publiées manquant")
    need("python3 scripts/audit_public_surface.py --self-test" in workflow,
         "Autotests de l'inventaire global manquants")
    need("python3 scripts/audit_public_surface.py --source ." in workflow,
         "Vérification source de l'inventaire global manquante")
    need("python3 scripts/audit_public_surface.py --source . --built _site" in workflow,
         "Audit complet de l'artefact avant upload manquant")
    need("python3 scripts/audit_pwa_precache.py --self-test" in workflow,
         "Autotests des ressources PWA absents")
    need("python3 scripts/audit_pwa_precache.py --source ." in workflow,
         "Contrôle des ressources PWA sources manquant")
    need("python3 scripts/audit_pwa_precache.py --source . --built _site" in workflow,
         "Contrôle des 46 ressources PWA compilées manquant")
    need("python3 scripts/audit_pages_secrets.py --self-test" in workflow,
         "Autotests des secrets du build manquants")
    need("python3 scripts/audit_pages_secrets.py --built _site" in workflow,
         "Analyse des secrets du build avant upload manquante")
    need("python3 scripts/pages_release_proof.py --self-test" in workflow,
         "Autotests du reçu SHA/run manquants")
    need("python3 scripts/pages_release_proof.py --write _site --sha" in workflow,
         "Reçu Pages non ajouté à l'artefact")
    need("python3 scripts/pages_release_proof.py --verify _site --sha" in workflow,
         "Reçu Pages non contrôlé avant upload")
    need("python3 scripts/verify_pages_tar_archive.py --self-test" in workflow,
         "Autotests du TAR avec reçu caché manquants")
    need("python3 scripts/validate_sinjira_public_links.py --self-test" in workflow,
         "Autotests de navigation des catalogues manquants")
    need("python3 scripts/validate_boussole_home_visual.py --self-test" in workflow,
         "Autotests visuels de la Boussole manquants")
    need('python3 scripts/verify_pages_tar_archive.py --built _site --sha "$GITHUB_SHA" --run-id "$GITHUB_RUN_ID"' in workflow,
         "Preuve TAR hors ligne des fichiers cachés et contenus absente")
    need("python3 scripts/audit_public_json.py --source . --built _site --release-sha" in workflow,
         "Reçu Pages non inclus dans le contrôle JSON")
    need("python3 scripts/audit_public_surface.py --source . --built _site --release-sha" in workflow,
         "Reçu Pages non inclus dans l'inventaire intégral")
    need("python3 scripts/verify_pages_live.py --check --release-sha" in workflow,
         "Vérification HTTP ne prouve pas le SHA exact de la publication")
    verify_job = workflow.split("\n  verify-live:", 1)[-1]
    need(verify_job != workflow and
         'python3 scripts/verify_pages_live.py --check --release-sha "$GITHUB_SHA" --release-run-id "$GITHUB_RUN_ID" --await-release' in verify_job,
         "Attente bornée du reçu CDN exact avant les vérifications live absente")
    need("timeout-minutes: 20" in verify_job,
         "Délai du job HTTP insuffisant pour 22 fichiers CDN et la propagation bornée")
    need("Confirmer les octets CDN des 22 ressources critiques dans le budget borné" in verify_job,
         "Intégrité des 22 ressources non annoncée dans le job")
    need('python3 scripts/verify_pages_integrity.py --self-test' in workflow,
         "Autotests de l'intégrité des octets publics absents")
    need('python3 scripts/verify_pages_integrity.py --check --expected-sha "$GITHUB_SHA"' in verify_job,
         "Contrôle des 22 fichiers CDN contre le commit approuvé manquant")
    need(verify_job.find("verify_pages_integrity.py --check") >
         verify_job.find("verify_pages_live.py --check"),
         "Intégrité statique lancée avant la validation du reçu SHA/run")
    need("python3 scripts/verify_pages_live.py --check" in workflow,
         "Contrôle externe des chemins techniques absent")
    need("needs: deploy" in workflow,
         "Contrôle HTTP non dépendant du déploiement")
    need("pages: read" in workflow and "GH_PAGES_READ_TOKEN" in workflow,
         "Lecture de la configuration Pages manquante")
    need("python3 scripts/attest_pages_production.py --self-test" in workflow,
         "Autotests de l'attestation de production manquants")
    need(workflow.count("python3 scripts/attest_pages_production.py --check") == 2,
         "L'attestation Pages doit précéder la construction ET le déploiement")
    need(workflow.count("GH_PAGES_READ_TOKEN: ${{ github.token }}") == 2,
         "Token Pages read-only requis pour les deux attestations")
    deploy = workflow.split("\n  deploy:", 1)[-1].split("\n  verify-live:", 1)[0]
    need(deploy != workflow, "Job de déploiement séparé manquant")
    need("contents: read" in deploy and "pages: write" in deploy,
         "Permissions du job de déploiement insuffisantes pour attester main")
    need("Revérifier Pages et HEAD main immédiatement avant le déploiement" in deploy,
         "Attestation post-approbation avant déploiement absente")
    need("pages: write" in workflow and "id-token: write" in workflow,
         "Identité Pages requise pour le seul job de publication")
    errors.extend(executable_guards(workflow))
    errors.extend(
        "Audit Jekyll obligatoire : " + issue
        for issue in validate_jekyll_ci(JEKYLL_AUDIT_PATH.read_text("utf-8"))
    )
    return errors


def smoke_summary_bash(workflow: str) -> None:
    """Exécuter le vrai résumé du workflow en local avec un SHA fictif, sans GitHub."""
    anchor = "      - name: Tracer l'origine du publish\n"
    if workflow.count(anchor) != 1:
        raise RuntimeError("Etape de résumé absente ou dupliquée")
    tail = workflow.split(anchor, 1)[1].split("\n  deploy:", 1)[0]
    start = "        run: |\n"
    if tail.count(start) != 1:
        raise RuntimeError("Bloc Bash de résumé invalide")
    raw_lines = tail.split(start, 1)[1].splitlines()
    if not raw_lines or any(not ln.startswith("          ") for ln in raw_lines if ln.strip()):
        raise RuntimeError("Indentation Bash incorrecte")
    script = "\n".join(ln[10:] if ln.startswith("          ") else "" for ln in raw_lines)
    if "`" in script:
        raise RuntimeError("Backticks interdits dans le résumé Bash")
    env = os.environ.copy()
    with tempfile.TemporaryDirectory() as directory:
        out = Path(directory) / "summary.md"
        env.update({
            "GITHUB_SHA": "a" * 40,
            "MODE": "DRY_RUN",
            "GITHUB_STEP_SUMMARY": str(out),
        })
        run = subprocess.run(
            ["bash"], input=script, text=True, capture_output=True,
            env=env, timeout=8, check=False,
        )
        if run.returncode != 0 or run.stderr:
            raise RuntimeError(
                "Résumé Bash invalide: " + (run.stderr.strip() or str(run.returncode))
            )
        rendered = out.read_text("utf-8")
        for expected in ("Source commit : " + "a" * 40,
                         "Mode : DRY_RUN",
                         "upload-pages-artifact : _site"):
            if expected not in rendered:
                raise RuntimeError("Résumé Bash incomplet: " + expected)


def self_test(workflow: str) -> None:
    errors = validate(workflow)
    if errors:
        raise SystemExit("Workflow sain rejeté: " + "; ".join(errors))
    smoke_summary_bash(workflow)
    self_test_jekyll_ci()
    mutations = {
        "Publication root": workflow.replace("path: _site", "path: .", 1),
        "Job deploy dupliqué": workflow + "\n  deploy:\n    runs-on: ubuntu-latest\n",
        "Job de publication supplémentaire": workflow + "\n  publish-root:\n    runs-on: ubuntu-latest\n",
        "Dossier .well-known exclu de l'upload": workflow.replace(
            "include-hidden-files: 'true'", "include-hidden-files: 'false'", 1
        ),
        "Retour au pin upload Pages 2024 incompatible": workflow.replace(
            f"actions/upload-pages-artifact@{UPLOAD_SHA}",
            f"actions/upload-pages-artifact@{LEGACY_UPLOAD_SHA}", 1,
        ),
        "DRY_RUN téléverse l'artefact": workflow.replace(
            "        if: ${{ inputs.mode == 'PUBLISH' && inputs.confirm_actions_source == 'ACTIONS_ONLY' }}\n"
            "        uses: actions/upload-pages-artifact@",
            "        uses: actions/upload-pages-artifact@", 1,
        ),

        "Preuve de Boussole neutralisée": workflow.replace(
            "          python3 scripts/validate_boussole_home_visual.py --built _site",
            "          echo VISUEL_BOUSSOLE_NON_VERIFIE", 1,
        ),
        "Test de la porte privée Livre I neutralisé": workflow.replace(
            "          python3 scripts/validate_get_private_book_url_security.py\n"
            "          node --test tests/test_private_book_authorization.cjs",
            "          python3 scripts/validate_get_private_book_url_security.py\n"
            "          echo TEST_LIVRE_I_NON_EXECUTE", 1,
        ),
        "Contrat de la porte privée Livre I neutralisé": workflow.replace(
            "          node --test tests/test_novel_file_authorization.cjs\n"
            "          python3 scripts/validate_get_private_book_url_security.py\n"
            "          node --test tests/test_private_book_authorization.cjs",
            "          node --test tests/test_novel_file_authorization.cjs\n"
            "          echo CONTRAT_LIVRE_I_NON_EXECUTE\n"
            "          node --test tests/test_private_book_authorization.cjs", 1,
        ),
        "Test de droits romans neutralisé": workflow.replace(
            "          python3 scripts/validate_sinjira_catalogues_metadata.py --built _site\n"
            "          node --test tests/test_sinjira_library_access.cjs\n"
            "          node --test tests/test_document_url_authorization.cjs\n"
            "          node --test tests/test_novel_file_authorization.cjs",
            "          python3 scripts/validate_sinjira_catalogues_metadata.py --built _site\n"
            "          node --test tests/test_sinjira_library_access.cjs\n"
            "          node --test tests/test_document_url_authorization.cjs\n"
            "          echo TEST_ROMANS_NEUTRALISE", 1,
        ),
        "Test de signature des documents neutralisé": workflow.replace(
            "          python3 scripts/validate_sinjira_catalogues_metadata.py --built _site\n"
            "          node --test tests/test_sinjira_library_access.cjs\n"
            "          node --test tests/test_document_url_authorization.cjs",
            "          python3 scripts/validate_sinjira_catalogues_metadata.py --built _site\n"
            "          node --test tests/test_sinjira_library_access.cjs\n"
            "          echo TEST_SIGNATURE_DOCUMENTS_NEUTRALISE", 1,
        ),
        "Tests droits bibliothèque neutralisés": workflow.replace(
            "          python3 scripts/validate_sinjira_catalogues_metadata.py --built _site\n"
            "          node --test tests/test_sinjira_library_access.cjs",
            "          python3 scripts/validate_sinjira_catalogues_metadata.py --built _site\n"
            "          echo TEST_ACCES_NON_EXECUTE", 1,
        ),
        "Contrôle SEO des catalogues neutralisé": workflow.replace(
            "          python3 scripts/validate_sinjira_catalogues_metadata.py --built _site",
            "          echo SEO_CATALOGUES_NON_VERIFIE", 1,
        ),
        "Contrôle SEO ne vérifiant que les sources": workflow.replace(
            "          python3 scripts/validate_sinjira_catalogues_metadata.py --built _site",
            "          python3 scripts/validate_sinjira_catalogues_metadata.py", 1,
        ),
        "Validation de navigation publique neutralisée": workflow.replace(
            "          python3 scripts/validate_sinjira_public_links.py --check",
            "          echo NAVIGATION_PUBLIQUE_NON_VERIFIEE", 1,
        ),
        "Audit PDF post-build supprimé": workflow.replace(
            "python3 scripts/audit_public_documents.py --source . --built _site",
            "echo DOCUMENTS_NON_AUDITES", 1,
        ),
        "Audit JSON post-build supprimé": workflow.replace(
            "python3 scripts/audit_public_json.py --source . --built _site",
            "echo JSON_NON_AUDITES", 1,
        ),
        "Audit CSV post-build supprimé": workflow.replace(
            "python3 scripts/audit_public_csv.py --source . --built _site",
            "echo CSV_NON_AUDITES", 1,
        ),
        "Audit global post-build supprimé": workflow.replace(
            "python3 scripts/audit_public_surface.py --source . --built _site",
            "echo MANIFEST_NON_AUDITE", 1,
        ),
        "Audit global commenté": workflow.replace(
            '          python3 scripts/audit_public_surface.py --source . --built _site --release-sha "$GITHUB_SHA" --release-run-id "$GITHUB_RUN_ID"',
            '          # python3 scripts/audit_public_surface.py --source . --built _site --release-sha "$GITHUB_SHA" --release-run-id "$GITHUB_RUN_ID"', 1,
        ),
        "Audit secrets seulement imprimé": workflow.replace(
            '          python3 scripts/audit_pages_secrets.py --built _site',
            '          echo python3 scripts/audit_pages_secrets.py --built _site', 1,
        ),
        "Contrôle HTTP commenté": workflow.replace(
            '        run: python3 scripts/verify_pages_live.py --check --release-sha "$GITHUB_SHA" --release-run-id "$GITHUB_RUN_ID" --await-release',
            '        run: echo python3 scripts/verify_pages_live.py --check --release-sha "$GITHUB_SHA" --release-run-id "$GITHUB_RUN_ID" --await-release', 1,
        ),
        "Attestation post approbation commentée": workflow.replace(
            '        run: python3 scripts/attest_pages_production.py --check',
            '        run: echo python3 scripts/attest_pages_production.py --check', 1,
        ),
        "Audit secrets post-build supprimé": workflow.replace(
            "python3 scripts/audit_pages_secrets.py --built _site",
            "echo SECRETS_NON_AUDITES", 1,
        ),
        "Audit PWA post-build supprimé": workflow.replace(
            "python3 scripts/audit_pwa_precache.py --source . --built _site",
            "echo CORE_PWA_NON_AUDITE", 1,
        ),
        "Reçu de publication supprimé": workflow.replace(
            "python3 scripts/pages_release_proof.py --write _site --sha",
            "python3 scripts/pages_release_proof.py --self-test # ", 1,
        ),
        "Budget d'exécution CDN réduit": workflow.replace(
            "    timeout-minutes: 20\n    permissions:\n      contents: read\n    steps:\n"
            "      - name: Checkout pour le validateur HTTP",
            "    timeout-minutes: 2\n    permissions:\n      contents: read\n    steps:\n"
            "      - name: Checkout pour le validateur HTTP", 1,
        ),
        "Dénomination critique CDN obsolète": workflow.replace(
            "Confirmer les octets CDN des 22 ressources critiques dans le budget borné",
            "Confirmer les octets CDN des 8 ressources critiques", 1,
        ),
        "Contrôle TAR .well-known supprimé": workflow.replace(
            'python3 scripts/verify_pages_tar_archive.py --built _site --sha "$GITHUB_SHA" --run-id "$GITHUB_RUN_ID"',
            'echo ARCHIVE_TAR_NON_VERIFIEE', 1,
        ),
        "Identité sur le domaine absente": workflow.replace(
            "python3 scripts/verify_pages_live.py --check --release-sha",
            "python3 scripts/verify_pages_live.py --check #", 1,
        ),
        "Attente propagation CDN désactivée": workflow.replace(
            ' --release-run-id "$GITHUB_RUN_ID" --await-release',
            ' --release-run-id "$GITHUB_RUN_ID"', 1,
        ),
        "Intégrité CDN supprimée": workflow.replace(
            'python3 scripts/verify_pages_integrity.py --check --expected-sha "$GITHUB_SHA"',
            'echo CDN_INTEGRITE_NON_VERIFIEE', 1,
        ),
        "Ouverture sur push": workflow.replace("  workflow_dispatch:\n", "  push:\n    branches: [main]\n  workflow_dispatch:\n", 1),
        "SHA non vérifié": workflow.replace('test "$EXPECTED_SHA" = "$GITHUB_SHA"', "true", 1),
        "Confirmation disparue": workflow.replace('test "$SOURCE" = "ACTIONS_ONLY"', "true", 1),
        "Autorisation deploy perdue": workflow.replace("inputs.mode == 'PUBLISH' && inputs.confirm_actions_source == 'ACTIONS_ONLY'", "inputs.mode == 'PUBLISH'", 1),
        "Vérification live supprimée": workflow.replace("python3 scripts/verify_pages_live.py --check", "echo SKIP", 1),
        "Identifiant non immuable": workflow.replace(f"actions/deploy-pages@{DEPLOY_SHA}", "actions/deploy-pages@v5", 1),
        "Résumé Bash avec substitution": workflow.replace(
            "printf '%s\\n' '- Répertoire upload-pages-artifact : _site (jamais la racine)'",
            'echo "- Répertoire upload-pages-artifact : `_site`"',
            1,
        ),
        "Attestation avant build retirée": workflow.replace(
            "run: python3 scripts/attest_pages_production.py --check", "run: echo SKIP", 1,
        ),
        "Attestation après approbation retirée": workflow.replace(
            "Revérifier Pages et HEAD main immédiatement avant le déploiement",
            "Etape de déploiement sans confirmation",
            1,
        ),
        "Token Pages indisponible": workflow.replace(
            "GH_PAGES_READ_TOKEN: ${{ github.token }}", "GH_PAGES_READ_TOKEN: ''", 1,
        ),
    }
    for name, candidate in mutations.items():
        if candidate == workflow or not validate(candidate):
            raise SystemExit(f"Mutation interdite non détectée: {name}")
    print(f"OK workflow Pages : {len(mutations)} régressions dangereuses détectées, résumé Bash exécuté")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    workflow = PATH.read_text("utf-8")
    if args.self_test:
        self_test(workflow)
        return 0
    errors = validate(workflow)
    for error in errors:
        print("ERREUR: " + error)
    if errors:
        return 1
    print("OK workflow Pages : manuel, SHA exact, artefact isolé, contrôle HTTPS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
