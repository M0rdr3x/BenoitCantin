#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / '.github' / 'workflows' / 'main-governance.yml'
CONTRACT_WORKFLOW = ROOT / '.github' / 'workflows' / 'main-governance-contract.yml'
README = ROOT / 'README.md'
GITHUB_SCRIPT_SHA = 'ed597411d8f924073f98dfc5c65a23a2325f34cd'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'


def require(errors, condition, message):
    if not condition:
        errors.append(message)


def action_targets(text):
    targets = []
    for line in text.splitlines():
        match = re.match(r'^\s*(?:-\s*)?uses:\s+(\S+)', line)
        if match:
            targets.append(match.group(1))
    return targets


def validate_immutable_actions(errors, text, label):
    targets = action_targets(text)
    require(errors, bool(targets), f'{label}: aucune action réutilisable détectée')
    for target in targets:
        require(
            errors,
            re.search(r'@[0-9a-f]{40}$', target) is not None,
            f'{label}: référence d’action non immuable: {target}',
        )


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

    require(
        errors,
        f'uses: actions/github-script@{GITHUB_SCRIPT_SHA}' in text,
        'actions/github-script doit rester épinglé au SHA vérifié',
    )
    validate_immutable_actions(errors, text, 'workflow gouvernance main')

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


def validate_project_principles(text):
    errors = []
    lower = text.lower()

    for marker, message in (
        ('## principes obligatoires', 'section Principes obligatoires absente du README canonique'),
        ("### l'humain avant tout", "principe L'humain avant tout absent"),
        ('### protéger sans surveiller', 'principe Protéger sans surveiller absent'),
        ("### solaire : surfaces déjà artificialisées d'abord", 'principe solaire surfaces artificialisées d’abord absent'),
        ('la priorité est obligatoire', 'caractère obligatoire de la priorité solaire absent'),
        ('toitures de bâtiments', 'priorité solaire sur les toitures absente'),
        ('stationnements avec ombrières solaires', 'priorité solaire sur les stationnements absente'),
        ('friches déjà artificialisées', 'priorité solaire sur les friches artificialisées absente'),
        ('une forêt', 'protection des forêts absente du principe solaire'),
        ('une terre agricole productive', 'protection des terres agricoles absente du principe solaire'),
        ('un milieu humide', 'protection des milieux humides absente du principe solaire'),
        ('un habitat naturel', 'protection des habitats naturels absente du principe solaire'),
        ('non une simple préférence', 'le principe solaire doit rester un critère obligatoire, pas une préférence'),
    ):
        require(errors, marker in lower, message)

    return errors


def validate_contract_workflow(text):
    errors = []
    lower = text.lower()
    require(errors, 'name: contrat gouvernance main sinjira' in lower, 'nom du workflow contrat absent')
    require(errors, re.search(r'(?m)^\s{2}pull_request:\s*$', text) is not None, 'le contrat doit tourner sur les PR vers main')
    require(errors, re.search(r'(?m)^\s{2}push:\s*$', text) is not None, 'le contrat doit aussi tourner après push sur main')
    require(errors, lower.count('branches: [main]') >= 2, 'PR et push doivent tous deux cibler main')
    require(errors, lower.count("- 'readme.md'") >= 2, 'README.md doit déclencher le contrat sur PR et push main')
    require(errors, 'python scripts/validate_main_governance_contract.py --self-test' in text, 'auto-tests du validateur absents')
    require(errors, 'python scripts/validate_main_governance_contract.py' in text, 'validation du workflow réel absente')
    require(errors, re.search(r'(?m)^\s{2}contents:\s*read\s*$', text) is not None, 'workflow contrat: contents doit être read')
    require(errors, re.search(r'(?im)^\s*[a-z0-9_-]+:\s*write\s*$', text) is None, 'workflow contrat: permission write interdite')
    require(
        errors,
        f'uses: actions/checkout@{CHECKOUT_SHA}' in text,
        'workflow contrat: actions/checkout doit rester épinglé au SHA vérifié',
    )
    require(errors, 'persist-credentials: false' in text, 'workflow contrat: credentials Git ne doivent pas être persistés')
    require(errors, 'persist-credentials: true' not in text, 'workflow contrat: persist-credentials=true interdit')
    validate_immutable_actions(errors, text, 'workflow contrat gouvernance main')
    return errors


