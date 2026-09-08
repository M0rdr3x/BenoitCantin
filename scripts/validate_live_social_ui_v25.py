#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'assets'/'js'/'sinjira-live-ui-model-v25.js'
UI=ROOT/'assets'/'js'/'sinjira-live-ui-v25.js'
RUNTIME=ROOT/'assets'/'js'/'sinjira-live-runtime-v25.js'
CSS=ROOT/'assets'/'css'/'v25-live-ui.css'
TEST=ROOT/'scripts'/'test_live_social_ui_model_v25.mjs'
WORKFLOW=ROOT/'.github'/'workflows'/'sinjira-live-social-ui-v25.yml'
COMMUNITY=ROOT/'compte'/'communaute.html'


def require(condition,message):
    if not condition:
        raise SystemExit(f'ERREUR interface En direct V25: {message}')


def main():
    model=MODEL.read_text('utf-8')
    ui=UI.read_text('utf-8')
    runtime=RUNTIME.read_text('utf-8')
    css=CSS.read_text('utf-8')
    test=TEST.read_text('utf-8')
    workflow=WORKFLOW.read_text('utf-8')
    community=COMMUNITY.read_text('utf-8')
    ml=model.lower(); ul=ui.lower(); rl=runtime.lower(); cl=css.lower(); tl=test.lower(); wl=workflow.lower()

    for marker in (
        'normalizeliveme','normalizeliverooms','normalizeliveinvites','livepresencelabel','liveroomaccesslabel','livecommandhelp','liveuierrormessage'
    ):
        require(marker in ml,f'modèle UI incomplet: {marker}')
    require("profilelabel:label" in ml and "ownedrooms:" in ml and "joinedrooms:" in ml,'/me doit rester minimisé')
    require('owner_user_id' not in ml and "user_id" not in ml and 'inviter_user_id' not in ml,'modèle UI ne doit pas conserver des UUID utilisateur')
    require('rooms.length>=100' in ml,'liste salons doit rester bornée à 100')
    require('invites.length>=50' in ml,'liste invitations doit rester bornée à 50')

    for marker in (
        'document.createelement(',
        'root.replacechildren(shell)',
        "setattribute('role','log')",
        "setattribute('aria-live','polite')",
        "setattribute('aria-pressed'",
        'executeliveinput(',
        'openliverealtimesession(',
        'appendmessage(result.message)',
        "if(room.visibility!=='public')",
        'await closesession',
        'socialerrormessage(',
        'loadliveinvites(',
        'respondliveinvite(',
        "network:'live'",
        "targettype:'message'",
        'opensocialreport(',
        "if(message?.own===true)return"
    ):
        require(marker in ul,f'contrat UI absent: {marker}')

    for forbidden in (
        'innerhtml','outerhtml','insertadjacenthtml','eval(','new function','document.cookie','localstorage','sessionstorage',
        'navigator.geolocation','geolocation.getcurrentposition','owner_user_id','date_of_birth','inviter_user_id'
    ):
        require(forbidden not in ul,f'construction ou donnée interdite dans UI: {forbidden}')
    require('console.log' not in ul and 'console.error' not in ul,'UI ne doit pas journaliser messages ou erreurs sensibles')
    require("textcontent" in ul,'UI doit rendre le texte via textContent')
    require("room.visibility!=='public'" in ul and 'invitation acceptée' in ul,'salons privés ne doivent jamais passer par auto-join')
    require('social_live_invite_create' not in ul,'UI ne doit pas créer d invitation sans résolution sûre de cible')

    for marker in (
        "rpc('social_live_my_invites'",
        "rpc('social_live_invite_respond'",
        'p_invite_id:id',
        'p_accept:accept===true',
        'const {user_id,...message}=row',
        'own:!!selfid'
    ):
        require(marker in rl,f'contrat runtime invitation/sécurité absent: {marker}')
    require('social_live_invite_create' not in rl,'runtime ne doit pas exposer la création d invitation')
    require('return {...message,author_label:' in rl and 'own:' in rl,'runtime doit réduire auteur à label + booléen own')

    for marker in (
        '.v25-live-shell','.v25-live-log','.v25-live-composer','.v25-live-room-button','.v25-live-invite-card','.v25-live-message-report','@media(max-width:700px)','prefers-reduced-motion'
    ):
        require(marker in cl,f'style UI absent: {marker}')
    require(':focus-visible' in cl,'focus clavier visible absent')

    for marker in (
        'normalizeliveme(','normalizeliverooms(','normalizeliveinvites(','livepresencelabel(','liveroomaccesslabel(','livecommandhelp()','liveuierrormessage('
    ):
        require(marker in tl,f'test modèle absent: {marker}')
    require("object.hasown(rooms[0],'owner_user_id')" in tl,'test minimisation owner_user_id absent')
    require("object.hasown(rooms[1],'user_id')" in tl,'test minimisation user_id absent')
    require("object.hasown(invites[0],'inviter_user_id')" in tl,'test minimisation inviter_user_id absent')

    # Dark launch strict: ni JS ni CSS En direct ne sont chargés par une page HTML.
    html='\n'.join(p.read_text('utf-8',errors='ignore').lower() for p in ROOT.rglob('*.html'))
    for asset in ('sinjira-live-ui-v25.js','sinjira-live-ui-model-v25.js','v25-live-ui.css'):
        require(asset not in html,f'asset UI chargé avant preuve production: {asset}')
    require('prochaine étape' in community.lower() and 'realtime sécurisé' in community.lower(),'carte Communauté ne doit pas annoncer En direct actif')

    for marker in (
        'node scripts/test_live_social_ui_model_v25.mjs',
        'python scripts/validate_live_social_ui_v25.py',
        'python scripts/validate_live_social_runtime_v25.py',
        'python scripts/validate_live_social_typed_commands_v25.py',
        'python scripts/validate_live_social_foundation_v25.py',
        'python scripts/validate_live_social_safety_v25.py',
        'python scripts/validate_social_home_v25.py'
    ):
        require(marker in wl,f'workflow incomplet: {marker}')
    for forbidden in ('supabase_access_token','supabase_db_password','--linked','db push','inputs.apply'):
        require(forbidden not in wl,f'workflow UI ne doit jamais viser production: {forbidden}')

    print('OK interface En direct V25 dark launch: DOM sûr, signalement live, invitations reçues self-only, minimisation des UUID, salons privés invitation-only et aucun chargement HTML avant preuve production.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
