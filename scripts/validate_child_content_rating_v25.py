#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260918013000_sinjira_v25_child_content_rating.sql'
HARDENING=ROOT/'supabase/migrations/20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql'
PRODUCT_ACCESS=ROOT/'supabase/migrations/20260922033000_sinjira_v25_project_product_access.sql'
TEST=ROOT/'supabase/tests/child_content_rating_v25.test.sql'
ACCOUNT=ROOT/'assets/js/sinjira-account.js'
LIBRARY=ROOT/'assets/js/sinjira-library-v24-4-61.js'
LIBRARY_CORE=ROOT/'assets/js/sinjira-library.js'
ADMIN=ROOT/'assets/js/sinjira-admin-console-core.js'
ADMIN_EDGE=ROOT/'supabase/functions/admin-console/index.ts'
DOC_EDGE=ROOT/'supabase/functions/get-document-url/index.ts'
DOC=ROOT/'docs/SINJIRA_CHILD_ACCESS_MATRIX_V25.md'
errors=[]

def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8')

def compact(text): return ''.join(text.lower().split())
def req(cond,msg):
    if not cond: errors.append(msg)

mig=read(MIG); hardening=read(HARDENING); product_access=read(PRODUCT_ACCESS); test=read(TEST); account=read(ACCOUNT); library=read(LIBRARY)
core=read(LIBRARY_CORE); admin=read(ADMIN); admin_edge=read(ADMIN_EDGE); doc_edge=read(DOC_EDGE); doc=read(DOC)
m=compact(mig); h=compact(hardening); pa=compact(product_access); t=compact(test); a=compact(account); l=compact(library); lc=compact(core); ad=compact(admin); ae=compact(admin_edge); de=compact(doc_edge); d=doc.lower()

for table in ('projects','documents'):
    req(f'altertablepublic.{table}' in m,f'Classement 11–12 absent de {table}.')
req("child_access_statusin('unreviewed','approved_11_12','blocked_11_12')" in m,'Enum de classement 11–12 incomplet.')
req("default'unreviewed'" in m,'Le classement 11–12 ne ferme pas par défaut.')
req('child_access_reviewed_byuuidreferencesauth.users(id)' in m,'Le réviseur humain n est pas conservé.')
req('createorreplacefunctionpublic.sinjira_child_project_available' in m,'Helper projet 11–12 absent.')
req('createorreplacefunctionpublic.sinjira_child_document_available' in m,'Helper document 11–12 absent.')
req("p.child_access_status='approved_11_12'" in m,'Projet non borné à approved_11_12.')
req("d.child_access_status='approved_11_12'" in m,'Document non borné à approved_11_12.')
req('public.sinjira_child_project_available(d.project_id)' in m,'Le document ne dépend pas aussi du classement du projet.')
req('createorreplacefunctionsinjira_v25_internal.sinjira_child_project_available' in h,'Le helper projet effectif n est pas durci après la frontière RPC.')
req("p.visibility='public'or(p.visibility='account'andauth.uid()isnotnull)" in h,'Le helper projet expose encore visibility=account à anon.')
req('createorreplacefunctionsinjira_v25_internal.sinjira_child_document_available' in h,'Le helper document effectif n est pas durci après la frontière RPC.')
req('sinjira_catalog_internal.project_access_rank(d.project_id,auth.uid())>=public.document_access_rank(d.access_level)' in h,'Le helper document ne respecte pas le rang réel du compte courant.')
req('createorreplacefunctionsinjira_v25_internal.sinjira_child_project_available' in pa,'La frontière projet/produit ne remplace pas le helper enfant effectif.')
req("p.child_access_status='approved_11_12'andp.product_slugisnull" in pa,'Le helper enfant effectif ne ferme pas les projets liés à un produit.')
req("visibility='public'andproduct_slugisnull" in pa,'La RLS générale réexpose un projet public payant sans droit.')
req("public.sinjira_my_age_band()='child'andvisibility='account'andchild_access_status='approved_11_12'andproduct_slugisnull" in pa,'La branche child account n exclut pas explicitement les projets payants.')
req('createpolicyprojects_purchased_read_v25' in pa and "public.sinjira_my_age_band()in('adult','youth')" in pa and 'public.has_sinjira_product(product_slug,(selectauth.uid()))' in pa,'La policy projet acheté n est pas bornée adult/youth + droit produit.')
req("p.visibility='public'or(p.visibility='account'andauth.uid()isnotnull)" in m,'La migration d introduction expose encore visibility=account à anon.')
req('public.project_access_rank(d.project_id,auth.uid())>=public.document_access_rank(d.access_level)' in m,'La migration d introduction ne borne pas le helper document au rang réel.')
req("p.visibility='public'" in m and "p.visibility='account'" in m,'Un projet restricted pourrait devenir Junior par simple classement.')
req("public.sinjira_my_age_band()in('adult','youth')" in m and "public.sinjira_my_age_band()='child'" in m and "public.sinjira_my_age_band()<>'child'" not in m,'Les politiques de contenu ne séparent pas explicitement standard, child et restricted.')
for legacy_policy in ('projects_public_read','projects_authenticated_read','documents_anon_read','documents_authenticated_read'):
    req(f'droppolicyifexists{legacy_policy}' in m,f'Politique SELECT héritée non retirée: {legacy_policy}.')

