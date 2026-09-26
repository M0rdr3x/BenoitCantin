#!/usr/bin/env python3
"""Fail-closed contract for SINJIRA V25 Mode Voyage retention purge."""

from __future__ import annotations

import argparse
import hashlib
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = Path("supabase/migrations/20260913230000_sinjira_v25_travel_mode_retention_purge.sql")
TEST = Path("supabase/tests/security_travel_retention_v25.test.sql")
WORKFLOW = Path(".github/workflows/sinjira-security-travel-retention-v25.yml")
LEDGER = Path("supabase/production-migration-ledger.txt")
STAMP = "20260913230000"
NAME = "sinjira_v25_travel_mode_retention_purge"
EXPECTED_BLOB_SHA = "41b8dc3d1b1e09c018e588755edb053e63e9904a"
FUNCTION = "private.security_purge_expired_travel_plans_v25()"


def _read(root: Path, rel: Path) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    required = (MIGRATION, TEST, WORKFLOW, LEDGER)
    missing = [str(path) for path in required if not (root / path).is_file()]
    if missing:
        return [f"fichier requis absent: {path}" for path in missing]

    migration = _read(root, MIGRATION)
    test = _read(root, TEST)
    workflow = _read(root, WORKFLOW)
    ledger = _read(root, LEDGER)
    mlow = migration.lower()
    compact = re.sub(r"\s+", " ", mlow)

    if _blob_sha(root / MIGRATION) != EXPECTED_BLOB_SHA:
        errors.append("l’empreinte A1 de la migration de purge a changé sans revue explicite")
    if not re.search(
        r"create\s+or\s+replace\s+function\s+private\.security_purge_expired_travel_plans_v25\s*\(\s*\)",
        mlow,
    ):
        errors.append("la purge doit rester une fonction privée sans paramètre")
    if "returns bigint" not in compact:
        errors.append("la purge doit retourner uniquement un bigint")
    if "security definer" not in compact:
        errors.append("la purge doit rester SECURITY DEFINER")
    if "set search_path = pg_catalog, public, private" not in compact:
        errors.append("le search_path verrouillé de la purge a changé")
    if not re.search(
        r"delete\s+from\s+public\.security_travel_plans\s+where\s+delete_after\s*<=\s*statement_timestamp\(\)\s*;",
        mlow,
    ):
        errors.append("la suppression doit dépendre uniquement de delete_after <= statement_timestamp()")
    if re.search(r"\bends_at\b", mlow):
        errors.append("la purge ne doit jamais recalculer la rétention depuis ends_at")
    if not re.search(
        r"revoke\s+all\s+on\s+function\s+private\.security_purge_expired_travel_plans_v25\(\)\s+from\s+public,\s*anon,\s*authenticated\s*;",
        mlow,
    ):
        errors.append("les rôles public/anon/authenticated doivent être révoqués")
    if not re.search(
        r"grant\s+execute\s+on\s+function\s+private\.security_purge_expired_travel_plans_v25\(\)\s+to\s+service_role\s*;",
        mlow,
    ):
        errors.append("seul service_role doit recevoir EXECUTE explicitement")
    if "cron.schedule" in mlow or "pg_cron" in mlow:
        errors.append("cette convergence ne doit pas prétendre configurer un ordonnanceur production")

    precise_location_patterns = (
        r"\braw_ip\b", r"\bip_address\b", r"\blatitude\b", r"\blongitude\b",
        r"\bgps\b", r"\bhotel\b", r"\bflight\b", r"\bitinerary\b",
    )
    if any(re.search(pattern, mlow) for pattern in precise_location_patterns):
        errors.append("la migration ne doit introduire aucune localisation précise")

    tlow = test.lower()
    if "select plan(11);" not in tlow:
        errors.append("le pgTAP doit conserver ses 11 assertions")
    for required_text in (
        FUNCTION, "delete_after", "ends_at", "statement_timestamp()",
        "service_role", "authenticated", "anon",
    ):
        if required_text.lower() not in tlow:
            errors.append(f"preuve pgTAP manquante: {required_text}")

    required_workflow_fragments = (
        "python scripts/validate_security_travel_retention_v25.py --self-test",
        "python scripts/validate_security_travel_retention_v25.py",
        "supabase db start",
        "supabase test db supabase/tests/security_travel_retention_v25.test.sql --local",
        "supabase stop --no-backup || true",
    )
    for fragment in required_workflow_fragments:
        if fragment not in workflow:
            errors.append(f"commande CI manquante: {fragment}")
    for path in (str(MIGRATION), str(TEST), "scripts/validate_security_travel_retention_v25.py", str(LEDGER)):
        if path not in workflow:
            errors.append(f"déclencheur CI manquant pour {path}")
    if "production-reviewed-migration-batch.txt" in workflow:
        errors.append("la convergence A1 ne doit pas dépendre du lot production reviewed")

    if re.search(rf"^{STAMP}\s+", ledger, re.MULTILINE):
        errors.append("la migration est marquée production alors que #240 interdit ce déploiement")

    return errors


def _self_test() -> None:
    baseline_errors = validate(ROOT)
    if baseline_errors:
        raise SystemExit("SELF-TEST impossible, baseline invalide:\n- " + "\n- ".join(baseline_errors))

    paths = (MIGRATION, TEST, WORKFLOW, LEDGER)
    baseline = {path: (ROOT / path).read_bytes() for path in paths}

    cases = [
        ("échéance ends_at", MIGRATION, b"delete_after <= statement_timestamp()", b"ends_at <= statement_timestamp()"),
        ("grant authenticated", MIGRATION, b"to service_role;", b"to authenticated;"),
        ("instant arbitraire", MIGRATION, b"security_purge_expired_travel_plans_v25()", b"security_purge_expired_travel_plans_v25(p_before timestamptz)"),
        ("cron implicite", MIGRATION, b"commit;", b"select cron.schedule('travel-purge', '* * * * *', 'select 1');\ncommit;"),
        ("self-test CI retiré", WORKFLOW, b"python scripts/validate_security_travel_retention_v25.py --self-test", b"echo self-test-retire"),
        ("empreinte migration changée", MIGRATION, b"-- SINJIRA", b"-- mutation-SINJIRA"),
        ("faux déploiement production", LEDGER, b"\n", f"\n{STAMP} {NAME}\n".encode("utf-8")),
    ]

    for label, target, needle, replacement in cases:
        with tempfile.TemporaryDirectory(prefix="sinjira-travel-retention-") as tmp:
            root = Path(tmp)
            for path, data in baseline.items():
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
            data = (root / target).read_bytes()
            if needle not in data:
                raise SystemExit(f"SELF-TEST mutation introuvable: {label}")
            (root / target).write_bytes(data.replace(needle, replacement, 1))
            if not validate(root):
                raise SystemExit(f"SELF-TEST fail-open détecté: {label}")

    print(f"OK: {len(cases)} mutations fail-closed détectées")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        return

    errors = validate(ROOT)
    if errors:
        raise SystemExit("Contrat Mode Voyage rétention invalide:\n- " + "\n- ".join(errors))
    print("OK: contrat Mode Voyage rétention V25 valide, empreinte A1 verrouillée, production intacte")


if __name__ == "__main__":
    main()
