#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/submit-fracture-endgame/index.ts'
MIGRATION = ROOT / 'supabase/migrations/20260911225500_sinjira_v25_fracture_endgame_atomic_submit.sql'
REQUEST_LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4096\s*;')
PARTY_RE = re.compile(r'\^FRM-\[A-Z0-9\]\{6\}\$')

EDGE_REQUIRED = {
    'auth partagée': "import { requiredUser, serviceClient } from '../_shared/auth.ts';",
    'POST uniquement': "req.method !== 'POST'",
    'auth avant traitement': 'const user = await requiredUser(req);',
    'lecture texte bornable': 'const rawBody = await req.text();',
    'taille UTF-8 réelle': 'new TextEncoder().encode(rawBody).byteLength',
    'content-type JSON': "contentType.startsWith('application/json')",
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma': 'no-cache'",
    'nosniff': "'X-Content-Type-Options': 'nosniff'",
    'no-referrer': "'Referrer-Policy': 'no-referrer'",
    'lecture partie minimisée': ".select('id,party_code,owner_user_id,human_player_count,effective_player_count,play_mode,round_count,updated_at,status')",
    'erreur lecture partie fail-closed': "if (partyError) throw new Error('PARTY_LOOKUP_FAILED');",
    'lecture rapport minimisée': ".select('id,party_id,owner_user_id,fields,submitted_at,updated_at')",
    'erreur lecture rapport fail-closed': "if (reportError) throw new Error('REPORT_LOOKUP_FAILED');",
    'propriétaire rapport vérifié': "if (report.owner_user_id !== user.id) throw new Error('REPORT_OWNER_INCONSISTENT');",
    'RPC transactionnelle': ".rpc('service_submit_fracture_endgame'",
    'snapshot partie transmis': 'p_party_updated_at: party.updated_at',
    'snapshot rapport transmis': 'p_report_updated_at: report.updated_at',
    'doublon idempotent traité': 'submitResult?.already_submitted === true',
    'services payants désactivés': 'const PAID_EXTERNAL_SERVICES_ENABLED = false;',
    'log RPC sanitizé': "code: codeFromRpc || 'FRACTURE_ENDGAME_RPC_FAILED'",
    'log final sanitizé': "code: 'FRACTURE_ENDGAME_FAILED'",
}

EDGE_FORBIDDEN = {
    'JSON direct non borné': 'await req.json()',
    'insert contribution direct': ".from('internal_gameplay_contributions').insert",
    'update rapport direct': ".from('fracture_endgame_reports').update",
    'update partie direct': ".from('fracture_parties').update",
    'update session direct': ".from('game_sessions').update",
    'log erreur brute': 'console.error(error)',
    'log exception brute': 'console.error(e)',
    'log RPC brut': 'console.error(submitError)',
    'message RPC renvoyé': 'submitError.message',
}

SQL_REQUIRED = {
    'RPC service': 'create or replace function public.service_submit_fracture_endgame(',
    'security definer': 'security definer',
    'search_path fermé': "set search_path to 'pg_catalog','public','auth'",
    'service_role obligatoire': "if coalesce(auth.jwt()->>'role','') <> 'service_role' then",
    'propriétaire obligatoire': "if v_party.owner_user_id <> p_user_id then raise exception 'fracture_owner_required'; end if;",
    'rapport lié au compte': 'where id = p_report_id and party_id = p_party_id and owner_user_id = p_user_id',
    'détection contribution existante': "c.source_kind = 'fracture_endgame'",
    'réparation idempotente': "'already_submitted', true",
    'archive préservée': "if v_party.status = 'archived' then",
    'réparation partie seulement active': "where id = p_party_id and status = 'in_progress';",
    'partie active': "if v_party.status <> 'in_progress' then raise exception 'fracture_party_not_active'; end if;",
    'rapport non soumis': "if v_report.submitted_at is not null then raise exception 'fracture_endgame_inconsistent'; end if;",
    'snapshot partie': "v_party.updated_at is distinct from p_party_updated_at",
    'snapshot rapport': "v_report.updated_at is distinct from p_report_updated_at",
    'insert contribution': 'insert into public.internal_gameplay_contributions(',
    'rapport finalisé': 'update public.fracture_endgame_reports',
    'partie finalisée': 'update public.fracture_parties',
    'sessions finalisées': 'update public.game_sessions',
    'session obligatoire': "if v_session_count < 1 then raise exception 'fracture_session_not_found'; end if;",
    'ACL révoquée': 'from public, anon, authenticated;',
    'ACL service_role': 'to service_role;',
}


