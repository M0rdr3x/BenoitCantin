#!/usr/bin/env python3
"""Empêche de sauter les tests SINJIRA quand un module partagé change.

Le contrôle obligatoire Jekyll l'exécute sur toutes les PR vers main,
indépendamment de la propre configuration de ce workflow. Aucun réseau.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/validate-sinjira-catalogues.yml"

CHECKOUT = "d23441a48e516b6c34aea4fa41551a30e30af803"
PYTHON = "ece7cb06caefa5fff74198d8649806c4678c61a1"
PLAYWRIGHT = (
    "mcr.microsoft.com/playwright/python:v1.61.0-noble@sha256:"
    "a9731514f24121d1dcd25d58d0a38146646d290a5998fd80d3e533e7b5e21c69"
)


def validate(source: str) -> list[str]:
    """Exiger la CI universelle des catalogues sur PR + les vrais tests."""
    errors: list[str] = []
    active = "\n".join(
        line for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ) + "\n"
    head, separator, jobs = active.partition("\njobs:\n")
    if not separator or active.count("\njobs:\n") != 1:
        return ["Structure du workflow de catalogues invalide"]
    if head.count(
        "on:\n  pull_request:\n    branches: [main]\n"
        "    types: [opened, synchronize, reopened, ready_for_review]\n"
    ) != 1:
        errors.append("Les catalogues doivent être contrôlés à chaque PR vers main")
    if head.count("  push:\n    branches: [main]\n") != 1:
        errors.append("Le contrôle des catalogues doit aussi suivre main")
    if head.count("  workflow_dispatch:\n") != 1:
        errors.append("Exécution manuelle des catalogues manquante")
    if re.search(r"(?m)^\s+paths(?:-ignore)?:", head):
        errors.append("Tout filtre paths est interdit sur le contrôle des catalogues")
    if re.search(
        r"(?m)^  (?:schedule|workflow_run|repository_dispatch|pull_request_target):",
        head,
    ):
        errors.append("Déclencheur de catalogue inattendu")
    if head.count("permissions:\n  contents: read\n") != 1 or re.search(
        r"(?m)^  (?:contents|pages|actions|id-token): write", head
    ):
        errors.append("Seul le droit contents: read est autorisé")
    if re.findall(r"(?m)^  ([a-z][a-z0-9-]*):\s*$", jobs) != [
        "verify", "visual-browser"
    ]:
        errors.append("Les jobs verify et visual-browser doivent rester présents")
        return errors

    verify, visual_separator, visual = jobs.partition("\n  visual-browser:\n")
    if not visual_separator:
        errors.append("Vérifications des trois navigateurs manquantes")
        return errors
    # partition() consomme le saut de ligne avant le prochain job.
    # Une commande en dernière ligne du job doit garder sa frontière.
    verify += "\n"
    if "    name: Contrôler les trois catalogues et les routes publiques\n" not in verify:
        errors.append("Nom du contrôle principal modifié")
    if verify.count("    runs-on: ubuntu-24.04\n") != 1:
        errors.append("Runner du contrôle principal non épinglé")
    if "    timeout-minutes: 10\n" not in verify:
        errors.append("Budget de contrôle de 10 minutes absent")
    if re.search(r"(?m)^    (?:if|continue-on-error|permissions):", verify):
        errors.append("Le contrôle principal ne doit jamais être conditionnel")
    if re.search(r"(?m)^        (?:if|continue-on-error):", verify):
        errors.append("Une étape de vérification pourrait être désactivée")

    required_verify = (
        "          python3 scripts/validate_sinjira_catalogues_workflow.py --self-test\n",
        "          python3 scripts/validate_sinjira_catalogues_workflow.py\n",
        "        run: python3 scripts/validate_sinjira_catalogues.py --self-test\n",
        "          python3 scripts/validate_nova_survey.py --self-test\n",
        "        run: node --test tests/test_nova_survey_body.mjs\n",
        "          python3 scripts/validate_nova_survey.py\n",
        "        run: python3 scripts/validate_sinjira_catalogues.py\n",
        "          python3 scripts/validate_sinjira_public_links.py --self-test\n",
        "          python3 scripts/validate_sinjira_public_links.py --check\n",
        "        run: python3 scripts/validate_sinjira_library_status.py --self-test\n",
        "        run: node --test tests/test_sinjira_library_access.cjs\n",
        "        run: node --test tests/test_document_url_authorization.cjs\n",
        "        run: node --test tests/test_novel_file_authorization.cjs\n",
        "          node --test tests/test_private_book_authorization.cjs\n",
        "        run: python3 scripts/validate_site.py\n",
        "          python3 scripts/validate_sinjira_catalogues_metadata.py --self-test\n",
        "          python3 scripts/validate_sinjira_catalogues_metadata.py\n",
    )
    for command in required_verify:
        if verify.count(command) != 1:
            errors.append("Commande de validation absente ou dupliquée : " + command.strip())
    if verify.count(f"uses: actions/checkout@{CHECKOUT}") != 1:
        errors.append("Checkout des catalogues non épinglé")
    if verify.count("persist-credentials: false") != 1:
        errors.append("Identifiants GitHub persistés dans le checkout")
    if verify.count(f"uses: actions/setup-python@{PYTHON}") != 1:
        errors.append("Python du job principal non épinglé")
    if verify.count("python-version: '3.12.14'") != 1:
        errors.append("Version Python du job principal non épinglée")

    if visual.count("    needs: verify\n") != 1:
        errors.append("Les navigateurs doivent dépendre du job verify")
    if visual.count("    if: github.event_name == 'pull_request'\n") != 1:
        errors.append("Les navigateurs ne doivent être exécutés que sur PR")
    if visual.count("    runs-on: ubuntu-24.04\n") != 1:
        errors.append("Runner navigateur non épinglé")
    if visual.count("    timeout-minutes: 15\n") != 1:
        errors.append("Délai navigateur requis")
    if visual.count("        browser: [chromium, firefox, webkit]\n") != 1:
        errors.append("Les trois moteurs navigateur sont obligatoires")
    if visual.count("      fail-fast: false\n") != 1:
        errors.append("Les trois navigateurs doivent rendre leur verdict")
    if visual.count(f"      image: {PLAYWRIGHT}\n") != 1:
        errors.append("Conteneur Playwright non épinglé au digest")
    if visual.count('run: python -m pip install --disable-pip-version-check "playwright==1.61.0"') != 1:
        errors.append("Paquet Playwright non figé")
    if visual.count("run: python tests/e2e/test_sinjira_catalogues_visual.py\n") != 1:
        errors.append("Vrai test des images et ancres absent")
    if visual.count("run: python tests/e2e/test_nova_survey_visual.py\n") != 1:
        errors.append("Vrai parcours du sondage 18+ absent")
    if "          BROWSER: \${{ matrix.browser }}\n".replace(r"\$", "$") not in visual:
        errors.append("Navigateur matriciel non transmis aux tests")
    if "python -m http.server 4173 --bind 127.0.0.1" not in visual:
        errors.append("Serveur local de test manquant")
    if visual.count(f"uses: actions/checkout@{CHECKOUT}") != 1:
        errors.append("Checkout des navigateurs non épinglé")
    if visual.count("persist-credentials: false") != 1:
        errors.append("Identifiants GitHub persistés par les navigateurs")
    if visual.count(f"uses: actions/setup-python@{PYTHON}") != 1:
        errors.append("Python du navigateur non épinglé")
    if re.search(r"(?m)^    (?:continue-on-error|permissions):", visual) or re.search(
        r"(?m)^        continue-on-error:", visual
    ):
        errors.append("Échec navigateur ignoré ou permissions supplémentaires")
    if any(word in active for word in ("pages: write", "id-token: write",
                                       "actions/deploy-pages@", "upload-pages-artifact@")):
        errors.append("La vérification des catalogues ne doit pas publier")
    return errors


def self_test(source: str) -> None:
    assert not validate(source), validate(source)
    mutations = {
        "filtre PR réintroduit": (
            "    types: [opened, synchronize, reopened, ready_for_review]\n",
            "    types: [opened, synchronize, reopened, ready_for_review]\n"
            "    paths:\n      - 'projets/sinjira/**'\n",
        ),
        "push filtré": (
            "  push:\n    branches: [main]\n",
            "  push:\n    branches: [main]\n"
            "    paths-ignore:\n      - 'assets/js/**'\n",
        ),
        "PR désactivée": ("  pull_request:\n", "  pull_request_disabled:\n"),
        "branche de PR détournée": ("    branches: [main]\n",
                                    "    branches: [develop]\n"),
        "synchronisation ignorée": (
            "opened, synchronize, reopened, ready_for_review",
            "opened, reopened, ready_for_review",
        ),
        "mode ready for review ignoré": (
            "opened, synchronize, reopened, ready_for_review",
            "opened, synchronize, reopened",
        ),
        "job principal conditionnel": (
            "  verify:\n", "  verify:\n    if: false\n",
        ),
        "échec principal toléré": (
            "    timeout-minutes: 10\n",
            "    timeout-minutes: 10\n    continue-on-error: true\n",
        ),
        "contrat de CI neutralisé": (
            "          python3 scripts/validate_sinjira_catalogues_workflow.py\n",
            "          echo PAS_DE_CONTRAT_CI\n",
        ),
        "autotest neutralisé": (
            "          python3 scripts/validate_sinjira_catalogues_workflow.py --self-test\n",
            "          echo PAS_D_AUTOTEST\n",
        ),
        "bibliothèque non testée": (
            "        run: node --test tests/test_sinjira_library_access.cjs\n",
            "        run: echo TEST_BIBLIOTHEQUE_IGNORÉ\n",
        ),
        "autorisation document non testée": (
            "        run: node --test tests/test_document_url_authorization.cjs\n",
            "        run: echo PAS_DE_TEST_DROITS\n",
        ),
        "tests navigateur ignorés": (
            "    needs: verify\n", "    needs: verify\n    continue-on-error: true\n",
        ),
        "matrice réduite": (
            "browser: [chromium, firefox, webkit]",
            "browser: [chromium]",
        ),
        "navigateur non épinglé": (
            "mcr.microsoft.com/playwright/python:v1.61.0-noble@sha256:",
            "mcr.microsoft.com/playwright/python:latest#",
        ),
        "test visuel remplacé": (
            "run: python tests/e2e/test_sinjira_catalogues_visual.py",
            "run: echo VISUEL_NON_TESTÉ",
        ),
        "contrat sondage Nova retiré": (
            "          python3 scripts/validate_nova_survey.py\n",
            "          echo SONDAGE_NON_TESTÉ\n",
        ),
        "parcours sondage Nova retiré": (
            "run: python tests/e2e/test_nova_survey_visual.py",
            "run: echo SONDAGE_NAVIGATEUR_IGNORÉ",
        ),
        "PR visuelle désactivée": (
            "    if: github.event_name == 'pull_request'\n",
            "    if: false\n",
        ),
        "publication injectée": (
            "permissions:\n  contents: read\n",
            "permissions:\n  contents: read\n  pages: write\n",
        ),
    }
    for name, (original, replacement) in mutations.items():
        if original not in source:
            raise AssertionError("Mutation impossible : " + name)
        candidate = source.replace(original, replacement, 1)
        if candidate == source or not validate(candidate):
            raise AssertionError("Régression de la CI non détectée : " + name)
    print(
        f"OK workflow catalogues universel : {len(mutations)} mutations "
        "de déclenchement/test/publication refusées"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    source = WORKFLOW.read_text("utf-8")
    if args.self_test:
        self_test(source)
    issues = validate(source)
    for issue in issues:
        print("ERREUR : " + issue)
    if issues:
        return 1
    print("OK workflow catalogues : PR et main universels, trois navigateurs, zéro publication")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
