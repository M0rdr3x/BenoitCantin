#!/usr/bin/env python3
"""Fail-closed regression checks for the public Content Security Policy.

This covers the Netlify source, Vercel preview, and the generated _headers.
No network calls, user data, or production configuration are changed.
"""
from __future__ import annotations

import json
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_netlify_public import public_csp_blocks_objects, render_standalone_headers  # noqa: E402


def find_object_policy_errors(policy: str) -> list[str]:
    """Reject missing, duplicate, or non-'none' object-src directives."""
    statements = [piece.strip().split() for piece in policy.split(";") if piece.strip()]
    object_directives = [words for words in statements if words[0].lower() == "object-src"]
    if object_directives != [["object-src", "'none'"]]:
        return ["CSP publique: object-src 'none' doit être unique et strict"]
    return []


def policies() -> tuple[str, str, str]:
    netlify = tomllib.loads((ROOT / "netlify.toml").read_text("utf-8"))
    global_rule = next(item for item in netlify["headers"] if item["for"] == "/*")
    netlify_csp = global_rule["values"]["Content-Security-Policy"]

    vercel = json.loads((ROOT / "vercel.json").read_text("utf-8"))
    preview_rule = next(item for item in vercel["headers"] if item["source"] == "/(.*)")
    vercel_csp = next(
        header["value"] for header in preview_rule["headers"]
        if header["key"] == "Content-Security-Policy"
    )

    # The output builder copies Netlify header rules into standalone Netlify
    # deployment artifacts. Test that production and preview agree.
    generated = render_standalone_headers("production").split("\n\n", 1)[0]
    generated_csp = next(
        line.split(":", 1)[1].strip()
        for line in generated.splitlines()
        if line.strip().startswith("Content-Security-Policy:")
    )
    return netlify_csp, vercel_csp, generated_csp


class PublicContentSecurityPolicyTests(unittest.TestCase):
    def test_all_public_entrypoints_block_objects_and_agree(self):
        sources = policies()
        for origin, policy in zip(("Netlify", "Vercel", "generated _headers"), sources):
            with self.subTest(origin=origin):
                self.assertEqual(find_object_policy_errors(policy), [])
                self.assertTrue(public_csp_blocks_objects(policy))
        self.assertEqual(sources[0], sources[1])
        self.assertEqual(sources[0], sources[2])

    def test_private_and_preview_routes_remain_separately_protected(self):
        preview = render_standalone_headers("deploy-preview")
        self.assertIn("X-Robots-Tag: noindex, nofollow, noarchive", preview)
        self.assertIn("object-src 'none'", preview)

    def test_adversarial_csp_mutations_are_rejected(self):
        good = policies()[0]
        target = "object-src 'none'"
        self.assertIn(target, good)
        mutants = {
            "self": good.replace(target, "object-src 'self'"),
            "wildcard": good.replace(target, "object-src *"),
            "external": good.replace(target, "object-src https://evil.invalid"),
            "data URI": good.replace(target, "object-src data:"),
            "removed": good.replace(target, ""),
            "duplicate": good + "; object-src 'self'",
            "mixed": good.replace(target, "object-src 'none' 'self'"),
            "no value": good.replace(target, "object-src"),
        }
        for label, broken in mutants.items():
            with self.subTest(case=label):
                self.assertNotEqual(broken, good)
                self.assertTrue(find_object_policy_errors(broken))
                self.assertFalse(public_csp_blocks_objects(broken))

    def test_no_public_policy_allows_active_object(self):
        netlify, vercel, generated = policies()
        for policy in (netlify, vercel, generated):
            directives = policy.split(";")
            self.assertEqual(
                len([item for item in directives if item.strip().startswith("object-src")]), 1
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
