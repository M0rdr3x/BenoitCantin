#!/usr/bin/env python3
"""Garde non mutant du snapshot de revue release V25 enfant/Junior."""

from __future__ import annotations

import argparse
import copy
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase/migrations"
REVIEWED = ROOT / "supabase/production-reviewed-migration-batch.txt"
LEDGER = ROOT / "supabase/production-migration-ledger.txt"
DOSSIER = ROOT / "docs/SINJIRA_V25_CHILD_JUNIOR_RELEASE_REVIEW_2026-09-18.md"

EXPECTED_REVIEWED_BLOB = "2392a7b9f2ce06952555446771933b05d6d47387"
EXPECTED_LEDGER_BLOB = "0eb7b0d886e9f24d5592b7014ed4d92d28fded63"
EXPECTED_NON_REVIEWED = {
    "20260913030500_sinjira_v25_travel_mode_geo_scope_hardening.sql": "7285d1e30ea288004d17c1dbfbf9f01662b36bb7",
    "20260913230000_sinjira_v25_travel_mode_retention_purge.sql": "41b8dc3d1b1e09c018e588755edb053e63e9904a",
    "20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql": "2d7b8ccbfc79fed6a03208086a138618779d6e2d",
    "20260916210000_sinjira_v25_child_guardian_signup.sql": "51544dee4322d809a8116fb5614962de78691b31",
    "20260917223000_sinjira_v25_junior_community.sql": "64e66dc8d9c45de9ecbb1174fdb842e4444b9b6b",
    "20260918010000_sinjira_v25_child_sensitive_boundary.sql": "d526702c0c32bda7628a37134b9f64e9c66d6351",
    "20260918013000_sinjira_v25_child_content_rating.sql": "b0a2bfda90579830083d128035ee533d06dd2159",
    "20260918020000_sinjira_v25_account_capabilities.sql": "0a16bfcc49e51ee2b96cb98742442ae3d00e5c76",
    "20260918023000_sinjira_v25_minor_content_policy_compat.sql": "c0556e3baa218f9529f185010455984a0bc1cd03",
    "20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql": "efa9d6a29c4decfe0180e9262827022ff752f670",
    "20260919013000_sinjira_v25_child_pending_guardian_redeem.sql": "faaccf3cce0bf725d0f42a5cbecaecbba4b89aa2",
    "20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql": "e14c41364246929054282bccb0e4abc5641b8643",
    "20260919023000_sinjira_v25_guardian_invite_aal2.sql": "5700bfaa2b5a95d84d37ad475524960bdb78fc9b",
    "20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql": "f08102d4bc2485bc229e21076f361bf31552c928",
    "20260919033000_sinjira_v25_guardian_invite_read_aal2.sql": "b2439fbad69798db42c17a04887dff50d9f184cc",
    "20260919040000_sinjira_v25_junior_enable_aal2.sql": "df5475777abd5bb8fff26510a727d3d04cffce53",
    "20260919043000_sinjira_v25_guardian_revoke_aal2.sql": "7dada317202bdd1add1d4dc5113e3aca682459e4",
    "20260919050000_sinjira_v25_guardian_majority_visibility.sql": "d7a65f65e1a870620809f1a2e669ef031d6f6d8a",
    "20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql": "ac18154c958b707d94ddc557b1af6b2af01ba62f",
    "20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql": "d2ef613bfb372efe620e413d5e059b4d1b1e6c64",
    "20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql": "2d91c64a90f5c8bca506577ef359078fdf558fad",
    "20260919070000_sinjira_v25_guardian_contacts_minimization.sql": "e684227b322aa88dbd43376d8bd9aa19a6161f6e",
    "20260919073000_sinjira_v25_junior_guardian_summary_aal2.sql": "07b1ea063e57d3dd4a31e689fac6f44fd1ca6d18",
    "20260919080000_sinjira_v25_guardian_character_identity_isolation.sql": "7c169564095bb440bde8a2a106c4e00aa2f307e4",
    "20260919083000_sinjira_v25_guardian_junior_alias_privacy.sql": "8e0fd367bd0c30ed77f947ae0583408b370121a1",
    "20260919090000_sinjira_v25_account_content_hub.sql": "29358d27f8f505897b924062e208b8d5c740f8c5",
    "20260919093000_sinjira_v25_private_novel_catalog.sql": "7ca3cf47f5f67205cb2a36310513273faacb7dea",
    "20260919100000_sinjira_v25_private_profile_age_11.sql": "db4d0c04f4fba2a6044e12b28d882382ed077086",
    "20260919103000_sinjira_v25_livre_i_catalog_seed.sql": "04929202946a0cda629c1f8005dbf51e4bfb2d68",
    "20260919110000_sinjira_v25_social_public_pseudo_privacy.sql": "ac4f11e8e1591c35f0be91f541a21763fdb3ec8d",
    "20260919113000_sinjira_v25_private_novel_asset_rls.sql": "745ae12098e538415dde16bac198d05610b99954",
    "20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql": "5ed558a9426173fdb714479d28f170ada542803b",
    "20260919123000_sinjira_v25_public_rpc_boundary.sql": "61377e409f769ed94646791acaf8f3c1f86328d0",
    "20260919130000_sinjira_v25_account_catalog_browser_privileges.sql": "4436b3d183fa975f5eedeb0427d66da050dfa961",
    "20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql": "1653597f4c9fe053a1b691fe810a3d1b8ca60955",
    "20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql": "1a6f22628bf7dc944e7d3b77c2744c40e3204b03",
    "20260922014000_sinjira_v25_creator_family_catalog_access.sql": "378b32d59781285c9781785075ba73c15b0a66e9",
    "20260922023000_sinjira_v25_paid_order_product_access.sql": "41643696fdfba9f1075e1388dcf9fab64132a09e",
    "20260922030000_sinjira_v25_extension_product_access.sql": "1eef2537b45a074f06857ec20596d320194dc4d1",
    "20260922031500_sinjira_v25_catalog_age_helper_boundary.sql": "b0b2495e24cc0a23c7d50f32f4caef24314cc85a",
    "20260922033000_sinjira_v25_project_product_access.sql": "f95a4d85fdcd679682228fc865dad9be106d0ffe",
}


