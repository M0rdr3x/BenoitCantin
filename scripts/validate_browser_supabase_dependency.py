#!/usr/bin/env python3
"""Reject unreviewed literal browser Supabase SDK URLs; no remote calls."""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPROVED = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.2/+esm"
SHARED = "assets/js/sinjira-supabase.js"
URL = re.compile(r"""(?:https?://|//)[^\s'"<>`\\]*supabase-js[^\s'"<>`\\]*""", re.I)

def audit(source, path):
    urls = URL.findall(source)
    errors = []
    for url in urls:
        if url != APPROVED:
            errors.append(f"{path}: unreviewed Supabase SDK URL")
        elif path != SHARED:
            errors.append(f"{path}: SDK must be imported via the shared module")
    if path == SHARED:
        expected = "import { createClient } from '" + APPROVED + "';"
        if source.count(expected) != 1 or urls != [APPROVED]:
            errors.append(f"{path}: exactly one reviewed SDK import required")
    return errors

def self_test():
    clean = "import { createClient } from '" + APPROVED + "';"
    assert not audit(clean, SHARED)
    for version in ("2", "latest", "^2", "~2.119.2", "2.119.0", "2.119.2?x=1"):
        assert audit(clean.replace("2.119.2", version), SHARED)
    for host in ("unpkg.com", "evil.example", "esm.sh"):
        assert audit(clean.replace("cdn.jsdelivr.net", host), SHARED)
    assert audit(clean.replace("https:", ""), SHARED)
    assert audit(clean + "\n" + clean, SHARED)
    assert audit("", SHARED)
    assert audit(clean, "assets/js/another.js")
    assert not audit("import {getSupabase} from './sinjira-supabase.js';", "assets/js/another.js")
    print("PASS: 13 negative browser SDK import cases")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return
    files = sorted(x for x in (ROOT / "assets/js").rglob("*") if x.is_file() and x.suffix in {".js", ".mjs"})
    if len(files) < 100 or not (ROOT / SHARED).is_file():
        raise SystemExit("Browser source inventory incomplete")
    errors = [error for path in files for error in audit(path.read_text(encoding="utf-8"), path.relative_to(ROOT).as_posix())]
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(files)} browser JS sources; exact shared SDK URL")

if __name__ == "__main__":
    main()
