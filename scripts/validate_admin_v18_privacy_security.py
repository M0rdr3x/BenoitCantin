#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-sinjira-v18/index.ts'
CLIENT = ROOT / 'assets/js/sinjira-admin-v18.js'
LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*262_?144\s*;')

EDGE_REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'admin explicite': 'requiredAdmin(req)',
    'JSON strict': "contentType!=='application/json'",
    'lecture bornée': 'readBoundedJson(req)',
    'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'nosniff': "'X-Content-Type-Options':'nosniff'",
    'no-referrer': "'Referrer-Policy':'no-referrer'",
    'log allowlisté': 'SAFE_LOG_CODES',
    'fallback backend fixe': "'ADMIN_V18_BACKEND_FAILED'",
    'confirmation purge serveur': 'b.author_confirmed_source_purge!==true',
    'état purge chargé': "select('photo_path,source_purged_at')",
    'purge déjà faite refusée': "if(sub.source_purged_at)throw new Error('SOURCE_PURGED')",
    'erreur Storage capturée': "const {error:storageError}=await s.storage.from('sinjira-character-sources').remove([sub.photo_path])",
    'échec Storage fermé': "if(storageError)throw new Error('SOURCE_PURGE_STORAGE_FAILED')",
    'confirmation CANON': "canonStatus==='CANON'&&c.author_confirmed_canon!==true",
    'verrou retcon Roman I': "novel?.slug==='la-cendre-du-jugement'&&c.author_confirmed_retcon!==true",
    'IA distante désactivée': "code:'REMOTE_AI_DISABLED_FREE_ONLY'",
    'photo signée courte': "createSignedUrl(sub.photo_path,600)",
    'santé backend sanitizée': "code:error?'CHECK_FAILED':null",
}

CLIENT_REQUIRED = {
    'confirmation visuelle destructive': "confirm('Supprimer définitivement les réponses sources personnelles de ce dossier?",
    'confirmation purge transmise': 'author_confirmed_source_purge:true',
    'confirmation CANON transmise': 'author_confirmed_canon:Boolean(',
    'confirmation retcon transmise': 'author_confirmed_retcon:Boolean(',
}

EDGE_FORBIDDEN = {
    'JSON direct non borné': 'await req.json()',
    'auth admin indirecte': 'requiredUser(req)',
    'service client recréé avant admin': 'serviceClient()',
    'log global brut': "console.error('[admin-sinjira-v18]',e)",
    'log message brut': "console.error('[admin-sinjira-v18]',e?.message)",
    'message backend dans system_health': 'error:error?.message',
}


def validate(edge_path: Path, client_path: Path) -> list[str]:
    try:
        edge = edge_path.read_text('utf-8', errors='strict')
        client = client_path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'Fichier admin V18 illisible: {exc}']

    errors: list[str] = []
    for label, marker in EDGE_REQUIRED.items():
        if marker not in edge:
            errors.append(f'Garde admin V18 absent: {label}.')
    for label, marker in CLIENT_REQUIRED.items():
        if marker not in client:
            errors.append(f'Garde client admin V18 absent: {label}.')
    if not LIMIT_RE.search(edge):
        errors.append('Garde admin V18 absent ou affaibli: requête exactement bornée à 262144 octets.')

    lowered = edge.lower()
    for label, marker in EDGE_FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde admin V18 violé: {label}.')

    auth_pos = edge.find('const {user,service:s}=await requiredAdmin(req)')
    body_pos = edge.find('const b=await readBoundedJson(req)')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre admin/corps V18 impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('Le corps V18 ne doit pas être lu avant admin/JWT/AAL2.')

    confirm_pos = edge.find('b.author_confirmed_source_purge!==true')
    select_pos = edge.find("select('photo_path,source_purged_at')")
    already_pos = edge.find("if(sub.source_purged_at)throw new Error('SOURCE_PURGED')")
    remove_pos = edge.find("remove([sub.photo_path])")
    storage_check_pos = edge.find("if(storageError)throw new Error('SOURCE_PURGE_STORAGE_FAILED')")
    db_update_pos = edge.find("update({source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()})")
    if min(confirm_pos, select_pos, already_pos, remove_pos, storage_check_pos, db_update_pos) < 0:
        errors.append('Ordre de purge V18 impossible à vérifier.')
    elif not (confirm_pos < select_pos < already_pos < remove_pos < storage_check_pos < db_update_pos):
        errors.append('La purge doit confirmer, vérifier l’état, supprimer Storage avec contrôle d’erreur, puis seulement purger la DB.')

    safe_log_pos = edge.find("console.error('[admin-sinjira-v18]',adminV18LogCode(e))")
    fallback_pos = edge.find("return SAFE_LOG_CODES.has(code)?code:'ADMIN_V18_BACKEND_FAILED'")
    if safe_log_pos < 0 or fallback_pos < 0:
        errors.append('Les logs V18 doivent rester sanitizés par allowlist et fallback fixe.')

    ui_confirm_pos = client.find("confirm('Supprimer définitivement les réponses sources personnelles de ce dossier?")
    client_call_pos = client.find("call('purge_submission_source'")
    client_flag_pos = client.find('author_confirmed_source_purge:true')
    if min(ui_confirm_pos, client_call_pos, client_flag_pos) < 0:
        errors.append('Ordre confirmation client/purge V18 impossible à vérifier.')
    elif not (ui_confirm_pos < client_call_pos <= client_flag_pos):
        errors.append('Le client doit demander confirmation avant d’envoyer la purge confirmée.')

    if edge.count("author_confirmed_canon!==true") != 1:
        errors.append('La confirmation humaine CANON doit rester unique et obligatoire.')
    if edge.count("author_confirmed_retcon!==true") != 1:
        errors.append('La confirmation humaine retcon Roman I doit rester unique et obligatoire.')
    return errors


