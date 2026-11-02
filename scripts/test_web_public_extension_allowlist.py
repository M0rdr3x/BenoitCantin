#!/usr/bin/env python3
"""Independent regression test for public-artifact file type confinement.

Executes the real builder's allowlist policy; no network access, deployments,
secrets or modification of production files. Run with Python 3.12.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_netlify_public.py"
spec = importlib.util.spec_from_file_location("sinjira_public_builder", BUILDER)
assert spec is not None and spec.loader is not None
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PublicArtifactExtensionAllowlist(unittest.TestCase):
    def test_unreviewed_nested_sources_archives_exports_not_published(self):
        for directory in (
            "assets", "projets/sinjira/romans", "projets/sinjira/logiciels",
            "projets/sinjira/jeux", "projets/autre-projet",
        ):
            for filename in (
                "sauvegarde.zip", "bundle.7z", "full-source.tar.gz",
                "secrets.json", "reponses.csv", "README.md", "notes.txt",
                "source.ts", "interface.tsx", "bootstrap.sh", "setup.ps1",
                "config.ini", "dependencies.lock", "app.php",
                "batch.cmd", "Makefile",
            ):
                with self.subTest(directory=directory, filename=filename):
                    self.assertFalse(builder.relative_path_allowed(Path(directory) / filename))

    def test_published_runtime_still_allowed(self):
        for name in (
            "assets/js/site.js", "assets/css/ai-transparency.css",
            "projets/sinjira/romans/index.html",
            "projets/sinjira/jeux/game.mjs", "projets/sinjira/logiciels/demo.webp",
            "projets/projet-nova/index.html", "compte/index.html", "admin/index.html",
            "projets/sinjira/jeux/illustration.svg",
        ):
            with self.subTest(path=name):
                self.assertTrue(builder.relative_path_allowed(Path(name)))

    def test_explicitly_approved_documents_remain_available(self):
        for name in (
            "projets/projet-nova/data/boussole-partis-2026.json",
            "projets/projet-nova/data/sources.json",
            "projets/projet-nova/official/reference/programme.md",
            "projets/projet-nova/PROPOSITIONS_PUBLIQUES.md",
            "projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf",
        ):
            with self.subTest(path=name):
                self.assertTrue(builder.relative_path_allowed(Path(name)))

    def test_unapproved_public_data_and_private_pdfs_are_denied(self):
        for name in (
            "projets/projet-nova/data/sondage-individuel.json",
            "projets/projet-nova/data/votes-bruts.csv",
            "projets/projet-nova/official/versions/V400/private-state.json",
            "projets/sinjira/romans/Livre-I-complet.pdf",
            "projets/sinjira/documents/Livre-I-edition-privee.pdf",
            "assets/diagnostics.js.map",
        ):
            with self.subTest(path=name):
                self.assertFalse(builder.relative_path_allowed(Path(name)))

    def test_only_public_document_extensions_are_privileged(self):
        self.assertEqual(builder.PUBLIC_APPROVED_PDFS & builder.SINJIRA_PUBLIC_DOCUMENTS,
                         builder.SINJIRA_PUBLIC_DOCUMENTS)
        self.assertTrue(all(p.suffix.lower() == ".pdf" for p in builder.PUBLIC_APPROVED_PDFS))
        self.assertFalse(any(ext in builder.RUNTIME_WEB_SUFFIXES for ext in (
            ".zip", ".7z", ".rar", ".tar", ".gz", ".csv", ".json",
            ".md", ".txt", ".ts", ".tsx", ".sh", ".php", ".lock",
        )))


if __name__ == "__main__":
    unittest.main(verbosity=2)
