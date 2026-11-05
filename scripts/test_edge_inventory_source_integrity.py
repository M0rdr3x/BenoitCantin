#!/usr/bin/env python3
"""Tests synthétiques du garde de lecture des sources Edge, sans secrets."""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from validate_edge_function_inventory import (
    MAX_SOURCE_BYTES,
    UnsafeSource,
    find_edge_calls,
    read_security_text,
    read_tree_text,
)


class InventorySourceIntegrityTests(unittest.TestCase):
    def test_utf8_source_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.ts"
            path.write_text("// sécurité vérifiée\n", encoding="utf-8")
            self.assertIn("sécurité", read_security_text(path))

    def test_invalid_utf8_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.ts"
            path.write_bytes(b"// guard\xff")
            with self.assertRaisesRegex(UnsafeSource, "UTF-8 invalide"):
                read_security_text(path)
            with self.assertRaises(UnsafeSource):
                read_tree_text(Path(directory))

    def test_binary_nul_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.ts"
            path.write_bytes(b"// synthetique\x00pass")
            with self.assertRaisesRegex(UnsafeSource, "NUL"):
                read_security_text(path)

    def test_oversized_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.ts"
            with path.open("wb") as output:
                output.truncate(MAX_SOURCE_BYTES + 1)
            with self.assertRaisesRegex(UnsafeSource, "volumineux"):
                read_security_text(path)

    def test_symlink_never_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside.txt"
            outside.write_text("synthetic private fixture", encoding="utf-8")
            tracked = root / "index.ts"
            tracked.symlink_to(outside)
            with self.assertRaisesRegex(UnsafeSource, "symbolique"):
                read_security_text(tracked)
            with self.assertRaises(UnsafeSource):
                read_tree_text(root)
            self.assertEqual(outside.read_text("utf-8"), "synthetic private fixture")

    def test_retired_edge_call_search_fails_on_corrupted_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "page.html").write_bytes(b"untrusted\xff/functions/v1/admin-reader")
            with self.assertRaisesRegex(UnsafeSource, "UTF-8 invalide"):
                find_edge_calls([root], "admin-reader")

    def test_retired_edge_call_search_detects_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "page.html").write_text(
                '<a href="/functions/v1/admin-reader">call</a>', encoding="utf-8"
            )
            self.assertEqual(len(find_edge_calls([root], "admin-reader")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
