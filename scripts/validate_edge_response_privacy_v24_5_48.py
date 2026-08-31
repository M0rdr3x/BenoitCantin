#!/usr/bin/env python3
from pathlib import Path
import re
import tomllib

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'supabase/functions/send-game-report/index.ts'
DOCURL=ROOT/'supabase/functions/get-document-url/index.ts'
CONFIG=ROOT/'supabase/config.toml'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'EDGE_RESPONSE_PRIVACY_V24_5_48.md'


def read(path:Path)->str:
    return path.read_text('utf-8',errors='ignore') if path.exists() else ''


def compact(text:str)->str:
    return re.sub(r'\s+',' ',text).lower()


def main()->int:
    errors=[]
    for path in (REPORT,DOCURL,CONFIG,LEDGER,DOC):
        if not path.exists(): errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors: print('- '+error)
        return 1

    report=read(REPORT); report_low=compact(report)
    docurl=read(DOCURL); docurl_low=compact(docurl)
    doc=read(DOC).lower()
    ledger_rows=[x.strip() for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]
    config=tomllib.loads(read(CONFIG))

    report_markers=[
        'MAX_REQUEST_BYTES=220_000',
        'TextEncoder().encode(raw).byteLength',
        "'Cache-Control': 'private, no-store, max-age=0'",
        "'Referrer-Policy': 'no-referrer'",
        "'X-Content-Type-Options': 'nosniff'",
        'PAID_EXTERNAL_SERVICES_ENABLED=false',
        'optionalUser(req)',
        ".eq('user_id', userId)",
    ]
    for marker in report_markers:
        if marker not in report: errors.append(f'send-game-report: garde-fou absent: {marker}')

    doc_markers=[
        'MAX_REQUEST_BYTES=8_192',
        'UUID_RE=',
        'TextEncoder().encode(raw).byteLength',
        "doc.status!=='approved'",
        "doc.projects?.status!=='active'",
        'externalUrlAllowed',
        "value.startsWith('/')&&!value.startsWith('//')",
        "new URL(value).protocol==='https:'",
        'createSignedUrl(doc.storage_path,600)',
        "'Cache-Control':'private, no-store, max-age=0'",
        "'Referrer-Policy':'no-referrer'",
        "'X-Content-Type-Options':'nosniff'",
    ]
    for marker in doc_markers:
        if marker not in docurl: errors.append(f'get-document-url: garde-fou absent: {marker}')

    if ".select('*" in docurl_low or ".select(\"*" in docurl_low:
        errors.append('get-document-url ne doit plus sélectionner toutes les colonnes du document.')

    functions=config.get('functions',{})
    for slug in ('get-document-url','send-game-report'):
        cfg=functions.get(slug,{})
        if cfg.get('verify_jwt') is not False:
            errors.append(f'{slug}: verify_jwt doit rester false pour son contrat custom-auth/public actuel.')

    if len(ledger_rows)!=174:
        errors.append(f'Ledger: {len(ledger_rows)} migrations au lieu de 174.')
    expected_last='20260831004411 sinjira_v24_5_46_preorder_uuid_output_hardening'
    if not ledger_rows or ledger_rows[-1]!=expected_last:
        errors.append('V24.5.48 ne doit pas modifier la dernière migration production.')

    for marker in ('174 migrations','private, no-store','220 000','8 kib','https','paid_external_services_enabled=false','aucun paiement','aucun transporteur'):
        if marker not in doc: errors.append(f'Document V24.5.48 incomplet: {marker}')

    forbidden_enabled=[
        r'PAID_EXTERNAL_SERVICES_ENABLED\s*=\s*true',
        r'REMOTE_AI_ENABLED\s*=\s*true',
        r'payment_enabled\s*=\s*true',
        r'checkout_enabled\s*=\s*true',
    ]
    joined=report+'\n'+docurl
    for pattern in forbidden_enabled:
        if re.search(pattern,joined,re.I): errors.append(f'Activation interdite détectée: {pattern}')

    if errors:
        print(f'ECHEC V24.5.48 confidentialité Edge: {len(errors)} problème(s).')
        for error in errors: print('- '+error)
        return 1
    print('OK V24.5.48: liens signés et PDF no-store, taille réelle bornée, URL sûres, services payants désactivés, ledger 174 inchangé.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
