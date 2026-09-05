#!/usr/bin/env python3
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'histoire-de-vie' / 'remise.html'
CLIENT = ROOT / 'assets' / 'js' / 'sinjira-life-story-delivery-v24-5-50.js'
DELIVERY = ROOT / 'supabase' / 'functions' / 'life-story-delivery' / 'index.ts'
EXPORT = ROOT / 'supabase' / 'functions' / 'life-story-export' / 'index.ts'
CONFIG = ROOT / 'supabase' / 'config.toml'
LEDGER = ROOT / 'supabase' / 'production-migration-ledger.txt'
MIGRATIONS = ROOT / 'supabase' / 'migrations'
DOC = ROOT / 'LIFE_STORY_DELIVERY_PRIVACY_V24_5_50.md'


def read(path: Path) -> str:
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def compact(value: str) -> str:
    return re.sub(r'\s+', '', value.lower())


def main() -> int:
    errors: list[str] = []
    for path in (PAGE, CLIENT, DELIVERY, EXPORT, CONFIG, LEDGER, DOC):
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors:
            print('- ' + error)
        return 1

    page = read(PAGE)
    page_low = page.lower()
    client = read(CLIENT)
    delivery = read(DELIVERY)
    delivery_flat = compact(delivery)
    export = read(EXPORT)
    config = tomllib.loads(read(CONFIG))
    ledger = read(LEDGER)
    doc = read(DOC).lower()

    page_markers = [
        'noindex,nofollow,noarchive,nosnippet',
        'no-referrer',
        "default-src 'none'",
        'connect-src https://gpvivleexywljowcqkru.supabase.co',
        '/assets/js/sinjira-life-story-delivery-v24-5-50.js?v=24.5.50',
        'le registre des consciences n’est pas une source',
    ]
    for marker in page_markers:
        if marker not in page_low:
            errors.append(f'Page de remise incomplète: {marker}')
    for forbidden in ('google-analytics', 'googletagmanager', 'facebook.com/tr', 'segment.io', 'mixpanel', 'hotjar'):
        if forbidden in page_low:
            errors.append(f'Analytique externe interdite sur la page de remise: {forbidden}')

    client_markers = [
        'location.hash',
        'history.replaceState',
        "method: 'POST'",
        "'Content-Type': 'application/json'",
        'JSON.stringify({ token })',
        "cache: 'no-store'",
        "credentials: 'omit'",
        "referrerPolicy: 'no-referrer'",
        'MAX_PDF_BYTES = 15 * 1024 * 1024',
        "'%PDF-'",
        'URL.createObjectURL',
        'URL.revokeObjectURL',
    ]
    for marker in client_markers:
        if marker not in client:
            errors.append(f'Client de remise incomplet: {marker}')
    replace_pos = client.find('history.replaceState')
    fetch_pos = client.find('fetch(')
    if replace_pos < 0 or fetch_pos < 0 or replace_pos > fetch_pos:
        errors.append('Le fragment secret doit être retiré avant le premier fetch réseau.')
    for forbidden in ('localStorage', 'sessionStorage', 'document.cookie', '?token=', 'sendBeacon'):
        if forbidden in client:
            errors.append(f'Client de remise: stockage/transport du jeton interdit: {forbidden}')

    delivery_markers = [
        "req.method !== 'POST'",
        'requestUrl.search',
        'MAX_REQUEST_BYTES=256',
        'MAX_PDF_BYTES=15*1024*1024',
        "type.startsWith('application/json')",
        'Object.keys(body).length!==1',
        '/^[a-f0-9]{64}$/',
        'sha256Hex(token)',
        "eq('token_hash',hash)",
        'revoked_at',
        'expires_at',
        'max_downloads',
        'download_count',
        "record.storage_bucket!=='sinjira-life-story-exports'",
        'hasPdfSignature(bytes)',
        "String.fromCharCode(...head)==='%PDF-'",
        "service.rpc('service_life_story_register_download'",
        'allowedOrigin(req)',
        "'https://www.benoitcantin.com'",
        "'https://benoitcantin.com'",
        "'Cache-Control':'private,no-store,max-age=0'",
        "'Referrer-Policy':'no-referrer'",
        "'X-Frame-Options':'DENY'",
    ]
    for marker in delivery_markers:
        if compact(marker) not in delivery_flat:
            errors.append(f'Edge delivery incomplète: {marker}')
    if "searchparams.get('token')" in delivery.lower() or 'searchparams.get("token")' in delivery.lower():
        errors.append('Le backend ne doit jamais lire le jeton depuis la query string.')
    validate_pos = delivery.find('hasPdfSignature(bytes)')
    count_pos = delivery.find("service.rpc('service_life_story_register_download'")
    if validate_pos < 0 or count_pos < 0 or validate_pos > count_pos:
        errors.append('Le PDF doit être validé avant de consommer un téléchargement.')

    export_markers = [
        "const DELIVERY_PAGE = 'https://www.benoitcantin.com/histoire-de-vie/remise.html'",
        '`${DELIVERY_PAGE}#${raw}`',
        'crypto.getRandomValues(new Uint8Array(32))',
        'sha256Hex(raw)',
        'token_hash: tokenHash',
        'source_boundary',
        'registry_access_prohibited',
        "transport: 'manual_or_future_sender'",
    ]
    for marker in export_markers:
        if marker not in export:
            errors.append(f'Edge export incomplète: {marker}')
    if '?token=' in export:
        errors.append('life-story-export ne doit plus générer de jeton dans la query string.')
    for forbidden in ('reader_characters', 'registry_account_links'):
        if forbidden in export:
            errors.append(f'life-story-export ne doit pas interroger le Registre: {forbidden}')

    functions = config.get('functions', {})
    if functions.get('life-story-delivery', {}).get('verify_jwt') is not False:
        errors.append('life-story-delivery doit rester verify_jwt=false avec authentification custom.')
    if functions.get('life-story-export', {}).get('verify_jwt') is not True:
        errors.append('life-story-export doit rester verify_jwt=true.')

    # Contrat historique : V24.5.50 n'a aucune migration SQL propre.
    # Le ledger global courant est validé séparément par validate_production_migration_ledger.py.
    rows = [line.strip() for line in ledger.splitlines() if line.strip() and not line.startswith('#')]
    baseline = '20260831004411 sinjira_v24_5_46_preorder_uuid_output_hardening'
    if rows.count(baseline) != 1:
        errors.append('La baseline historique V24.5.46 doit apparaître exactement une fois dans le ledger.')
    if any('v24_5_50' in line.lower() for line in rows):
        errors.append('V24.5.50 ne doit pas ajouter de ligne au ledger SQL.')
    if any('v24_5_50' in path.name.lower() for path in MIGRATIONS.glob('*.sql')):
        errors.append('V24.5.50 ne doit pas ajouter de migration SQL.')

    for marker in ('256 bits', 'fragment', 'post', '15 mib', '0 lien', '174 migrations', 'aucun paiement', 'registre des consciences'):
        if marker not in doc:
            errors.append(f'Document V24.5.50 incomplet: {marker}')

    paid_tokens = ('stripe', 'paypal', 'api.resend.com', 'twilio', 'shippo', 'easypost', 'fedex', 'purolator', 'openai.com/v1')
    combined = '\n'.join((client.lower(), delivery.lower(), export.lower(), page_low))
    for token in paid_tokens:
        if token in combined:
            errors.append(f'Service externe/payant interdit dans V24.5.50: {token}')

    if errors:
        print(f'ECHEC V24.5.50 remise Histoire de vie: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK V24.5.50: jeton 256 bits en fragment, retrait avant réseau, POST JSON borné, PDF validé avant comptage, réponses no-store, aucune migration V24.5.50 ni service payant.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
