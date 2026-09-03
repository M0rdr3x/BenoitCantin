#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def read(rel):
    p=ROOT/rel
    if not p.exists(): raise AssertionError(f'Fichier absent: {rel}')
    return p.read_text('utf-8',errors='ignore')

def require(text, markers, label):
    missing=[m for m in markers if m not in text]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')

def forbid(text, markers, label):
    found=[m for m in markers if m in text]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')

def numeric_version(value):
    try:
        parts=tuple(int(part) for part in str(value).split('.'))
    except (TypeError,ValueError):
        raise AssertionError(f'app.json: version mobile invalide: {value!r}')
    if len(parts)!=3:
        raise AssertionError(f'app.json: version mobile invalide: {value!r}')
    return parts

def main():
    migration=read('supabase/migrations/20260822011003_v24_4_99_recovery_and_lost_device_security.sql')
    require(migration,[
        'security_after_password_recovery',
        'security_report_lost_device',
        'security_require_aal2_if_available',
        "event_type,summary,severity",
        "'password_recovery_completed'",
        "'device_reported_lost'",
        'security_push_endpoints',
        "grant execute on function public.security_after_password_recovery(text) to authenticated",
        "grant execute on function public.security_report_lost_device(uuid) to authenticated",
    ],'migration récupération/appareil perdu')
    forbid(migration,['grant execute on function public.security_after_password_recovery(text) to anon','grant execute on function public.security_report_lost_device(uuid) to anon'],'ACL récupération')

    recovery=read('assets/js/sinjira-recovery-v24-4-99.js')
    require(recovery,[
        'getAuthenticatorAssuranceLevel',
        "data?.nextLevel==='aal2'",
        "data?.currentLevel!=='aal2'",
        'mfa.html?recovery=1',
        'updateUser({password})',
        "security_after_password_recovery",
        "signOut({scope:'global'})",
        's.auth.getUser()',
    ],'client récupération')
    forbid(recovery,['auth.getSession()'],'récupération serveur-vérifiée')

    security=read('assets/js/sinjira-security-v24-4-99.js')
    require(security,[
        "security_report_lost_device",
        "signOut({scope:'others'})",
        "data-device-lost",
        "PublicKeyCredential",
        "RP ID définitif",
        "non activé",
    ],'Centre sécurité V24.4.99')
    forbid(security,['navigator.credentials.create','navigator.credentials.get'],'passkeys avant domaine final')

    reset=read('compte/reinitialiser-mot-de-passe.html')
    require(reset,['sinjira-recovery-v24-4-99.js?v=24.4.99','second facteur'],'page récupération')
    center=read('compte/securite.html')
    require(center,['sinjira-security-v24-4-99.js?v=24.4.99','Déclarer perdu','aucun SMS, aucun numéro de téléphone et aucun fournisseur payant n’est requis'],'page Ma sécurité')

    app=json.loads(read('mobile-native/app.json'))['expo']
    version=numeric_version(app.get('version'))
    if version<(24,4,99): raise AssertionError('app.json: la version mobile ne peut pas régresser sous 24.4.99')
    if app.get('extra',{}).get('webOrigin')!='https://www.benoitcantin.com': raise AssertionError('app.json: origine active ne doit pas migrer avant le DNS')
    try:
        ios_build=int(app.get('ios',{}).get('buildNumber','0'))
    except (TypeError,ValueError):
        raise AssertionError('app.json: buildNumber iOS invalide')
    if ios_build<24499: raise AssertionError('app.json: buildNumber iOS ne peut pas régresser sous 24499')
    android_build=app.get('android',{}).get('versionCode')
    if not isinstance(android_build,int) or android_build<24499: raise AssertionError('app.json: versionCode Android ne peut pas régresser sous 24499')
    domains=set(app.get('ios',{}).get('associatedDomains',[]))
    for domain in ('applinks:www.benoitcantin.com','applinks:sinjira.com','applinks:www.sinjira.com'):
        if domain not in domains: raise AssertionError(f'app.json: domaine iOS absent: {domain}')

    native=read('mobile-native/App.tsx')
    require(native,[
        "DEFAULT_ORIGIN = 'https://www.benoitcantin.com'",
        "Constants.expoConfig?.extra?.webOrigin",
        "parsed.protocol === 'https:'",
        "'sinjira.com'",
        "'www.sinjira.com'",
        'Application mobile · V',
        'v=24.4.99',
    ],'runtime mobile')

    domain_plan=read('DOMAIN_MIGRATION_SINJIRA.md')
    require(domain_plan,[
        'aucun changement DNS autorisé',
        'RP ID prévu est **`sinjira.com`**',
        'apple-app-site-association',
        'assetlinks.json',
        'Apple Team ID',
        'SHA-256 du certificat de signature de production',
        'Rollback',
    ],'plan domaine')

    codeowners=read('.github/CODEOWNERS')
    require(codeowners,['* @M0rdr3x'],'CODEOWNERS')
    governance=read('.github/workflows/main-governance.yml')
    require(governance,['listPullRequestsAssociatedWithCommit','mergedToMain','core.setFailed'],'garde main')

    ledger=read('supabase/production-migration-ledger.txt')
    require(ledger,['20260822011003 v24_4_99_recovery_and_lost_device_security'],'ledger production')

    print(f'OK SINJIRA >=V24.4.99 ({app.get("version")}): récupération AAL2, appareil perdu, mobile migrable, passkeys différées, domaine et gouvernance contrôlés.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
