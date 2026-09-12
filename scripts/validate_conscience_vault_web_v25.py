#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read(path:str)->str:
    target=ROOT/path
    if not target.exists():raise AssertionError(f'Fichier absent: {path}')
    return target.read_text('utf-8',errors='strict')


def require(text:str,markers:list[str],label:str)->None:
    missing=[m for m in markers if m not in text]
    if missing:raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text:str,markers:list[str],label:str)->None:
    found=[m for m in markers if m in text]
    if found:raise AssertionError(f'{label}: marqueurs interdits: {found}')


def block(text:str,start_marker:str,end_marker:str)->str:
    start=text.find(start_marker)
    if start<0:raise AssertionError(f'Bloc absent: {start_marker}')
    end=text.find(end_marker,start+len(start_marker))
    if end<0:raise AssertionError(f'Fin de bloc absente: {end_marker}')
    return text[start:end]


def delete_contract_errors(edge:str,js:str,migration:str)->list[str]:
    errors=[]
    server_check="if (body.human_confirmed_delete !== true) throw new Error('VAULT_DELETE_CONFIRMATION_REQUIRED');"
    client_confirm="globalThis.confirm('Supprimer définitivement cette entrée du Registre personnel ? Cette action ne crée pas de copie dans l’Histoire de vie.')"
    client_call="await invokeVault({action:'delete_entry',vault_session_id:sessionId,entry_id:entryId,human_confirmed_delete:true});"

    try:edge_delete=block(edge,"    if (action === 'delete_entry') {","    if (action === 'revoke_session') {")
    except AssertionError as exc:errors.append(str(exc));edge_delete=''
    try:client_delete=block(js,'async function deleteEntry(entryId){','function handleVaultFailure(error){')
    except AssertionError as exc:errors.append(str(exc));client_delete=''
    try:sql_delete=block(migration,'create or replace function public.service_conscience_delete_entry(','revoke all on function public.service_conscience_open_session')
    except AssertionError as exc:errors.append(str(exc));sql_delete=''

    if server_check not in edge_delete:errors.append('Edge: confirmation humaine stricte === true absente avant suppression.')
    if "'VAULT_DELETE_CONFIRMATION_REQUIRED'" not in edge:errors.append('Edge: code fixe de confirmation de suppression absent.')
    if "code === 'VAULT_DELETE_CONFIRMATION_REQUIRED'" not in edge:errors.append('Edge: réponse dédiée à la confirmation de suppression absente.')
    rpc_pos=edge_delete.find("service.rpc('service_conscience_delete_entry'")
    check_pos=edge_delete.find(server_check)
    if check_pos<0 or rpc_pos<0 or check_pos>rpc_pos:errors.append('Edge: la confirmation humaine doit précéder la RPC de suppression.')
    if edge.count('human_confirmed_delete')!=1:errors.append('Edge: human_confirmed_delete doit être lu exactement une fois, uniquement dans delete_entry.')

    if client_confirm not in client_delete:errors.append('Web: dialogue explicite de suppression définitive absent.')
    if client_call not in client_delete:errors.append('Web: marqueur human_confirmed_delete:true absent de l’appel confirmé.')
    confirm_pos=client_delete.find(client_confirm)
    call_pos=client_delete.find(client_call)
    if confirm_pos<0 or call_pos<0 or confirm_pos>call_pos:errors.append('Web: la confirmation humaine doit précéder l’appel de suppression.')
    if js.count('human_confirmed_delete:true')!=1:errors.append('Web: le marqueur de confirmation doit exister une seule fois et seulement dans deleteEntry.')

    sql_required=[
        'perform private.conscience_vault_require_service_role();',
        'perform private.conscience_vault_assert_session(p_user_id,p_session_id);',
        'delete from private.conscience_entries\n   where id=p_entry_id and user_id=p_user_id;',
        'revoke all on function public.service_conscience_delete_entry(uuid,uuid,uuid) from public, anon, authenticated;',
        'grant execute on function public.service_conscience_delete_entry(uuid,uuid,uuid) to service_role;',
    ]
    for marker in sql_required:
        if marker not in migration:errors.append(f'SQL suppression coffre affaiblie: {marker}')
    if 'delete from private.conscience_entries' not in sql_delete:errors.append('SQL: la nature physique/irréversible de la suppression n’est plus explicitement couverte.')
    return errors


def self_test_delete_contract(edge:str,js:str,migration:str)->None:
    server_check="if (body.human_confirmed_delete !== true) throw new Error('VAULT_DELETE_CONFIRMATION_REQUIRED');"
    client_confirm="globalThis.confirm('Supprimer définitivement cette entrée du Registre personnel ? Cette action ne crée pas de copie dans l’Histoire de vie.')"
    cases={
        'verrou serveur retiré':(edge.replace(server_check,'',1),js,migration),
        'booléen serveur affaibli':(edge.replace('body.human_confirmed_delete !== true','!body.human_confirmed_delete',1),js,migration),
        'confirmation UI retirée':(edge,js.replace(client_confirm,'true',1),migration),
        'marqueur client retiré':(edge,js.replace(',human_confirmed_delete:true','',1),migration),
        'marqueur client faux':(edge,js.replace('human_confirmed_delete:true','human_confirmed_delete:false',1),migration),
        'scope propriétaire SQL retiré':(edge,js,migration.replace('delete from private.conscience_entries\n   where id=p_entry_id and user_id=p_user_id;','delete from private.conscience_entries\n   where id=p_entry_id;',1)),
        'ACL suppression élargie':(edge,js,migration.replace('grant execute on function public.service_conscience_delete_entry(uuid,uuid,uuid) to service_role;','grant execute on function public.service_conscience_delete_entry(uuid,uuid,uuid) to authenticated;',1)),
    }
    for label,(mut_edge,mut_js,mut_sql) in cases.items():
        if (mut_edge,mut_js,mut_sql)==(edge,js,migration):raise AssertionError(f'Auto-test suppression sans effet: {label}')
        if not delete_contract_errors(mut_edge,mut_js,mut_sql):raise AssertionError(f'Régression suppression non détectée: {label}')


