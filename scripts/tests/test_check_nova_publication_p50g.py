"""Contrôles P50G sans réseau; les succès ne valent jamais GO."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

src=Path(__file__).resolve().parents[1]/"check_nova_publication_p50g.py"
spec=importlib.util.spec_from_file_location("p50g",src)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class TestsP50G(unittest.TestCase):
    def make_page(self,page):
        return '<!doctype html><main>'+m.REQUIRED[page]+'</main>'
    def test_six_pages_saines(self):
        for page in m.PAGES:
            self.assertEqual(m.inspect(page,self.make_page(page))["statut"],"OK_STATIQUE")
    def test_formulaire_interdit(self):
        h=self.make_page("recrutement.html")+'<form action="/envoi"></form>'
        self.assertIn("FORMULAIRE_PRESENT",m.inspect("recrutement.html",h)["ecarts"])
    def test_endpoint_tiers_interdit(self):
        h=self.make_page("contact.html")+'<iframe src="https://formspree.io/f/abc"></iframe>'
        self.assertIn("COLLECTE_OU_PAIEMENT_EXTERNE",m.inspect("contact.html",h)["ecarts"])
    def test_script_tiers_interdit(self):
        h=self.make_page("contact.html")+'<script>fetch("https://formspree.io/f/abc")</script>'
        self.assertIn("COLLECTE_OU_PAIEMENT_EXTERNE",m.inspect("contact.html",h)["ecarts"])
    def test_mentions_anciennes_interdites(self):
        p="participer.html"
        h=self.make_page(p)+m.OLD[p]
        self.assertIn("MENTION_OBSOLETE",m.inspect(p,h)["ecarts"])
    def test_manquants_non_valides(self):
        with tempfile.TemporaryDirectory() as d:
            r=m.report(d)
            self.assertEqual(r["controle_statique"],"ECART_OU_INDETERMINE")
            self.assertFalse(r["deploiement_confirme"])
            self.assertEqual(r["decision_publication"],"NO_GO_AUTOMATIQUE")
    def test_source_conforme_ne_donne_jamais_go(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);site=root/"projets"/"projet-nova";site.mkdir(parents=True)
            for p in m.PAGES: (site/p).write_text(self.make_page(p),encoding="utf-8")
            (site/"VERIFICATION_AVANT_PUBLICATION.md").write_text(
                "Les formulaires externes demeurent suspendus. NE PAS FUSIONNER la PR 640.",encoding="utf-8")
            r=m.report(root)
            self.assertEqual(r["controle_statique"],"OK")
            self.assertEqual(r["decision_publication"],"NO_GO_AUTOMATIQUE")
            self.assertFalse(r["autorisation_juridique_confirmee"])

if __name__=="__main__": unittest.main()
