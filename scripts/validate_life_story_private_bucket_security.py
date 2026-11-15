#!/usr/bin/env python3
"""Contrat de sécurité négatif : bucket Histoire de vie privé obligatoire.

Pas de secrets Supabase, de données personnelles ni d'accès de production.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "supabase/functions/life-story-export/index.ts"
DELIVERY = ROOT / "supabase/functions/life-story-delivery/index.ts"
GUARD = ROOT / "supabase/functions/_shared/private-life-story-bucket.mjs"
HELPER = "await hasVerifiedPrivateLifeStoryBucket(service.storage)"

def validate(export: str, delivery: str, guard: str) -> list[str]:
    problems: list[str] = []
    if export.count(HELPER) != 2:
        problems.append("Export : vérifier bucket privé avant génération ET liens.")
    if delivery.count(HELPER) != 1:
        problems.append("Remise : vérifier bucket privé avant lecture PDF.")
    if "hasVerifiedPrivateLifeStoryBucket" not in export or "hasVerifiedPrivateLifeStoryBucket" not in delivery:
        problems.append("Import du garde de confidentialité absent.")

    generate = export.find("if (action === 'generate') {")
    link = export.find("if (action === 'create_delivery_links') {")
    revoke = export.find("if (action === 'revoke') {")
    purge = export.find("if (action === 'purge') {")
    gen_guard = export.find(HELPER, generate)
    links_guard = export.find(HELPER, link)
    upload = export.find("service.storage.from(BUCKET).upload(", generate)
    token_create = export.find("crypto.getRandomValues(new Uint8Array(32))", link)
    rpc = export.find("service.rpc('service_life_story_rotate_delivery_links'", link)
    rpc_error = export.find("if (rotationError || !rotation || rotation.link_count !== tokenHashes.length", link)
    if not (0 <= generate < gen_guard < upload < link < links_guard < token_create < rpc < rpc_error < revoke < purge):
        problems.append("Génération et délivrance : RPC atomique après preuve privée obligatoire.")
    if "p_export_id: exportId, p_token_hashes: tokenHashes" not in export:
        problems.append("La rotation doit transmettre seulement les empreintes à SQL.")
    if "from('life_story_delivery_links').delete()" in export or "from('life_story_delivery_links').insert(" in export:
        problems.append("Ancienne rotation en deux requêtes interdite.")
    if not (0 <= export.find("await requiredAdmin(req)") < gen_guard):
        problems.append("Le contrôle administrateur doit précéder Storage.")
    # Révoquer les liens ou purger le contenu doit rester possible lors d'un incident Storage.
    if not (links_guard < revoke < purge) or export.count(HELPER) != 2:
        problems.append("La révocation/purge ne doit pas dépendre du bucket.")

    tok=delivery.find(".eq('token_hash', hash)")
    doc=delivery.find("record.storage_bucket !== 'sinjira-life-story-exports'")
    check=delivery.find(HELPER)
    read=delivery.find("await readPrivateLifeStoryPdf(")
    counter=delivery.find("service.rpc('service_life_story_register_download'")
    if not (0 <= tok < doc < check < read < counter):
        problems.append("Remise : jeton, document, bucket privé, PDF borné, quota dans cet ordre.")
    if "if (!(await hasVerifiedPrivateLifeStoryBucket(service.storage))) return errorResponse(req, 410);" not in delivery:
        problems.append("Remise : fail closed en HTTP 410 sans PDF.")

    required_guard = [
        "LIFE_STORY_PRIVATE_BUCKET = 'sinjira-life-story-exports'",
        "metadata.id === LIFE_STORY_PRIVATE_BUCKET",
        "metadata.public === false",
        "typeof storage.getBucket !== 'function'",
        "await storage.getBucket(LIFE_STORY_PRIVATE_BUCKET)",
        "return !error && isVerifiedPrivateLifeStoryBucket(data);",
        "} catch {",
        "return false;",
    ]
    for marker in required_guard:
        if marker not in guard:
            problems.append("Contrôle Storage manquant : " + marker)
    for text in (export, delivery, guard):
        if "getPublicUrl(" in text or "console.error(bucketMetadataError)" in text:
            problems.append("Repli public ou diagnostic brut interdit.")
    return problems

def self_test(export: str, delivery: str, guard: str) -> None:
    if errors := validate(export, delivery, guard):
        raise AssertionError("Source saine refusée : " + "; ".join(errors))
    cases = [
        ("génération non protégée", export.replace(HELPER, "true", 1), delivery, guard),
        ("remise non protégée", export, delivery.replace(HELPER, "true", 1), guard),
        ("bucket public accepté", export, delivery, guard.replace("metadata.public === false", "metadata.public !== undefined", 1)),
        ("mauvais identifiant de bucket accepté", export, delivery, guard.replace("metadata.id === LIFE_STORY_PRIVATE_BUCKET", "true", 1)),
        ("métadonnées Storage non interrogées", export, delivery, guard.replace("await storage.getBucket(LIFE_STORY_PRIVATE_BUCKET)", "Promise.resolve({data:{id:LIFE_STORY_PRIVATE_BUCKET,public:false}})", 1)),
        ("erreur bucket ignorée", export, delivery, guard.replace("return !error && isVerifiedPrivateLifeStoryBucket(data);", "return isVerifiedPrivateLifeStoryBucket(data);", 1)),
        ("durée/lecture PDF non imposée", export, delivery.replace("await readPrivateLifeStoryPdf(", "await Promise.resolve(", 1), guard),
        ("quota avant lecture", export, delivery.replace("service.rpc('service_life_story_register_download'", "service.rpc('ignore_count'", 1), guard),
        ("appel RPC retiré", export.replace("service.rpc('service_life_story_rotate_delivery_links'", "service.rpc('unsafe_rotate'", 1), delivery, guard),
        ("mutation des autorisations admin", export.replace("await requiredAdmin(req)", "await Promise.resolve({service})", 1), delivery, guard),
        ("erreur RPC ignorée", export.replace("if (rotationError || !rotation || rotation.link_count !== tokenHashes.length", "if (false && rotation.link_count !== tokenHashes.length", 1), delivery, guard),
        ("hashes RPC omis", export.replace("p_export_id: exportId, p_token_hashes: tokenHashes", "p_export_id: exportId, p_token_hashes: []", 1), delivery, guard),
    ]
    for label, bad_export, bad_delivery, bad_guard in cases:
        if bad_export == export and bad_delivery == delivery and bad_guard == guard:
            raise AssertionError("Mutation impossible : " + label)
        if not validate(bad_export, bad_delivery, bad_guard):
            raise AssertionError("Mutant non détecté : " + label)
    print(f"OK : {len(cases)} mutations de sécurité de PDF personnels rejetées")

def main() -> int:
    args=argparse.ArgumentParser()
    args.add_argument("--self-test", action="store_true")
    options=args.parse_args()
    sources=(EXPORT.read_text("utf-8"),DELIVERY.read_text("utf-8"),GUARD.read_text("utf-8"))
    if options.self_test:
        self_test(*sources)
    errors=validate(*sources)
    if errors:
        print("\n".join("ECHEC : "+message for message in errors))
        return 1
    print("OK : génération, jetons et PDF personnels conditionnés par Storage privé vérifié")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
