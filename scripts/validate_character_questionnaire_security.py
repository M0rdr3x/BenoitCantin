#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/submit-character-questionnaire/index.ts'
REQUEST_LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*2\s*\*\s*1024\s*\*\s*1024\s*;')
ANSWER_LIMIT_RE = re.compile(r'\bMAX_ANSWERS_CHARS\s*=\s*500000\s*;')

REQUIRED = {
    'version fonctionnelle stable': "const VERSION='24.5.2';",
    'POST uniquement': "req.method!=='POST'",
    'auth utilisateur explicite': 'requiredUser(req)',
    'lecture JSON bornée': 'readBoundedJson(req)',
    'content-type JSON strict': "if(contentType!=='application/json')throw new Error('JSON_REQUIRED');",
    'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'nosniff': "'X-Content-Type-Options':'nosniff'",
    'no-referrer': "'Referrer-Policy':'no-referrer'",
    'IA distante désactivée': 'const REMOTE_AI_ENABLED=false;',
    'services payants désactivés': 'const PAID_EXTERNAL_SERVICES_ENABLED=false;',
    'filtre données privées': "if(PRIVATE_KEYS.includes(k)||k.startsWith('parent_')||k.startsWith('photo'))continue",
    'état demande interrogé': "service.from('character_submissions').select('*').eq('user_id',user.id)",
    'état personnage interrogé': "service.from('characters').select('id,status,submission_id').eq('user_id',user.id)",
    'état unique fail-closed': "if(submissionResult.error||characterResult.error)throw new Error('CHARACTER_STATE_LOOKUP_FAILED');",
    'unicité compte': "code:'ONE_CHARACTER_PER_ACCOUNT'",
    'mise à jour existante explicitement demandée': 'owner&&update_existing&&(existingSubmission||existingCharacter)',
    'photo limitée au compte': "String(photo_path).startsWith(`${user.id}/`)",
    'traversée photo refusée': "String(photo_path).includes('..')",
    'canon provisoire': "canon_status:'PROVISOIRE'",
    'revue auteur': "status:'author_review'",
    'Roman I verrouillé dans le prompt': 'Le Roman 1 — La Cendre du Jugement est verrouillé.',
    'arbitrage non automatique': 'Les éléments À ARBITRER ne sont jamais tranchés automatiquement.',
    'pas de coordonnées dans génération': 'Ne produis jamais de coordonnées personnelles.',
    'log principal sanitizé': "console.error('[submit-character-questionnaire]',safeLogCode(e));",
    'notification admin sanitizée': "console.warn('[submit-character-questionnaire]','ADMIN_NOTIFICATION_FAILED')",
    'courriel admin sanitizé': "console.warn('[submit-character-questionnaire]','ADMIN_EMAIL_FAILED')",
    'courriel participant sanitizé': "console.warn('[submit-character-questionnaire]','PARTICIPANT_EMAIL_FAILED')",
    'erreur génération persistée fixe': "error_text:'CHARACTER_GENERATION_FAILED'",
    'MFA fermé': "e?.message==='MFA_STATE_UNAVAILABLE'||e?.message==='SECURITY_STATE_UNAVAILABLE'",
    'JSON requis explicite': "e?.message==='JSON_REQUIRED'",
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'helper JSON générique': 'return json(',
    'import helper JSON générique': 'corsHeaders,json',
    'log erreur principal brut': 'console.error(e)',
    'log notification backend brut': "console.warn('admin notification unavailable',e)",
    'log resend backend brut': "console.warn('admin resend',await r.text())",
    'log courriel backend brut': "console.warn('admin email failed',e)",
    'log participant backend brut': "console.warn('participant resend',await r.text())",
    'erreur génération brute persistée': "error_text:String(e?.message||e)",
}


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'submit-character-questionnaire illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde questionnaire absent: {label}.')
    if not REQUEST_LIMIT_RE.search(source):
        errors.append('Garde questionnaire absent ou affaibli: corps exactement borné à 2 MiB.')
    if not ANSWER_LIMIT_RE.search(source):
        errors.append('Garde questionnaire absent ou affaibli: limite sémantique de 500000 caractères.')

    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde questionnaire violé: {label}.')

    auth_pos = source.find('const user=await requiredUser(req);')
    body_pos = source.find('const body=await readBoundedJson(req);')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre auth/corps impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('Le questionnaire ne doit pas être lu avant auth/JWT/MFA.')

    state_check = source.find("if(submissionResult.error||characterResult.error)throw new Error('CHARACTER_STATE_LOOKUP_FAILED');")
    uniqueness = source.find("code:'ONE_CHARACTER_PER_ACCOUNT'")
    if state_check < 0 or uniqueness < 0 or state_check > uniqueness:
        errors.append('Les erreurs de lecture de l’état doivent bloquer avant la décision un-personnage-par-compte.')

    private_success = source.count('return privateJson(successPayload(')
    if private_success < 3:
        errors.append('Toutes les réponses de succès contenant le dossier doivent rester privées/no-store.')
    if source.count('privateJson(') < 14:
        errors.append('Les réponses du questionnaire doivent rester uniformément privées/no-store.')

    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'json direct': real.replace('const body=await readBoundedJson(req);', 'const body=await req.json();', 1),
        'content-type retiré': real.replace("  if(contentType!=='application/json')throw new Error('JSON_REQUIRED');\n", '', 1),
        'no-store retiré': real.replace("'Cache-Control':'private, no-store, max-age=0',", '', 1),
        'limite HTTP augmentée': real.replace('MAX_REQUEST_BYTES=2*1024*1024;', 'MAX_REQUEST_BYTES=20*1024*1024;', 1),
        'limite réponses augmentée': real.replace('MAX_ANSWERS_CHARS=500000;', 'MAX_ANSWERS_CHARS=5000000;', 1),
        'ordre auth inversé': real.replace(
            'const user=await requiredUser(req);\n    const service=serviceClient();\n    const body=await readBoundedJson(req);',
            'const body=await readBoundedJson(req);\n    const user=await requiredUser(req);\n    const service=serviceClient();',
            1,
        ),
        'erreurs état ignorées': real.replace("    if(submissionResult.error||characterResult.error)throw new Error('CHARACTER_STATE_LOOKUP_FAILED');\n", '', 1),
        'unicité retirée': real.replace("code:'ONE_CHARACTER_PER_ACCOUNT'", "code:'DUPLICATE_ALLOWED'", 1),
        'IA distante activée': real.replace('const REMOTE_AI_ENABLED=false;', 'const REMOTE_AI_ENABLED=true;', 1),
        'services payants activés': real.replace('const PAID_EXTERNAL_SERVICES_ENABLED=false;', 'const PAID_EXTERNAL_SERVICES_ENABLED=true;', 1),
        'canon automatique': real.replace("canon_status:'PROVISOIRE'", "canon_status:'CANON'", 1),
        'revue auteur retirée': real.replace("status:'author_review'", "status:'approved'", 1),
        'filtre privé retiré': real.replace("if(PRIVATE_KEYS.includes(k)||k.startsWith('parent_')||k.startsWith('photo'))continue;", '', 1),
        'photo hors compte acceptée': real.replace("!String(photo_path).startsWith(`${user.id}/`)||", '', 1),
        'log principal brut': real.replace("console.error('[submit-character-questionnaire]',safeLogCode(e));", 'console.error(e);', 1),
        'log notification brut': real.replace("console.warn('[submit-character-questionnaire]','ADMIN_NOTIFICATION_FAILED')", "console.warn('admin notification unavailable',e)", 1),
        'erreur génération brute': real.replace("error_text:'CHARACTER_GENERATION_FAILED'", "error_text:String(e?.message||e)", 1),
        'réponse succès cacheable': real.replace('return privateJson(successPayload(sub.id,{ai_generated:false},n))', 'return json(successPayload(sub.id,{ai_generated:false},n))', 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test questionnaire Registre: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la confidentialité et l’unicité fail-closed du questionnaire privé du Registre.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC questionnaire Registre: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK questionnaire Registre: auth/MFA avant corps, JSON 2 MiB, réponses privées, unicité fail-closed, IA distante désactivée et canon humain préservé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