def fail(message: str) -> None:
    raise ValueError(message)


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def migration_version(filename: str) -> int | None:
    match = re.match(r"^(\d{14})_.+\.sql$", filename)
    return int(match.group(1)) if match else None


def ledger_max_version(ledger_text: str) -> int:
    versions: list[int] = []
    for raw in ledger_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        first = line.split(maxsplit=1)[0]
        if not re.fullmatch(r"\d{14}", first):
            fail(f"ledger production: ligne invalide: {line}")
        versions.append(int(first))
    if not versions:
        fail("ledger production: aucune version canonique")
    return max(versions)


def reviewed_filenames(reviewed_text: str) -> set[str]:
    names: set[str] = set()
    for raw in reviewed_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 3:
            fail(f"lot revu production: ligne invalide: {line}")
        version, slug, blob = parts
        if not re.fullmatch(r"\d{14}", version):
            fail(f"lot revu production: timestamp invalide: {version}")
        if not re.fullmatch(r"[0-9a-f]{40}", blob):
            fail(f"lot revu production: blob invalide pour {version}_{slug}")
        names.add(f"{version}_{slug}.sql")
    return names


def validate_snapshot(
    migration_names: list[str],
    snapshot_contents: dict[str, bytes],
    reviewed: bytes,
    ledger: bytes,
    dossier: str,
) -> None:
    if git_blob_sha1(reviewed) != EXPECTED_REVIEWED_BLOB:
        fail("snapshot release: production-reviewed-migration-batch.txt a changé")
    if git_blob_sha1(ledger) != EXPECTED_LEDGER_BLOB:
        fail("snapshot release: production-migration-ledger.txt a changé")

    ledger_text = ledger.decode("utf-8")
    reviewed_text = reviewed.decode("utf-8")
    max_deployed = ledger_max_version(ledger_text)
    reviewed_names = reviewed_filenames(reviewed_text)

    future_local = {
        name
        for name in migration_names
        if (version := migration_version(name)) is not None and version > max_deployed
    }
    non_reviewed = future_local - reviewed_names
    expected_names = set(EXPECTED_NON_REVIEWED)

    if non_reviewed != expected_names:
        missing = sorted(expected_names - non_reviewed)
        extra = sorted(non_reviewed - expected_names)
        details: list[str] = []
        if missing:
            details.append("absente(s) du lot non revu attendu: " + ", ".join(missing))
        if extra:
            details.append("nouvelle(s) migration(s) future(s) non documentée(s): " + ", ".join(extra))
        fail("snapshot release: ensemble des migrations non revues différent; " + "; ".join(details))

    if set(snapshot_contents) != expected_names:
        fail("snapshot release: contenus chargés incomplets pour les migrations attendues")

    for filename, expected_blob in EXPECTED_NON_REVIEWED.items():
        actual_blob = git_blob_sha1(snapshot_contents[filename])
        if actual_blob != expected_blob:
            fail(
                f"snapshot release: {filename} a changé "
                f"({actual_blob} != {expected_blob}); nouvelle revue humaine requise"
            )
        row = f"| `{filename}` | `{expected_blob}` |"
        if row not in dossier:
            fail(f"snapshot release: empreinte absente ou différente dans le dossier pour {filename}")

    required_statements = (
        "**lot production revu : non**",
        "**prévol distant : non exécuté dans ce dossier**",
        "**application production : non autorisée / non exécutée**",
        "**PR #435 : doit rester draft",
        "L’humain avant tout. Protéger sans surveiller.",
    )
    for statement in required_statements:
        if statement not in dossier:
            fail(f"snapshot release: garde documentaire manquante: {statement}")


