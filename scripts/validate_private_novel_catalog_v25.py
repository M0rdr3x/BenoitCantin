#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

FILES={
    "migration":ROOT/"supabase/migrations/20260919093000_sinjira_v25_private_novel_catalog.sql",
    "catalog_seed":ROOT/"supabase/migrations/20260919103000_sinjira_v25_livre_i_catalog_seed.sql",
    "shared":ROOT/"supabase/functions/_shared/privateNovel.ts",
    "edge":ROOT/"supabase/functions/get-private-novel-url/index.ts",
    "reader_js":ROOT/"assets/js/sinjira-private-book-reader.js",
    "reader_html":ROOT/"projets/sinjira/romans/lire-integral.html",
    "library_js":ROOT/"assets/js/sinjira-library-v24-4-61.js",
    "library_html":ROOT/"compte/bibliotheque.html",
    "literature_js":ROOT/"assets/js/sinjira-literature-catalog-v25.js",
    "literature_html":ROOT/"projets/sinjira/romans/index.html",
    "test":ROOT/"supabase/tests/private_novel_catalog_v25.test.sql",
}

def fail(message:str)->None:
    raise ValueError(message)

def compact(value:str)->str:
    return "".join(value.lower().split())

def validate(contents:dict[str,str])->None:
    m=compact(contents["migration"])
    seed=compact(contents["catalog_seed"])
    shared=compact(contents["shared"])
    edge=compact(contents["edge"])
    reader=compact(contents["reader_js"])
    reader_html=compact(contents["reader_html"])
    library=compact(contents["library_js"])
    library_html=compact(contents["library_html"])
    literature=compact(contents["literature_js"])
    literature_html=compact(contents["literature_html"])
    test=compact(contents["test"])

    for marker in (
        "createtableifnotexistsprivate.sinjira_private_novel_assets",
        "createorreplacefunctionpublic.sinjira_my_novel_catalog()",
        "createorreplacefunctionpublic.sinjira_private_novel_asset_for_delivery(p_novel_slugtext)",
        "service_role_required",
        "revokeallontableprivate.sinjira_private_novel_assetsfrompublic,anon,authenticated",
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
        "sinjira_age_band",
        "requireprivatenovelaccess",
        "resolveprivatenovelstorage",
        "createsignedurl",
        "novel_slug",
        "cache-control':'private,no-store,max-age=0",
    ):
        if marker not in edge:
            fail(f"Edge roman privé: garde absente: {marker}")

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
    if "get-private-novel-url" not in library:
        fail("bibliothèque: livraison générique absente")
    if "sinjira-library-v24-4-61.js?v=25.1.0" not in library_html:
        fail("bibliothèque: cache générique roman non forcé")

    if "sinjira_my_novel_catalog" not in literature:
        fail("Littérature: RPC roman self-only absent")
    if "from('sinjira_novels')" not in contents["literature_js"]:
        fail("Littérature: fallback public anonyme absent")
    if "?novel=" not in contents["literature_js"] or "encodeURIComponent(novel.slug)" not in contents["literature_js"]:
        fail("Littérature: lecteur intégral générique non lié")
    if "sinjira-literature-catalog-v25.js?v=25.1.0" not in literature_html:
        fail("Littérature: cache catalogue générique non forcé")

    if "selectplan(12);" not in test:
        fail("pgTAP roman privé: plan(12) absent")
    for marker in (
        "unmembrenevoitpaslebrouilloncréateur",
        "unentitlementdonneaccèsintégralauromanprivéconfiguré",
        "lecataloguenavigateurnerévèleaucunchemindestockageprivé",
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
        broken=dict(contents)
        broken["library_js"]=broken["library_js"].replace("sinjira_my_novel_catalog","sinjira_novels",1)
        try:
            validate(broken)
        except ValueError:
            print("OK auto-test: retour à un catalogue non self-only détecté")
            return
        fail("auto-test: dérive catalogue non détectée")
    print("OK V25 romans privés: catalogue self-only, créateur générique et livraison signée validés.")

if __name__=="__main__":
    main()
