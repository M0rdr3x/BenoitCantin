#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260918020000_sinjira_v25_account_capabilities.sql'
TEST=ROOT/'supabase/tests/account_capabilities_v25.test.sql'
ACCOUNT=ROOT/'assets/js/sinjira-account.js'
LIBRARY=ROOT/'assets/js/sinjira-library-v24-4-61.js'
LIBRARY_CORE=ROOT/'assets/js/sinjira-library.js'
COMMUNITY=ROOT/'assets/js/sinjira-community-real.js'
errors=[]

def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8')

def compact(text): return ''.join(text.lower().split())
def req(cond,msg):
    if not cond: errors.append(msg)

mig=read(MIG); test=read(TEST); account=read(ACCOUNT); library=read(LIBRARY); core=read(LIBRARY_CORE); community=read(COMMUNITY)
m=compact(mig); t=compact(test); a=compact(account); l=compact(library); lc=compact(core); co=compact(community)

req('createorreplacefunctionpublic.sinjira_my_account_capabilities()' in m,'RPC capacités self-only absent.')
req('sinjira_my_account_capabilities(uuid)' not in m,'Une variante UUID arbitraire des capacités existe.')
req('revokeallonfunctionpublic.sinjira_my_account_capabilities()frompublic,anon' in m,'anon/public conserve un droit sur les capacités.')
req('grantexecuteonfunctionpublic.sinjira_my_account_capabilities()toauthenticated,service_role' in m,'authenticated ne reçoit pas le RPC self-only.')
req("ifuidisnullthenraiseexception'auth_required'" in m,'RPC capacités sans garde auth.uid fail-closed.')
req("bandin('adult','youth')" in m,'Mode standard non borné aux bandes vérifiées adult/youth.')
req("'account_mode',casewhenband='child'then'child'whenstandardthen'standard'else'restricted'end" in m,'Mode restricted pour bandes pending/unverified absent.')
req("'library_mode',casewhenband='child'then'reviewed_11_12'whenstandardthen'full'else'none'end" in m,'Mode Bibliothèque centralisé absent.')
req("'native_general_hubs',standard" in m,'Capacité hubs natifs généraux absente.')
req("'dating',band='adult'" in m,'Rencontres n est pas strictement adulte dans les capacités.')
for forbidden in ('date_of_birth','birth_date','email','display_name','pseudo','guardian_user_id','minor_user_id'):
    req(forbidden not in m,f'Donnée personnelle interdite renvoyée/consultée dans le contrat capacités: {forbidden}')

req("rpc('sinjira_my_account_capabilities')" in a,'Navigation compte n utilise pas le RPC capacités.')
req("constaccountmode=string(capabilities.account_mode||'restricted')" in a and "accountmode==='standard'?'nonchild':'unknown'" in a,'Le pont natif ne traite pas restricted comme fail-closed.')
req("capabilities.child_11_12===true" in a,'Navigation compte ne lit pas child_11_12.')
req("rpc('sinjira_my_account_capabilities')" in l and "capabilities.library_mode==='reviewed_11_12'" in l,'Bibliothèque V24.4.61 non pilotée par library_mode.')
req("rpc('sinjira_my_account_capabilities')" in lc and "capabilities.library_mode==='reviewed_11_12'" in lc,'Bibliothèque cœur non pilotée par library_mode.')
req("rpc('sinjira_my_account_capabilities')" in co and 'capabilities.general_community!==true' in co,'Communauté générale non pilotée par les capacités.')

req('selectplan(25);' in t,'Plan pgTAP capacités inattendu.')
for marker in (
    'aucunrpccapacitésavecuuidarbitraire',
    'uncomptesansprofildesécuritévérifiéresterestricted',
    'restrictednepeutpasouvrirleshubsnatifsgénéraux',
    'restrictednereçoitaucunebibliothèque',
    'restrictednepeutpasouvrirlacommunautégénérale',
    'hubsnatifs générauxfermésà11–12'.replace(' ',''),
    'bibliothèquebornéeaucontenurevu',
    'communautégénéraleferméeà11–12',
    'rencontresferméeà11–12',
    'communautéjunioréligibleà11–12',
    'aprèsrévocationparentaleun11–12devientchild_pending',
    'child_pendingdevientimmédiatementrestricted',
    'child_pendingperdimmédiatementlabibliothèquejunior',
    'child_pendingperdimmédiatementléligibilitécommunautéjunior',
):
    req(marker in t,f'Preuve pgTAP capacités absente: {marker}')

if errors:
    print(f'ECHEC capacités compte V25: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK V25: capacités self-only centralisées; child/standard/restricted fail-closed et clients critiques alignés.')
