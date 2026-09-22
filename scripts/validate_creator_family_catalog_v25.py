#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

FILES={
    "migration":ROOT/"supabase/migrations/20260922014000_sinjira_v25_creator_family_catalog_access.sql",
    "paid_access_migration":ROOT/"supabase/migrations/20260922023000_sinjira_v25_paid_order_product_access.sql",
    "shared":ROOT/"supabase/functions/_shared/privateNovel.ts",
    "library":ROOT/"assets/js/sinjira-library-v24-4-61.js",
    "secondary_library":ROOT/"assets/js/sinjira-library.js",
    "purchases":ROOT/"assets/js/sinjira-purchases-v25.js",
    "literature":ROOT/"assets/js/sinjira-literature-catalog-v25.js",
    "library_html":ROOT/"compte/bibliotheque.html",
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
    shared=compact(contents["shared"])
    library=compact(contents["library"])
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
        "o.status='paid'",
        "createorreplacefunctionpublic.has_sinjira_product(",
        "frompublic.orderso",
        "joinpublic.order_itemsoionoi.order_id=o.id",
        "o.status='paid'",
        "p.slug=p_product_slug",
        "p_user_idisdistinctfromauth.uid()thenfalse",
    ):
        if paid_marker not in paid_access_migration:
            fail(f"droit produit payé: invariant absent: {paid_marker}")
    if "o.status<>'cancelled'" in paid_access_migration or "o.status!='cancelled'" in paid_access_migration:
        fail("droit produit payé: une commande non annulée ne suffit pas; le statut paid doit être explicite")

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
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_novel_catalog()",
        "createorreplacefunctionpublic.sinjira_my_novel_catalog()",
        "full_catalog_mode:=owner_modeorfamily_mode",
        "ifband='child'andnotfull_catalog_modethen",
        "private_asset_configuredandbandin('adult','youth')and(full_catalog_modeorentitled)",
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
        "constproductright=isowner||familycatalog||fractureright",
        "constfracturerightverified=!fracturerightresult.error,fractureright=fracturerightverified&&fracturerightresult.data===true",
        "s.rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'})",
        "cataloguefamilial·accèsprotégé",
        "touteslescréationssontvisibles,maisseulslescontenusapprouvés11–12anspeuventêtreouverts",
        "rendernovels(juniorresolved?juniornovels:[],[],false,true,familycatalog)",
    ):
        if marker not in library:
            fail(f"bibliothèque famille: invariant absent: {marker}")

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

    if "sinjira-library-v24-4-61.js?v=25.1.4" not in contents["library_html"]:
        fail("cache bibliothèque famille non forcé")
    if "sinjira-purchases-v25.js?v=25.0.3" not in contents["purchases_html"]:
        fail("cache achats famille non forcé")
    if "sinjira-literature-catalog-v25.js?v=25.1.2" not in contents["literature_html"]:
        fail("cache littérature famille non forcé")

    if "selectplan(47);" not in test:
        fail("pgTAP famille: plan(47) absent")
    if test.count("anditem->>'cover_url'isnull") < 2:
        fail("pgTAP famille: masquage des couvertures 11–12 non prouvé sur projet et roman")
    for marker in (
        "aucuncourrielneststockédansleregistrefamilial",
        "aucunlibellénominatifneststockédansleregistrefamilial",
        "service_rolepeutassocieruncomptefamilialparcourrielsansconserverlecourriel",
        "unmembrestandardnereçoitpaslecataloguefamilial",
        "unmembrestandardvoitlecontenugratuitinclusavecsoncompte",
        "uncomptefamilialyouth/adultvoituneextensioninterneducataloguecréateur",
        "unmembrestandardnevoitpasuneextensioninternenonpublique",
        "lecomptefamilial11–12nereçoitpasuneextensioninternenonclassée",
        "lerôlefamilialnecontournepaslarlschild",
        "lafiche11–12nonclasséeestminimiséeetsanscheminouvrable",
        "laficheromanfamiliale11–12nedonnejamaislintégraleprivée",
        "uncomptefamilialyouth/adultsatisfaitledroitproduitsansfauxentitlement",
        "uncomptefamilialnevalidejamaisunslugproduitinexistant",
        "unmembrestandardsansachatnientitlementnesatisfaitpasledroitproduit",
        "unecommandepaidrendleproduitachetévisibleaumembrestandard",
        "unecommandepaidsatisfaitledroitproduitsansentitlementartificiel",
        "unromanprivéachetéparcommandepaiddevientdisponibledanslecataloguesansentitlement",
        "uncomptefamilial11–12nesatisfaitpasledroitproduitnonclassé",
        "lesrpcpublicsfamillerestentsecurityinvoker",
        "lessiximplémentationsprivilégiéesfamillerestenthorsduschémapublic",
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