for route in ('bibliotheque.html','documents.html','projet.html'):
    req(f"'{route}'" in a,f'Route classée non ouverte au compte child: {route}.')
req("s.rpc('sinjira_my_account_capabilities')" in l,'Bibliothèque moderne sans capacités serveur.')
req("constchildmode=capabilities.library_mode==='reviewed_11_12'" in l,'Bibliothèque moderne sans mode child centralisé.')
for forbidden in ('access_requests','sinjira_reader_library','user_entitlements'):
    child_block=l[l.find("if(childmode){"):l.find("const[adminresult",l.find("if(childmode){"))]
    req(forbidden not in child_block,f'Bibliothèque Junior interroge encore {forbidden}.')
req('aucuncontenun’aencoreétéapprouvépourlescomptesde11–12ans' in l,'État vide sûr de Bibliothèque Junior absent.')
req("childmode?'approuvé11–12ans'" in lc,'Fiche projet/document n indique pas le mode 11–12.')
req('if(childmode)' in lc and 'lesplaytestsnesontpasdisponibles' in lc,'La fiche projet Junior expose encore les playtests.')
req("!childmode&&p.play_path" in lc,'La fiche projet Junior expose encore le bouton Jouer.')

req("const{user,service,aal}=awaitrequiredadmin(req)" in ae,'La console admin ne conserve pas le niveau AAL pour la révision 11–12.')
req("action==='set_child_access_review'" in ae,'Action admin explicite de révision 11–12 absente.')
req("aal.nextlevel!=='aal2'" in ae and "mfa_setup_required" in ae,'La révision 11–12 ne force pas la configuration MFA.')
req("aal.currentlevel!=='aal2'" in ae and "mfa_required" in ae,'La révision 11–12 ne force pas une session AAL2 active.')
req(ae.find("aal.currentlevel!=='aal2'") < ae.find("service.from(table).update(update)"),'Le contrôle AAL2 doit précéder toute écriture de classement 11–12.')
req("targettype==='project'?'projects':targettype==='document'?'documents':''" in ae,'Action admin de révision cible des tables arbitraires.')
req("['unreviewed','approved_11_12','blocked_11_12'].includes(childstatus)" in ae,'Action admin accepte un état de classement non borné.')
req('update.child_access_reviewed_by=user.id' in ae,'La décision admin n enregistre pas le réviseur humain.')
req('data-child-review-status="approved_11_12"' in admin,'Bouton admin Approuver 11–12 absent.')
req('data-child-review-status="blocked_11_12"' in admin,'Bouton admin Bloquer 11–12 absent.')

req("doc.child_access_status!=='approved_11_12'" in de,'get-document-url ne revérifie pas le classement document.')
req("doc.projects?.child_access_status!=='approved_11_12'" in de,'get-document-url ne revérifie pas le classement projet.')

req('selectplan(26);' in t,'Plan pgTAP classement 11–12 inattendu.')
for marker in ('unprojetnonréviséestindisponible11–12','unprojetaccountactifexplicitementapprouvédevientdisponible','anonnepeutpassonderunprojetaccountapprouvé11–12paruuid','unprojetrestrictednedevientpasjuniorparsimpleclassement','undocumentnonréviséestindisponible11–12','document+projetdoublementapprouvésdeviennentdisponibles','unprojetpayantresteindisponible11–12mêmeavecapprobationhumaine','undocumentdunprojetpayantresteindisponible11–12mêmedoublementapprouvé','anonnepeutpassonderundocumentaccountapprouvé11–12paruuid','bloquerensuiteleprojetrefermeimmédiatementledocument','uneseulepolitiquegénéraleprojetsresteactive;lesexceptionsowner,familleetachatv25restentexplicitementbornées','uneseulepolitiqueselectdocumentsresteactive','rlsprojetsséparestandard,childetbandesrestreintes','lapolicyprojetachetéresteinterditeauxcomptes11–12etexigeundroitproduitréel','rlsdocumentsséparestandard,childetbandesrestreintes'):
    req(marker in t,f'Preuve pgTAP classement enfant absente: {marker}')

req('défaut `unreviewed` reste fermé' in d,'Documentation: défaut unreviewed non expliqué.')
req('décision humaine' in d,'Documentation: révision humaine explicite absente.')

if errors:
    print(f'ECHEC classement contenu enfant V25: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK V25: Bibliothèque 11–12 fail-closed; projets payants exclus, projet + document gratuits doublement approuvés avant exposition.')
