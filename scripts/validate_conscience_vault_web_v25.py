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


def main()->int:
    page=read('compte/registre-personnel.html')
    js=read('assets/js/sinjira-consciousness-vault-v25.js')
    css=read('assets/css/sinjira-consciousness-vault-v25.css')
    dashboard=read('compte/index.html')

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
        "rpc('security_list_devices'",
    ] if False else [
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
        'Registre narratif',
    ],'accès dashboard et séparation des deux Registres')

    print('OK Web V25: Registre personnel distinct du narratif, Edge uniquement, capacité mémoire, auto-verrouillage, aucun export ni stockage local du contenu.')
    return 0


if __name__=='__main__':raise SystemExit(main())