def load_inputs() -> tuple[list[str], dict[str, bytes], bytes, bytes, str]:
    migration_names = sorted(path.name for path in MIGRATIONS.glob("*.sql") if path.is_file())
    snapshot_contents = {
        filename: (MIGRATIONS / filename).read_bytes()
        for filename in EXPECTED_NON_REVIEWED
    }
    return (
        migration_names,
        snapshot_contents,
        REVIEWED.read_bytes(),
        LEDGER.read_bytes(),
        DOSSIER.read_text(encoding="utf-8"),
    )


def self_test(values: tuple[list[str], dict[str, bytes], bytes, bytes, str]) -> None:
    migration_names, snapshot_contents, reviewed, ledger, dossier = values
    validate_snapshot(*values)

    first_name = next(iter(EXPECTED_NON_REVIEWED))
    first_blob = EXPECTED_NON_REVIEWED[first_name]

    changed_contents = copy.deepcopy(snapshot_contents)
    changed_contents[first_name] += b"\n-- mutation test\n"

    dossier_bad_hash = dossier.replace(first_blob, "0" * 40, 1)
    dossier_bad_gate = dossier.replace("**lot production revu : non**", "**lot production revu : oui**", 1)
    reviewed_changed = reviewed + b"\n# mutation test\n"
    ledger_changed = ledger + b"\n# mutation test\n"
    migration_names_extra = migration_names + ["20260919000000_sinjira_v25_unreviewed_probe.sql"]

    mutations = {
        "migration modifiée après empreinte": (migration_names, changed_contents, reviewed, ledger, dossier),
        "empreinte dossier altérée": (migration_names, snapshot_contents, reviewed, ledger, dossier_bad_hash),
        "garde humaine documentaire altérée": (migration_names, snapshot_contents, reviewed, ledger, dossier_bad_gate),
        "lot reviewed modifié": (migration_names, snapshot_contents, reviewed_changed, ledger, dossier),
        "ledger production modifié": (migration_names, snapshot_contents, reviewed, ledger_changed, dossier),
        "nouvelle migration future non documentée": (migration_names_extra, snapshot_contents, reviewed, ledger, dossier),
    }

    for label, mutated in mutations.items():
        try:
            validate_snapshot(*mutated)
        except ValueError:
            continue
        fail(f"auto-test non détecté: {label}")

    print(f"OK snapshot release V25: {len(mutations)}/{len(mutations)} dérives critiques détectées")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    values = load_inputs()
    if args.self_test:
        self_test(values)
        return

    validate_snapshot(*values)
    print(
        "OK snapshot release V25: 41 migrations futures non revues correspondent au dossier, "
        "empreintes intactes, reviewed/ledger inchangés et garde humaine conservée."
    )


if __name__ == "__main__":
    main()
