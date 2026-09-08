#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / '.github' / 'workflows' / 'main-governance.yml'
CONTRACT_WORKFLOW = ROOT / '.github' / 'workflows' / 'main-governance-contract.yml'


def require(errors, condition, message):
    if not condition:
        errors.append(message)


def validate_governance_text(text):
    errors = []
    lower = text.lower()

    require(errors, 'name: gouvernance main sinjira' in lower, 'nom canonique du workflow absent')
    require(
        errors,
        re.search(r'(?m)^on:\s*$\n\s{2}push:\s*$\n\s{4}branches:\s*\[main\]\s*$', text) is not None,
        'le workflow doit se déclencher sur tout push vers main',
    )
    for forbidden in ('paths:', 'paths-ignore:', 'branches-ignore:'):
        require(errors, forbidden not in lower, f'filtre de déclenchement interdit: {forbidden}')

    require(errors, re.search(r'(?m)^permissions:\s*$', text) is not None, 'permissions explicites absentes')
    require(errors, re.search(r'(?m)^\s{2}contents:\s*read\s*$', text) is not None, 'contents doit rester en lecture seule')
    require(errors, re.search(r'(?m)^\s{2}pull-requests:\s*read\s*$', text) is not None, 'pull-requests doit rester en lecture seule')
    require(errors, re.search(r'(?im)^\s*[a-z0-9_-]+:\s*write\s*$', text) is None, 'permission write interdite dans le workflow de détection')

    for marker, message in (
        ('repos.listPullRequestsAssociatedWithCommit', 'association commit → PR non vérifiée'),
        ('commit_sha: sha', 'le SHA courant doit être utilisé pour la recherche de PR'),
        ("pr.merged_at && pr.base?.ref === 'main'", 'la PR doit être fusionnée explicitement vers main'),
        ('if (!mergedToMain)', 'branche de refus des pushes directs absente'),
        ('core.setFailed(', 'un push direct doit faire échouer le job'),
        ("process.env.GITHUB_REF_PROTECTED === 'true'", 'état serveur GITHUB_REF_PROTECTED non contrôlé'),
        ("core.warning('La branche main n’est pas protégée", 'alerte main non protégée absente'),
    ):
        require(errors, marker in text, message)

    for forbidden in ('continue-on-error: true', 'continue-on-error:true'):
        require(errors, forbidden not in lower, 'le contrôle ne doit jamais être rendu non bloquant')

    return errors


def validate_contract_workflow(text):
    errors = []
    lower = text.lower()
    require(errors, 'name: contrat gouvernance main sinjira' in lower, 'nom du workflow contrat absent')
    require(errors, re.search(r'(?m)^\s{2}pull_request:\s*$', text) is not None, 'le contrat doit tourner sur les PR vers main')
    require(errors, re.search(r'(?m)^\s{2}push:\s*$', text) is not None, 'le contrat doit aussi tourner après push sur main')
    require(errors, lower.count('branches: [main]') >= 2, 'PR et push doivent tous deux cibler main')
    require(errors, 'python scripts/validate_main_governance_contract.py --self-test' in text, 'auto-tests du validateur absents')
    require(errors, 'python scripts/validate_main_governance_contract.py' in text, 'validation du workflow réel absente')
    require(errors, re.search(r'(?m)^\s{2}contents:\s*read\s*$', text) is not None, 'workflow contrat: contents doit être read')
    require(errors, re.search(r'(?im)^\s*[a-z0-9_-]+:\s*write\s*$', text) is None, 'workflow contrat: permission write interdite')
    return errors


def run_self_tests(canonical):
    cases = {
        'sans push main': canonical.replace('  push:\n    branches: [main]\n', ''),
        'avec filtre paths': canonical.replace('    branches: [main]\n', '    branches: [main]\n    paths: ["scripts/**"]\n', 1),
        'sans échec': canonical.replace('core.setFailed(', 'core.info(', 1),
        'PR non fusionnée': canonical.replace("pr.merged_at && pr.base?.ref === 'main'", "pr.base?.ref === 'main'", 1),
        'permission écriture': canonical.replace('contents: read', 'contents: write', 1),
        'contrôle protection retiré': canonical.replace("process.env.GITHUB_REF_PROTECTED === 'true'", "'true' === 'true'", 1),
    }
    for name, mutated in cases.items():
        if not validate_governance_text(mutated):
            raise SystemExit(f'ERREUR auto-test gouvernance main: mutation non détectée: {name}')
    print(f'OK auto-tests gouvernance main: {len(cases)} affaiblissements critiques détectés.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    governance = GOVERNANCE.read_text('utf-8')
    if args.self_test:
        run_self_tests(governance)
        return 0

    errors = validate_governance_text(governance)
    if not CONTRACT_WORKFLOW.is_file():
        errors.append('workflow de contrat main-governance-contract.yml absent')
    else:
        errors.extend(validate_contract_workflow(CONTRACT_WORKFLOW.read_text('utf-8')))

    if errors:
        for error in errors:
            print(f'ERREUR contrat gouvernance main: {error}')
        return 1

    print('OK contrat gouvernance main: tout push main est surveillé, les pushes sans PR échouent, permissions lecture seule et alerte protection serveur conservées.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