def self_test() -> None:
    edge = EDGE.read_text('utf-8', errors='strict')
    client = CLIENT.read_text('utf-8', errors='strict')
    clean = validate(EDGE, CLIENT)
    if clean:
        raise AssertionError('Les fichiers réels sains doivent passer: ' + ' | '.join(clean))

    edge_cases = {
        'limite augmentée': edge.replace('MAX_REQUEST_BYTES=262144;', 'MAX_REQUEST_BYTES=1048576;', 1),
        'admin après corps': edge.replace(
            'const {user,service:s}=await requiredAdmin(req);\n    const b=await readBoundedJson(req)',
            'const b=await readBoundedJson(req)\n    const {user,service:s}=await requiredAdmin(req);',
            1,
        ),
        'confirmation purge serveur retirée': edge.replace("if(b.author_confirmed_source_purge!==true)throw new Error('SOURCE_PURGE_CONFIRMATION_REQUIRED');", '', 1),
        'idempotence purge retirée': edge.replace("if(sub.source_purged_at)throw new Error('SOURCE_PURGED');", '', 1),
        'erreur Storage ignorée': edge.replace("if(storageError)throw new Error('SOURCE_PURGE_STORAGE_FAILED');", '', 1),
        'log backend brut': edge.replace("console.error('[admin-sinjira-v18]',adminV18LogCode(e));", "console.error('[admin-sinjira-v18]',e);", 1),
        'message santé brut': edge.replace("code:error?'CHECK_FAILED':null", 'error:error?.message||null', 1),
        'no-store retiré': edge.replace("'Cache-Control':'private, no-store, max-age=0',", '', 1),
        'confirmation CANON retirée': edge.replace("if(canonStatus==='CANON'&&c.author_confirmed_canon!==true)throw new Error('CANON_CONFIRMATION_REQUIRED');", '', 1),
        'verrou retcon retiré': edge.replace("&&c.author_confirmed_retcon!==true", '', 1),
        'IA distante réactivée': edge.replace("code:'REMOTE_AI_DISABLED_FREE_ONLY'", "code:'REMOTE_AI_ENABLED'", 1),
        'durée photo signée augmentée': edge.replace('createSignedUrl(sub.photo_path,600)', 'createSignedUrl(sub.photo_path,86400)', 1),
    }
    client_cases = {
        'confirmation UI retirée': client.replace("if(!confirm('Supprimer définitivement les réponses sources personnelles de ce dossier? Le personnage créé et sa Bible seront conservés.'))return;", '', 1),
        'marqueur serveur retiré': client.replace(',author_confirmed_source_purge:true', '', 1),
    }

    with TemporaryDirectory() as tmp:
        edge_path = Path(tmp) / 'index.ts'
        client_path = Path(tmp) / 'client.js'
        client_path.write_text(client, encoding='utf-8')
        for label, mutated in edge_cases.items():
            if mutated == edge:
                raise AssertionError(f'Auto-test invalide, mutation Edge sans effet: {label}')
            edge_path.write_text(mutated, encoding='utf-8')
            if not validate(edge_path, client_path):
                raise AssertionError(f'Affaiblissement Edge non détecté: {label}')
        edge_path.write_text(edge, encoding='utf-8')
        for label, mutated in client_cases.items():
            if mutated == client:
                raise AssertionError(f'Auto-test invalide, mutation client sans effet: {label}')
            client_path.write_text(mutated, encoding='utf-8')
            if not validate(edge_path, client_path):
                raise AssertionError(f'Affaiblissement client non détecté: {label}')
    print(f'OK auto-test admin V18: {len(edge_cases)+len(client_cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la confidentialité, les purges irréversibles et les décisions humaines de admin-sinjira-v18.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(EDGE, CLIENT)
    if errors:
        print(f'ÉCHEC sécurité admin V18: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK admin V18: AAL2 avant corps, purge explicitement confirmée et fail-closed, logs/health sanitizés, CANON/retcon humains préservés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
