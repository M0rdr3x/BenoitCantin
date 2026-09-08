#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'assets'/'js'/'sinjira-live-invites-model-v25.js'
CLIENT=ROOT/'assets'/'js'/'sinjira-live-invites-client-v25.js'
TEST=ROOT/'scripts'/'test_live_social_invites_client_v25.mjs'
WORKFLOW=ROOT/'.github'/'workflows'/'sinjira-live-social-ui-v25.yml'


def require(condition,message):
    if not condition:
        raise SystemExit(f'ERREUR client invitations privées En direct V25: {message}')


def main():
    model=MODEL.read_text('utf-8')
    client=CLIENT.read_text('utf-8')
    test=TEST.read_text('utf-8')
    workflow=WORKFLOW.read_text('utf-8')
    ml=model.lower(); cl=client.lower(); tl=test.lower(); wl=workflow.lower()

    for marker in (
        'normalizeliveinvitecreate(',
        'normalizeliveinvites(',
        'normalizeliveinviteresponse(',
        'if(invites.length>=50)break',
        "'membre sinjira™'"
    ):
        require(marker in ml,f'modèle client incomplet: {marker}')

    # Le modèle d'affichage ne doit jamais conserver les identités privées serveur.
    for forbidden in ('inviter_user_id','invitee_user_id','owner_user_id','user_id','responded_at'):
        require(forbidden not in ml,f'modèle ne doit pas connaître {forbidden}')

    for marker in (
        "rpc('social_live_invite_create'",
        "rpc('social_live_my_invites'",
        "rpc('social_live_invite_respond'",
        "rpc('social_live_invite_revoke'",
        'p_room_id:room',
        'p_invitee_user_id:invitee',
        'p_invite_id:id',
        'p_accept:accept',
        "throw new error('social_live_invite_response_invalid')",
        "throw new error('social_live_invite_decision_invalid')"
    ):
        require(marker in cl,f'contrat RPC client absent: {marker}')

    # Le client n'a aucun accès direct à la table privée et aucune voie implicite de persistance/URL/log.
    joined=(model+'\n'+client).lower()
    for forbidden in (
        'private.social_live_room_invites',
        "from('social_live_room_invites",
        'localstorage','sessionstorage','indexeddb','document.cookie','urlsearchparams',
        'location.href','location.search','location.hash','history.pushstate','history.replacestate',
        'console.log','console.error','console.warn','sendbeacon('
    ):
        require(forbidden not in joined,f'voie de fuite/persistance ou accès direct interdit: {forbidden}')
    require('fetch(' not in cl,'client doit passer uniquement par les RPC Supabase existants')

    for marker in (
        "object.hasown(created,forbidden)",
        "object.hasown(invites[0],forbidden)",
        "'inviter_user_id'",
        "'invitee_user_id'",
        "status:'accepted'",
        "status:'unavailable'"
    ):
        require(marker in tl,f'test de minimisation absent: {marker}')

    # Dark launch strict : aucun asset client d'invitations ne doit être chargé par HTML.
    html='\n'.join(p.read_text('utf-8',errors='ignore').lower() for p in ROOT.rglob('*.html'))
    for asset in ('sinjira-live-invites-model-v25.js','sinjira-live-invites-client-v25.js'):
        require(asset not in html,f'asset chargé avant preuve production: {asset}')

    for marker in (
        'assets/js/sinjira-live-invites-model-v25.js',
        'assets/js/sinjira-live-invites-client-v25.js',
        'scripts/test_live_social_invites_client_v25.mjs',
        'scripts/validate_live_social_invites_client_v25.py',
        'node scripts/test_live_social_invites_client_v25.mjs',
        'python scripts/validate_live_social_invites_client_v25.py'
    ):
        require(marker in wl,f'workflow client incomplet: {marker}')
    for forbidden in ('supabase_access_token','supabase_db_password','--linked','db push','inputs.apply'):
        require(forbidden not in wl,f'workflow client ne doit jamais viser production: {forbidden}')

    print('OK client invitations privées En direct V25: RPC bornés, accès table privée interdit, identités non persistées/non journalisées/non placées en URL et dark launch HTML maintenu.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
