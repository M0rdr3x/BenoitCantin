#!/usr/bin/env python3
"""Read-only comparison of an exported Supabase migration inventory.

No network, SQL, repair, deployment, or modification of either manifest.
An exact version/name match proves history metadata only, not SQL equivalence.
"""
import argparse
import json
import re
import sys
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


def self_test():
    base = {"20260101000000":"base"}
    future = {"20260201000000":"future"}
    v, name = next(iter(future.items()))
    assert reconcile(base, future, base)["history_aligned"]
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
    print("OK: réconciliation lecture seule, 19 assertions/scénarios de sécurité")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--remote-json", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.remote_json:
        p.error("--remote-json requis")
    try:
        with args.remote_json.open("rb") as stream:
            raw = stream.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("inventaire trop volumineux")
        remote = validate(json.loads(raw))
        base = manifest(ROOT / "supabase/production-migration-ledger.txt")
        future = manifest(ROOT / "supabase/production-reviewed-migration-batch.txt", True)
        report = reconcile(base, future, remote)
    except (OSError, ValueError, UnicodeError):
        print("REFUS: inventaire ou manifestes invalides", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["history_aligned"] else 1


if __name__ == "__main__":
    sys.exit(main())
