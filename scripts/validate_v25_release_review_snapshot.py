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
    "20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql": "b08af7275d0d89b122505da413458fa9a24d2603",
    "20260916210000_sinjira_v25_child_guardian_signup.sql": "e4e16d20af50d9cd0c9672fda9b79cc3501aaedc",
    "20260917223000_sinjira_v25_junior_community.sql": "c56785a7b9f6e3ec8933d9782af5110a2ca22f4e",
    "20260918010000_sinjira_v25_child_sensitive_boundary.sql": "2c8758e1ada9993645cac661f5d7676a93a31cb1",
    "20260918013000_sinjira_v25_child_content_rating.sql": "5cc1d572f97f080bcc43ae3d20e85b441e62b9e0",
    "20260918020000_sinjira_v25_account_capabilities.sql": "0a16bfcc49e51ee2b96cb98742442ae3d00e5c76",
    "20260918023000_sinjira_v25_minor_content_policy_compat.sql": "c0556e3baa218f9529f185010455984a0bc1cd03",
    "20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql": "f60c6e7a6717f7b5818ff0b9a1ba7b055aa418ff",
    "20260919013000_sinjira_v25_child_pending_guardian_redeem.sql": "983ac4b48f25f29c0c62becb692b9203cdec80a1",
    "20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql": "e14c41364246929054282bccb0e4abc5641b8643",
    "20260919023000_sinjira_v25_guardian_invite_aal2.sql": "5700bfaa2b5a95d84d37ad475524960bdb78fc9b",
    "20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql": "f08102d4bc2485bc229e21076f361bf31552c928",
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
        "OK snapshot release V25: 14 migrations futures non revues correspondent au dossier, "
        "empreintes intactes, reviewed/ledger inchangés et garde humaine conservée."
    )


if __name__ == "__main__":
    main()
