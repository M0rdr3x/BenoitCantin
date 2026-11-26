#!/usr/bin/env python3
"""Install only the reviewed mobile snapshot, with no credentials or lifecycle hooks."""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from validate_mobile_locked_dependencies import verified_bytes, zero_audit

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "mobile-native"

def snapshot():
    manifest = PROJECT / "package.json"
    lock = PROJECT / "package-lock.json"
    if any(not p.is_file() or p.is_symlink() for p in (manifest, lock)):
        raise ValueError("Regular manifest and lock required")
    return verified_bytes(manifest.read_bytes(), lock.read_bytes())

def main():
    if Path.cwd() != PROJECT or PROJECT.is_symlink():
        raise ValueError("Unexpected project directory")
    if any(p.exists() or p.is_symlink() for p in (PROJECT / "node_modules", PROJECT / ".npmrc", ROOT / ".npmrc")):
        raise ValueError("Unexpected local npm state")
    snapshot()
    npm = shutil.which("npm")
    if npm is None:
        raise ValueError("npm unavailable")
    with tempfile.TemporaryDirectory(prefix="sinjira-mobile-npm-") as temp:
        base = Path(temp)
        user, global_ = base / "user.conf", base / "global.conf"
        user.touch()
        global_.touch()
        env = {"PATH": os.environ["PATH"], "HOME": temp, "CI": "true"}
        version = subprocess.run([npm, "--version"], env=env, check=True, capture_output=True, text=True, timeout=20)
        if version.stdout.strip() != "10.9.8":
            raise ValueError("Unreviewed npm version")
        config = ["--registry=https://registry.npmjs.org/", f"--userconfig={user}", f"--globalconfig={global_}",
                  "--ignore-scripts", "--no-fund", "--no-progress"]
        audit = subprocess.run([npm, "audit", "--json", "--package-lock-only", *config],
                               env=env, capture_output=True, timeout=120)
        zero_audit(audit.stdout, audit.returncode)
        snapshot()
        subprocess.run([npm, "ci", "--no-audit", *config], env=env, check=True, timeout=180)
        snapshot()
    print("PASS: exact mobile lock, zero npm audit findings, npm ci without lifecycle scripts.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
