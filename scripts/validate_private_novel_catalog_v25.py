#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

FILES={
    "migration":ROOT/"supabase/migrations/20260919093000_sinjira_v25_private_novel_catalog.sql",
    "catalog_seed":ROOT/"supabase/migrations/20260919103000_sinjira_v25_livre_i_catalog_seed.sql",
    "rls":ROOT/"supabase/migrations/20260919113000_sinjira_v25_private_novel_asset_rls.sql",
    "shared":ROOT/"supabase/functions/_shared/privateNovel.ts",
    "edge":ROOT/"supabase/functions/get-private-novel-url/index.ts",
    "reader_js":ROOT/"assets/js/sinjira-private-book-reader.js",
    "reader_html":ROOT/"projets/sinjira/romans/lire-integral.html",
    "library_js":ROOT/"assets/js/sinjira-library-v24-4-61.js",
    "library_html":ROOT/"compte/bibliotheque.html",
    "literature_js":ROOT/"assets/js/sinjira-literature-catalog-v25.js",
    "literature_html":ROOT/"projets/sinjira/romans/index.html",
    "test":ROOT/"supabase/tests/private_novel_catalog_v25.test.sql",
    "workflow":ROOT/".github/workflows/sinjira-private-novel-catalog-v25.yml",
    "config":ROOT/"supabase/config.toml",
}

def fail(message:str)->None:
    raise ValueError(message)

def compact(value:str)->str:
    return "".join(value.lower().split())

