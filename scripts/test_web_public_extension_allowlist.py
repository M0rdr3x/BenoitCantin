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
    def test_hidden_root_files_never_inherit_browser_extension_allowlist(self):
        # A dotfile is not public simply because it ends in .html/.js/.css.
        # Check the real policy used by both build and preflight.
        for name in (
            ".credentials.html", ".secrets.js", ".internal.css",
            ".debug.mjs", ".private.webp", ".HIDDEN.JS",
            ".hidden.webmanifest", ".env.html", ".env.production.js",
        ):
            with self.subTest(path=name):
                self.assertFalse(builder.root_file_allowed(ROOT / name))
                self.assertFalse(builder.relative_path_allowed(Path(name)))

        # Only the known Jekyll marker is an approved root dotfile.
        self.assertTrue(builder.root_file_allowed(ROOT / ".nojekyll"))
        self.assertTrue(builder.relative_path_allowed(Path(".nojekyll")))
        self.assertTrue(builder.root_file_allowed(ROOT / "index.html"))
        self.assertTrue(builder.root_file_allowed(ROOT / "robots.txt"))
        self.assertTrue(builder.root_file_allowed(ROOT / "CNAME"))

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

    def test_nova_data_default_denies_unreviewed_formats_and_subdirectories(self):
        for name in (
            "sauvegarde.html", "diagnostic.js", "image.svg",
            "rapport-confidentiel.pdf", "donnees.xml", "interne.webp",
            "reponses.json", "exports.csv", "subdir/fuite.html",
            "subdir/fuite.pdf", "subdir/extra.json",
        ):
            with self.subTest(filename=name):
                self.assertFalse(builder.relative_path_allowed(
                    Path("projets/projet-nova/data") / name
                ))
        self.assertEqual(len(builder.PROJECT_NOVA_PUBLIC_DATA_JSON), 12)
        for expected_public in builder.PROJECT_NOVA_PUBLIC_DATA_JSON:
            with self.subTest(path=expected_public):
                self.assertTrue(builder.relative_path_allowed(expected_public))

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
        ):
            with self.subTest(path=name):
                self.assertTrue(builder.relative_path_allowed(Path(name)))

    def test_unapproved_public_data_and_private_pdfs_are_denied(self):
        for name in (
            "projets/projet-nova/data/sondage-individuel.json",
            "projets/projet-nova/data/votes-bruts.csv",
            "projets/projet-nova/official/versions/V400/private-state.json",
            "projets/sinjira/romans/Livre-I-complet.pdf",
            "projets/sinjira/romans/SINJIRA_ROMAN_04_LES_CICATRICES_DU_SALUT.pdf",
            "projets/sinjira/romans/roman-4-release.json",
            "projets/sinjira/romans/SINJIRA_ROMAN_04_LES_CICATRICES_DU_SALUT.epub",
            "projets/sinjira/documents/Livre-I-edition-privee.pdf",
            "projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf",
            "assets/diagnostics.js.map",
        ):
            with self.subTest(path=name):
                self.assertFalse(builder.relative_path_allowed(Path(name)))

    def test_restricted_catalog_pdfs_are_not_publicly_published(self):
        # Les quatre URL recoupees en lecture seule avec le catalogue prive
        # sont exclues, y compris celle dont le document reste "approved".
        quarantine = builder.PUBLIC_QUARANTINED_RESTRICTED_PDFS
        self.assertEqual(len(quarantine), 4)
        self.assertEqual(quarantine & builder.PUBLIC_APPROVED_PDFS, set())
        self.assertTrue(all(path.suffix == ".pdf" for path in quarantine))
        for path in sorted(quarantine):
            with self.subTest(path=path.name):
                self.assertFalse(builder.relative_path_allowed(path))
        # La cinquieme fiche publique, sans correspondance restreinte dans
        # l'inventaire du 2026-11-21, demeure utilisable.
        public_copy = Path(
            "projets/sinjira/jeux/fracture-du-reseau-mere/documents/"
            "SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf"
        )
        self.assertTrue(builder.relative_path_allowed(public_copy))
        self.assertTrue(builder.relative_path_allowed(Path("compte/index.html")))

    def test_readding_quarantined_pdf_to_public_allowlist_fails_closed(self):
        old = builder.PUBLIC_APPROVED_PDFS
        try:
            builder.PUBLIC_APPROVED_PDFS = set(old)
            builder.PUBLIC_APPROVED_PDFS.add(
                sorted(builder.PUBLIC_QUARANTINED_RESTRICTED_PDFS)[0]
            )
            self.assertFalse(builder.relative_path_allowed(
                sorted(builder.PUBLIC_QUARANTINED_RESTRICTED_PDFS)[0]
            ))
            errors = builder.validate_plan()
            self.assertTrue(any("Conflit entre PDF publics" in item for item in errors))
        finally:
            builder.PUBLIC_APPROVED_PDFS = old

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
