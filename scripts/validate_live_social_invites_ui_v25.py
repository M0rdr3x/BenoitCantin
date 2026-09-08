#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UI=ROOT/'assets'/'js'/'sinjira-live-invites-ui-v25.js'
CSS=ROOT/'assets'/'css'/'v25-live-invites.css'
SHELL=ROOT/'assets'/'js'/'sinjira-live-ui-shell-v25.js'
WORKFLOW=ROOT/'.github'/'workflows'/'sinjira-live-social-ui-v25.yml'
GATE=ROOT/'scripts'/'validate_live_social_activation_gate_v25.py'


def require(condition,message):
    if not condition:
        raise SystemExit(f'ERREUR UI invitations privées En direct V25: {message}')


def main():
    ui=UI.read_text('utf-8')
    css=CSS.read_text('utf-8')
    shell=SHELL.read_text('utf-8')
    workflow=WORKFLOW.read_text('utf-8')
    gate=GATE.read_text('utf-8')
    ul=ui.lower(); cl=css.lower(); sl=shell.lower(); wl=workflow.lower(); gl=gate.lower()

    for marker in (
        "import {listmyliveinvites,respondtoliveinvite} from './sinjira-live-invites-client-v25.js'",
        'createliveinvitesui(',
        'listmyliveinvites({limit:20,supabase})',
        'respondtoliveinvite(item.inviteid,accept,{supabase})',
        "acceptbutton=button('accepter'",
        "declinebutton=button('refuser'",
        "if(result.status==='accepted')await promise.resolve(onaccepted(result))",
        "node('p','v25-live-muted',`#${item.roomslug} · invitation de ${item.inviterlabel}`)"
    ):
        require(marker in ul,f'contrat UI manquant: {marker}')

    # Réception seulement : aucun formulaire de destinataire, création ou révocation d'invitation.
    for forbidden in (
        'createliveinvite(',
        'revokeliveinvite(',
        "createelement('input')",
        'contenteditable',
        '.innerhtml',
        'insertadjacenthtml',
        'document.write',
        'inviter_user_id',
        'invitee_user_id',
        'owner_user_id'
    ):
        require(forbidden not in ul,f'primitive UI ou identité privée interdite: {forbidden}')

    for forbidden in (
        'localstorage','sessionstorage','indexeddb','document.cookie','urlsearchparams',
        'location.href','location.search','location.hash','history.pushstate','history.replacestate',
        'console.log','console.error','console.warn','sendbeacon(','fetch('
    ):
        require(forbidden not in ul,f'voie de fuite/persistance interdite: {forbidden}')

    for marker in (
        '.v25-live-invites-shell',
        '.v25-live-invites-list',
        '.v25-live-invite-card',
        '.v25-live-invite-actions',
        '@media (max-width:640px)'
    ):
        require(marker in cl,f'style UI absent: {marker}')

    for marker in (
        "import {createliveinvitesui} from './sinjira-live-invites-ui-v25.js'",
        "invitesroot.classname='v25-live-shell-invites'",
        'const invites=createliveinvitesui(invitesroot,{',
        'await live.refresh()',
        'promise.all([live.ready,share.ready,invites.ready])',
        'promise.all([live.refresh(),share.refresh(),invites.refresh()])',
        'promise.all([live.destroy(),share.destroy(),invites.destroy()])'
    ):
        require(marker in sl,f'composition shell incomplète: {marker}')

    # Dark launch strict : ni l'UI ni sa feuille de style ne sont montées par HTML.
    html='\n'.join(p.read_text('utf-8',errors='ignore').lower() for p in ROOT.rglob('*.html'))
    for asset in ('sinjira-live-invites-ui-v25.js','v25-live-invites.css'):
        require(asset not in html,f'asset chargé avant preuve production: {asset}')

    for marker in (
        'assets/js/sinjira-live-invites-ui-v25.js',
        'assets/css/v25-live-invites.css',
        'scripts/validate_live_social_invites_ui_v25.py',
        'python scripts/validate_live_social_invites_ui_v25.py'
    ):
        require(marker in wl,f'workflow UI incomplet: {marker}')
    for forbidden in ('supabase_access_token','supabase_db_password','--linked','db push','inputs.apply'):
        require(forbidden not in wl,f'workflow UI ne doit jamais viser production: {forbidden}')

    require('invites-ui-v25' in gl,'garde activation ne détecte pas le montage JS des invitations')
    require('v25-live-invites' in gl,'garde activation ne détecte pas le montage CSS des invitations')

    print('OK UI invitations privées En direct V25: réception/acceptation/refus seulement, rendu texte sûr, aucune saisie UUID et dark launch protégé par le garde production.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
