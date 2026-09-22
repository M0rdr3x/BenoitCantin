#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/'.github/workflows/validate-safety-v24-4-82.yml'
CHECKOUT_SHA='d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA='ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION='3.12.14'
SELF='python scripts/validate_minor_safety_workflow_security.py --self-test'
META='python scripts/validate_minor_safety_workflow_security.py'
CONTRACT='python scripts/validate_minor_exploitation_safety_v24_4_82.py'
LEDGER='python scripts/validate_production_migration_ledger.py'
TRIGGER="      - 'scripts/validate_minor_safety_workflow_security.py'\n"
FORBIDDEN=('supabase db push','supabase functions deploy','supabase secrets set','supabase link')

def validate_text(text:str)->list[str]:
    errors:list[str]=[]
    def need(ok:bool,msg:str)->None:
        if not ok: errors.append(msg)
    need('permissions:\n  contents: read' in text,'permissions.contents doit rester read')
    need('contents: write' not in text,'permission contents:write interdite')
    need(re.search(r'\$\{\{\s*secrets\.',text) is None,'aucun secret GitHub ne doit être référencé')
    need('pull_request_target:' not in text,'pull_request_target interdit')
    need('runs-on: ubuntu-24.04' in text,'runner Ubuntu 24.04 exact requis')
    need('ubuntu-latest' not in text,'ubuntu-latest interdit')
    need('timeout-minutes: 5' in text,'timeout 5 minutes requis')
    need(text.count(f'actions/checkout@{CHECKOUT_SHA}')==1,'checkout SHA exact requis')
    need(text.count(f'actions/setup-python@{SETUP_PYTHON_SHA}')==1,'setup-python SHA exact requis')
    need(text.count('persist-credentials: false')==1,'credentials checkout non persistés requis')
    need('persist-credentials: true' not in text,'persist-credentials=true interdit')
    need(f"python-version: '{PYTHON_VERSION}'" in text,'Python exact requis')
    actions=re.findall(r'^\s*-?\s*uses:\s+(\S+)\s*$',text,flags=re.MULTILINE)
    need(len(actions)==2,f'nombre inattendu d actions réutilisables: {len(actions)}')
    for action in actions:
        need(re.search(r'@[0-9a-f]{40}$',action) is not None,f'action non immuable: {action}')
    for cmd in (SELF,META,CONTRACT,LEDGER):
        need(text.count(f'        run: {cmd}\n')==1,f'commande directe et unique requise: {cmd}')
    order=[text.find(x) for x in (SELF,META,CONTRACT,LEDGER)]
    need(all(x>=0 for x in order) and order==sorted(order),
         'ordre requis: auto-test métagarde -> métagarde -> contrat mineurs -> ledger')
    need(text.count(TRIGGER)==2,'le métagarde doit déclencher pull_request et push')
    need('continue-on-error: true' not in text,'continue-on-error interdit')
    for cmd in FORBIDDEN:
        need(cmd not in text,f'commande production distante interdite: {cmd}')
    return errors

def self_test(text:str)->None:
    mutations={
      'checkout mobile':text.replace(f'actions/checkout@{CHECKOUT_SHA}','actions/checkout@v4',1),
      'python mobile':text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}','actions/setup-python@v5',1),
      'runner mobile':text.replace('ubuntu-24.04','ubuntu-latest',1),
      'python large':text.replace(f"python-version: '{PYTHON_VERSION}'","python-version: '3.12'",1),
      'credentials persistés':text.replace('persist-credentials: false','persist-credentials: true',1),
      'permission écriture':text.replace('contents: read','contents: write',1),
      'pull_request_target':text.replace('  pull_request:\n','  pull_request_target:\n',1),
      'auto-test retiré':text.replace(f'        run: {SELF}\n','',1),
      'métagarde retiré':text.replace(f'        run: {META}\n','',1),
      'contrat retiré':text.replace(f'        run: {CONTRACT}\n','',1),
      'ledger retiré':text.replace(f'        run: {LEDGER}\n','',1),
      'déclencheur retiré':text.replace(TRIGGER,'',1),
      'production ajoutée':text+'\n# supabase db push\n',
    }
    base=validate_text(text)
    if base:
        raise SystemExit('ERREUR auto-test workflow mineurs: source invalide: '+'; '.join(base))
    for label,mutated in mutations.items():
        if mutated==text: raise SystemExit(f'ERREUR auto-test workflow mineurs: mutation sans effet: {label}')
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test workflow mineurs: mutation non détectée: {label}')
    print(f'OK auto-test workflow sécurité mineurs: {len(mutations)}/{len(mutations)} affaiblissements critiques détectés.')

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if not WORKFLOW.is_file():
        print(f'ÉCHEC workflow sécurité mineurs: absent: {WORKFLOW.relative_to(ROOT)}')
        return 1
    text=WORKFLOW.read_text('utf-8',errors='strict')
    if args.self_test:
        self_test(text); return 0
    errors=validate_text(text)
    if errors:
        print(f'ÉCHEC workflow sécurité mineurs: {len(errors)} problème(s).')
        for error in errors: print('- '+error)
        return 1
    print('OK workflow sécurité mineurs: actions/runtimes immuables, credentials non persistés, preuves locales avant ledger production bloquant.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
