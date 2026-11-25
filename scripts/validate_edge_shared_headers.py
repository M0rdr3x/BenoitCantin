#!/usr/bin/env python3
"""Static regression guard for shared Edge Function response security headers.

Never fetches production data or secrets. All tests operate on tracked source.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "supabase/functions/_shared/cors.ts"

HEADERS = {
    "Access-Control-Allow-Origin": "https://www.benoitcantin.com",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
    "Cache-Control": "private, no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


def inspect(source: str) -> list[str]:
    errors: list[str] = []
    prefix = "export const corsHeaders = {"
    if source.count(prefix) != 1:
        return ["Missing or ambiguous shared CORS header object."]
    object_source = source.split(prefix, 1)[1].split("};", 1)[0]
    if not source.split(prefix, 1)[1].startswith(object_source + "};"):
        errors.append("Shared CORS header object is not closed.")

    for key, expected in HEADERS.items():
        matches = re.findall(
            rf"(?m)^\s*'{re.escape(key)}'\s*:\s*'([^']*)'\s*,?\s*$",
            object_source,
        )
        if matches != [expected]:
            errors.append(f"{key}: missing, duplicate or insecure value")

    if re.search(r"Access-Control-Allow-Origin['\"]\s*:\s*['\"]\*", object_source):
        errors.append("Wildcard CORS origin is forbidden")
    if re.search(r"'(?:Cache-Control|Pragma|Referrer-Policy)'[\s\S]*?\n\s*\.\.\.", object_source):
        errors.append("Shared headers may not be overwritten with a spread")
    if "export function json(data: unknown, status = 200)" not in source:
        errors.append("Expected shared JSON response helper is missing")
    if "new Response(JSON.stringify(data)" not in source:
        errors.append("The helper must construct a JSON Response")
    if not re.search(
        r"headers:\s*\{\s*\.\.\.corsHeaders\s*,\s*'Content-Type':\s*"
        r"'application/json; charset=utf-8'\s*\}",
        source,
    ):
        errors.append("JSON helper does not inherit the security headers")
    return errors


def self_test(source: str) -> None:
    baseline = inspect(source)
    if baseline:
        raise AssertionError("Baseline header contract failed: " + "; ".join(baseline))
    mutants = {
        "remove no-store": source.replace("  'Cache-Control': 'private, no-store, max-age=0',\n", ""),
        "cache public": source.replace("private, no-store, max-age=0", "public, max-age=3600"),
        "remove MIME guard": source.replace("  'X-Content-Type-Options': 'nosniff',\n", ""),
        "MIME sniffing allowed": source.replace("'X-Content-Type-Options': 'nosniff'", "'X-Content-Type-Options': 'sniff'"),
        "referrer disclosure": source.replace("'Referrer-Policy': 'no-referrer'", "'Referrer-Policy': 'unsafe-url'"),
        "wildcard origin": source.replace("'Access-Control-Allow-Origin': 'https://www.benoitcantin.com'", "'Access-Control-Allow-Origin': '*'"),
        "vary missing": source.replace("  'Vary': 'Origin',\n", ""),
        "JSON headers bypass": source.replace("headers: { ...corsHeaders, 'Content-Type'", "headers: { 'Content-Type'"),
        "duplicate conflicting cache": source.replace("  'Pragma': 'no-cache',", "  'Cache-Control': 'public',\n  'Pragma': 'no-cache',"),
    }
    for label, mutant in mutants.items():
        if mutant == source or not inspect(mutant):
            raise AssertionError("Regression not detected: " + label)
    print(f"PASS: {len(mutants)} negative security mutations were rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    source = TARGET.read_text(encoding="utf-8", errors="strict")
    if args.self_test:
        self_test(source)
        return 0
    findings = inspect(source)
    for finding in findings:
        print("ERROR Edge shared headers:", finding)
    if findings:
        return 1
    print("PASS: restrictive CORS origin, no-store, no-sniff and no-referrer "
          "are inherited by shared Edge responses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
