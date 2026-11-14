#!/usr/bin/env python3
"""Fail-closed scanner for raw exceptions in SINJIRA Edge runtime logs.

Runs on the committed function sources only. Does not inspect live user logs,
connect to Supabase, or print potentially sensitive source lines.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / "supabase/functions"
EXTENSIONS = frozenset({".ts", ".tsx", ".js", ".mjs", ".mts"})

LOG = r"\bconsole\.(?:error|warn|log|info|debug)\s*\("
RAW_NAMES = r"(?:error|err|exception|e|req|request|res|response|user|session|token|jwt|payload|body)"
PATTERNS = {
    "raw_exception_argument": re.compile(
        LOG + r"(?:[^;\n]*?,\s*)?" + RAW_NAMES
        + r"(?:\s*\??\.\s*(?:message|stack|details|hint|body|headers))?"
        + r"\s*(?:,|\))"
    ),
    "serialized_exception": re.compile(
        LOG + r"[^;\n]*?JSON\.stringify\s*\(\s*" + RAW_NAMES + r"\s*\)"
    ),
    "raw_exception_property": re.compile(
        LOG + r"[^;\n]*?\{\s*(?:error|exception|message|stack|details|hint)"
        + r"\s*:\s*" + RAW_NAMES + r"(?:\b|\s*\??\.)"
    ),
    "string_interpolation": re.compile(
        LOG + r"[^;\n]*?\$\{\s*" + RAW_NAMES
        + r"\s*\??\.\s*(?:message|stack|details|hint|body)"
    ),
    "raw_response_body": re.compile(
        LOG + r"[^;\n]*?(?:await\s+)?(?:req|request|response|res)\s*\."
        + r"(?:text|json|arrayBuffer|formData)\s*\("
    ),
}


def scan(source: str) -> list[tuple[str, int]]:
    findings: set[tuple[str, int]] = set()
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            findings.add((name, line))
    return sorted(findings, key=lambda x: (x[1], x[0]))


def scan_repository(root: Path) -> list[str]:
    if root.is_symlink() or not root.is_dir():
        return ["Répertoire de fonctions manquant ou lien symbolique"]
    result: list[str] = []
    paths = sorted(p for p in root.rglob("*") if p.suffix in EXTENSIONS)
    if len(paths) < 25:
        return ["Nombre de sources Edge anormalement faible"]
    for path in paths:
        rel = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.is_file():
            result.append(rel + " : fichier non régulier")
            continue
        if path.stat().st_size > 250_000:
            result.append(rel + " : fichier source anormalement volumineux")
            continue
        try:
            source = path.read_text("utf-8", errors="strict")
        except (OSError, UnicodeError):
            result.append(rel + " : lecture UTF-8 impossible")
            continue
        for rule, line in scan(source):
            result.append(rel + ":" + str(line) + " : " + rule)
    return result


def self_test() -> None:
    safe = (
        "console.error('[SINJIRA]', { code:'FAILED' });\n"
        "console.warn('[SINJIRA]', safeLogCode(error));\n"
        "console.warn('[security-context] HTTP', response.status);\n"
    )
    assert scan(safe) == [], "Journaux expurgés refusés"
    mutants = {
        "exception brute": "console.error('[SINJIRA]', error);",
        "exception seule": "console.warn(e);",
        "message brut": "console.error('[SINJIRA]', error?.message);",
        "sérialisation": "console.log('[SINJIRA]', JSON.stringify(error));",
        "objet error": "console.error('[SINJIRA]', { error: err });",
        "pile": "console.error('[SINJIRA]', { stack: exception.stack });",
        "interpolation": "console.warn(\`Détail \${error.message}\`);",
        "corps brut": "console.log('[SINJIRA]', await response.text());",
        "réponse brute": "console.warn('[SINJIRA]', response);",
        "profil utilisateur": "console.error('[SINJIRA]', user);",
        "jeton de session": "console.log('[SINJIRA]', token);",
    }
    for name, mutant in mutants.items():
        findings = scan(mutant)
        if not findings:
            raise AssertionError("Fuite simulée acceptée : " + name)
    print("OK : codes fixes autorisés, onze journaux sensibles simulés refusés.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    problems = scan_repository(FUNCTIONS)
    if problems:
        for problem in problems:
            print("NO_GO journaux Edge : " + problem)
        return 1
    print("OK : confidentialité des journaux vérifiée dans les sources Edge suivies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
