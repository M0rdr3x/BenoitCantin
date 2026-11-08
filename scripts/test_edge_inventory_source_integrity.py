#!/usr/bin/env python3
"""Tests synthétiques du garde de lecture des sources Edge, sans secrets."""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from validate_edge_function_inventory import (
    MAX_SOURCE_BYTES,
    UnsafeSource,
    find_edge_calls,
    read_security_text,
    read_tree_text,
    unpinned_supabase_js_versions,
    has_unsanitized_auth_error_log,
    fracture_gateway_body_boundary_valid,
)


class InventorySourceIntegrityTests(unittest.TestCase):
    def test_supabase_js_deps_must_use_exact_versions(self):
        safe = (
            "import { createClient } from 'npm:@supabase/supabase-js@2.119.0';\n"
            "import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.119.0';\n"
        )
        self.assertEqual(unpinned_supabase_js_versions(safe), [])
        for unsafe in ("2", "2.119", "latest", "^2.119.0"):
            with self.subTest(unsafe=unsafe):
                snippet = f"import {{ createClient }} from 'npm:@supabase/supabase-js@{unsafe}';"
                self.assertEqual(unpinned_supabase_js_versions(snippet), [unsafe])
        self.assertEqual(
            unpinned_supabase_js_versions(
                "import 'https://esm.sh/@supabase/supabase-js@2';"
            ),
            ["2"],
        )

    def test_private_auth_errors_are_not_logged_raw(self):
        self.assertTrue(has_unsanitized_auth_error_log("console.warn('auth', error);"))
        self.assertTrue(has_unsanitized_auth_error_log("console.error(error);"))
        self.assertFalse(has_unsanitized_auth_error_log(
            "console.error('[SINJIRA auth]', { code: 'MFA_STATE_UNAVAILABLE' });"
        ))

    def test_fracture_gateway_rejects_unbounded_or_preauth_body(self):
        secure = (
            "const user=await client.auth.getUser(token);\\n"
            "const limited=await readLimitedUtf8Body(req,MAX_BODY_BYTES);\\n"
            "await client.rpc(action,args);\\n"
        )
        self.assertTrue(fracture_gateway_body_boundary_valid(secure))
        for unsafe in (
            secure.replace("await readLimitedUtf8Body(req,MAX_BODY_BYTES)", "await req.text()"),
            secure.replace("await readLimitedUtf8Body(req,MAX_BODY_BYTES)", "await req.json()"),
            secure.replace("await client.auth.getUser(token)", "if(token){}"),
            secure.replace(
                "await client.auth.getUser(token);\\n",
                ""
            ) + "await client.auth.getUser(token);\\n",
            secure.replace(
                "await readLimitedUtf8Body(req,MAX_BODY_BYTES);\\n",
                ""
            ) + "await readLimitedUtf8Body(req,MAX_BODY_BYTES);\\n",
        ):
            with self.subTest(unsafe=unsafe):
                self.assertFalse(fracture_gateway_body_boundary_valid(unsafe))

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

    def test_symlinked_parent_directory_never_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "private"
            real.mkdir()
            (real / "index.ts").write_text("synthetic private source", encoding="utf-8")
            shortcut = root / "functions"
            shortcut.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(UnsafeSource, "symbolique"):
                read_security_text(shortcut / "index.ts")
            with self.assertRaisesRegex(UnsafeSource, "symbolique"):
                read_tree_text(shortcut)

    def test_symlinked_directory_inside_source_tree_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / "external"
            external.mkdir()
            (external / "index.ts").write_text("synthetic external source", encoding="utf-8")
            scanned = root / "scanned"
            scanned.mkdir()
            (scanned / "real.ts").write_text("// normal source", encoding="utf-8")
            (scanned / "redirect").symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(UnsafeSource, "symbolique"):
                read_tree_text(scanned)

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
            with patch("validate_edge_function_inventory.ROOT", root):
                self.assertEqual(len(find_edge_calls([root], "admin-reader")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
