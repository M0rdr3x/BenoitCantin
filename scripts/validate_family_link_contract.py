#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / 'supabase' / 'migrations'
EXPECTED = MIGRATIONS / '20260817004645_family_link_contract_repair_v24_4_27.sql'
RETIRE_GUARDIAN = MIGRATIONS / '20260816150000_sinjira_v24_4_12_retire_legacy_guardian_rpcs.sql'
VERSION = '24.4.27'


def latest_function_block(files, name):
    rx = re.compile(
        rf'create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',
        re.I | re.S,
    )
    for path in reversed(files):
        matches = list(rx.finditer(path.read_text('utf-8', errors='ignore')))
        if matches:
            return path, matches[-1].group(0)
    return None, ''


def compact(value):
    return re.sub(r'\s+', '', value.lower())


def require_function_contract(errors, files, name, markers, search_paths=('setsearch_path=public',)):
    path, block = latest_function_block(files, name)
    if not path:
        errors.append(f'{name} introuvable.')
        return '', ''
    c = compact(block)
    if 'securitydefiner' not in c:
        errors.append(f'{name}: SECURITY DEFINER attendu.')
    if not any(marker in c for marker in search_paths):
        errors.append(f'{name}: search_path explicite absent ou inattendu.')
    for marker in markers:
        if compact(marker) not in c:
            errors.append(f'{name}: garde manquante: {marker}')
    return path, c


def main() -> int:
    errors = []
    files = sorted(MIGRATIONS.glob('*.sql'))

    if not EXPECTED.exists():
        errors.append(f'Migration canonique absente: {EXPECTED.name}')

    path, redeem = latest_function_block(files, 'redeem_family_link_invite')
    if not path:
        errors.append('redeem_family_link_invite introuvable.')
    else:
        c = compact(redeem)
        required = (
            "ifauth.uid()isnullthen",
            "sinjira_age_band(auth.uid())<>'adult'",
            "when'adult_child'then'child'",
            "when'family'then'other'",
            "'confirmed'",
            "mirror_to_fiction,owner_consented_at,related_consented_at",
            "p_started_on,false,inv.created_at,now()",
            "forupdate;",
        )
        for marker in required:
            if marker not in c:
                errors.append(f'Contrat de rédemption familiale incomplet: {marker}')

        # Valeurs historiques qui faisaient échouer les contraintes SQL.
        if "values(inv.owner_user_id,auth.uid(),rel,'active'" in c:
            errors.append("La RPC réutilise encore le statut invalide 'active'.")
        if "relin('partner','spouse','sibling','parent','adult_child','family')" in c:
            errors.append('La RPC utilise encore directement les anciens types de relation sans normalisation.')

    hpath, health = latest_function_block(files, 'sinjira_family_link_health')
    if not hpath:
        errors.append('sinjira_family_link_health introuvable.')
    else:
        ch = compact(health)
        for marker in (
            f"'version','{VERSION}'",
            "'confirmed_status',confirmed_status",
            "'legacy_relationship_mapping',adult_child_mappedandfamily_mapped",
            "'mirror_defaults_private',mirror_defaults_private",
        ):
            if marker not in ch:
                errors.append(f'Health famille incomplet: {marker}')

    sql = EXPECTED.read_text('utf-8', errors='ignore').lower() if EXPECTED.exists() else ''
    for marker in (
        "revoke all on function public.redeem_family_link_invite(text,text,date,boolean) from public, anon;",
        "grant execute on function public.redeem_family_link_invite(text,text,date,boolean) to authenticated;",
        "revoke all on function public.sinjira_family_link_health() from public, anon, authenticated;",
        "grant execute on function public.sinjira_family_link_health() to service_role;",
    ):
        if marker not in sql:
            errors.append(f'ACL famille V{VERSION} incomplète: {marker}')

    # Supervision jeunesse: l'API exposée au tuteur ne doit jamais accepter un UUID
    # arbitraire. Le caller doit être authentifié et posséder un guardian_link vérifié.
    _, contacts = require_function_contract(
        errors,
        files,
        'get_guardian_youth_contacts',
        (
            "uid uuid:=auth.uid()",
            "if uid is null then raise exception 'AUTH_REQUIRED'",
            "if not public.sinjira_parent_can_supervise(uid,p_child_user_id) then raise exception 'GUARDIAN_ACCESS_REQUIRED'",
            "p_child_user_id in(m.sender_user_id,m.recipient_user_id)",
        ),
        search_paths=('setsearch_path=public,auth',),
    )

    # Helper interne: adulte + jeune confirmé + lien guardian vérifié. Il reste
    # nécessaire à la RPC ci-dessus, mais sa surface directe navigateur est retirée.
    _, parent_guard = require_function_contract(
        errors,
        files,
        'sinjira_parent_can_supervise',
        (
            "sinjira_age_band(p_parent)='adult'",
            "sinjira_age_band(p_child)='youth'",
            "g.guardian_user_id=p_parent",
            "g.minor_user_id=p_child",
            "g.status='verified'",
        ),
    )

    all_sql = '\n'.join(p.read_text('utf-8', errors='ignore').lower() for p in files)
    all_compact = compact(all_sql)
    if 'revokeallonfunctionpublic.get_guardian_youth_contacts(uuid)frompublic,anon;' not in all_compact:
        errors.append('get_guardian_youth_contacts: PUBLIC/anon ne sont pas révoqués explicitement.')
    if 'grantexecuteonfunctionpublic.get_guardian_youth_contacts(uuid)toauthenticated;' not in all_compact:
        errors.append('get_guardian_youth_contacts: exécution authenticated absente.')

    if not RETIRE_GUARDIAN.exists():
        errors.append(f'Migration de retrait des helpers parentaux absente: {RETIRE_GUARDIAN.name}')
    else:
        retired = compact(RETIRE_GUARDIAN.read_text('utf-8', errors='ignore'))
        for marker in (
            "'public.sinjira_parent_can_supervise(uuid,uuid)'",
            "revokeexecuteonfunction%sfromauthenticated",
            "grantexecuteonfunction%stoservice_role",
        ):
            if compact(marker) not in retired:
                errors.append(f'Retrait helper parental incomplet: {marker}')

    # Le contrat SQL historique de la table reste la source canonique :
    # confirmed est valide; active ne l'est pas. child/other sont valides;
    # adult_child/family sont seulement des alias d'entrée de la RPC.
    status_constraints = re.findall(r"private_family_links_status_check.*?(?:;|\n\s*\))", all_sql, re.S)
    relationship_constraints = re.findall(r"private_family_links_relationship_type_check.*?(?:;|\n\s*\))", all_sql, re.S)
    if status_constraints:
        latest_status = status_constraints[-1]
        if "'confirmed'" not in latest_status:
            errors.append("La contrainte private_family_links n'autorise plus 'confirmed'.")
    if relationship_constraints:
        latest_rel = relationship_constraints[-1]
        for allowed in ("'partner'", "'spouse'", "'parent'", "'child'", "'sibling'", "'other'"):
            if allowed not in latest_rel:
                errors.append(f'Contrainte relation familiale sans valeur canonique {allowed}.')

    if errors:
        print(f'ECHEC contrat liens familiaux: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK liens familiaux V24.4.27: rédemption compatible, consentement adulte, miroir fiction privé et supervision jeunesse limitée au tuteur vérifié.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
