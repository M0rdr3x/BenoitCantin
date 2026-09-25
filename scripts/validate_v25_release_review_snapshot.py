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
WORKSHEET = ROOT / "docs/SINJIRA_V25_PRODUCTION_MIGRATION_REVIEW_WORKSHEET_2026-09-23.md"
MATRIX = ROOT / "docs/SINJIRA_V25_PRODUCTION_MIGRATION_TECHNICAL_REVIEW_MATRIX_2026-09-23.md"
STATIC_SCAN = ROOT / "docs/SINJIRA_V25_PRODUCTION_MIGRATION_STATIC_RISK_SCAN_2026-09-23.md"
WORKFLOW = ROOT / ".github/workflows/sinjira-v25-release-review-snapshot.yml"

EXPECTED_REVIEWED_BLOB = "2392a7b9f2ce06952555446771933b05d6d47387"
EXPECTED_LEDGER_BLOB = "0eb7b0d886e9f24d5592b7014ed4d92d28fded63"
EXPECTED_NON_REVIEWED = {
    "20260913030500_sinjira_v25_travel_mode_geo_scope_hardening.sql": "7285d1e30ea288004d17c1dbfbf9f01662b36bb7",
    "20260913230000_sinjira_v25_travel_mode_retention_purge.sql": "41b8dc3d1b1e09c018e588755edb053e63e9904a",
    "20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql": "2d7b8ccbfc79fed6a03208086a138618779d6e2d",
    "20260916210000_sinjira_v25_child_guardian_signup.sql": "baa11566a920ee8ba9f08810f542d9ad78046d24",
    "20260917223000_sinjira_v25_junior_community.sql": "64e66dc8d9c45de9ecbb1174fdb842e4444b9b6b",
    "20260918010000_sinjira_v25_child_sensitive_boundary.sql": "ea0426172caba27fc3446c696575a19a1eae08d7",
    "20260918013000_sinjira_v25_child_content_rating.sql": "b0a2bfda90579830083d128035ee533d06dd2159",
    "20260918020000_sinjira_v25_account_capabilities.sql": "0a16bfcc49e51ee2b96cb98742442ae3d00e5c76",
    "20260918023000_sinjira_v25_minor_content_policy_compat.sql": "c0556e3baa218f9529f185010455984a0bc1cd03",
    "20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql": "efa9d6a29c4decfe0180e9262827022ff752f670",
    "20260919013000_sinjira_v25_child_pending_guardian_redeem.sql": "04561c62e7f4002e5ef34d34775c846784fb9727",
    "20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql": "e14c41364246929054282bccb0e4abc5641b8643",
    "20260919023000_sinjira_v25_guardian_invite_aal2.sql": "2e440ddfc9aa3f082cc271a61288abe3d3b6ac2a",
    "20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql": "f08102d4bc2485bc229e21076f361bf31552c928",
    "20260919033000_sinjira_v25_guardian_invite_read_aal2.sql": "b2439fbad69798db42c17a04887dff50d9f184cc",
    "20260919040000_sinjira_v25_junior_enable_aal2.sql": "eaaff78322e0ea02235dbf3f4a4d1507a85e72f4",
    "20260919043000_sinjira_v25_guardian_revoke_aal2.sql": "260c4723af7245af27744fbc8472e5ed0954b93e",
    "20260919050000_sinjira_v25_guardian_majority_visibility.sql": "d7a65f65e1a870620809f1a2e669ef031d6f6d8a",
    "20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql": "ac18154c958b707d94ddc557b1af6b2af01ba62f",
    "20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql": "d2ef613bfb372efe620e413d5e059b4d1b1e6c64",
    "20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql": "2d91c64a90f5c8bca506577ef359078fdf558fad",
    "20260919070000_sinjira_v25_guardian_contacts_minimization.sql": "e684227b322aa88dbd43376d8bd9aa19a6161f6e",
    "20260919073000_sinjira_v25_junior_guardian_summary_aal2.sql": "07b1ea063e57d3dd4a31e689fac6f44fd1ca6d18",
    "20260919080000_sinjira_v25_guardian_character_identity_isolation.sql": "7c169564095bb440bde8a2a106c4e00aa2f307e4",
    "20260919083000_sinjira_v25_guardian_junior_alias_privacy.sql": "8e0fd367bd0c30ed77f947ae0583408b370121a1",
    "20260919090000_sinjira_v25_account_content_hub.sql": "29358d27f8f505897b924062e208b8d5c740f8c5",
    "20260919093000_sinjira_v25_private_novel_catalog.sql": "41fec69fe7b720a909558a8a1429a7c39cd4772c",
    "20260919100000_sinjira_v25_private_profile_age_11.sql": "d51142e51ba109492b31c14216367287ef51fbc0",
    "20260919103000_sinjira_v25_livre_i_catalog_seed.sql": "2a5bb6ae5c25b92c8f963909e95d5949bb82df07",
    "20260919110000_sinjira_v25_social_public_pseudo_privacy.sql": "ac4f11e8e1591c35f0be91f541a21763fdb3ec8d",
    "20260919113000_sinjira_v25_private_novel_asset_rls.sql": "745ae12098e538415dde16bac198d05610b99954",
    "20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql": "5ed558a9426173fdb714479d28f170ada542803b",
    "20260919123000_sinjira_v25_public_rpc_boundary.sql": "61377e409f769ed94646791acaf8f3c1f86328d0",
    "20260919130000_sinjira_v25_account_catalog_browser_privileges.sql": "4436b3d183fa975f5eedeb0427d66da050dfa961",
    "20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql": "1653597f4c9fe053a1b691fe810a3d1b8ca60955",
    "20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql": "1a6f22628bf7dc944e7d3b77c2744c40e3204b03",
    "20260922014000_sinjira_v25_creator_family_catalog_access.sql": "44f0e779fc667aaf6b39dbcb121b47a0f2e1054a",
    "20260922023000_sinjira_v25_paid_order_product_access.sql": "41643696fdfba9f1075e1388dcf9fab64132a09e",
    "20260922030000_sinjira_v25_extension_product_access.sql": "0bdc1677d4efe669b8ec1503ed41f745136c6680",
    "20260922031500_sinjira_v25_catalog_age_helper_boundary.sql": "b0b2495e24cc0a23c7d50f32f4caef24314cc85a",
    "20260922033000_sinjira_v25_project_product_access.sql": "a07f22b7801a6182e0c15dc05e2cf09df92e7dde",
    "20260924173000_sinjira_v25_junior_comment_author_visibility.sql": "3c80073c9bc027707d1f12a129cebd91a8d7ba4f",
    "20260924191000_sinjira_v25_junior_hidden_post_comment_guard.sql": "5cdb8c576aae2ff7adcf75dd1270ba446b063e59",
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


def matrix_migration_names(matrix: str) -> list[str]:
    rows: list[tuple[int, str]] = []
    pattern = re.compile(r"^\|\s*(\d+)\s*\|\s*`([^`]+\.sql)`\s*\|", re.MULTILINE)
    for match in pattern.finditer(matrix):
        rows.append((int(match.group(1)), match.group(2)))
    if not rows:
        fail("snapshot release: matrice technique sans ligne de migration")
    expected_indexes = list(range(1, len(rows) + 1))
    actual_indexes = [index for index, _ in rows]
    if actual_indexes != expected_indexes:
        fail("snapshot release: numérotation de la matrice technique non canonique")
    return [name for _, name in rows]


def validate_snapshot(
    migration_names: list[str],
    snapshot_contents: dict[str, bytes],
    reviewed: bytes,
    ledger: bytes,
    dossier: str,
    worksheet: str,
    matrix: str,
    static_scan: str,
    workflow: str,
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
        worksheet_row = f"| `{filename}` | `{expected_blob}` |"
        if worksheet_row not in worksheet:
            fail(f"snapshot release: empreinte absente ou différente dans la feuille de revue pour {filename}")

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

    worksheet_statements = (
        "**Statut global : NON REVU / NON APPROUVÉ**",
        "Aucune case cochée ne vaut à elle seule approbation production.",
        "Ne pas modifier automatiquement `supabase/production-reviewed-migration-batch.txt`",
        "L’humain avant tout. Protéger sans surveiller.",
    )
    for statement in worksheet_statements:
        if statement not in worksheet:
            fail(f"snapshot release: garde feuille de revue manquante: {statement}")

    matrix_names = matrix_migration_names(matrix)
    expected_matrix_names = list(EXPECTED_NON_REVIEWED)
    if matrix_names != expected_matrix_names:
        missing = sorted(set(expected_matrix_names) - set(matrix_names))
        extra = sorted(set(matrix_names) - set(expected_matrix_names))
        details: list[str] = []
        if missing:
            details.append("absente(s): " + ", ".join(missing))
        if extra:
            details.append("inattendue(s): " + ", ".join(extra))
        if not details:
            details.append("ordre différent de l'ordre canonique")
        fail("snapshot release: matrice technique désynchronisée; " + "; ".join(details))

    matrix_statements = (
        "**Statut : AIDE DE REVUE AUTOMATISÉE — NON REVU / NON APPROUVÉ**",
        "**L’humain avant tout. Protéger sans surveiller.**",
        "elle ne doit jamais remplir automatiquement la colonne « Décision humaine »",
        "aucun prévol distant ni déploiement production n'est autorisé",
    )
    for statement in matrix_statements:
        if statement not in matrix:
            fail(f"snapshot release: garde matrice technique manquante: {statement}")

    static_scan_statements = (
        "**Statut : TRIAGE AUTOMATISÉ — AUCUNE APPROBATION PRODUCTION**",
        "Le scan a porté sur les **43 migrations futures non revues** figées par le snapshot release.",
        "Ce scan ne conclut pas qu'une migration est sûre pour la production.",
        "**L’humain avant tout. Protéger sans surveiller.**",
    )
    for statement in static_scan_statements:
        if statement not in static_scan:
            fail(f"snapshot release: garde scan statique manquante: {statement}")

    workflow_paths = (
        "docs/SINJIRA_V25_CHILD_JUNIOR_RELEASE_REVIEW_2026-09-18.md",
        "docs/SINJIRA_V25_PRODUCTION_MIGRATION_REVIEW_WORKSHEET_2026-09-23.md",
        "docs/SINJIRA_V25_PRODUCTION_MIGRATION_TECHNICAL_REVIEW_MATRIX_2026-09-23.md",
        "docs/SINJIRA_V25_PRODUCTION_MIGRATION_STATIC_RISK_SCAN_2026-09-23.md",
        "scripts/validate_v25_release_review_snapshot.py",
    )
    for path in workflow_paths:
        if path not in workflow:
            fail(f"snapshot release: workflow ne surveille pas {path}")


def load_inputs() -> tuple[list[str], dict[str, bytes], bytes, bytes, str, str, str, str, str]:
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
        WORKSHEET.read_text(encoding="utf-8"),
        MATRIX.read_text(encoding="utf-8"),
        STATIC_SCAN.read_text(encoding="utf-8"),
        WORKFLOW.read_text(encoding="utf-8"),
    )


def self_test(values: tuple[list[str], dict[str, bytes], bytes, bytes, str, str, str, str, str]) -> None:
    migration_names, snapshot_contents, reviewed, ledger, dossier, worksheet, matrix, static_scan, workflow = values
    validate_snapshot(*values)

    first_name = next(iter(EXPECTED_NON_REVIEWED))
    first_blob = EXPECTED_NON_REVIEWED[first_name]

    changed_contents = copy.deepcopy(snapshot_contents)
    changed_contents[first_name] += b"\n-- mutation test\n"

    dossier_bad_hash = dossier.replace(first_blob, "0" * 40, 1)
    dossier_bad_gate = dossier.replace("**lot production revu : non**", "**lot production revu : oui**", 1)
    worksheet_bad_hash = worksheet.replace(first_blob, "0" * 40, 1)
    worksheet_bad_gate = worksheet.replace("**Statut global : NON REVU / NON APPROUVÉ**", "**Statut global : APPROUVÉ**", 1)
    matrix_bad_gate = matrix.replace("**Statut : AIDE DE REVUE AUTOMATISÉE — NON REVU / NON APPROUVÉ**", "**Statut : APPROUVÉ**", 1)
    matrix_bad_set = matrix.replace(first_name, "20260913030500_sinjira_v25_unreviewed_probe.sql", 1)
    static_scan_bad_gate = static_scan.replace("**Statut : TRIAGE AUTOMATISÉ — AUCUNE APPROBATION PRODUCTION**", "**Statut : APPROUVÉ PRODUCTION**", 1)
    workflow_bad_path = workflow.replace("docs/SINJIRA_V25_PRODUCTION_MIGRATION_TECHNICAL_REVIEW_MATRIX_2026-09-23.md", "docs/matrix-review-missing.md", 1)
    reviewed_changed = reviewed + b"\n# mutation test\n"
    ledger_changed = ledger + b"\n# mutation test\n"
    migration_names_extra = migration_names + ["20260919000000_sinjira_v25_unreviewed_probe.sql"]

    mutations = {
        "migration modifiée après empreinte": (migration_names, changed_contents, reviewed, ledger, dossier, worksheet, matrix, static_scan, workflow),
        "empreinte dossier altérée": (migration_names, snapshot_contents, reviewed, ledger, dossier_bad_hash, worksheet, matrix, static_scan, workflow),
        "garde humaine documentaire altérée": (migration_names, snapshot_contents, reviewed, ledger, dossier_bad_gate, worksheet, matrix, static_scan, workflow),
        "empreinte feuille de revue altérée": (migration_names, snapshot_contents, reviewed, ledger, dossier, worksheet_bad_hash, matrix, static_scan, workflow),
        "garde feuille de revue altérée": (migration_names, snapshot_contents, reviewed, ledger, dossier, worksheet_bad_gate, matrix, static_scan, workflow),
        "garde matrice technique altérée": (migration_names, snapshot_contents, reviewed, ledger, dossier, worksheet, matrix_bad_gate, static_scan, workflow),
        "ensemble matrice technique altéré": (migration_names, snapshot_contents, reviewed, ledger, dossier, worksheet, matrix_bad_set, static_scan, workflow),
        "garde scan statique altérée": (migration_names, snapshot_contents, reviewed, ledger, dossier, worksheet, matrix, static_scan_bad_gate, workflow),
        "workflow matrice non surveillée": (migration_names, snapshot_contents, reviewed, ledger, dossier, worksheet, matrix, static_scan, workflow_bad_path),
        "lot reviewed modifié": (migration_names, snapshot_contents, reviewed_changed, ledger, dossier, worksheet, matrix, static_scan, workflow),
        "ledger production modifié": (migration_names, snapshot_contents, reviewed, ledger_changed, dossier, worksheet, matrix, static_scan, workflow),
        "nouvelle migration future non documentée": (migration_names_extra, snapshot_contents, reviewed, ledger, dossier, worksheet, matrix, static_scan, workflow),
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
        "OK snapshot release V25: 43 migrations futures non revues correspondent au dossier, "
        "empreintes intactes, feuille/matrice/scan de revue synchronisés, reviewed/ledger inchangés et garde humaine conservée."
    )


if __name__ == "__main__":
    main()
