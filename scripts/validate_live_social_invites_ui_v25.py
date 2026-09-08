#!/usr/bin/env python3
import importlib.util
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


def load_gate():
    spec=importlib.util.spec_from_file_location('sinjira_live_activation_gate_v25',GATE)
    require(spec is not None and spec.loader is not None,'garde activation illisible')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    ui=UI.read_text('utf-8')
    css=CSS.read_text('utf-8')
    shell=SHELL.read_text('utf-8')
    workflow=WORKFLOW.read_text('utf-8')
    ul=ui.lower(); cl=css.lower(); sl=shell.lower(); wl=workflow.lower()

    for marker in (
        "import {executeliveinput} from './sinjira-live-runtime-v25.js'",
        "import {normalizeliverooms} from './sinjira-live-ui-model-v25.js'",
        "import {createliveinvite,listmyliveinvites,respondtoliveinvite} from './sinjira-live-invites-client-v25.js'",
        'createliveinvitesui(',
        'listmyliveinvites({limit:20,supabase})',
        'respondtoliveinvite(item.inviteid,accept,{supabase})',
        "acceptbutton=button('accepter'",
        "declinebutton=button('refuser'",
        "if(result.status==='accepted')await promise.resolve(onaccepted(result))",
        "node('p','v25-live-muted',`#${item.roomslug} · invitation de ${item.inviterlabel}`)"
    ):
        require(marker in ul,f'contrat UI réception manquant: {marker}')

    # Envoi contextuel : la cible vient uniquement d'un contexte social déjà affiché.
    for marker in (
        'createliveinvitetargetui(',
        "const targetid=string(targetuserid||'').trim().tolowercase()",
        "if(!uuid_re.test(targetid))throw new error('social_live_invitee_unavailable')",
        "const publiclabel=string(targetlabel||'').trim().slice(0,80)||'membre sinjira™'",
        "executeliveinput('/rooms',{supabase})",
        "filter(room=>room.visibility==='private'&&room.owned===true)",
        'createliveinvite(roomid,targetid,{supabase})',
        'await promise.resolve(onsent({roomid}))',
        "setstatus('invitation privée envoyée.','success')"
    ):
        require(marker in ul,f'contrat envoi contextuel manquant: {marker}')

    # Aucune recherche/énumération de personnes et aucune saisie d'identité.
    for forbidden in (
        "createelement('input')",
        'contenteditable',
        'social_profiles',
        '.ilike(',
        '.like(',
        '.neq(',
        'display_name',
        'pseudo',
        'dataset.target',
        'dataset.user',
        "setattribute('data-user",
        "setattribute('data-target",
        'inviter_user_id',
        'invitee_user_id',
        'owner_user_id'
    ):
        require(forbidden not in ul,f'annuaire, saisie ou identité technique interdite: {forbidden}')

    for forbidden in (
        '.innerhtml','outerhtml','insertadjacenthtml','document.write',
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
        '.v25-live-invite-target-shell',
        '.v25-live-invite-target-controls',
        '.v25-live-invite-target-label',
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

    # L'envoi contextuel n'est pas auto-monté dans le shell : le contexte hôte devra
    # fournir explicitement la personne déjà affichée lorsque la production sera prête.
    require('createliveinvitetargetui' not in sl,'envoi contextuel ne doit pas être monté sans cible explicite')

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

    # Vérifier le comportement du garde, pas une chaîne littérale de son implémentation.
    gate=load_gate()
    script_match=gate.SCRIPT_MOUNT_RE.search(
        '<script type="module" src="/assets/js/sinjira-live-invites-ui-v25.js"></script>'
    )
    style_match=gate.STYLE_MOUNT_RE.search(
        '<link rel="stylesheet" href="/assets/css/v25-live-invites.css">'
    )
    require(script_match is not None,'garde activation ne détecte pas le montage JS des invitations')
    require(style_match is not None,'garde activation ne détecte pas le montage CSS des invitations')
    require(script_match.group(1).lower()=='sinjira-live-invites-ui-v25.js','garde JS capture le mauvais asset invitations')
    require(style_match.group(1).lower()=='v25-live-invites.css','garde CSS capture le mauvais asset invitations')

    print('OK UI invitations privées En direct V25: réception/réponse et envoi contextuel sans annuaire, saisie UUID, URL, persistance ou montage prématuré.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
