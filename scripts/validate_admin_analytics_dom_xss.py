#!/usr/bin/env python3
"""Bloque les régressions XSS du tableau analytique administrateur.

Le navigateur doit écrire les données de contribution exclusivement avec
textContent et des éléments DOM créés, jamais avec un interpréteur HTML.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'assets/js/sinjira-admin.js'
EDGE = ROOT / 'supabase/functions/admin-analytics/index.ts'

REQUIRED_CLIENT = {
    'authentification côté client': "await requireUser('/compte/connexion.html')",
    'invocation admin-analytics': "supabase.functions.invoke('admin-analytics'",
    'rendu DOM unique': 'function renderSafeAnalyticsTable(node, entries)',
    'création de ligne sûre': "document.createElement('tr')",
    'création de cellule sûre': "document.createElement('td')",
    'libellé uniquement texte': "name.textContent = String(label ?? '');",
    'comptage uniquement texte': "value.textContent = String(count ?? '');",
    'remplacement atomique des enfants': "node.replaceChildren(...elements);",
    'message absence de données': "[['Aucune donnée', null]]",
    'cellule colspan': "name.colSpan = 2;",
    'tableau de résultats': "renderSafeAnalyticsTable(results, Object.entries(a.results || {})",
    'tableau de difficulté': "renderSafeAnalyticsTable(difficulty, Object.entries(a.difficulty || {})",
    'tableau des cartes': "renderSafeAnalyticsTable(cards, (Array.isArray(a.top_cards) ? a.top_cards : [])",
    'libellé manquant neutre': "[label || 'Non indiqué', count]",
}
REQUIRED_EDGE = {
    'authentification admin AAL2': 'await requiredAdmin(req)',
    'données analytiques réduites': ".select('metrics,feedback')",
    'réponse sans cache': "'Cache-Control': 'private, no-store, max-age=0'",
    'méthode POST': "req.method !== 'POST'",
}
FORBIDDEN_PATTERNS = (
    re.compile(r'\.(?:innerHTML|outerHTML)\s*='),
    re.compile(r'\binsertAdjacentHTML\s*\('),
    re.compile(r'\bdocument\.write\s*\('),
    re.compile(r'\bnew\s+DOMParser\s*\('),
)


def validate(client: str, edge: str) -> list[str]:
    errors: list[str] = []
    for label, marker in REQUIRED_CLIENT.items():
        if marker not in client:
            errors.append('XSS analytique : contrôle client absent : '+label)
    for label, marker in REQUIRED_EDGE.items():
        if marker not in edge:
            errors.append('XSS analytique : contrat serveur absent : '+label)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(client):
            errors.append('XSS analytique : un interpréteur HTML dynamique est réintroduit')
    if client.count("renderSafeAnalyticsTable(results,") != 1:
        errors.append('Tableau résultats non rendu par DOM texte exactement une fois')
    if client.count("renderSafeAnalyticsTable(difficulty,") != 1:
        errors.append('Tableau difficulté non rendu par DOM texte exactement une fois')
    if client.count("renderSafeAnalyticsTable(cards,") != 1:
        errors.append('Tableau cartes non rendu par DOM texte exactement une fois')
    if client.count("document.createElement('td')") != 2:
        errors.append('Le helper de tableau doit créer deux cellules DOM sûres')
    auth = client.find("await requireUser('/compte/connexion.html')")
    invoke = client.find("supabase.functions.invoke('admin-analytics'")
    result = client.find("renderSafeAnalyticsTable(results,")
    difficulty = client.find("renderSafeAnalyticsTable(difficulty,")
    cards = client.find("renderSafeAnalyticsTable(cards,")
    if min(auth,invoke,result,difficulty,cards) < 0 or not (
        auth < invoke < result < difficulty < cards
    ):
        errors.append('L’ordre auth/invocation/tableaux doit rester strict')
    return errors


def self_test(client: str, edge: str) -> None:
    if errors := validate(client, edge):
        raise AssertionError('Version saine invalide : '+' ; '.join(errors))
    mutations = [
        ('HTML dans libellés', 'client',
         "name.textContent = String(label ?? '');",
         "name.innerHTML = String(label ?? '');"),
        ('HTML dans comptages', 'client',
         "value.textContent = String(count ?? '');",
         "value.innerHTML = String(count ?? '');"),
        ('HTML au niveau du tableau', 'client',
         'node.replaceChildren(...elements);',
         "node.innerHTML = String(elements);"),
        ('script via insertAdjacentHTML', 'client',
         "node.replaceChildren(...elements);",
         "node.insertAdjacentHTML('beforeend',String(elements));"),
        ('résultats sans helper', 'client',
         "renderSafeAnalyticsTable(results, Object.entries(a.results || {})",
         "results.innerHTML = Object.entries(a.results || {})"),
        ('difficultés sans helper', 'client',
         "renderSafeAnalyticsTable(difficulty, Object.entries(a.difficulty || {})",
         "difficulty.innerHTML = Object.entries(a.difficulty || {})"),
        ('cartes sans helper', 'client',
         "renderSafeAnalyticsTable(cards, (Array.isArray(a.top_cards) ? a.top_cards : [])",
         "cards.innerHTML = ((a.top_cards || [])"),
        ('cellule de carte absente', 'client',
         "document.createElement('td')",
         "document.createElement('span')"),
        ('sans option valeur manquante', 'client',
         "[['Aucune donnée', null]]",
         "[['', null]]"),
        ('sans client authentifié', 'client',
         "await requireUser('/compte/connexion.html')",
         "await Promise.resolve()"),
        ('sans permission admin AAL2', 'edge',
         "await requiredAdmin(req)", "await requiredUser(req)"),
        ('cache administrateur public', 'edge',
         "'Cache-Control': 'private, no-store, max-age=0'",
         "'Cache-Control': 'public, max-age=300'"),
    ]
    for label, component, old, replacement in mutations:
        target = client if component == 'client' else edge
        matches = target.count(old)
        # Une cellule td est déclarée deux fois : muter la première seulement.
        if matches != (2 if label == 'cellule de carte absente' else 1):
            raise AssertionError(f'Mutation invalide : {label} ({matches} occurrences)')
        changed = target.replace(old,replacement,1)
        checked_client = changed if component == 'client' else client
        checked_edge = changed if component == 'edge' else edge
        if not validate(checked_client,checked_edge):
            raise AssertionError('Régression XSS non détectée : '+label)
    print(f'OK sécurité DOM analytique : {len(mutations)} mutations détectées.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test',action='store_true')
    args = parser.parse_args()
    client = CLIENT.read_text('utf-8')
    edge = EDGE.read_text('utf-8')
    if args.self_test:
        self_test(client,edge)
    errors = validate(client,edge)
    if errors:
        for error in errors:
            print('ÉCHEC : '+error)
        return 1
    print('OK sécurité DOM analytique : trois tableaux en texte, authentification AAL2.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
