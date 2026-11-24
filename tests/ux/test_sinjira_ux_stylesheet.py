#!/usr/bin/env python3
"""Non-régression des feuilles CSS SINJIRA, chemins relatifs et intégrité locale."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/validate_sinjira_ux_v1.py"
spec = importlib.util.spec_from_file_location("sinjira_ux_contract", SOURCE)
assert spec and spec.loader
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class UxStylesheetPaths(unittest.TestCase):
    def test_local_versioned_paths_are_valid(self):
        samples = [
            ("projets/sinjira/romans/les-cicatrices-du-salut/index.html",
             "/assets/css/site-ux-sinjira-v1.css?v=1.0.1"),
            ("compte/index.html", "../assets/css/site-ux-sinjira-v1.css?v=1.0.0"),
            ("projets/sinjira/romans/index.html",
             "../../../assets/css/site-ux-sinjira-v1.css?v=2.1.11"),
            ("index.html", "assets/css/site-ux-sinjira-v1.css?v=1"),
        ]
        for page, href in samples:
            with self.subTest(page=page, href=href):
                self.assertTrue(contract.is_approved_ux_stylesheet(href, page))

    def test_external_wrong_missing_or_injected_assets_are_rejected(self):
        page = "compte/index.html"
        forbidden = [
            "https://example.invalid/assets/css/site-ux-sinjira-v1.css?v=1.0.0",
            "//example.invalid/assets/css/site-ux-sinjira-v1.css?v=1.0.0",
            "../assets/css/other.css?v=1.0.0",
            "../assets/css/site-ux-sinjira-v1.css",
            "../assets/css/site-ux-sinjira-v1.css?v=abc",
            "../assets/css/site-ux-sinjira-v1.css?v=1.0.0&debug=1",
            "../assets/css/site-ux-sinjira-v1.css?v=1.0.0#incorrect",
            "/assets/css/site-ux-sinjira-v1.css?v=1.0.0/evil",
        ]
        for href in forbidden:
            with self.subTest(href=href):
                self.assertFalse(contract.is_approved_ux_stylesheet(href, page))


if __name__ == "__main__":
    unittest.main(verbosity=2)