def validate(contents:dict[str,str])->None:
    m=compact(contents["migration"])
    seed=compact(contents["catalog_seed"])
    rls=compact(contents["rls"])
    shared=compact(contents["shared"])
    edge=compact(contents["edge"])
    reader=compact(contents["reader_js"])
    reader_html=compact(contents["reader_html"])
    library=compact(contents["library_js"])
    library_html=compact(contents["library_html"])
    literature=compact(contents["literature_js"])
    literature_html=compact(contents["literature_html"])
    test=compact(contents["test"])
    workflow=compact(contents["workflow"])
    config=contents["config"]

    for marker in (
        "createtableifnotexistsprivate.sinjira_private_novel_assets",
        "createorreplacefunctionpublic.sinjira_my_novel_catalog()",
        "createorreplacefunctionpublic.sinjira_private_novel_asset_for_delivery(p_novel_slugtext)",
        "service_role_required",
        "altertableprivate.sinjira_private_novel_assetsenablerowlevelsecurity",
        "revokeallontableprivate.sinjira_private_novel_assetsfrompublic,anon,authenticated",
        "selectpublic.is_sinjira_owner(uid)intoowner_mode",
        "'full_access',private_asset_configuredand(owner_modeorentitled)",
        "'access_source',case",
        "1066,falsefrompublic.sinjira_novels",
    ):
        if marker not in m:
            fail(f"catalogue privé: garde SQL absente: {marker}")

    for marker in (
        "insertintopublic.sinjira_novels",
        "'la-cendre-du-jugement'",
        "'published'",
        "onconflict(slug)doupdate",
        "insertintoprivate.sinjira_private_novel_assets",
        "'legacy_env'",
        "1066",
        "enabled=false",
        "onconflict(novel_id)doupdate",
    ):
        if marker not in seed:
            fail(f"seed Livre I: garde absente: {marker}")

    for marker in (
        "altertableprivate.sinjira_private_novel_assetsenablerowlevelsecurity",
        "revokeallontableprivate.sinjira_private_novel_assetsfrompublic,anon,authenticated",
        "grantselect,insert,update,deleteontableprivate.sinjira_private_novel_assetstoservice_role",
    ):
        if marker not in rls:
            fail(f"RLS roman privé: garde absente: {marker}")

    self_section=m[m.find("createorreplacefunctionpublic.sinjira_my_novel_catalog()"):m.find("createorreplacefunctionpublic.sinjira_private_novel_asset_for_delivery")]
    if "'storage_bucket'" in self_section or "'storage_path'" in self_section:
        fail("catalogue self-only: un chemin de stockage privé est retourné")

    for marker in (
        "sinjira_private_novel_asset_for_delivery",
        "is_sinjira_owner",
        "user_entitlements",
        "legacy_env",
        "sinjira_livre_i_private_bucket",
    ):
        if marker not in shared:
            fail(f"helper privé roman: élément absent: {marker}")

    for marker in (
        "requireduser(req)",
        "max_request_bytes=2048",
        r"if(!/^\d+$/.test(normalizedlength))",
        "constbody=awaitreadboundedjson(req)",
        "req.body.getreader()",
        "reader.cancel",
        "newtextdecoder('utf-8',{fatal:true})",
        "json_required",
        "request_too_large",
        "invalid_json",
        "sinjira_age_band",
        "requireprivatenovelaccess",
        "resolveprivatenovelstorage",
        "createsignedurl",
        "novel_slug",
        "cache-control':'private,no-store,max-age=0",
    ):
        if marker not in edge:
            fail(f"Edge roman privé: garde absente: {marker}")
    if "awaitreq.json()" in edge:
        fail("Edge roman privé: lecture JSON directe non bornée interdite")

    if "get-private-novel-url" not in reader:
        fail("lecteur intégral: fonction générique absente")
    if "params.get('novel')" not in reader:
        fail("lecteur intégral: slug dynamique absent")
    if "novel_slug:novelslug" not in reader or "invokedelivery('download')" not in reader:
        fail("lecteur intégral: contrat de livraison générique absent")
    if "data-private-reader-title" not in reader_html or "data-private-reader-meta" not in reader_html:
        fail("lecteur intégral: métadonnées dynamiques absentes")

    if "sinjira_my_novel_catalog" not in library:
        fail("bibliothèque: RPC roman self-only absent")
    if "cataloguecomplet" not in library or "manuscritintégralprivénonchargé" not in library:
        fail("bibliothèque: état créateur honnête absent")
    if "constfullaccess=boolean(novel.full_access);" not in library or "fullaccess?" not in library:
        fail("bibliothèque: accès intégral non lié au full_access canonique")
    for forbidden in (
        "get-private-novel-url",
        "functions.invoke(",
        "data-private-book-download",
        "functiondownloadprivatebook",
        "functionbookactions",
        "accèsauteur",
    ):
        if forbidden in library:
            fail(f"bibliothèque: livraison privée directe ou rôle dupliqué interdit: {forbidden}")
    if "sinjira-library-v24-4-61.js?v=25.1.2" not in library_html:
        fail("bibliothèque: cache générique roman non forcé")

    if "sinjira_my_novel_catalog" not in literature:
        fail("Littérature: RPC roman self-only absent")
    if "from('sinjira_novels')" not in contents["literature_js"]:
        fail("Littérature: fallback public anonyme absent")
    if "?novel=" not in contents["literature_js"] or "encodeURIComponent(novel.slug)" not in contents["literature_js"]:
        fail("Littérature: lecteur intégral générique non lié")
    if "sinjira-literature-catalog-v25.js?v=25.1.2" not in literature_html:
        fail("Littérature: cache catalogue générique non forcé")

    if "supabase/migrations/20260919113000_sinjira_v25_private_novel_asset_rls.sql" not in contents["workflow"]:
        fail("workflow romans privés: migration RLS 20260919113000 non surveillée")

    if "supabase/config.toml" not in contents["workflow"]:
        fail("workflow romans privés: config.toml non surveillé")
    if "[functions.get-private-novel-url]\nverify_jwt = true" not in config:
        fail("config romans privés: get-private-novel-url doit garder verify_jwt=true")

    if "selectplan(13);" not in test:
        fail("pgTAP roman privé: plan(13) absent")
    for marker in (
        "rlsestactivéesurleregistreprivédesactifsromans",
        "unmembrenevoitpaslebrouilloncréateur",
        "unentitlementdonneaccèsintégralauromanprivéconfiguré",
        "lecataloguenavigateurnerévèleaucunchemindestockageprivé",
        "insertintopublic.internal_admin_users(user_id,role)",
        "'kingtyrano@gmail.com'",
        "'owner'",
        "lecréateurvoitlebrouillonetsonintégraleprivéeconfigurée",
        "uncomptenonvérifiénereçoitaucuncatalogueromanprivé",
        "lelivreiresteenregistrémaisdésactivétantquelestockageprivénestpasconfiguré",
    ):
        if marker not in test:
            fail(f"pgTAP roman privé: preuve absente: {marker}")

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    contents={name:path.read_text(encoding="utf-8") for name,path in FILES.items()}
    validate(contents)
    if args.self_test:
        mutations={
            "catalogue non self-only":("library_js","sinjira_my_novel_catalog","sinjira_novels"),
            "full_access bibliothèque contourné":("library_js","const fullAccess=Boolean(novel.full_access);","const fullAccess=true;"),
            "livraison privée réintroduite dans bibliothèque":("library_js","const fullAccess=Boolean(novel.full_access);","const fullAccess=Boolean(novel.full_access); functions.invoke('get-private-novel-url');"),
            "JSON Edge non borné":("edge","const body=await readBoundedJson(req);","const body=await req.json();"),
            "regex Content-Length doublement échappée":("edge",r"if(!/^\d+$/.test(normalizedLength))",r"if(!/^\\d+$/.test(normalizedLength))"),
            "migration RLS hors paths CI":("workflow","supabase/migrations/20260919113000_sinjira_v25_private_novel_asset_rls.sql","supabase/migrations/rls-missing.sql"),
            "config JWT hors paths CI":("workflow","supabase/config.toml","supabase/config-missing.toml"),
            "JWT Edge désactivé":("config","[functions.get-private-novel-url]\nverify_jwt = true","[functions.get-private-novel-url]\nverify_jwt = false"),
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
        print(f"OK auto-test romans privés: {len(mutations)}/{len(mutations)} dérives critiques détectées")
        return
    print("OK V25 romans privés: catalogue self-only, créateur générique, corps Edge borné et livraison signée validés.")

if __name__=="__main__":
    main()
