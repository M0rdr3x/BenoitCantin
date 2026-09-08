#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UI=ROOT/'assets'/'js'/'sinjira-live-share-codes-ui-v25.js'
SHELL=ROOT/'assets'/'js'/'sinjira-live-ui-shell-v25.js'
CLIENT=ROOT/'assets'/'js'/'sinjira-live-share-codes-client-v25.js'
CSS=ROOT/'assets'/'css'/'v25-live-share-codes.css'
WORKFLOW=ROOT/'.github'/'workflows'/'sinjira-live-social-ui-v25.yml'


def require(condition,message):
    if not condition:
        raise SystemExit(f'ERREUR UI codes privés En direct V25: {message}')


def main():
    ui=UI.read_text('utf-8')
    shell=SHELL.read_text('utf-8')
    client=CLIENT.read_text('utf-8')
    css=CSS.read_text('utf-8')
    workflow=WORKFLOW.read_text('utf-8')
    ul=ui.lower(); sl=shell.lower(); cl=client.lower(); cssl=css.lower(); wl=workflow.lower()

    for marker in (
        'document.createelement(',
        'root.replacechildren(shell)',
        "codeinput.type='password'",
        "codeinput.autocomplete='off'",
        "codeinput.autocapitalize='off'",
        'codeinput.spellcheck=false',
        'codeinput.maxlength=64',
        "filter(room=>room.visibility==='private'&&room.owned===true)",
        'createlivesharecode(roomid,{supabase})',
        'listlivesharecodes({supabase,limit:20})',
        'revokelivesharecode(item.codeid,{supabase})',
        'redeemlivesharecode(codeinput.value,{supabase})',
        "codeinput.value=''",
        'secret.textcontent=result.code',
        "navigator.clipboard?.writetext",
        'clearsecret()',
        "document.addeventlistener('visibilitychange',onvisibilitychange)",
        "document.removeeventlistener('visibilitychange',onvisibilitychange)"
    ):
        require(marker in ul,f'contrat UI secret-safe absent: {marker}')

    require(ul.count("codeinput.value=''")>=2,'champ bearer doit être vidé succès et erreur')
    require('const pending=redeemlivesharecode(codeinput.value,{supabase})' in ul,'rachat doit démarrer avant nettoyage immédiat du champ')
    require(ul.index("codeinput.value=''")>ul.index('const pending=redeemlivesharecode(codeinput.value,{supabase})'),'nettoyage du champ doit suivre immédiatement le lancement RPC')
    require("if(document.hidden)clearsecret()" in ul,'secret affiché doit être masqué quand la page devient cachée')
    require('secret.dataset' not in ul and 'codeinput.dataset' not in ul,'secret ne doit jamais entrer dans dataset')
    require("setattribute('aria-live','polite')" in ul,'retour accessible aria-live absent')
    require("setattribute('role','list')" in ul,'liste de codes accessible absente')

    joined=(ui+'\n'+shell).lower()
    for forbidden in (
        'innerhtml','outerhtml','insertadjacenthtml','localstorage','sessionstorage','indexeddb',
        'document.cookie','urlsearchparams','location.href','location.search','location.hash',
        'history.pushstate','history.replacestate','console.log','console.error','console.warn',
        'sendbeacon(','eval(','new function','/redeem ','/share-code '
    ):
        require(forbidden not in joined,f'voie de fuite/persistance/commande interdite: {forbidden}')
    require('fetch(' not in joined,'UI doit réutiliser le client RPC, sans fetch parallèle')

    # Le shell compose maintenant trois modules dark-launch. Le validateur des codes
    # privés doit suivre cette composition sans perdre les garanties historiques.
    for marker in (
        "import {createliveui} from './sinjira-live-ui-v25.js'",
        "import {createlivesharecodesui} from './sinjira-live-share-codes-ui-v25.js'",
        "import {createliveinvitesui} from './sinjira-live-invites-ui-v25.js'",
        'const live=createliveui(liveroot,{supabase})',
        'const share=createlivesharecodesui(shareroot,{',
        'const invites=createliveinvitesui(invitesroot,{',
        'onjoined:async()=>',
        'onaccepted:async()=>',
        'await live.refresh()',
        'promise.all([live.ready,share.ready,invites.ready])',
        'promise.all([live.refresh(),share.refresh(),invites.refresh()])',
        'promise.all([live.destroy(),share.destroy(),invites.destroy()])'
    ):
        require(marker in sl,f'composition dark-launch absente: {marker}')

    for marker in (
        '.v25-live-share-shell','.v25-live-share-reveal','.v25-live-share-secret',
        '.v25-live-share-redeem','.v25-live-share-list','.v25-live-share-card',
        ':focus-visible','@media(max-width:700px)','prefers-reduced-motion'
    ):
        require(marker in cssl,f'style codes privés absent: {marker}')

    # Le client sous-jacent doit toujours être la couche RPC validée par #258.
    for rpc in (
        "rpc('social_live_share_code_create'","rpc('social_live_share_code_list'",
        "rpc('social_live_share_code_revoke'","rpc('social_live_share_code_redeem'"
    ):
        require(rpc in cl,f'RPC client manquant: {rpc}')

    # Dark launch strict: aucun asset de cette composition ne doit être chargé par HTML.
    html='\n'.join(p.read_text('utf-8',errors='ignore').lower() for p in ROOT.rglob('*.html'))
    for asset in (
        'sinjira-live-share-codes-ui-v25.js','sinjira-live-ui-shell-v25.js','v25-live-share-codes.css',
        'sinjira-live-share-codes-client-v25.js','sinjira-live-share-codes-model-v25.js'
    ):
        require(asset not in html,f'asset chargé avant preuve production: {asset}')

    for marker in (
        'assets/js/sinjira-live-share-codes-ui-v25.js',
        'assets/js/sinjira-live-ui-shell-v25.js',
        'assets/css/v25-live-share-codes.css',
        'scripts/validate_live_social_share_codes_ui_v25.py',
        'python scripts/validate_live_social_share_codes_ui_v25.py'
    ):
        require(marker in wl,f'workflow UI incomplet: {marker}')
    for forbidden in ('supabase_access_token','supabase_db_password','--linked','db push','inputs.apply'):
        require(forbidden not in wl,f'workflow UI ne doit jamais viser production: {forbidden}')

    print('OK UI codes privés En direct V25: création/copie/masquage/révocation/rachat séparés des commandes, secret non persisté et composition live/share/invites maintenue en dark launch.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
