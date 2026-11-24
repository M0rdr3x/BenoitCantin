#!/usr/bin/env python3
"""Fail-closed contract for the pinned CodeQL SAST workflow.

This is intentionally a static guard; it never invokes a code scanner,
executes repository content from a privileged token, or reads secrets.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/codeql-sast.yml"
CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
CODEQL_INIT = "github/codeql-action/init@1bd86f2fdb4b86187fa4059f16f31a3202acc9ea"
CODEQL_ANALYZE = "github/codeql-action/analyze@1bd86f2fdb4b86187fa4059f16f31a3202acc9ea"


def inspect(source: str) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, explanation: str) -> None:
        if not condition:
            errors.append(explanation)

    # A broad scan uses a non-privileged PR event, while the weekly scan
    # also sees code changes not covered by event path filters.
    for event in ("pull_request", "push", "schedule", "workflow_dispatch"):
        require(bool(re.search(r"^  " + event + r":", source, re.M)),
                f"required event missing: {event}")
    for forbidden in ("pull_request_target", "id-token: write",
                      "contents: write", "permissions: write-all",
                      "secrets.", "persist-credentials: true",
                      "ubuntu-latest"):
        require(forbidden not in source, f"forbidden privileged construct: {forbidden}")

    require(source.count(f"uses: {CHECKOUT}") == 2, "two SHA-pinned checkouts required")
    require(source.count(f"uses: {CODEQL_INIT}") == 1, "CodeQL init must be SHA-pinned")
    require(source.count(f"uses: {CODEQL_ANALYZE}") == 1, "CodeQL analyze must be SHA-pinned")
    require(source.count("persist-credentials: false") == 2,
            "checkout must not retain the repository token")
    require(source.count("runs-on: ubuntu-24.04") == 2,
            "stable runner must be used for both jobs")
    require(source.count("security-events: write") == 1,
            "Code Scanning upload permission must exist only in the analysis job")
    require(bool(re.search(r"^permissions:\n  contents: read\n", source, re.M)),
            "default GITHUB_TOKEN permissions must be read-only")
    analyze_part = source.split("\n  analyze:\n", 1)
    require(len(analyze_part) == 2, "CodeQL analysis job missing")
    if len(analyze_part) == 2:
        analyze = analyze_part[1]
        require(bool(re.search(r"^    permissions:\n      contents: read\n      security-events: write\n", analyze, re.M)),
                "Code Scanning upload permission must be scoped to the analysis job")
        require("needs: contract" in analyze, "analysis must wait for the security contract")
        require("github.event.pull_request.draft == false" in analyze,
                "draft PRs must not consume CodeQL analysis capacity")
        require("build-mode: none" in analyze, "PR code must not be built/executed by CodeQL")
        require("queries: +security-extended" in analyze,
                "extended CodeQL security queries required")
        require("language: ['actions', 'javascript-typescript', 'python']" in analyze,
                "all three supported project languages must be scanned")
        require("run:" not in analyze,
                "the privileged upload job may not execute repository shell scripts")
    require("scripts/validate_codeql_workflow_security.py --self-test" in source,
            "validator mutation tests must run")
    require("scripts/validate_codeql_workflow_security.py\n" in source,
            "validator contract must run")
    return errors


def self_test(source: str) -> None:
    if inspect(source):
        raise RuntimeError("CodeQL baseline contract is invalid")
    mutations = {
        "mutable scanner": source.replace(CODEQL_INIT, "github/codeql-action/init@v4", 1),
        "mutable checkout": source.replace(CHECKOUT, "actions/checkout@main", 1),
        "privileged trigger": source.replace("  pull_request:", "  pull_request_target:", 1),
        "token privileges": source.replace("  contents: read", "  contents: write", 1),
        "secret exposure": source.replace("  cancel-in-progress: true",
                                           "  cancel-in-progress: true\n  # secrets.SOME_TOKEN", 1),
        "missing analysis scope": source.replace("      security-events: write\n", "", 1),
        "unsafe build": source.replace("build-mode: none", "build-mode: manual", 1),
        "weaker queries": source.replace("queries: +security-extended", "queries: default", 1),
        "removed JS/TS": source.replace("'javascript-typescript', ", "", 1),
        "unchecked shell": source.replace("          queries: +security-extended",
                                          "          queries: +security-extended\n      - run: npm install", 1),
    }
    for label, altered in mutations.items():
        if not inspect(altered):
            raise RuntimeError(f"security regression not detected: {label}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    if not WORKFLOW.is_file():
        raise SystemExit("CodeQL workflow is missing")
    source = WORKFLOW.read_text(encoding="utf-8", errors="strict")
    if options.self_test:
        self_test(source)
        print("OK: 10 security regressions are detected by the CodeQL workflow contract.")
        return 0
    findings = inspect(source)
    if findings:
        for item in findings:
            print(f"ERROR CodeQL security contract: {item}")
        return 1
    print("OK: pinned CodeQL, three languages, no PR execution, minimal upload scope.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
