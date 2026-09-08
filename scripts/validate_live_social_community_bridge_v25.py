#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BRIDGE=ROOT/'assets'/'js'/'sinjira-live-community-bridge-v25.js'
COMMUNITY=ROOT/'assets'/'js'/'sinjira-community-real.js'
WORKFLOW=ROOT/'.github'/'workflows'/'sinjira-live-social-ui-v25.yml'
GATE=ROOT/'scripts'/'validate_live_social_activation_gate_v25.py'


def require(condition,message):
    if not condition:
        raise SystemExit(f'ERREUR pont Communauté → En direct V25: {message}')


def load_gate():
    spec=importlib.util.spec_from_file_location('sinjira_live_activation_gate_v25',GATE)
    require(spec is not None and spec.loader is not None,'garde activation illisible')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    bridge=BRIDGE.read_text('utf-8')
    community=COMMUNITY.read_text('utf-8')
    workflow=WORKFLOW.read_text('utf-8')
    bl=bridge.lower(); cl=community.lower(); wl=workflow.lower()

    for marker in (
        'normalizecommunityliveinvitecontext(',
        'mountcommunityliveinvite(',
        "social_live_community_context_unavailable",
        "social_live_community_self_invite_forbidden",
        "await import('./sinjira-live-invites-ui-v25.js')",
        'createliveinvitetargetui(root,options)',
        'object.freeze({targetuserid:targetid,targetlabel:label})'
    ):
        require(marker in bl,f'contrat pont manquant: {marker}')

    for forbidden in (
        'social_profiles','.from(','queryselector','queryselectorall','localstorage','sessionstorage',
        'indexeddb','document.cookie','urlsearchparams','location.href','location.search','location.hash',
        'history.pushstate','history.replacestate','fetch(','sendbeacon(','dataset','innerhtml',
        'insertadjacenthtml','document.write','console.log','console.error','console.warn'
    ):
        require(forbidden not in bl,f'primitive d’annuaire, fuite ou persistance interdite: {forbidden}')

    # Tant que la preuve production est incomplète, Communauté ne doit pas charger le pont.
    require('sinjira-live-community-bridge-v25.js' not in cl,'Communauté importe le pont avant preuve production')
    html='\n'.join(p.read_text('utf-8',errors='ignore').lower() for p in ROOT.rglob('*.html'))
    require('sinjira-live-community-bridge-v25.js' not in html,'pont chargé par HTML avant preuve production')

    for marker in (
        'assets/js/sinjira-live-community-bridge-v25.js',
        'scripts/test_live_social_community_bridge_v25.mjs',
        'scripts/validate_live_social_community_bridge_v25.py',
        'node scripts/test_live_social_community_bridge_v25.mjs /tmp/sinjira-live-community-bridge-v25.mjs',
        'python scripts/validate_live_social_community_bridge_v25.py'
    ):
        require(marker in wl,f'workflow UI incomplet: {marker}')
    for forbidden in ('supabase_access_token','supabase_db_password','--linked','db push','inputs.apply'):
        require(forbidden not in wl,f'workflow UI ne doit jamais viser production: {forbidden}')

    gate=load_gate()
    match=gate.SCRIPT_MOUNT_RE.search(
        '<script type="module" src="/assets/js/sinjira-live-community-bridge-v25.js"></script>'
    )
    require(match is not None,'garde activation ne détecte pas le pont Communauté')
    require(match.group(1).lower()=='sinjira-live-community-bridge-v25.js','garde capture le mauvais asset pour le pont')

    print('OK pont Communauté → En direct V25: contexte social borné, aucun annuaire/UUID exposé, aucun montage prématuré et garde production étendu.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
