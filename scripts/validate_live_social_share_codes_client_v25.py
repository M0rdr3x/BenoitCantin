#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'assets'/'js'/'sinjira-live-share-codes-model-v25.js'
CLIENT=ROOT/'assets'/'js'/'sinjira-live-share-codes-client-v25.js'
TEST=ROOT/'scripts'/'test_live_social_share_codes_client_v25.mjs'
WORKFLOW=ROOT/'.github'/'workflows'/'sinjira-live-social-ui-v25.yml'


def require(condition,message):
    if not condition:
        raise SystemExit(f'ERREUR client codes privés En direct V25: {message}')


def main():
    model=MODEL.read_text('utf-8')
    client=CLIENT.read_text('utf-8')
    test=TEST.read_text('utf-8')
    workflow=WORKFLOW.read_text('utf-8')
    ml=model.lower(); cl=client.lower(); tl=test.lower(); wl=workflow.lower()

    for marker in (
        'normalizelivesharecode(',
        'normalizelivesharecodecreate(',
        'normalizelivesharecodes(',
        'normalizelivesharecoderedeem(',
        "const share_code_re=/^[a-f0-9]{64}$/",
        "new set(['active','used','revoked','expired'])",
        'if(codes.length>=50)break'
    ):
        require(marker in ml,f'modèle client incomplet: {marker}')

    for forbidden in ('code_hash','creator_user_id','redeemed_by_user_id','inviter_user_id','owner_user_id','user_id'):
        require(forbidden not in ml,f'modèle ne doit pas connaître {forbidden}')

    for marker in (
        "rpc('social_live_share_code_create'",
        "rpc('social_live_share_code_list'",
        "rpc('social_live_share_code_revoke'",
        "rpc('social_live_share_code_redeem'",
        'p_room_id:id',
        'p_code_id:id',
        'p_code:code',
        'normalizelivesharecode(value)',
        "throw new error('social_live_share_code_unavailable')",
        "throw new error('social_live_share_code_response_invalid')"
    ):
        require(marker in cl,f'contrat RPC client absent: {marker}')

    # Le bearer brut ne doit avoir aucune voie implicite de persistance, URL ou log.
    joined=(model+'\n'+client).lower()
    for forbidden in (
        'localstorage','sessionstorage','indexeddb','document.cookie','urlsearchparams',
        'location.href','location.search','location.hash','history.pushstate','history.replacestate',
        'console.log','console.error','console.warn','sendbeacon('
    ):
        require(forbidden not in joined,f'voie de fuite/persistance interdite: {forbidden}')
    require('fetch(' not in cl,'client doit passer uniquement par les RPC Supabase existants')

    for marker in (
        "normalizelivesharecode(`  ${code.touppercase()}  `)",
        "object.hasown(created,'code_hash')",
        "object.hasown(codes[0],forbidden)",
        "'redeemed_by_user_id'",
        "status:'already_member'"
    ):
        require(marker in tl,f'test de minimisation absent: {marker}')

    # Dark launch strict : aucun nouvel asset de codes de partage ne doit être chargé par HTML.
    html='\n'.join(p.read_text('utf-8',errors='ignore').lower() for p in ROOT.rglob('*.html'))
    for asset in ('sinjira-live-share-codes-model-v25.js','sinjira-live-share-codes-client-v25.js'):
        require(asset not in html,f'asset chargé avant preuve production: {asset}')

    for marker in (
        'assets/js/sinjira-live-share-codes-model-v25.js',
        'assets/js/sinjira-live-share-codes-client-v25.js',
        'scripts/test_live_social_share_codes_client_v25.mjs',
        'scripts/validate_live_social_share_codes_client_v25.py',
        'node scripts/test_live_social_share_codes_client_v25.mjs',
        'python scripts/validate_live_social_share_codes_client_v25.py'
    ):
        require(marker in wl,f'workflow client incomplet: {marker}')
    for forbidden in ('supabase_access_token','supabase_db_password','--linked','db push','inputs.apply'):
        require(forbidden not in wl,f'workflow client ne doit jamais viser production: {forbidden}')

    print('OK client codes privés En direct V25: RPC bornés, secret non persisté/non journalisé/non placé en URL, réponses minimisées et dark launch HTML maintenu.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
