#!/usr/bin/env python3
"""Refuse tout élargissement de la procédure GitHub de déploiement Edge SINJIRA.

Le vérificateur travaille uniquement sur le fichier YAML local. Zéro secret,
réseau, déploiement, compte ou accès à la base Supabase.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-registry-edge-scoped-deploy.yml'
GUARD = ("github.event_name == 'workflow_dispatch' && inputs.apply == true && "
         "inputs.confirmation == 'DEPLOY-SINJIRA-REGISTRY-EDGE' && "
         "github.ref == 'refs/heads/main'")
COMMAND = 'supabase functions deploy submit-character-questionnaire --project-ref "$PROJECT_ID" --use-api'


def validate(source: str) -> list[str]:
    errors: list[str] = []

    def need(marker: str, message: str) -> None:
        if marker not in source:
            errors.append(message)

    need('name: SINJIRA — déploiement ciblé Edge Registre', 'Nom de procédure cible absent.')
    need('  pull_request:\n', 'Tests sur PR absents.')
    need('  push:\n', 'Tests sur main absents.')
    need('  workflow_dispatch:\n', 'Déclenchement manuel absent.')
    need('        default: false', 'Apply doit être false par défaut.')
    need('        default: "PREFLIGHT_ONLY"', 'Confirmation sûre par défaut absente.')
    need('permissions:\n  contents: read\n', 'Permissions GitHub non minimales.')
    need('  cancel-in-progress: false', 'Annulation automatique de déploiement interdite.')
    need('  contract:\n', 'Job de tests sans secret absent.')
    need('  deploy:\n', 'Job de déploiement absent.')
    need('    needs: contract\n', 'Déploiement doit dépendre des tests.')
    need('    if: ${{ ' + GUARD + ' }}', 'Job de déploiement non limité à main/manuel/confirmation.')
    need('    environment: production\n', 'Frontière production absente.')
    need('          persist-credentials: false', 'Checkout sans identifiants persistants absent.')
    need('          ref: ${{ github.sha }}', 'Checkout du commit exact testé absent.')
    need("test \"$GITHUB_REF\" = 'refs/heads/main'", 'Vérification de branche après approbation absente.')
    need('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
         'Identité du commit entre tests et déploiement non contrôlée.')
    need("test \"$CONFIRMATION\" = 'DEPLOY-SINJIRA-REGISTRY-EDGE'",
         'Confirmation explicite après approbation absente.')
    need("grep -Fq 'isCanonicalRegistryPhotoPath(photo_path,user.id)'",
         'Contrôle du garde photo canonique absent.')
    need("config['functions']['submit-character-questionnaire']['verify_jwt'] is True",
         'Vérification de JWT pour ce slug absent.')
    need('      PROJECT_ID: gpvivleexywljowcqkru', 'Projet de production non figé.')
    need('          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
         'Jeton de production borné à une étape absent.')
    need('          version: 2.111.0', 'CLI Supabase v2 non épinglée.')
    need('uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803',
         'Checkout non épinglé.')
    need('uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444',
         'Node non épinglé.')
    need('uses: supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf',
         'Installation de CLI non épinglée.')
    need("          node-version: '22.16.0'", 'Node de CI non épinglé.')
    need('node scripts/test_sinjira_character_photo_path.cjs',
         'Test de l’authenticité du validateur Edge absent.')
    need('python3 scripts/verify_sinjira_registry_edge_deployment.py --self-test',
         'Autotest des versions Edge absent.')
    need('python3 scripts/verify_sinjira_registry_edge_deployment.py',
         'Comparaison de versions Edge absente.')
    need('--before /tmp/sinjira-registry-edge-before.txt',
         'Version de production avant déploiement non vérifiée.')
    need('--after /tmp/sinjira-registry-edge-after.txt',
         'Version de production après déploiement non vérifiée.')
    need('python3 scripts/validate_sinjira_registry_edge_scoped_deploy.py --self-test',
         'Auto-test du garde de déploiement absent.')
    need(COMMAND, 'Commande de déploiement mono-slug attendue absente.')

    if source.count(COMMAND) != 1:
        errors.append('Une seule commande exacte de déploiement autorisée.')
    if source.count('supabase functions deploy') != 1:
        errors.append('Second déploiement Edge interdit.')
    if source.count('    environment: production\n') != 1:
        errors.append('Un seul job peut accéder à l’environnement production.')
    if source.count('      - name: Déployer uniquement submit-character-questionnaire\n') != 1:
        errors.append('Étape de déploiement ciblée manquante.')
    if source.count('          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}') != 3:
        errors.append('Secret de production attendu dans exactement trois étapes bornées.')

    left, sep, deploy = source.partition('\n  deploy:\n')
    if not sep:
        errors.append('Séparation entre contrat et déploiement absente.')
    else:
        if 'secrets.' in left or 'SUPABASE_ACCESS_TOKEN' in left:
            errors.append('Aucun secret dans les jobs PR/push.')
        if 'supabase functions deploy' in left:
            errors.append('Déploiement sans approbation interdit.')
        if deploy.count('if: ${{ ' + GUARD + ' }}') != 3:
            errors.append('Garde manuel/main/confirmation requise sur job et deux étapes.')
        if not deploy.startswith('    name: Application manuelle du SEUL contrôleur Registre\n'):
            errors.append('Job d’application ciblé incorrect.')

    for forbidden in (
        'supabase db push', 'supabase migration repair', 'supabase db reset',
        '--include-all', '--prune', '--no-verify-jwt', 'supabase secrets set',
        'continue-on-error: true', 'contents: write', 'ubuntu-latest',
        'curl --insecure', 'set -x'
    ):
        if forbidden in source:
            errors.append('Primitive interdite dans ce workflow: ' + forbidden)
    return errors


def self_test() -> None:
    original = WORKFLOW.read_text('utf-8')
    assert not validate(original), 'Workflow initial non conforme : ' + ' | '.join(validate(original))
    mutations = {
        'autoriser PR': original.replace('    if: ${{ ' + GUARD + ' }}',
                                       "    if: ${{ github.event_name == 'pull_request' }}", 1),
        'retirer environnement': original.replace('    environment: production\n', '', 1),
        'étendre toutes les fonctions': original.replace(COMMAND,
                                                         'supabase functions deploy --project-ref "$PROJECT_ID" --use-api', 1),
        'JWT désactivé': original.replace(COMMAND, COMMAND + ' --no-verify-jwt', 1),
        'application par défaut': original.replace('        default: false', '        default: true', 1),
        'déployer depuis main flottant': original.replace(
            '          ref: ${{ github.sha }}', '          ref: main', 1),
        'retirer contrôle SHA': original.replace(
            'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', 'true', 1),
        'supprimer preuve de nouvelle version': original.replace(
            'python3 scripts/verify_sinjira_registry_edge_deployment.py \\',
            'true', 1),
        'retirer contrôle photo': original.replace(
            "grep -Fq 'isCanonicalRegistryPhotoPath(photo_path,user.id)'", 'true', 1),
        'supprimer confirmation': original.replace(
            "test \"$CONFIRMATION\" = 'DEPLOY-SINJIRA-REGISTRY-EDGE'", 'true', 1),
        'appliquer les migrations': original.replace(COMMAND, COMMAND + '\n          supabase db push', 1),
        'secret accessible aux PR': original.replace(
            '    timeout-minutes: 7\n',
            '    timeout-minutes: 7\n    env:\n'
            '      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n', 1),
        'rendre JWT optionnel': original.replace(
            "config['functions']['submit-character-questionnaire']['verify_jwt'] is True",
            "config['functions']['submit-character-questionnaire']['verify_jwt'] is not False", 1),
    }
    for label, bad in mutations.items():
        if bad == original:
            raise AssertionError('Mutation invalide non appliquée: ' + label)
        if not validate(bad):
            raise AssertionError('Affaiblissement non détecté: ' + label)
    print(f'OK déploiement ciblé : {len(mutations)} mutations dangereuses détectées.')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        errors = validate(WORKFLOW.read_text('utf-8'))
        if errors:
            raise SystemExit('ÉCHEC déploiement Registre Edge : ' + ' | '.join(errors))
        print('OK Edge Registre: un seul slug, revue production, confirmation manuelle, aucun secret en PR, aucune migration.')


if __name__ == '__main__':
    main()
