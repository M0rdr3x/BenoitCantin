#!/usr/bin/env python3
"""Contrôles de régression pour les 64 identifiants et 140 preuves NOVA."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_nova_compass_source_security import (  # noqa: E402
    inspect, read_corpora, safe_source_url
)


def fixture():
    q = {"questions": [{"id": f"q{i:02d}"} for i in range(1, 65)]}
    e = {"evidenceRecords": [
        {"questionId": "q01", "partyId": "party-01",
         "sourceUrl": "https://example.org/publication?ref=test&lang=fr"}
    ]}
    return q, e


class NovaCompassSourceSecurityTests(unittest.TestCase):
    def test_production_source_snapshot_passes(self):
        self.assertEqual(inspect(*read_corpora()), [])

    def test_baseline_synthetic_passes(self):
        self.assertEqual(inspect(*fixture()), [])

    def test_allow_https_sources(self):
        for good in (
            "https://www.electionsquebec.qc.ca/elections/",
            "https://example.org/publication?lang=fr&ref=public",
            "https://example.org:443/a",
        ):
            with self.subTest(good=good):
                self.assertTrue(safe_source_url(good))

    def test_reject_executable_or_ambiguous_urls(self):
        for bad in (
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:alert(1)", "blob:https://example.org/x",
            "file:///etc/passwd", "http://example.org/source",
            "//example.org/proof", "https://user:pass@example.org/p",
            "https://user@example.org/path", "https://example.org:8080/a",
            "https://example.org:invalid/a", "https://localhost/admin",
            "https://127.0.0.1/admin", "https://[::1]/private",
            "https://example.org\njavascript:alert(1)",
            "https://example.org\\@evil.test/path", "/source",
            " https://example.org", "https://example.org /path",
            "", None, 3, "https://example.org/" + "z" * 2500,
        ):
            with self.subTest(bad=str(bad)[:80]):
                self.assertFalse(safe_source_url(bad))

    def test_reject_html_attribute_injection_question_ids(self):
        for bad in (
            'q01" autofocus onfocus="alert(1)',
            'q01><img src=x onerror=1>',
            "q01' onclick='evil()",
            "<svg/onload=alert(1)>",
            "q01\n",
            1,
            None,
        ):
            with self.subTest(bad=str(bad)):
                q,e=fixture()
                q["questions"][0]["id"]=bad
                self.assertTrue(inspect(q,e))

    def test_refuse_missing_duplicate_and_wrong_question_count(self):
        q,e=fixture()
        q["questions"].pop()
        self.assertTrue(inspect(q,e))
        q,e=fixture()
        q["questions"][1]["id"]="q01"
        self.assertTrue(inspect(q,e))

    def test_reject_duplicate_or_dangerous_proof_binding(self):
        q,e=fixture()
        e["evidenceRecords"].append(dict(e["evidenceRecords"][0]))
        self.assertTrue(inspect(q,e))
        q,e=fixture()
        e["evidenceRecords"][0]["partyId"]='p" onload="alert(1)'
        self.assertTrue(inspect(q,e))
        q,e=fixture()
        e["evidenceRecords"][0]["questionId"]="q99"
        self.assertTrue(inspect(q,e))

    def test_reject_malformed_evidence_url_in_corpus(self):
        q,e=fixture()
        e["evidenceRecords"][0]["sourceUrl"]="javascript:alert(1)"
        errors=inspect(q,e)
        self.assertTrue(errors)
        self.assertFalse(any("alert(1)" in error for error in errors))

    def test_reject_empty_corpus_and_non_dict(self):
        self.assertTrue(inspect([],{}))
        q,e=fixture()
        e["evidenceRecords"]=[]
        self.assertTrue(inspect(q,e))


if __name__ == "__main__":
    unittest.main(verbosity=2)
