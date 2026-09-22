#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

FILES={
    "migration":ROOT/"supabase/migrations/20260922014000_sinjira_v25_creator_family_catalog_access.sql",
    "paid_access_migration":ROOT/"supabase/migrations/20260922023000_sinjira_v25_paid_order_product_access.sql",
    "extension_access_migration":ROOT/"supabase/migrations/20260922030000_sinjira_v25_extension_product_access.sql",
    "age_boundary_migration":ROOT/"supabase/migrations/20260922031500_sinjira_v25_catalog_age_helper_boundary.sql",
    "project_access_migration":ROOT/"supabase/migrations/20260922033000_sinjira_v25_project_product_access.sql",
    "shared":ROOT/"supabase/functions/_shared/privateNovel.ts",
    "library":ROOT/"assets/js/sinjira-library-v24-4-61.js",
    "licenses":ROOT/"assets/js/v24-licenses.js",
    "secondary_library":ROOT/"assets/js/sinjira-library.js",
    "purchases":ROOT/"assets/js/sinjira-purchases-v25.js",
    "literature":ROOT/"assets/js/sinjira-literature-catalog-v25.js",
    "library_html":ROOT/"compte/bibliotheque.html",
    "licenses_html":ROOT/"compte/licences.html",
    "purchases_html":ROOT/"compte/mes-achats.html",
    "literature_html":ROOT/"projets/sinjira/romans/index.html",
    "dashboard":ROOT/"assets/js/sinjira-account-dashboard-v24-4-60.js",
    "account_index":ROOT/"compte/index.html",
    "test":ROOT/"supabase/tests/creator_family_catalog_access_v25.test.sql",
    "provision":ROOT/"scripts/provision_creator_family_catalog.py",
    "account_workflow":ROOT/".github/workflows/sinjira-account-content-hub-v25.yml",
    "novel_workflow":ROOT/".github/workflows/sinjira-private-novel-catalog-v25.yml",
}

EMAIL_LITERAL_RE=re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")

def fail(message:str)->None:
    raise ValueError(message)

def compact(value:str)->str:
    return "".join(value.lower().split())

