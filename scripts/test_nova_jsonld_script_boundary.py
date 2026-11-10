#!/usr/bin/env python3
"""Anti-XSS du JSON-LD NOVA; tests sur fichiers temporaires sans réseau.

Une métadonnée HTML peut être écrite sous forme d'entités puis décodée par
html.unescape(). Le texte JSON d'une balise <script> doit empêcher '</script>'.
"""
from __future__ import annotations

import html
import json
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_nova_seo import json_for_html_script, normalize  # noqa: E402


class ScriptReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.script_tags = []
        self.script_text = []
        self._script = False

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.script_tags.append(dict(attrs))
            self._script = True

    def handle_endtag(self, tag):
        if tag == "script":
            self._script = False

    def handle_data(self, data):
        if self._script:
            self.script_text.append(data)


class NovaJsonLdScriptSecurityTests(unittest.TestCase):
    def test_json_round_trip_preserves_public_text(self):
        value = {
            "description": 'Source & texte "qualité" > archive',
            "nested": ["</ScRiPt>", '<img src=x onerror=alert(1)>',
                       "ligne\u2028paragraphe\u2029fin"],
        }
        encoded = json_for_html_script(value)
        self.assertEqual(json.loads(encoded), value)
        self.assertNotIn("<", encoded)
        self.assertNotIn(">", encoded)
        self.assertNotIn("&", encoded)
        self.assertNotIn("\u2028", encoded)
        self.assertNotIn("\u2029", encoded)

    def test_script_breakout_is_never_emitted_literal(self):
        vectors = [
            "</script><script>window.injected=1</script>",
            "</ScRiPt><img src=x onerror=alert(1)>",
            "</SCRIPT><svg/onload=alert(2)>",
            "<script/src=evil></script>",
            "& </script> \u2028 \u2029",
        ]
        for vector in vectors:
            with self.subTest(vector=vector):
                safe = json_for_html_script({"description": vector})
                self.assertNotIn("<", safe)
                self.assertEqual(json.loads(safe)["description"], vector)

    def test_output_page_contains_single_script_and_is_idempotent(self):
        exploit = "</script><script>window.fake=1</script>"
        description = html.escape("Actualité " + exploit, quote=True)
        source = f"""<!doctype html>
<html lang="fr-CA"><head>
<title>Projet NOVA &lt;/script&gt;</title>
<meta name="description" content="{description}">
<link rel="canonical" href="https://www.benoitcantin.com/projets/projet-nova/">
</head><body><main>Contenu public légitime</main></body></html>
"""
        with tempfile.TemporaryDirectory(prefix="nova-jsonld-security-") as directory:
            file = Path(directory) / "index.html"
            file.write_text(source, encoding="utf-8")
            self.assertTrue(normalize(file))
            output = file.read_text("utf-8")
            parsed = ScriptReader()
            parsed.feed(output)
            self.assertEqual(len(parsed.script_tags), 1,
                             "La chaîne hostile a créé une deuxième balise script")
            self.assertEqual(parsed.script_tags[0].get("type"), "application/ld+json")
            self.assertEqual(len(parsed.script_text), 1)
            schema = json.loads(parsed.script_text[0])
            self.assertIn(exploit, schema["description"])
            self.assertIn("</script>", schema["name"])
            self.assertNotIn("<script>window.fake=1</script>", output)
            self.assertIn("Contenu public légitime", output)
            self.assertFalse(normalize(file), "La normalisation doit être idempotente")

    def test_reject_unprotected_serializer_regression(self):
        exploit = "</script><script>window.fake=1</script>"
        unprotected = json.dumps({"description": exploit}, ensure_ascii=False)
        self.assertIn(exploit, unprotected,
                      "La fixture doit prouver la différence avant le correctif")
        protected = json_for_html_script({"description": exploit})
        self.assertNotIn(exploit, protected)

    def test_no_unsafe_inline_serializer_in_source(self):
        source = (ROOT / "scripts/normalize_nova_seo.py").read_text("utf-8")
        self.assertIn("json_for_html_script(schema)", source)
        self.assertNotIn('json.dumps(schema, ensure_ascii=False', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
