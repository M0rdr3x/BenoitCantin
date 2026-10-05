#!/usr/bin/env python3
"""Garde V25 de diffusion privée Livre I: intégrité, bucket privé, décision humaine."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20261005150000_sinjira_v25_private_novel_integrity_gate.sql"
TEST = ROOT / "supabase/tests/private_novel_integrity_gate_v25.test.sql"
EDGE = ROOT / "supabase/functions/admin-private-novel-release/index.ts"
CONFIG = ROOT / "supabase/config.toml"
WORKFLOW = ROOT / ".github/workflows/sinjira-private-novel-integrity-gate-v25.yml"
MANIFEST = ROOT / "projets/sinjira/codex/livre-i-source-artifacts-2026-10-04.json"

FULL_SHA = "9acc8f561962850158cb073b122ee038c2731ee3b165deae482260c0cc1ad2d8"
FULL_SIZE = "7325502"
ENABLE_CONFIRMATION = "ACTIVER_LA_DIFFUSION_PRIVEE"


def compact(text: str) -> str:
    return "".join(text.lower().split())


def load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate(migration: str, test: str, edge: str, config: str, workflow: str, manifest: str) -> list[str]:
    errors: list[str] = []
    m = compact(migration)
    t = compact(test)
    e = compact(edge)
    w = compact(workflow)

    for marker in (
        "addcolumnifnotexistssource_sha256text",
        "addcolumnifnotexistssource_size_bytesbigint",
        "addcolumnifnotexistsintegrity_verified_sha256text",
        "addcolumnifnotexistsintegrity_verified_attimestamptz",
        f"source_sha256='{FULL_SHA}'",
        f"source_size_bytes={FULL_SIZE}",
        "source_mime_type='application/pdf'",
        "source_received_on=date'2026-10-05'",
        "createorreplacefunctionpublic.sinjira_private_novel_release_status(p_novel_slugtext)",
        "createorreplacefunctionpublic.sinjira_record_private_novel_integrity(",
        "createorreplacefunctionpublic.sinjira_set_private_novel_delivery(",
        "coalesce(auth.jwt()->>'role','')<>'service_role'",
        "storage.buckets",
        "storage.objects",
        "b.publicisfalse",
        "object_size=item.source_size_bytes",
        "object_mime=item.source_mime_type",
        "item.integrity_verified_sha256=item.source_sha256",
        "raiseexception'novel_private_release_not_ready'",
        "setenabled=true",
        "setenabled=false",
        "revokeallonfunctionpublic.sinjira_private_novel_release_status(text)",
    ):
        if marker not in m:
            errors.append(f"Migration intégrité: marqueur absent: {marker}")

    pre_functions = m[: m.find("createorreplacefunctionpublic.sinjira_private_novel_release_status")]
    for forbidden in ("storage_bucket=", "storage_path=", "delivery_mode='storage'", "enabled=true", "insertintostorage.objects"):
        if forbidden in pre_functions:
            errors.append(f"Migration intégrité: auto-déploiement interdit: {forbidden}")

    for signature in (
        "public.sinjira_private_novel_release_status(text)",
        "public.sinjira_record_private_novel_integrity(text,text,bigint)",
        "public.sinjira_set_private_novel_delivery(text,boolean)",
    ):
        expected = f"not has_function_privilege('authenticated','{signature.lower()}','execute')"
        if expected not in t:
            errors.append(f"pgTAP: frontière authenticated absente pour {signature}.")

    for marker in (
        "selectplan(13);",
        FULL_SHA,
        FULL_SIZE,
        "'sinjira-private-novels-test'",
        "'application/pdf'",
        "not(public.sinjira_private_novel_release_status('la-cendre-du-jugement')->>'can_enable')::boolean",
        "public.sinjira_record_private_novel_integrity(",
        "public.sinjira_set_private_novel_delivery(",
        "setpublic=true",
    ):
        if compact(marker) not in t:
            errors.append(f"pgTAP intégrité: preuve absente: {marker}")

    for marker in (
        "requiredadmin(req)",
        "max_request_bytes=4096",
        "req.body.getreader()",
        "reader.cancel('request_too_large')",
        "newtextdecoder('utf-8',{fatal:true})",
        "['status','record_integrity','enable','disable']",
        "service.rpc('sinjira_private_novel_release_status'",
        "service.rpc('sinjira_record_private_novel_integrity'",
        "service.rpc('sinjira_set_private_novel_delivery'",
        f"enable_confirmation='{ENABLE_CONFIRMATION.lower()}'",
        "if(!before?.can_enable)thrownewerror('novel_private_release_not_ready')",
        "if(string(before?.expected_sha256||'').tolowercase()!==sha256)",
        "cache-control':'private,no-store,max-age=0",
    ):
        if marker not in e:
            errors.append(f"Edge release privée: garde absente: {marker}")

    if "awaitreq.json()" in e or "awaitreq.text()" in e:
        errors.append("Edge release privée: lecture corps non bornée interdite.")
    if "[functions.admin-private-novel-release]\nverify_jwt = true" not in config:
        errors.append("Config: admin-private-novel-release doit exiger JWT.")

    for path_marker in (
        "20261005150000_sinjira_v25_private_novel_integrity_gate.sql",
        "private_novel_integrity_gate_v25.test.sql",
        "admin-private-novel-release/**",
        "validate_private_novel_integrity_gate_v25.py",
        "supabase/config.toml",
    ):
        if path_marker.lower() not in w:
            errors.append(f"Workflow intégrité: path manquant: {path_marker}")

    if "supabase db reset" not in workflow or "supabase test db supabase/tests/private_novel_integrity_gate_v25.test.sql" not in workflow:
        errors.append("Workflow intégrité: reconstruction/test SQL local manquant.")

    if FULL_SHA not in manifest or '"public_repository_allowed": false' not in manifest:
        errors.append("Manifeste Livre I: intégrale privée attendue absente.")
    if '"production_deployment_authorized": false' not in manifest:
        errors.append("Manifeste Livre I: autorisation production doit rester false.")

    return errors


def self_test(contents: dict[str, str]) -> None:
    clean = validate(**contents)
    if clean:
        raise AssertionError("Le cas sain doit passer: " + " | ".join(clean))

    mutations = {
        "activation automatique": ("migration", "    updated_at=now()", "    enabled=true,\n    updated_at=now()"),
        "bucket forcé par migration": ("migration", "    total_pages=1027,", "    storage_bucket='public-books',\n    total_pages=1027,"),
        "service role retiré": ("migration", "coalesce(auth.jwt()->>'role','') <> 'service_role'", "false"),
        "confirmation humaine retirée": ("edge", "if(confirmation!==ENABLE_CONFIRMATION)throw new Error('ENABLE_CONFIRMATION_REQUIRED');", ""),
        "JWT désactivé": ("config", "[functions.admin-private-novel-release]\nverify_jwt = true", "[functions.admin-private-novel-release]\nverify_jwt = false"),
        "test bucket public retiré": ("test", "set public=true", "set public=false"),
    }
    for label, (key, old, new) in mutations.items():
        broken = dict(contents)
        if old not in broken[key]:
            raise AssertionError(f"Auto-test: marqueur absent pour {label}")
        broken[key] = broken[key].replace(old, new, 1)
        if not validate(**broken):
            raise AssertionError(f"Auto-test: dérive non détectée: {label}")

    print(f"OK auto-test release privée: {len(mutations)}/{len(mutations)} dérives critiques détectées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    contents = {
        "migration": load(MIGRATION),
        "test": load(TEST),
        "edge": load(EDGE),
        "config": load(CONFIG),
        "workflow": load(WORKFLOW),
        "manifest": load(MANIFEST),
    }
    if args.self_test:
        self_test(contents)
        return 0
    errors = validate(**contents)
    if errors:
        print(f"ÉCHEC release privée Livre I: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1
    print("OK release privée Livre I: intégrité externe, bucket privé, objet conforme et activation humaine fail-closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
