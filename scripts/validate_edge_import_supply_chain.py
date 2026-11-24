#!/usr/bin/env python3
"""Fail-closed source-only dependency boundary for Supabase Edge Functions.

Only a reviewed set of pinned remote module specifiers is accepted. This is
a source-level guard, not a full package-vulnerability or lockfile audit.
No secrets, production services or external network connections are used.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / "supabase" / "functions"
SOURCE_SUFFIXES = frozenset({".ts", ".mts", ".js", ".mjs", ".tsx"})
REMOTE_APPROVED = frozenset({
    "npm:@supabase/supabase-js@2.119.0",
    "https://esm.sh/@supabase/supabase-js@2.119.0",
    "npm:pdf-lib@1.17.1",
    # Existing type-only Edge runtime declaration, reviewed as a legacy
    # exception. Do not allow other floating jsr: dependencies.
    "jsr:@supabase/functions-js/edge-runtime.d.ts",
})
START = re.compile(r"^\s*(?:import\b|export\s+(?:\*|\{))")
FROM = re.compile(r"\bfrom\s*(['\"])([^'\"\r\n]+)\1")
SIDE_EFFECT = re.compile(r"^\s*import\s*(['\"])([^'\"\r\n]+)\1")
DYNAMIC = re.compile(r"\bimport\s*\(")
REQUIRE = re.compile(r"\brequire\s*\(")


def statements(source: str) -> tuple[list[str], list[str]]:
    statements_found: list[str] = []
    errors: list[str] = []
    collecting: list[str] = []
    for line in source.splitlines():
        if not collecting and not START.match(line):
            continue
        if not collecting:
            collecting = [line]
        else:
            collecting.append(line)
        joined = "\n".join(collecting)
        if len(joined) > 4096 or len(collecting) > 30:
            errors.append("Import/export declaration exceeds review limits")
            collecting = []
        elif ";" in line:
            statements_found.append(joined)
            collecting = []
    if collecting:
        errors.append("Unterminated or ambiguous import/export declaration")
    return statements_found, errors


def audit_source(source: str, file: Path, functions_root: Path) -> list[str]:
    errors: list[str] = []
    if DYNAMIC.search(source):
        errors.append("Dynamic import() is not permitted in Edge source")
    if REQUIRE.search(source):
        errors.append("Dynamic CommonJS require() is not permitted in Edge source")
    imports, parse_errors = statements(source)
    errors.extend(parse_errors)
    for statement in imports:
        match = FROM.search(statement) or SIDE_EFFECT.search(statement)
        if not match:
            errors.append("Unrecognized module declaration")
            continue
        spec = match.group(2)
        if spec in REMOTE_APPROVED:
            continue
        if not spec.startswith("./") and not spec.startswith("../"):
            errors.append(f"Unapproved or unpinned module dependency: {spec}")
            continue
        if any(ch in spec for ch in ("\x00", "\\", "?", "#", "%")):
            errors.append("Ambiguous relative import path")
            continue
        module = (file.parent / spec).resolve()
        boundary = functions_root.resolve()
        if not module.is_relative_to(boundary):
            errors.append("Relative import escapes the Supabase Functions tree")
        elif module.suffix not in SOURCE_SUFFIXES:
            errors.append("Relative import must name an explicit source extension")
        elif not module.is_file() or module.is_symlink():
            errors.append(f"Relative module is missing or is a symlink: {spec}")
    return errors


def run_self_tests() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory) / "functions"
        func = root / "sample"
        func.mkdir(parents=True)
        (func / "helper.ts").write_text("export const value=1;\n", encoding="utf-8")
        file = func / "index.ts"
        good = (
            "import { value } from './helper.ts';\n"
            "import type { SupabaseClient } from 'npm:@supabase/supabase-js@2.119.0';\n"
            "import {\n  something\n} from 'npm:pdf-lib@1.17.1';\n"
            "import 'jsr:@supabase/functions-js/edge-runtime.d.ts';\n"
        )
        if audit_source(good, file, root):
            raise AssertionError("Reviewed pinned import fixture must pass")
        mutations = {
            "floating npm dependency": good + "import 'npm:pdf-lib@latest';\n",
            "unknown remote": good + "import 'https://example.org/a.ts';\n",
            "unreviewed exact version": good + "import 'npm:pdf-lib@1.18.0';\n",
            "unversioned jsr": good + "import 'jsr:@example/core';\n",
            "unknown node builtin": good + "import 'node:fs';\n",
            "escape function root": good + "import '../../outside.ts';\n",
            "relative module missing": good + "import './does-not-exist.ts';\n",
            "dynamic runtime import": good + "await import(userControlledInput);\n",
            "require runtime import": good + "require(userControlledInput);\n",
            "ambiguous path": good + "import './helper.ts?raw';\n",
            "unterminated import": good + "import { module } from\n",
        }
        for name, mutant in mutations.items():
            if not audit_source(mutant, file, root):
                raise AssertionError("Security regression undetected: " + name)
        print(f"PASS: {len(mutations)} negative Edge import scenarios rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_tests()
        return 0
    if not FUNCTIONS.is_dir():
        print("ERROR: Supabase Functions directory is absent")
        return 1
    files = sorted(
        path for path in FUNCTIONS.rglob("*")
        if path.suffix in SOURCE_SUFFIXES and path.is_file()
    )
    if len(files) < 26:
        print("ERROR: Edge source inventory unexpectedly incomplete")
        return 1
    errors: list[str] = []
    for file in files:
        if file.is_symlink():
            errors.append(f"{file.relative_to(ROOT)}: tracked symlink is forbidden")
            continue
        try:
            source = file.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            errors.append(f"{file.relative_to(ROOT)}: source not inspectable")
            continue
        for finding in audit_source(source, file, FUNCTIONS):
            errors.append(f"{file.relative_to(ROOT)}: {finding}")
    if errors:
        print(f"FAIL: {len(errors)} Edge module supply-chain finding(s)")
        for error in errors:
            print("- " + error)
        return 1
    print(f"PASS: {len(files)} Edge source files; only reviewed pinned remote imports "
          "and local modules within the source tree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
