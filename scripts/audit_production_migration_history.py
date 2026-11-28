#!/usr/bin/env python3
"""Read-only comparison of an exported Supabase migration inventory.

No network, SQL, repair, deployment, or modification of either manifest.
An exact version/name match proves history metadata only, not SQL equivalence.
"""
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"[0-9]{14}")
NAME = re.compile(r"[a-zA-Z0-9_]+")


def validate(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("inventaire vide ou invalide")
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("ligne invalide")
        version, name = row.get("version"), row.get("name")
        if not isinstance(version, str) or not VERSION.fullmatch(version):
            raise ValueError("version invalide")
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise ValueError("nom invalide")
        if version in result:
            raise ValueError("version dupliquée")
        result[version] = name
    return result


def manifest(path, batch=False):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != (3 if batch else 2):
            raise ValueError("ligne manifeste invalide")
        if batch and not re.fullmatch(r"[0-9a-f]{40}", parts[2]):
            raise ValueError("empreinte manifeste invalide")
        rows.append(dict(version=parts[0], name=parts[1]))
    return validate(rows)


def fetched_inventory(directory):
    """Read CLI-exported names only; never open or publish remote SQL."""
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("répertoire distant invalide")
    rows = []
    for entry in directory.iterdir():
        if entry.is_symlink() or not entry.is_file():
            raise ValueError("entrée distante non régulière")
        match = re.fullmatch(r"([0-9]{14})_([a-zA-Z0-9_]+)\.sql", entry.name)
        if not match:
            raise ValueError("nom de migration distante invalide")
        rows.append(dict(version=match[1], name=match[2]))
        if len(rows) > 10000:
            raise ValueError("inventaire trop volumineux")
    return validate(rows)


def reconcile(baseline, future, remote):
    if set(baseline) & set(future) or min(future) <= max(baseline):
        raise ValueError("chevauchement des manifestes")
    names = {}
    for version, name in remote.items():
        names.setdefault(name, []).append(version)
    counts = Counter(names for names in remote.values())
    historical_missing = [v for v in baseline if v not in remote]
    historical_mismatch = [v for v in baseline if v in remote and remote[v] != baseline[v]]
    additional_remote = sorted(set(remote) - set(baseline))
    exact, conflicts, other_version, absent, ambiguous = [], [], [], [], []
    for version, name in sorted(future.items()):
        matches = names.get(name, [])
        if len(matches) > 1:
            ambiguous.append(version)
        elif version in remote:
            (exact if remote[version] == name else conflicts).append(version)
        elif matches:
            other_version.append({"local": version, "remote": matches[0]})
        else:
            absent.append(version)
    safe = not (historical_missing or historical_mismatch or additional_remote
                or exact or conflicts or other_version or ambiguous
                or any(n > 1 for n in counts.values()))
    return dict(baseline_count=len(baseline), remote_count=len(remote),
                future_count=len(future), historical_missing=historical_missing,
                historical_mismatch=historical_mismatch, additional_remote=additional_remote,
                future_exact=exact, future_version_conflicts=conflicts,
                future_other_version=other_version, future_absent=absent,
                future_ambiguous=ambiguous, duplicate_remote_names=sorted(n for n,c in counts.items() if c>1),
                history_aligned=safe, deployment_authorized=False)


def verify_applied(baseline, future, remote):
    # Reuse overlap/order validation. The exact remote inventory must equal
    # the baseline plus the reviewed batch, not merely have a successful dry-run.
    reconcile(baseline, future, remote)
    expected = {**baseline, **future}
    missing = sorted(set(expected) - set(remote))
    unexpected = sorted(set(remote) - set(expected))
    mismatched = sorted(v for v in expected.keys() & remote.keys()
                        if expected[v] != remote[v])
    return dict(expected_count=len(expected), remote_count=len(remote),
                missing=missing, unexpected=unexpected, mismatched=mismatched,
                history_aligned=not (missing or unexpected or mismatched),
                deployment_authorized=False)


def self_test():
    base = {"20260101000000":"base"}
    future = {"20260201000000":"future"}
    v, name = next(iter(future.items()))
    assert reconcile(base, future, base)["history_aligned"]
    assert verify_applied(base, future, {**base, **future})["history_aligned"]
    for remote in [base, future, {**base, v:"wrong"},
                   {**base, **future, "20260301000000":"unexpected"},
                   {**base, "20260301000000":name}]:
        result = verify_applied(base, future, remote)
        assert not result["history_aligned"]
        assert not result["deployment_authorized"]
    for remote in [
        {"20260101000000":"wrong"},
        {"20260102000000":"base"},
        {**base,v:name},
        {**base,v:"wrong"},
        {**base,"20260301000000":name},
        {**base,v:name,"20260301000000":name},
        {**base,"20260301000000":"unrelated"},
    ]:
        result = reconcile(base, future, remote)
        assert not result["history_aligned"] and not result["deployment_authorized"]
    for invalid in [None, [], {}, [None], [{"version":0,"name":"x"}],
                    [{"version":v,"name":"x\n"}],
                    [{"version":v,"name":"x"},{"version":v,"name":"y"}]]:
        try:
            validate(invalid)
        except ValueError:
            continue
        raise AssertionError("inventaire invalide accepté")
    assert validate([{"version":v,"name":name}]) == future
    assert reconcile(base,future,{**base,v:name})["future_exact"] == [v]
    assert reconcile(base,future,{**base,"20260301000000":name})["future_other_version"]
    assert reconcile(base,future,base)["future_absent"] == [v]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / f"{v}_{name}.sql").write_bytes(b"synthetic SQL never read")
        assert fetched_inventory(root) == future
        for invalid_name in [f"{v}_duplicate.sql", "unexpected.txt", "20260202000000_bad name.sql"]:
            probe = root / invalid_name
            probe.write_bytes(b"")
            try:
                fetched_inventory(root)
            except ValueError:
                pass
            else:
                raise AssertionError("fichier distant ambigu accepté")
            finally:
                probe.unlink()
        probe = root / "20260203000000_symlink.sql"
        probe.symlink_to(root / f"{v}_{name}.sql")
        try:
            fetched_inventory(root)
        except ValueError:
            pass
        else:
            raise AssertionError("lien distant accepté")
    print("OK: réconciliation lecture seule, 24 scénarios existants et 6 scénarios post-application")


def main():
    p = argparse.ArgumentParser()
    inputs = p.add_mutually_exclusive_group()
    inputs.add_argument("--remote-json", type=Path)
    inputs.add_argument("--remote-dir", type=Path)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--after-apply", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.remote_json and not args.remote_dir:
        p.error("--remote-json ou --remote-dir requis")
    try:
        if args.remote_dir:
            remote = fetched_inventory(args.remote_dir)
        else:
            with args.remote_json.open("rb") as stream:
                raw = stream.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError("inventaire trop volumineux")
            remote = validate(json.loads(raw))
        base = manifest(ROOT / "supabase/production-migration-ledger.txt")
        future = manifest(ROOT / "supabase/production-reviewed-migration-batch.txt", True)
        report = (verify_applied if args.after_apply else reconcile)(base, future, remote)
    except (OSError, ValueError, UnicodeError):
        print("REFUS: inventaire ou manifestes invalides", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["history_aligned"] else 1


if __name__ == "__main__":
    sys.exit(main())