def run_self_tests(governance, readme, contract):
    governance_cases = {
        'sans push main': governance.replace('  push:\n    branches: [main]\n', ''),
        'avec filtre paths': governance.replace('    branches: [main]\n', '    branches: [main]\n    paths: ["scripts/**"]\n', 1),
        'sans échec': governance.replace('core.setFailed(', 'core.info(', 1),
        'PR non fusionnée': governance.replace("pr.merged_at && pr.base?.ref === 'main'", "pr.base?.ref === 'main'", 1),
        'permission écriture': governance.replace('contents: read', 'contents: write', 1),
        'contrôle protection retiré': governance.replace("process.env.GITHUB_REF_PROTECTED === 'true'", "'true' === 'true'", 1),
        'github-script mobile': governance.replace(
            f'actions/github-script@{GITHUB_SCRIPT_SHA}',
            'actions/github-script@v8',
            1,
        ),
    }
    for name, mutated in governance_cases.items():
        if not validate_governance_text(mutated):
            raise SystemExit(f'ERREUR auto-test gouvernance main: mutation non détectée: {name}')

    principle_cases = {
        'humain retiré': readme.replace("### L'humain avant tout", '### Principe retiré', 1),
        'protéger sans surveiller retiré': readme.replace('### Protéger sans surveiller', '### Principe retiré', 1),
        'solaire non obligatoire': readme.replace('la priorité est obligatoire', 'la priorité est souhaitable', 1),
        'toitures retirées': readme.replace('toitures de bâtiments', 'surfaces disponibles', 1),
        'stationnements retirés': readme.replace('stationnements avec ombrières solaires', 'espaces disponibles', 1),
        'forêts non protégées': readme.replace('une forêt', 'un espace', 1),
        'terres agricoles non protégées': readme.replace('une terre agricole productive', 'une parcelle', 1),
        'préférence seulement': readme.replace('non une simple préférence', 'une simple préférence', 1),
    }
    for name, mutated in principle_cases.items():
        if not validate_project_principles(mutated):
            raise SystemExit(f'ERREUR auto-test principes obligatoires: mutation non détectée: {name}')

    contract_cases = {
        'checkout mobile': contract.replace(
            f'actions/checkout@{CHECKOUT_SHA}',
            'actions/checkout@v6',
            1,
        ),
        'credentials persistés': contract.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'permission écriture contrat': contract.replace('contents: read', 'contents: write', 1),
    }
    for name, mutated in contract_cases.items():
        if not validate_contract_workflow(mutated):
            raise SystemExit(f'ERREUR auto-test contrat gouvernance main: mutation non détectée: {name}')

    total = len(governance_cases) + len(principle_cases) + len(contract_cases)
    print(f'OK auto-tests gouvernance main: {total} affaiblissements critiques détectés.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    governance = GOVERNANCE.read_text('utf-8')
    readme = README.read_text('utf-8')
    contract = CONTRACT_WORKFLOW.read_text('utf-8') if CONTRACT_WORKFLOW.is_file() else ''
    if args.self_test:
        if not contract:
            raise SystemExit('ERREUR auto-test gouvernance main: workflow contrat absent')
        run_self_tests(governance, readme, contract)
        return 0

    errors = validate_governance_text(governance)
    errors.extend(validate_project_principles(readme))
    if not CONTRACT_WORKFLOW.is_file():
        errors.append('workflow de contrat main-governance-contract.yml absent')
    else:
        errors.extend(validate_contract_workflow(contract))

    if errors:
        for error in errors:
            print(f'ERREUR contrat gouvernance main: {error}')
        return 1

    print('OK contrat gouvernance main: pushes main surveillés, principes obligatoires conservés, permissions lecture seule, actions immuables et alerte protection serveur conservées.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