def validate(contents:dict[str,str])->None:
    migration=compact(contents["migration"])
    paid_access_migration=compact(contents["paid_access_migration"])
    extension_access_migration=compact(contents["extension_access_migration"])
    age_boundary_migration=compact(contents["age_boundary_migration"])
    project_access_migration=compact(contents["project_access_migration"])
    shared=compact(contents["shared"])
    library=compact(contents["library"])
    licenses=compact(contents["licenses"])
    secondary_library=compact(contents["secondary_library"])
    purchases=compact(contents["purchases"])
    literature=compact(contents["literature"])
    test=compact(contents["test"])
    dashboard=compact(contents["dashboard"])
    account_workflow=contents["account_workflow"]
    novel_workflow=contents["novel_workflow"]
    provision=compact(contents["provision"])

    # Aucune adresse réelle ou synthétique ne doit être gravée dans la migration publique.
    if EMAIL_LITERAL_RE.search(contents["migration"]):
        fail("accès famille: une adresse courriel littérale est présente dans la migration publique")

    for provision_marker in (
        'sinjira_creator_family_emails',
        'supabase_service_role_key',
        'set_sinjira_catalog_family_access_by_email',
        'authorization',
        'bearer{service_key}',
        'comptefamilial{index}/{len(emails)}',
    ):
        if provision_marker not in provision:
            fail(f"provisionnement famille: garde absente: {provision_marker}")
    if "outlook.com" in provision or "gmail.com" in provision:
        fail("provisionnement famille: une adresse personnelle ne doit jamais être gravée dans le script")


    for paid_marker in (
        "droppolicyifexistsproducts_ordered_readonpublic.products",
        "createpolicyproducts_ordered_read",
        "public.sinjira_my_age_band()in('adult','youth')",
        "o.status='paid'",
        "createorreplacefunctionpublic.has_sinjira_product(",
        "frompublic.orderso",
        "joinpublic.order_itemsoionoi.order_id=o.id",
        "o.status='paid'",
        "p.slug=p_product_slug",
        "p_user_idisdistinctfromauth.uid()thenfalse",
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_product_rights()",
        "selectauth.uid()asuid",
        "'paid_order'::textassource",
        "public.sinjira_age_band(auth.uid())",
        "a.bandin('adult','youth')",
        "distincton(product_id)",
        "revokeallonfunctionsinjira_v25_internal.sinjira_my_product_rights()frompublic,anon,authenticated",
        "createorreplacefunctionpublic.sinjira_my_product_rights()",
        "securityinvoker",
        "selectsinjira_v25_internal.sinjira_my_product_rights()",
        "revokeallonfunctionpublic.sinjira_my_product_rights()frompublic,anon",
        "grantexecuteonfunctionpublic.sinjira_my_product_rights()toauthenticated,service_role",
    ):
        if paid_marker not in paid_access_migration:
            fail(f"droit produit payé: invariant absent: {paid_marker}")
    if "o.status<>'cancelled'" in paid_access_migration or "o.status!='cancelled'" in paid_access_migration:
        fail("droit produit payé: une commande non annulée ne suffit pas; le statut paid doit être explicite")
    if paid_access_migration.count("o.status='paid'") < 2:
        fail("droit produit payé: policy produits et helper canonique doivent tous deux exiger status=paid")

    rights_start=paid_access_migration.find("createorreplacefunctionsinjira_v25_internal.sinjira_my_product_rights()")
    rights_end=paid_access_migration.find("$rights$;",rights_start)
    if rights_start < 0 or rights_end < 0:
        fail("droits produit effectifs: implémentation self-only absente ou incomplète")
    rights_segment=paid_access_migration[rights_start:rights_end]
    if "securitydefiner" not in rights_segment:
        fail("droits produit effectifs: implémentation interne doit rester SECURITY DEFINER")
    if "p_user_id" in rights_segment:
        fail("droits produit effectifs: aucun UUID arbitraire ne doit être accepté")
    if rights_segment.count("a.bandin('adult','youth')") < 2:
        fail("droits produit effectifs: entitlement et commande paid doivent tous deux rester masqués aux comptes 11–12")
    for forbidden in ("order_number","total_cents","currency","email"):
        if forbidden in rights_segment:
            fail(f"droits produit effectifs: détail commercial interdit dans la réponse: {forbidden}")
    wrapper_start=paid_access_migration.find("createorreplacefunctionpublic.sinjira_my_product_rights()")
    wrapper_end=paid_access_migration.find("$wrapper$;",wrapper_start)
    if wrapper_start < 0 or wrapper_end < 0:
        fail("droits produit effectifs: wrapper public absent")
    wrapper_segment=paid_access_migration[wrapper_start:wrapper_end]
    if "securityinvoker" not in wrapper_segment or "securitydefiner" in wrapper_segment:
        fail("droits produit effectifs: wrapper public doit rester SECURITY INVOKER")

    for extension_marker in (
        "altertablepublic.extensionsaddcolumnifnotexistsproduct_slugtext",
        "extensions_product_slug_fkey",
        "createpolicy\"extensionspublicread\"onpublic.extensions",
        "createpolicyextensions_purchased_read_v25",
        "parent_project.id=extensions.project_id",
        "parent_project.status<>'draft'",
        "p.status<>'draft'and(",
        "statusin('approved','released')",
        "public.sinjira_age_band((selectauth.uid()))in('adult','youth')",
        "public.has_sinjira_product(product_slug,(selectauth.uid()))",
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_extension_catalog()",
        "whenband='child'thenfull_catalog",
        "e.product_slugisnotnullandpublic.has_sinjira_product(e.product_slug,uid)",
        "then'product'",
    ):
        if extension_marker not in extension_access_migration:
            fail(f"accès extension payé: invariant absent: {extension_marker}")

    if extension_access_migration.count("parent_project.status<>'draft'") < 2:
        fail("accès extension: public et acheté doivent tous deux fermer un projet parent brouillon")

    for boundary_marker in (
        "createorreplacefunctionsinjira_v25_internal.has_sinjira_product(",
        "securitydefiner",
        "p_user_idisdistinctfromauth.uid()thenfalse",
        "public.sinjira_age_band(p_user_id)in('adult','youth')",
        "createorreplacefunctionpublic.has_sinjira_product(",
        "securityinvoker",
        "selectsinjira_v25_internal.has_sinjira_product(p_product_slug,p_user_id)",
        "public.sinjira_my_age_band()in('adult','youth')",
        "visibility='public'andproduct_slugisnulland(",
        "(visibility='account'andproduct_slugisnull)orsinjira_catalog_internal.project_access_rank(id,(selectauth.uid()))>=20",
        "createpolicyproducts_entitled_read",
        "createpolicyproducts_ordered_read",
        "public.sinjira_my_age_band()in('adult','youth')",
        "o.status='paid'",
        "createpolicyproducts_family_catalog_read_v25",
        "createpolicyprojects_family_catalog_read_v25",
        "createpolicyextensions_creator_family_catalog_read_v25",
        "createpolicyextensions_purchased_read_v25",
    ):
        if boundary_marker not in age_boundary_migration:
            fail(f"frontière âge catalogue: invariant absent: {boundary_marker}")
    if "public.sinjira_age_band((selectauth.uid()))" in age_boundary_migration:
        fail("frontière âge catalogue: une policy navigateur appelle encore sinjira_age_band(uuid)")

    effective_age_policies=(
        "createpolicysinjira_novels_family_catalog_read_v25onpublic.sinjira_novelsforselecttoauthenticatedusing(public.is_sinjira_catalog_family_member((selectauth.uid()))andpublic.sinjira_my_age_band()in('adult','youth'))",
        "createpolicyproducts_entitled_readonpublic.productsforselecttoauthenticatedusing(public.sinjira_my_age_band()in('adult','youth')andexists(select1frompublic.user_entitlementsuewhereue.product_id=products.idandue.user_id=(selectauth.uid())))",
        "createpolicyproducts_ordered_readonpublic.productsforselecttoauthenticatedusing(public.sinjira_my_age_band()in('adult','youth')andexists(select1frompublic.order_itemsoijoinpublic.ordersoono.id=oi.order_idwhereoi.product_id=products.idando.user_id=(selectauth.uid())ando.status='paid'))",
        "createpolicyproducts_family_catalog_read_v25onpublic.productsforselecttoauthenticatedusing(public.is_sinjira_catalog_family_member((selectauth.uid()))andpublic.sinjira_my_age_band()in('adult','youth'))",
        "createpolicyprojects_family_catalog_read_v25onpublic.projectsforselecttoauthenticatedusing(public.is_sinjira_catalog_family_member((selectauth.uid()))andpublic.sinjira_my_age_band()in('adult','youth'))",
        "createpolicyextensions_creator_family_catalog_read_v25onpublic.extensionsforselecttoauthenticatedusing(public.sinjira_has_full_catalog_access((selectauth.uid()))andpublic.sinjira_my_age_band()in('adult','youth'))",
        "createpolicyextensions_purchased_read_v25onpublic.extensionsforselecttoauthenticatedusing(statusin('approved','released')andproduct_slugisnotnullandexists(select1frompublic.projectsparent_projectwhereparent_project.id=extensions.project_idandparent_project.status<>'draft')andpublic.sinjira_my_age_band()in('adult','youth')andpublic.has_sinjira_product(product_slug,(selectauth.uid())))",
    )
    for policy_marker in effective_age_policies:
        if policy_marker not in age_boundary_migration:
            fail(f"frontière âge catalogue: policy effective finale non bornée: {policy_marker[:80]}")

    for project_marker in (
        "altertablepublic.projectsaddcolumnifnotexistsproduct_slugtext",
        "projects_product_slug_fkey",
        "createpolicyprojects_purchased_read_v25",
        "status<>'draft'andproduct_slugisnotnull",
        "public.sinjira_my_age_band()in('adult','youth')",
        "public.has_sinjira_product(product_slug,(selectauth.uid()))",
        "p.product_slugisnull",
        "p.child_access_status='approved_11_12'andp.product_slugisnulland(",
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_project_catalog()",
        "whenfull_catalogthentrue",
        "p.product_slugisnotnullandsinjira_v25_internal.has_sinjira_product(p.product_slug,uid)",
        "sinjira_catalog_internal.project_access_rank(p.id,uid)>=20",
        "then'product'",
        "else'free'",
    ):
        if project_marker not in project_access_migration:
            fail(f"accès projet produit: invariant absent: {project_marker}")
    if "public.sinjira_age_band((selectauth.uid()))" in project_access_migration:
        fail("accès projet produit: une policy navigateur appelle encore sinjira_age_band(uuid)")
    if project_access_migration.count("sinjira_v25_internal.has_sinjira_product(p.product_slug,uid)") < 2:
        fail("accès projet produit: droit produit requis à la fois pour la source d accès et le filtrage du catalogue")

    for marker in (
        "createtableifnotexistsprivate.sinjira_catalog_family_members(",
        "user_iduuidprimarykeyreferencesauth.users(id)ondeletecascade",
        "revokeallontableprivate.sinjira_catalog_family_membersfrompublic,anon,authenticated",
        "createorreplacefunctionsinjira_v25_internal.is_sinjira_catalog_family_member(",
        "createorreplacefunctionsinjira_v25_internal.sinjira_has_full_catalog_access(",
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_catalog_access_mode()",
        "createorreplacefunctionsinjira_v25_internal.set_sinjira_catalog_family_access_by_email(",
        "createorreplacefunctionpublic.is_sinjira_catalog_family_member(",
        "createorreplacefunctionpublic.sinjira_has_full_catalog_access(",
        "createorreplacefunctionpublic.sinjira_my_catalog_access_mode()",
        "createorreplacefunctionpublic.set_sinjira_catalog_family_access_by_email(",
        "coalesce(auth.jwt()->>'role','')<>'service_role'",
        "fromauth.usersu",
        "wherelower(coalesce(u.email,''))=v_email",
        "revokeallonfunctionpublic.set_sinjira_catalog_family_access_by_email(text,boolean)frompublic,anon,authenticated",
        "grantexecuteonfunctionpublic.set_sinjira_catalog_family_access_by_email(text,boolean)toservice_role",
        "createorreplacefunctionpublic.has_sinjira_product(",
        "public.is_sinjira_catalog_family_member(p_user_id)",
        "public.sinjira_age_band(p_user_id)in('adult','youth')",
        "frompublic.productsfamily_product",
        "wherefamily_product.slug=p_product_slug",
    ):
        if marker not in migration:
            fail(f"accès famille: invariant de provisionnement absent: {marker}")

    family_table=migration[migration.find("createtableifnotexistsprivate.sinjira_catalog_family_members"):migration.find("altertableprivate.sinjira_catalog_family_members")]
    if "emailtext" in family_table:
        fail("accès famille: le registre privé ne doit pas stocker le courriel")
    if "labeltext" in family_table:
        fail("accès famille: le registre privé ne doit pas stocker de libellé nominatif")

    public_family_rpcs=(
        "is_sinjira_catalog_family_member",
        "sinjira_has_full_catalog_access",
        "sinjira_my_catalog_access_mode",
        "set_sinjira_catalog_family_access_by_email",
        "sinjira_my_project_catalog",
        "sinjira_my_extension_catalog",
        "sinjira_my_novel_catalog",
    )
    for name in public_family_rpcs:
        start=migration.find(f"createorreplacefunctionpublic.{name}(")
        if start < 0:
            fail(f"frontière RPC famille: wrapper public absent: {name}")
        end=migration.find("$wrapper$;",start)
        if end < 0:
            fail(f"frontière RPC famille: fin wrapper absente: {name}")
        segment=migration[start:end]
        if "securityinvoker" not in segment or "securitydefiner" in segment:
            fail(f"frontière RPC famille: wrapper public privilégié: {name}")

    for marker in (
        "createpolicysinjira_novels_family_catalog_read_v25",
        "createpolicyproducts_family_catalog_read_v25",
        "createpolicyprojects_family_catalog_read_v25",
        "createpolicyextensions_creator_family_catalog_read_v25",
        "public.sinjira_has_full_catalog_access((selectauth.uid()))",
        "public.is_sinjira_catalog_family_member((selectauth.uid()))",
        "public.sinjira_age_band((selectauth.uid()))in('adult','youth')",
    ):
        if marker not in migration:
            fail(f"accès famille: policy standard manquante: {marker}")

    for marker in (
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_project_catalog()",
        "createorreplacefunctionpublic.sinjira_my_project_catalog()",
        "raiseexception'catalog_access_required'",
        "p.child_access_status='approved_11_12'",
        "'content_available',case",
        "whenband='child'thennull",
        "elsep.cover_urlend",
        "contenuprotégéselonl’âge",
    ):
        if marker not in migration:
            fail(f"catalogue projet famille: garde 11–12 absente: {marker}")

    for marker in (
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_extension_catalog()",
        "createorreplacefunctionpublic.sinjira_my_extension_catalog()",
        "whenband='child'then'extensionsinjira™protégée'",
        "whenband='child'thenfalseelsetrueend",
        "elsee.is_public=trueande.statusin('approved','released')",
    ):
        if marker not in migration:
            fail(f"catalogue extensions famille: garde absente: {marker}")

    for marker in (
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_novel_catalog()",
        "createorreplacefunctionpublic.sinjira_my_novel_catalog()",
        "full_catalog_mode:=owner_modeorfamily_mode",
        "ifband='child'andnotfull_catalog_modethen",
        "private_asset_configuredandbandin('adult','youth')and(full_catalog_modeorproduct_access)",
        "whenband='child'andfamily_modethen'family_catalog'",
        "'demo_path',casewhenband='child'thennullelsedemo_pathend",
        "'cover_url',casewhenband='child'thennullelsecover_urlend",
    ):
        if marker not in migration:
            fail(f"catalogue roman famille: garde absente: {marker}")

    for marker in (
        "sinjira_v25_internal.sinjira_has_full_catalog_access(p_user_id)",
        "public.sinjira_age_band(p_user_id)in('adult','youth')then90",
        "p_user_idisdistinctfromauth.uid()then0",
    ):
        if marker not in migration:
            fail(f"rang projet famille: garde absente: {marker}")

    for marker in (
        "privatenovelaccess='product'|'owner'|'family'",
        "sinjira_has_full_catalog_access",
        "if(fullcatalog===true)return'family'",
    ):
        if marker not in shared:
            fail(f"roman privé famille: garde Edge partagée absente: {marker}")

    for marker in (
        "sinjira_my_catalog_access_mode",
        "constfamilycatalog=catalogaccessmode==='family'",
        "source==='entitlement'||source==='product'",
        "sinjira_my_project_catalog",
        "sinjira_my_extension_catalog",
        "data-library-extensions",
        "data-library-extension-count",
        "functionrenderextensions",
        "constsource=string(extension.access_source||'catalogue')",
        "source==='product'",
        "acheté/droitnumérique",
        "constproductright=isowner||familycatalog||fractureright",
        "constfracturerightverified=!fracturerightresult.error,fractureright=fracturerightverified&&fracturerightresult.data===true",
        "s.rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'})",
        "cataloguefamilial·accèsprotégé",
        "touteslescréationssontvisibles,maisseulslescontenusapprouvés11–12anspeuventêtreouverts",
        "rendernovels(juniorresolved?juniornovels:[],[],false,true,familycatalog)",
        "s.rpc('sinjira_my_product_rights')",
        "product.source==='paid_order'?'achatpayé'",
    ):
        if marker not in library:
            fail(f"bibliothèque famille: invariant absent: {marker}")

    for forbidden in ("s.from('orders')","s.from('order_items')","s.from('user_entitlements')"):
        if forbidden in library:
            fail(f"bibliothèque: lecture commerciale directe interdite: {forbidden}")

    for marker in (
        "s.rpc('sinjira_my_product_rights')",
        "row.source==='paid_order'?'achatpayé'",
        "droitnumériquereconnu",
        "sinjira_my_account_capabilities",
        "constchildmode=capabilitiesresolved&&capabilitiesresult.data.library_mode==='reviewed_11_12'",
        "form.hidden=true",
        "licencesprotégéespourlescomptes11–12ans",
    ):
        if marker not in licenses:
            fail(f"licences: droit produit effectif absent: {marker}")
    for forbidden in ("s.from('orders')","s.from('order_items')","s.from('user_entitlements')"):
        if forbidden in licenses:
            fail(f"licences: lecture commerciale directe interdite: {forbidden}")

    if "v24-licenses.js?v=25.1.1" not in contents["licenses_html"]:
        fail("licences: cache V25.1.1 non forcé")

    for marker in (
        "sinjira_my_catalog_access_mode",
        "familycatalog=!catalogaccessresult.error",
        "constfamilyproductaccess=familycatalog&&!childmode",
        "active:owner||familyproductaccess",
        "s.rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'})",
    ):
        if marker not in secondary_library:
            fail(f"bibliothèque secondaire famille: invariant absent: {marker}")

    for marker in (
        "sinjira_my_catalog_access_mode",
        "constisfamily=catalogaccessmode==='family'",
        "consthascreatorcatalog=isowner||isfamily",
        "comptefamillecréateursinjira",
    ):
        if marker not in purchases:
            fail(f"achats famille: invariant absent: {marker}")

    for marker in (
        "sinjira_my_catalog_access_mode",
        "constfamilycatalog=catalogaccessmode==='family'",
        "famillecréateur·intégraleprivée",
        "modefamillecréateur",
    ):
        if marker not in literature:
            fail(f"littérature famille: invariant absent: {marker}")

    for marker in (
        "sinjira_my_catalog_access_mode",
        "dashboardfamily=catalogaccessmode==='family'",
        "sinjira_my_project_catalog",
        "famillecréateursinjira",
        "cataloguefamille·contenuprotégé",
    ):
        if marker not in dashboard:
            fail(f"tableau de bord famille: invariant absent: {marker}")
    if "sinjira-account-dashboard-v24-4-60.js?v=25.0.3" not in contents["account_index"]:
        fail("cache tableau de bord famille non forcé")

    if "sinjira-library-v24-4-61.js?v=25.1.8" not in contents["library_html"]:
        fail("cache bibliothèque famille non forcé")
    if "sinjira-purchases-v25.js?v=25.0.3" not in contents["purchases_html"]:
        fail("cache achats famille non forcé")
    if "sinjira-literature-catalog-v25.js?v=25.1.2" not in contents["literature_html"]:
        fail("cache littérature famille non forcé")

    if "selectplan(90);" not in test:
        fail("pgTAP famille: plan(90) absent")
    if test.count("anditem->>'cover_url'isnull") < 2:
        fail("pgTAP famille: masquage des couvertures 11–12 non prouvé sur projet et roman")
    for marker in (
        "anonnereçoitpaslalignecomplètedunprojetpublicliéàunproduit",
        "anonnevoitpasuneextensionpubliéedontleprojetparentestencorebrouillon",
        "aucuncourrielneststockédansleregistrefamilial",
        "aucunlibellénominatifneststockédansleregistrefamilial",
        "authenticatednepeuttoujourspassonderlabandeâgedunuuidarbitraire",
        "authenticatedconserveuniquementlehelperâgeself-onlyducomptecourant",
        "service_rolepeutassocieruncomptefamilialparcourrielsansconserverlecourriel",
        "unmembrestandardnereçoitpaslecataloguefamilial",
        "unmembrestandardvoitlecontenugratuitinclusavecsoncompte",
        "uncomptefamilialyouth/adultvoituneextensioninterneducataloguecréateur",
        "unmembrestandardnevoitpasuneextensioninternenonpublique",
        "unmembrestandardnevoitpasuneextensionpubliquesileprojetparentestbrouillon",
        "lecomptefamilial11–12nereçoitpasuneextensioninternenonclassée",
        "lecatalogueextensionself-onlydonnelesmétadonnéescomplètesàlafamille13+",
        "lecatalogueextensionself-onlynerévèlepaslextensioninterneaumembrestandard",
        "lecomptefamilial11–12voituneficheextensionminimiséesanscontenuouvrable",
        "lerôlefamilialnecontournepaslarlschild",
        "lafiche11–12nonclasséeestminimiséeetsanscheminouvrable",
        "laficheromanfamiliale11–12nedonnejamaislintégraleprivée",
        "uncomptefamilialyouth/adultsatisfaitledroitproduitsansfauxentitlement",
        "uncomptefamilialnevalidejamaisunslugproduitinexistant",
        "lecataloguefamillenefabriqueaucundroitproduitcommercial",
        "unecommandependingnapparaîtpasdanslesdroitsproduitducompte",
        "lesdeuxproduitsdunecommandepaidapparaissentdanslesdroitseffectifsducompte",
        "lesdroitsissusdunecommandepaidsontidentifiéssansexposerlacommande",
        "lesdroitscommerciauxrestentmasquéscôténavigateurà11–12malgrédesentitlementsréels",
        "unecommandepaidenfantresteundroitcomptableréel",
        "unecommandepaidenfantnerévèlepaslesmétadonnéesduproduità11–12",
        "unentitlementenfantnerévèlepaslesmétadonnéesduproduità11–12",
        "unmembrestandardsansachatnientitlementnesatisfaitpasledroitproduit",
        "test-family-pending-ext-001",
        "unecommandepaidrendleproduitachetévisibleaumembrestandard",
        "unecommandepaidsatisfaitledroitproduitsansentitlementartificiel",
        "unecommandepaidrendleprojetprivéliéauproduitvisibleaumembrestandard",
        "lecatalogueprojetreconnaîtleprojetachetésansentitlementartificiel",
        "unromanprivéachetéparcommandepaiddevientdisponibledanslecataloguesansentitlement",
        "unecommandependingnerendpaslextensionprivéevisibleaumembrestandard",
        "lerpcextensionrefuseuneextensionliéeseulementàunecommandepending",
        "unecommandepaidrendlextensionprivéeachetéevisibleaumembrestandard",
        "lecatalogueextensionreconnaîtunecommandepaidsansentitlementartificiel",
        "lafamilleadult/youthvoitaussiuneextensionproduitencoreenconception",
        "lafamilleadult/youthconservelavisibilitécataloguesuruneextensiondeprojetbrouillon",
        "unachatnerévèlepasuneextensionencoreenconception",
        "unachatpaidnerévèlepasuneextensionpubliéesisonprojetparentrestebrouillon",
        "lecataloguemembremasqueuneextensionachetéedontleprojetparentestbrouillon",
        "lecataloguemembremasqueaussilextensionproduitencoreenconception",
        "uncomptefamilial11–12nesatisfaitpasledroitproduitnonclassé",
        "unaccèsplayerexpliciteresteunrangtechniqueetnedevientpasundroitproduitenfant",
        "uncompte11–12nelitpasunprojetpayantmêmeapprouvéetavecproject_accessplayer",
        "lehelper11–12refuseaussileprojetpayantapprouvéavecaccèsexplicite",
        "uncompte11–12nelitpasledocumentdunprojetpayantmalgréunrangplayer",
        "lehelperdocument11–12refuselecontenupayantmalgrédoubleapprobationetaccèsplayer",
        "undroitproduitréelpeutexistercomptablementpouruncompte11–12",
        "undroitproduitréelnerouvrepaslaligneprojetaucompte11–12",
        "lecataloguefamilialgardeleprojetacheténonouvrableà11–12",
        "undroitproduitréelnerouvrepaslextensionprivéeaucompte11–12",
        "lecataloguefamilialgardelextensionachetéeminimiséeà11–12",
        "ledroitproduitréelnedonnejamaislintégraleduromanaucompte11–12",
        "unachatpaidnerévèlejamaisunprojetencoreenbrouillon",
        "unachatpaidnerévèlepasledocumentapprouvédunprojetencoreenbrouillon",
        "unaccèsplayerexplicitepeutouvrirleprojetbrouillonsansdépendredelachat",
        "unaccèsplayerexpliciteconservelaccèsaudocumentdubrouillon",
        "lesrpcpublicsfamillerestentsecurityinvoker",
        "lesseptimplémentationsprivilégiéesfamillerestenthorsduschémapublic",
    ):
        if marker not in test:
            fail(f"pgTAP famille: preuve absente: {marker}")

    for path in (
        "supabase/migrations/20260922014000_sinjira_v25_creator_family_catalog_access.sql",
        "supabase/tests/creator_family_catalog_access_v25.test.sql",
        "scripts/validate_creator_family_catalog_v25.py",
        "scripts/provision_creator_family_catalog.py",
        "supabase/functions/_shared/privateNovel.ts",
        "supabase/migrations/20260922023000_sinjira_v25_paid_order_product_access.sql",
        "supabase/migrations/20260922030000_sinjira_v25_extension_product_access.sql",
        "supabase/migrations/20260922031500_sinjira_v25_catalog_age_helper_boundary.sql",
        "supabase/migrations/20260922033000_sinjira_v25_project_product_access.sql",
        "assets/js/v24-licenses.js",
        "compte/licences.html",
    ):
        if path not in account_workflow:
            fail(f"CI compte famille: path absent: {path}")
    if "python3 scripts/validate_creator_family_catalog_v25.py --self-test" not in account_workflow:
        fail("CI compte famille: auto-test statique non exécuté")

    if "python3 scripts/provision_creator_family_catalog.py --self-test" not in account_workflow:
        fail("CI compte famille: auto-test provisionnement sécurisé non exécuté")
    if "supabase test db supabase/tests/creator_family_catalog_access_v25.test.sql" not in account_workflow:
        fail("CI compte famille: pgTAP non exécuté")

    if "supabase/migrations/20260922014000_sinjira_v25_creator_family_catalog_access.sql" not in novel_workflow:
        fail("CI romans privés: migration famille non surveillée")
    if "supabase/migrations/20260922023000_sinjira_v25_paid_order_product_access.sql" not in novel_workflow:
        fail("CI romans privés: migration droit paid non surveillée")
    if "supabase/migrations/20260922031500_sinjira_v25_catalog_age_helper_boundary.sql" not in novel_workflow:
        fail("CI romans privés: frontière âge catalogue non surveillée")

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    contents={name:path.read_text(encoding="utf-8") for name,path in FILES.items()}
    validate(contents)
    if args.self_test:
        mutations={
            "courriel gravé dans migration":("migration","commit;","-- contact: person@example.test\ncommit;"),
            "provisionnement ouvert navigateur":("migration","from public,anon,authenticated;\ngrant execute on function public.set_sinjira_catalog_family_access_by_email","from public,anon;\ngrant execute on function public.set_sinjira_catalog_family_access_by_email"),
            "rang famille enfant élevé":("migration","and public.sinjira_age_band(p_user_id) in ('adult','youth') then 90","then 90"),
            "intégrale child ouverte":("migration","private_asset_configured\n          and band in ('adult','youth')","private_asset_configured"),
            "catalogue enfant navigateur ancien":("library","s.rpc('sinjira_my_project_catalog')","s.from('projects').select('*')"),
            "helper famille roman retiré":("shared","sinjira_has_full_catalog_access","is_sinjira_owner"),
            "catalogue famille dashboard retiré":("dashboard","s.rpc(\'sinjira_my_project_catalog\')","Promise.resolve({data:[],error:null})"),
            "droit produit famille retiré":("migration","public.is_sinjira_catalog_family_member(p_user_id)","false"),
            "jeu famille retiré bibliothèque":("library","isOwner||familyCatalog||fractureRight","isOwner||fractureRight"),
            "extension achetée effective ouverte aux comptes child":("age_boundary_migration","and parent_project.status<>'draft'\n  )\n  and public.sinjira_my_age_band() in ('adult','youth')\n  and public.has_sinjira_product","and parent_project.status<>'draft'\n  )\n  and public.sinjira_my_age_band() in ('adult','youth','child')\n  and public.has_sinjira_product"),
            "extension interne vendue avant approbation":("age_boundary_migration","status in ('approved','released')\n  and product_slug is not null","product_slug is not null"),
            "extension publique réexpose parent brouillon":("extension_access_migration","and parent_project.status<>'draft'\n  )\n);","\n  )\n);"),
            "extension achetée effective réexpose parent brouillon":("age_boundary_migration","and parent_project.status<>'draft'\n  )\n  and public.sinjira_my_age_band()","\n  )\n  and public.sinjira_my_age_band()"),
            "rpc extension réexpose parent brouillon":("extension_access_migration","p.status<>'draft'\n        and (","("),
            "rpc extension vendue avant approbation":("extension_access_migration","e.status in ('approved','released')\n          and e.product_slug is not null","e.product_slug is not null"),
            "extension famille effective ouverte aux comptes child":("age_boundary_migration","public.sinjira_has_full_catalog_access((select auth.uid()))\n  and public.sinjira_my_age_band() in ('adult','youth')","public.sinjira_has_full_catalog_access((select auth.uid()))\n  and public.sinjira_my_age_band() in ('adult','youth','child')"),
            "policy catalogue réutilise oracle âge UUID":("age_boundary_migration","public.sinjira_my_age_band() in ('adult','youth')","public.sinjira_age_band((select auth.uid())) in ('adult','youth')"),
            "wrapper droit produit redevient privilégié":("age_boundary_migration","language sql\nstable\nsecurity invoker\nset search_path=''\nas $wrapper$","language sql\nstable\nsecurity definer\nset search_path=''\nas $wrapper$"),
            "projet payant rouvert aux comptes child":("project_access_migration","p.child_access_status='approved_11_12'\n      and p.product_slug is null\n      and (","p.child_access_status='approved_11_12'\n      and ("),
            "droit projet acheté retiré":("project_access_migration","public.has_sinjira_product(product_slug,(select auth.uid()))","true"),
            "projet public payant réexposé sans droit":("project_access_migration","visibility='public'\n      and product_slug is null","visibility='public'"),
            "achat rouvre les brouillons":("project_access_migration","status<>'draft'\n  and product_slug is not null","product_slug is not null"),
            "document acheté rouvre parent brouillon":("project_access_migration","parent_project.status<>'draft'\n          and parent_project.product_slug is not null","parent_project.product_slug is not null"),
            "catalogue projet acheté retiré":("project_access_migration","sinjira_v25_internal.has_sinjira_product(p.product_slug,uid)","false"),
            "extension produit sans droit canonique":("extension_access_migration","public.has_sinjira_product(product_slug,(select auth.uid()))","true"),
            "commande paid assouplie":("paid_access_migration","o.status='paid'","o.status<>'cancelled'"),
            "rpc droits produit accepte un UUID":("paid_access_migration","create or replace function sinjira_v25_internal.sinjira_my_product_rights()","create or replace function sinjira_v25_internal.sinjira_my_product_rights(p_user_id uuid)"),
            "wrapper droits produit redevient definer":("paid_access_migration","create or replace function public.sinjira_my_product_rights()\nreturns jsonb\nlanguage sql\nstable\nsecurity invoker","create or replace function public.sinjira_my_product_rights()\nreturns jsonb\nlanguage sql\nstable\nsecurity definer"),
            "droits produit enfant réexposés":("paid_access_migration","a.band in ('adult','youth')","true"),
            "policy commande produit rouverte enfant":("paid_access_migration","public.sinjira_my_age_band() in ('adult','youth')\n  and exists(","exists("),
            "policy entitlement produit rouverte enfant":("age_boundary_migration","create policy products_entitled_read\non public.products\nfor select\nto authenticated\nusing (\n  public.sinjira_my_age_band() in ('adult','youth')","create policy products_entitled_read\non public.products\nfor select\nto authenticated\nusing (\n  true"),
            "licences enfant sans garde capacités":("licenses","const childMode=capabilitiesResolved&&capabilitiesResult.data.library_mode==='reviewed_11_12';","const childMode=false;"),
            "bibliothèque relit directement les entitlements":("library","s.rpc('sinjira_my_product_rights')","s.from('user_entitlements')"),
            "licences relisent directement les commandes":("licenses","s.rpc('sinjira_my_product_rights')","s.from('orders')"),
            "wrapper famille redevient definer":("migration","security invoker\nset search_path=''\nas $wrapper$","security definer\nset search_path=''\nas $wrapper$"),
        }
        for label,(key,old,new) in mutations.items():
            broken=dict(contents)
            if old not in broken[key]:
                fail(f"auto-test: marqueur source absent pour {label}")
            broken[key]=broken[key].replace(old,new,1)
            try:
                validate(broken)
            except ValueError:
                continue
            fail(f"auto-test: dérive non détectée: {label}")
        print(f"OK auto-test catalogue famille créateur: {len(mutations)}/{len(mutations)} dérives critiques détectées")
        return
    print("OK V25 catalogue famille: UUID privé, provisionnement service_role, visibilité complète standard et catalogue 11–12 minimisé.")

if __name__=="__main__":
    main()
