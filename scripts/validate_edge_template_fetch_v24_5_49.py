#!/usr/bin/env python3
from pathlib import Path
import re
import tomllib

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'supabase/functions/send-game-report/index.ts'
CONFIG=ROOT/'supabase/config.toml'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'EDGE_TEMPLATE_FETCH_HARDENING_V24_5_49.md'
INVENTORY=ROOT/'scripts/validate_edge_function_inventory.py'


def read(path:Path)->str:
    return path.read_text('utf-8',errors='ignore') if path.exists() else ''


def main()->int:
    errors=[]
    for path in (REPORT,CONFIG,LEDGER,DOC,INVENTORY):
        if not path.exists(): errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors: print('- '+error)
        return 1

    report=read(REPORT)
    doc=read(DOC).lower()
    inventory=read(INVENTORY)
    config=tomllib.loads(read(CONFIG))
    ledger_rows=[x.strip() for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    report_markers=[
        'MAX_REQUEST_BYTES=220_000',
        'MAX_TEMPLATE_BYTES=15*1024*1024',
        "DEFAULT_TEMPLATE_URL='https://www.benoitcantin.com/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fracture_du_Reseau_Mere_Fiche_Joueur_Web.pdf'",
        "TEMPLATE_ORIGIN='https://www.benoitcantin.com'",
        "TEMPLATE_PATH_PREFIX='/projets/sinjira/jeux/fracture-du-reseau-mere/documents/'",
        "url.protocol!=='https:'",
        'url.origin!==TEMPLATE_ORIGIN',
        '!url.pathname.startsWith(TEMPLATE_PATH_PREFIX)',
        "!url.pathname.toLowerCase().endsWith('.pdf')",
        'url.username || url.password || url.search || url.hash',
        "redirect:'error'",
        "cache:'no-store'",
        'declared>MAX_TEMPLATE_BYTES',
        'bytes.byteLength===0||bytes.byteLength>MAX_TEMPLATE_BYTES',
        "String.fromCharCode(...bytes.subarray(0,5))!=='%PDF-'",
        'REPORT_TEMPLATE_URL_NOT_ALLOWED',
        'REPORT_TEMPLATE_TOO_LARGE',
        'REPORT_TEMPLATE_NOT_PDF',
        'PAID_EXTERNAL_SERVICES_ENABLED=false',
        "'Cache-Control': 'private, no-store, max-age=0'",
        "'Referrer-Policy': 'no-referrer'",
    ]
    for marker in report_markers:
        if marker not in report: errors.append(f'send-game-report: garde-fou absent: {marker}')

    if re.search(r"fetch\s*\(\s*(?:TEMPLATE_URL|Deno\.env\.get\(['\"]REPORT_TEMPLATE_URL)",report):
        errors.append('Le modèle ne doit pas être téléchargé directement depuis une URL non validée.')
    if re.search(r'PAID_EXTERNAL_SERVICES_ENABLED\s*=\s*true',report,re.I):
        errors.append('Le transport externe payant ne doit jamais être activé par V24.5.49.')

    cfg=config.get('functions',{}).get('send-game-report',{})
    if cfg.get('verify_jwt') is not False:
        errors.append('send-game-report: verify_jwt doit rester false pour le contrat custom-auth/public existant.')

    inventory_markers=[
        'MAX_TEMPLATE_BYTES=15*1024*1024',
        "TEMPLATE_ORIGIN='https://www.benoitcantin.com'",
        "redirect:'error'",
        'REPORT_TEMPLATE_TOO_LARGE',
        '%PDF-',
    ]
    for marker in inventory_markers:
        if marker not in inventory: errors.append(f'Inventaire Edge non aligné V24.5.49: {marker}')

    if len(ledger_rows)!=174:
        errors.append(f'Ledger: {len(ledger_rows)} migrations au lieu de 174.')
    expected_last='20260831004411 sinjira_v24_5_46_preorder_uuid_output_hardening'
    if not ledger_rows or ledger_rows[-1]!=expected_last:
        errors.append('V24.5.49 ne doit ajouter aucune migration Supabase.')

    doc_markers=[
        '15 mib','redirect: \'error\'','%pdf-','174 migrations','version 6',
        'paid_external_services_enabled=false','aucun paiement','aucun transporteur',
        'https://www.benoitcantin.com','/projets/sinjira/jeux/fracture-du-reseau-mere/documents/'
    ]
    for marker in doc_markers:
        if marker not in doc: errors.append(f'Document V24.5.49 incomplet: {marker}')

    if errors:
        print(f'ECHEC V24.5.49 modèle PDF Fracture: {len(errors)} problème(s).')
        for error in errors: print('- '+error)
        return 1
    print('OK V24.5.49: modèle PDF limité à l’origine SINJIRA, redirections refusées, 15 MiB max, signature PDF vérifiée, services payants désactivés et ledger 174 inchangé.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
