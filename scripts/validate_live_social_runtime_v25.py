#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARSER=ROOT/'assets'/'js'/'sinjira-live-command-parser-v25.js'
RUNTIME=ROOT/'assets'/'js'/'sinjira-live-runtime-v25.js'
NODE_TEST=ROOT/'scripts'/'test_live_social_command_parser_v25.mjs'
COMMUNITY=ROOT/'compte'/'communaute.html'
WORKFLOW=ROOT/'.github'/'workflows'/'sinjira-live-social-runtime-v25.yml'


def require(condition,message):
    if not condition:
        raise SystemExit(f'ERREUR runtime En direct V25: {message}')


def main():
    parser=PARSER.read_text('utf-8')
    runtime=RUNTIME.read_text('utf-8')
    test=NODE_TEST.read_text('utf-8')
    community=COMMUNITY.read_text('utf-8')
    workflow=WORKFLOW.read_text('utf-8')
    pl=parser.lower(); rl=runtime.lower(); cl=community.lower()

    for marker in (
        "case 'join'", "rpc:'social_live_join_public_room'",
        "case 'rooms'", "rpc:'social_live_list_rooms'",
        "case 'me'", "rpc:'social_live_me'"
    ):
        require(marker in pl,f'mapping fermé absent: {marker}')
    require("return {kind:'error',code:'live_command_unknown'" in pl,'commande inconnue doit rester fermée')
    require('eval(' not in pl and 'new function' not in pl,'parseur ne doit jamais exécuter du texte')

    for marker in (
        "from('social_live_messages')",
        '.insert(payload)',
        'const payload={room_id:id,body:safebody}',
        'await supabase.realtime.setauth(accesstoken)',
        'private:true',
        'presence:{key:presencekey}',
        "channel.on('broadcast',{event:'message_created'}",
        'payload?.message_id',
        "channel.on('presence',{event:'sync'}",
        'channel.track({online:true})',
        'crypto.randomuuid()',
        'fetchrealtimemessage(payload?.message_id,id,supabase)',
        'author_label',
        'const {user_id,...message}=row'
    ):
        require(marker in rl,f'contrat runtime absent: {marker}')

    require('payload?.body' not in rl,'le Broadcast ne doit jamais fournir le corps rendu')
    require("channel.track({user_id" not in rl and "channel.track({user" not in rl,'Presence ne doit pas publier UUID/profil')
    require('localstorage' not in rl and 'sessionstorage' not in rl,'Presence ne doit pas être persistée côté client')
    require('navigator.geolocation' not in rl and 'geolocation.getcurrentposition' not in rl,'runtime ne doit pas demander GPS')
    require('innerhtml' not in rl and 'insertadjacenthtml' not in rl,'runtime ne doit pas injecter HTML')
    require('document.cookie' not in rl,'runtime ne doit pas lire les cookies')
    require('console.log' not in rl,'runtime ne doit pas journaliser messages ou jetons')
    require("access_token" in rl and 'console' not in rl,'jeton seulement utilisé pour authentifier Realtime')

    for marker in (
        "parseLiveInput('/join salon-test')",
        "parseLiveInput('/rooms')",
        "parseLiveInput('/me')",
        "parseLiveInput('/drop table users')",
        "'/rpc evil_function'",
        'liveroomid(room.touppercase())' if False else 'normalizeliveroomid(room.touppercase())'
    ):
        require(marker.lower() in test.lower(),f'test parseur absent: {marker}')

    # Dark launch: aucune page HTML ne charge encore le runtime tant que #240 bloque le backend hébergé.
    html='\n'.join(p.read_text('utf-8',errors='ignore').lower() for p in ROOT.rglob('*.html'))
    require('sinjira-live-runtime-v25.js' not in html,'runtime chargé par une page avant preuve production')
    require('sinjira-live-command-parser-v25.js' not in html,'parseur chargé par une page avant preuve production')
    require('prochaine étape' in cl and 'realtime' in cl,'carte Communauté doit rester en état feuille de route')

    for marker in (
        'node --check assets/js/sinjira-live-command-parser-v25.js',
        'node --check assets/js/sinjira-live-runtime-v25.js',
        'node scripts/test_live_social_command_parser_v25.mjs',
        'python scripts/validate_live_social_runtime_v25.py',
        'python scripts/validate_live_social_typed_commands_v25.py',
        'python scripts/validate_live_social_foundation_v25.py',
        'python scripts/validate_live_social_safety_v25.py',
        'python scripts/validate_social_home_v25.py'
    ):
        require(marker in workflow,f'workflow incomplet: {marker}')

    for forbidden in ('SUPABASE_ACCESS_TOKEN','SUPABASE_DB_PASSWORD','--linked','db push','inputs.apply'):
        require(forbidden not in workflow,f'workflow dark launch ne doit jamais viser production: {forbidden}')

    print('OK runtime En direct V25 dark launch: mapping fermé, Realtime privé, Broadcast relu via RLS, Presence éphémère minimale et aucune activation HTML avant preuve production.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