def validate(edge_path: Path, migration_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        edge = edge_path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'Edge Fracture illisible: {exc}']
    try:
        sql = migration_path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'Migration Fracture illisible: {exc}']

    for label, marker in EDGE_REQUIRED.items():
        if marker not in edge:
            errors.append(f'Garde Edge Fracture absent: {label}.')
    if not REQUEST_LIMIT_RE.search(edge):
        errors.append('Garde Edge Fracture absent ou affaibli: corps exactement borné à 4096 octets.')
    if not PARTY_RE.search(edge):
        errors.append('Garde Edge Fracture absent ou affaibli: code de partie FRM strict.')

    lowered_edge = edge.lower()
    for label, marker in EDGE_FORBIDDEN.items():
        if marker.lower() in lowered_edge:
            errors.append(f'Garde Edge Fracture violé: {label}.')

    auth_pos = edge.find('const user = await requiredUser(req);')
    body_pos = edge.find('const rawBody = await req.text();')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre auth/corps Fracture impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('La fin de partie ne doit pas lire le corps avant authentification.')

    sql_lower = sql.lower()
    for label, marker in SQL_REQUIRED.items():
        if marker not in sql_lower:
            errors.append(f'Garde SQL Fracture absent: {label}.')
    if sql_lower.count('for update;') < 2:
        errors.append('La RPC doit verrouiller au moins la partie et le rapport avec FOR UPDATE.')
    if re.search(r'\n\s*exception\s+when\b', sql_lower):
        errors.append('La RPC atomique ne doit pas avaler les exceptions SQL.')
    if re.search(r'grant\s+execute\s+on\s+function\s+public\.service_submit_fracture_endgame\([^;]+\)\s+to\s+(?:public|anon|authenticated)\b', sql_lower, re.S):
        errors.append('La RPC transactionnelle ne doit être exécutable ni publiquement ni par authenticated.')

    for table in (
        'public.internal_gameplay_contributions',
        'public.fracture_endgame_reports',
        'public.fracture_parties',
        'public.game_sessions',
    ):
        if table not in sql_lower:
            errors.append(f'La transaction Fracture ne couvre plus {table}.')

    return errors


