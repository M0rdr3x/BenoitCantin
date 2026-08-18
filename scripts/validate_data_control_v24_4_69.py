#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read(path):
    p=ROOT/path
    if not p.exists():
        raise AssertionError(f'Fichier absent: {path}')
    return p.read_text('utf-8',errors='ignore')


def require(text,markers,label):
    missing=[m for m in markers if m not in text]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m in text]
    if found:
        raise AssertionError(f'{label}: marqueurs interdits: {found}')


def main():
    runtime=read('assets/js/v24-data-control.js')
    page=read('compte/parametres.html')
    delete_fn=read('supabase/functions/delete-player-account/index.ts')

    require(runtime,[
        'PAGE_SIZE=1000',
        'async function fetchAll',
        "format:'SINJIRA_USER_EXPORT_V24_4_69'",
        'complete:errors.length===0',
        'errors.push({section:label',
        "s.from('profiles')",
        "s.from('account_safety_profiles')",
        "s.from('user_notifications')",
        "s.from('playtest_participants')",
        "s.from('sinjira_reader_library')",
        "s.from('character_submissions')",
        "s.from('parallel_character_state')",
        "s.from('private_family_links')",
        "s.from('guardian_links')",
        "s.from('social_real_messages')",
        "s.from('social_character_messages')",
        "s.functions.invoke('delete-player-account'",
        "confirm:'SUPPRIMER MON COMPTE'",
        "data?.code==='OWNER_OR_ADMIN_DELETE_BLOCKED'",
        "data?.code==='MFA_REQUIRED'",
        "auth.signOut({scope:'local'})",
    ],'runtime contrôle des données')

    # Ces anciens noms produisaient auparavant des sections vides silencieuses.
    forbid(runtime,[
        "s.from('private_profiles')",
        "s.from('family_relationships')",
        "s.from('privacy_settings')",
        "s.from('notification_preferences')",
        "s.from('character_questionnaire_drafts')",
        "s.from('market_listings')",
        "s.from('token_ledger')",
        "s.from('parallel_responses')",
        "s.from('parallel_state')",
    ],'aucune source export obsolète')

    require(page,[
        'data-account-page="settings-v69"',
        'v24-data-control.js?v=24.4.69',
        'sinjira-account.js?v=24.4.69',
        'Les comptes propriétaire et administrateur sont protégés',
        'L’export indique explicitement s’il est complet',
    ],'page paramètres V24.4.69')

    require(delete_fn,[
        "CONFIRM_PHRASE='SUPPRIMER MON COMPTE'",
        "service.rpc('is_sinjira_admin'",
        "code:'OWNER_OR_ADMIN_DELETE_BLOCKED'",
        'getAuthenticatorAssuranceLevel(token)',
        "aal.nextLevel==='aal2'",
        "aal.currentLevel!=='aal2'",
        "code:'MFA_REQUIRED'",
        "'sinjira-avatars'",
        "'sinjira-character-sources'",
        "'sinjira-character-submissions'",
        "service.rpc('revoke_sinjira_contributions'",
        'service.auth.admin.deleteUser(user.id)',
        "throw new Error('STORAGE_DELETE_FAILED')",
        "error?.message==='STORAGE_DELETE_FAILED'",
        "throw new Error('CONTRIBUTION_REVOKE_FAILED')",
        "code:'CONTRIBUTION_REVOKE_FAILED'",
    ],'suppression serveur sûre')

    forbid(delete_fn,[
        "body?.confirm !== 'SUPPRIMER'",
        'api.openai.com',
        'OPENAI_API_KEY',
        'stripe',
        'twilio',
    ],'suppression sans ancien contrat ni service payant')

    print('OK données V24.4.69: export canonique paginé et explicite, suppression admin bloquée, AAL2 et Storage protégés.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
