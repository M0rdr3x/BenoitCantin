#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    p=ROOT/path
    if not p.exists():
        raise SystemExit(f'Fichier absent: {path}')
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
    core=read('assets/js/sinjira-supabase.js')
    challenge=read('assets/js/sinjira-mfa-v24-4-66.js')
    security=read('assets/js/v24-security.js')
    login=read('assets/js/sinjira-auth-pages.js')
    page=read('compte/mfa.html')
    login_page=read('compte/connexion.html')
    security_page=read('compte/securite.html')

    require(core,[
        'safeInternalDestination',
        "data?.nextLevel==='aal2'",
        "data?.currentLevel!=='aal2'",
        'state=aal-check',
        'await new Promise(()=>{})',
        "raw.startsWith('//')",
        "raw.includes('\\\\')",
        "[\\u0000-\\u001f\\u007f]"
    ],'garde MFA central')

    require(challenge,[
        'challengeAndVerify',
        'replaceChildren()',
        "document.createElement('option')",
        'option.textContent=String(factor.friendly_name',
        "status==='verified'",
        "security_resolve_connection_challenge_mfa",
        "aal?.currentLevel!=='aal2'",
        "signOut({scope:'local'})",
        'PENDING_CHALLENGE_STORAGE'
    ],'challenge MFA')
    forbid(challenge,['factorSelect.innerHTML'], 'challenge MFA')

    require(security,[
        'MAX_TOTP_FACTORS=10',
        "factorType:'totp'",
        'friendlyName:`SINJIRA TOTP ${verifiedCount+1}`',
        'challengeAndVerify',
        'mfa.unenroll',
        "qrCode.startsWith('data:image/')",
        "verified.length?'Ajouter une application d’authentification de secours'"
    ],'centre de sécurité MFA')
    forbid(security,["factorType:'phone'",'twilio','stripe'], 'centre de sécurité MFA')

    require(login,[
        "functions.invoke('security-context'",
        "outcome==='challenge'",
        "outcome==='block'",
        "getAuthenticatorAssuranceLevel",
        'PENDING_CHALLENGE_STORAGE',
        "signOut({scope:'local'})"
    ],'Bouclier au login')

    require(page,['data-mfa-challenge-form','data-mfa-factor','sinjira-mfa-v24-4-66.js?v=24.4.98'],'page challenge MFA')
    require(login_page,['sinjira-auth-pages.js?v=24.4.98'],'page connexion Bouclier')
    # Le runtime de sécurité continue d’évoluer après V24.4.66; ce contrat vérifie
    # le bon fichier et la promesse utilisateur, sans figer les autres composants.
    require(security_page,[
        'data-mfa-enroll',
        'data-mfa-factors',
        'v24-security.js?v=',
        'aucun SMS, aucun numéro de téléphone et aucun fournisseur payant n’est requis'
    ],'page sécurité MFA')

    print('OK MFA V24.4.98: TOTP gratuit, AAL2 fail-closed, Bouclier au login, redirections internes, rendu sans XSS et facteurs de secours autorisés.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