def self_test() -> None:
    real_edge = EDGE.read_text('utf-8', errors='strict')
    real_sql = MIGRATION.read_text('utf-8', errors='strict')
    clean = validate(EDGE, MIGRATION)
    if clean:
        raise AssertionError('Les fichiers réels sains doivent passer: ' + ' | '.join(clean))

    edge_cases = {
        'JSON direct': real_edge.replace('const rawBody = await req.text();', 'const rawBody = JSON.stringify(await req.json());', 1),
        'limite HTTP augmentée': real_edge.replace('MAX_REQUEST_BYTES = 4096;', 'MAX_REQUEST_BYTES = 40960;', 1),
        'content-type retiré': real_edge.replace("    if (!contentType.startsWith('application/json')) {", "    if (false) {", 1),
        'no-store retiré': real_edge.replace("      'Cache-Control': 'private, no-store, max-age=0',\n", '', 1),
        'auth retirée': real_edge.replace('    const user = await requiredUser(req);\n', '', 1),
        'code partie relâché': real_edge.replace('const PARTY_CODE_RE = /^FRM-[A-Z0-9]{6}$/;', 'const PARTY_CODE_RE = /^FRM-/;', 1),
        'erreur partie ignorée': real_edge.replace("    if (partyError) throw new Error('PARTY_LOOKUP_FAILED');\n", '', 1),
        'erreur rapport ignorée': real_edge.replace("    if (reportError) throw new Error('REPORT_LOOKUP_FAILED');\n", '', 1),
        'RPC retirée': real_edge.replace(".rpc('service_submit_fracture_endgame'", ".rpc('unsafe_submit_fracture_endgame'", 1),
        'écriture directe réintroduite': real_edge + "\nservice.from('fracture_parties').update({status:'finished'});\n",
        'log brut réintroduit': real_edge + '\nconsole.error(submitError);\n',
        'service payant activé': real_edge.replace('const PAID_EXTERNAL_SERVICES_ENABLED = false;', 'const PAID_EXTERNAL_SERVICES_ENABLED = true;', 1),
    }
    sql_cases = {
        'service_role retiré': real_sql.replace("  if coalesce(auth.jwt()->>'role','') <> 'service_role' then\n    raise exception 'SERVICE_ROLE_REQUIRED';\n  end if;\n", '', 1),
        'verrou partie retiré': real_sql.replace('  for update;\n', ';\n', 1),
        'archive non préservée': real_sql.replace("    if v_party.status = 'archived' then\n", "    if false then\n", 1),
        'snapshot partie retiré': real_sql.replace("  if p_party_updated_at is null or v_party.updated_at is distinct from p_party_updated_at then\n    raise exception 'FRACTURE_PARTY_CHANGED';\n  end if;\n", '', 1),
        'snapshot rapport retiré': real_sql.replace("  if p_report_updated_at is null or v_report.updated_at is distinct from p_report_updated_at then\n    raise exception 'FRACTURE_ENDGAME_REPORT_CHANGED';\n  end if;\n", '', 1),
        'insert contribution retiré': real_sql.replace('  insert into public.internal_gameplay_contributions(', '  insert into public.removed_contributions(', 1),
        'sessions non finalisées': real_sql.replace('update public.game_sessions', 'update public.removed_game_sessions'),
        'idempotence retirée': real_sql.replace("        'already_submitted', true,", "        'already_submitted', false,", 1),
        'ACL service élargie': real_sql.replace('to service_role;', 'to authenticated;', 1),
        'révocation retirée': real_sql.replace('from public, anon, authenticated;', 'from public;', 1),
    }

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        edge_path = tmp_path / 'index.ts'
        sql_path = tmp_path / 'migration.sql'
        for label, mutated in edge_cases.items():
            if mutated == real_edge:
                raise AssertionError(f'Auto-test Edge invalide, mutation sans effet: {label}')
            edge_path.write_text(mutated, encoding='utf-8')
            sql_path.write_text(real_sql, encoding='utf-8')
            if not validate(edge_path, sql_path):
                raise AssertionError(f'Affaiblissement Edge non détecté: {label}')
        for label, mutated in sql_cases.items():
            if mutated == real_sql:
                raise AssertionError(f'Auto-test SQL invalide, mutation sans effet: {label}')
            edge_path.write_text(real_edge, encoding='utf-8')
            sql_path.write_text(mutated, encoding='utf-8')
            if not validate(edge_path, sql_path):
                raise AssertionError(f'Affaiblissement SQL non détecté: {label}')

    print(f'OK auto-test fin de partie Fracture: {len(edge_cases) + len(sql_cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la frontière HTTP et la finalisation transactionnelle de Fracture.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    errors = validate(EDGE, MIGRATION)
    if errors:
        print(f'ÉCHEC fin de partie Fracture: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK fin de partie Fracture: auth avant corps, JSON 4 KiB, lectures fail-closed, réponses privées, archive préservée et finalisation SQL atomique service_role.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
