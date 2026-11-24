#!/usr/bin/env python3
"""Fail-closed manifest policy for SINJIRA mobile-native direct npm dependencies.

Exact versions are required to avoid silently selecting a newer direct
dependency on a later npm install. A lockfile is still necessary for fully
reproducible transitives; this guard does NOT certify those dependencies.
No npm execution, network requests or production secrets are used here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "mobile-native" / "package.json"
DIRECT_GROUPS = ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")
OVERRIDE_GROUPS = ("overrides", "resolutions")
EXACT_NPM_VERSION = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")
LIFECYCLE = frozenset({
    "preinstall", "install", "postinstall", "prepublish", "prepublishOnly",
    "prepare", "prepack", "postpack", "preversion", "version", "postversion",
    "pretest", "posttest", "prestart", "poststart",
})
REQUIRED = frozenset({"expo", "expo-secure-store", "react", "react-native", "react-native-webview"})


def inspect(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Invalid package.json object"]
    if data.get("private") is not True:
        errors.append("Mobile manifest must be private to prevent publication")
    if data.get("name") != "sinjira-mobile-native":
        errors.append("Unexpected package name")

    direct_names: set[str] = set()
    for group in DIRECT_GROUPS:
        table = data.get(group, {})
        if not isinstance(table, dict):
            errors.append(f"{group} must be an object")
            continue
        for name, version in table.items():
            if not isinstance(name, str) or not name or not isinstance(version, str):
                errors.append(f"{group}: invalid dependency")
                continue
            direct_names.add(name)
            if not EXACT_NPM_VERSION.fullmatch(version):
                errors.append(f"{group}: {name} must use an exact reviewed X.Y.Z version")

    if not REQUIRED.issubset(direct_names):
        errors.append("Mandatory mobile runtime dependencies unexpectedly missing")
    if len(direct_names) < 13:
        errors.append("Dependency inventory unexpectedly incomplete")

    for group in OVERRIDE_GROUPS:
        overrides = data.get(group)
        if overrides is not None:
            # Nested npm override syntax is difficult to audit with a narrow
            # static policy; require a separate dependency review before adding.
            errors.append(f"{group} requires a reviewed security policy")

    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        errors.append("npm scripts must be an object")
    else:
        for name, command in scripts.items():
            if not isinstance(name, str) or not isinstance(command, str):
                errors.append("Malformed npm script entry")
            elif name.casefold() in {s.casefold() for s in LIFECYCLE}:
                errors.append(f"Implicit npm lifecycle script forbidden: {name}")

    return errors


def self_test() -> None:
    healthy = {
        "name": "sinjira-mobile-native", "private": True,
        "dependencies": {
            "expo": "57.0.9", "expo-secure-store": "57.0.1",
            "react": "19.2.3", "react-native": "0.86.2",
            "react-native-webview": "13.16.1",
            **{f"synthetic-{i}": "1.2.3" for i in range(8)},
        },
        "scripts": {"typecheck": "tsc --noEmit"},
    }
    assert inspect(healthy) == [], "Exact pinned manifest rejected"
    mutants = {
        "caret": ("expo", "^57.0.9"),
        "tilde": ("expo", "~57.0.9"),
        "wildcard": ("expo", "57.x"),
        "moving latest": ("expo", "latest"),
        "unversioned": ("expo", ""),
        "git commit url": ("expo", "git+ssh://git@example.test/repo.git#main"),
        "http tarball": ("expo", "https://example.test/expo.tgz"),
        "npm alias": ("expo", "npm:unreviewed@1.2.3"),
        "workspace protocol": ("expo", "workspace:*"),
        "local file": ("expo", "file:../../package"),
        "range": ("expo", ">=57.0.9"),
        "prerelease": ("expo", "57.0.10-rc.1"),
    }
    for name, (package, version) in mutants.items():
        broken = json.loads(json.dumps(healthy))
        broken["dependencies"][package] = version
        if not inspect(broken):
            raise AssertionError(f"Supply-chain drift not rejected: {name}")
    for name, broken in {
        "public package": {**healthy, "private": False},
        "unapproved overrides": {**healthy, "overrides": {"expo": "^57.0.9"}},
        "malicious install hook": {**healthy, "scripts": {"postinstall": "node external.js"}},
        "missing runtime dependency": {
            **healthy, "dependencies": {
                k: v for k, v in healthy["dependencies"].items() if k != "react-native"
            }
        },
    }.items():
        if not inspect(broken):
            raise AssertionError(f"Manifest guard failed: {name}")
    print(f"PASS: {len(mutants) + 4} mobile dependency and lifecycle regressions rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, ValueError):
        print("FAIL: mobile manifest is missing or not strict JSON")
        return 1
    findings = inspect(data)
    if findings:
        for issue in findings:
            print("FAIL:", issue)
        return 1
    count = sum(len(data.get(key, {})) for key in DIRECT_GROUPS)
    print(f"PASS: {count} reviewed exact npm dependency pins; no implicit lifecycle scripts.")
    print("NOTE: A reviewed package-lock.json and npm ci are still required "
          "to lock transitive dependencies; pinning direct versions is not enough.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