def main()->int:
    page=read('compte/registre-personnel.html')
    js=read('assets/js/sinjira-consciousness-vault-v25.js')
    css=read('assets/css/sinjira-consciousness-vault-v25.css')
    dashboard=read('compte/index.html')
    life_story=read('compte/histoire-de-vie.html')
    edge=read('supabase/functions/conscience-vault/index.ts')
    migration=read('supabase/migrations/20260902223000_sinjira_v25_0_personal_consciousness_vault.sql')

    require(page,[
        '<meta content="noindex,nofollow" name="robots"/>',
        '<title>Mon Registre personnel | Compte SINJIRA™</title>',
        'Mon Registre personnel des consciences',
        'Registre narratif SINJIRA',
        'Jamais remis à vos proches ou héritiers.',
        'Jamais copié automatiquement dans l’Histoire de vie.',
        'Aucun export ou téléchargement depuis cette page.',
        'data-vault-locked',
        'data-vault-workspace hidden',
        'data-vault-open',
        'data-vault-lock',
        'data-vault-entry-form',
        'data-vault-challenge',
        'data-vault-retry',
        'sinjira-consciousness-vault-v25.js?v=25.0',
    ],'page Registre personnel')
    forbid(page,[
        'name="user_id"',
        'name="target_user_id"',
        ' download=',
        'download="',
        'Exporter',
        'Télécharger mon Registre',
        'clone IA de votre personne',
    ],'aucune identité cible, export ou promesse posthume dans la page')

    require(js,[
        "const VAULT_TTL_SECONDS=300;",
        "getSupabase().functions.invoke('conscience-vault',{body})",
        "action:'open_session'",
        "action:'list_entries'",
        "action:'create_entry'",
        "action:'update_entry'",
        "action:'delete_entry'",
        "action:'revoke_session'",
        'let vaultSessionId=null;',
        'function clearSensitiveDom()',
        'function localLock(',
        "document.addEventListener('visibilitychange'",
        "globalThis.addEventListener('pagehide'",
        'HIDDEN_LOCK_DELAY_MS=60_000',
        "error?.code==='SECURITY_CHALLENGE_REQUIRED'",
        "code==='MFA_SETUP_REQUIRED'",
        "code==='MFA_REQUIRED'",
        "code==='SECURITY_BLOCKED'",
    ],'cycle de vie privé du coffre Web')

    forbid(js,[
        ".schema('private')",
        ".from('conscience_entries')",
        ".from('conscience_vault_sessions')",
        ".from('conscience_vault_audit')",
        ".rpc('service_conscience_",
        "localStorage.setItem('vault",
        'localStorage.setItem("vault',
        "sessionStorage.setItem('vault",
        'sessionStorage.setItem("vault',
        "localStorage.setItem('conscience",
        'localStorage.setItem("conscience',
        "sessionStorage.setItem('conscience",
        'sessionStorage.setItem("conscience',
        'indexedDB',
        'caches.open',
        'navigator.serviceWorker',
        'new Blob(',
        'URL.createObjectURL',
        'download=',
        'console.log(content',
        'console.log(entries',
        'console.log(result',
        'body.user_id',
        'user_id:',
        'target_user_id',
    ],'aucune persistance locale, export, accès privé direct ou identité cible')

    require(js,[
        'localStorage.getItem(DEVICE_KEY_STORAGE)',
        'localStorage.setItem(DEVICE_KEY_STORAGE,value)',
        'sessionStorage.getItem(DEVICE_KEY_STORAGE)',
    ],'seul identifiant appareil partagé avec le Centre de sécurité')

    errors=delete_contract_errors(edge,js,migration)
    if errors:raise AssertionError('Suppression irréversible du coffre: '+' | '.join(errors))
    self_test_delete_contract(edge,js,migration)

    require(css,[
        '.conscience-page',
        '.conscience-lock-card',
        '.conscience-workspace',
        '.conscience-entry-card',
        '.conscience-danger',
        '@media(max-width:900px)',
    ],'styles dédiés et responsifs')

    require(dashboard,[
        'href="registre-personnel.html"',
        'Mon Registre personnel',
        'Registre narratif SINJIRA',
        'Coffre privé réel',
        'Son contenu n’est jamais transmis à vos proches.',
    ],'accès dashboard et séparation des deux Registres')

    require(life_story,[
        'href="registre-personnel.html">Registre personnel</a>',
        'href="/projets/sinjira/registre/">Registre narratif</a>',
        'sans donner accès à votre Registre personnel des consciences.',
        'L’Histoire de vie est séparée du Registre personnel.',
        'Histoire de vie uniquement. Jamais le Registre personnel.',
        'Elle ne transmet pas le Registre personnel des consciences.',
    ],'Histoire de vie ne confond plus le coffre réel et le Registre narratif')

    print('OK Web V25: Registre personnel distinct du narratif, Edge uniquement, capacité mémoire, auto-verrouillage, aucun export ni stockage local du contenu, suppression physique protégée par confirmation humaine côté client et serveur (7 mutations auto-testées).')
    return 0


if __name__=='__main__':raise SystemExit(main())
