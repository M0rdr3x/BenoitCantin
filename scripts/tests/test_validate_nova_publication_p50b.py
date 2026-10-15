#!/usr/bin/env python3
"""Régressions pour la suspension des formulaires Projet Nova; données fictives."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "validate_nova_publication_p50b.py"
spec = importlib.util.spec_from_file_location("nova_publication", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ValidationPublication(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pages = {
            "participer.html": (
                'contact volontaire, formulaires externes suspendus '
                '<a href="recrutement.html">Participer</a>'
                '<a href="confidentialite.html">Confidentialité</a>'
            ),
            "avis-legal.html": "Le site n’exploite actuellement pas de formulaire externe",
            "recrutement.html": "Aucun paiement; contact volontaire direct",
            "confidentialite.html": "Les formulaires publics externes sont suspendus.",
            "contact.html": (
                '<a href="mailto:officiellenovaparti@gmail.com">Contact</a>'
            ),
        }
        self.reset()

    def tearDown(self):
        self.tmp.cleanup()

    def reset(self):
        for name, content in self.pages.items():
            (self.root/name).write_text(content,encoding="utf-8")

    def modify(self, name, value):
        (self.root/name).write_text(value,encoding="utf-8")

    def add(self, name, text):
        self.modify(name, self.pages[name]+text)

    def test_corpus_minimal_ok(self):
        self.assertEqual(module.validate(self.root), [])

    def test_formulaire_reintroduit(self):
        self.add("contact.html", "<form action='/post'></form>")
        self.assertTrue(module.validate(self.root))

    def test_fournisseur_formspree_detecte(self):
        self.add("participer.html", '<a href="https://formspree.io/f/exemple">Form</a>')
        self.assertTrue(module.validate(self.root))

    def test_fournisseur_formsubmit_detecte(self):
        self.add("contact.html",'<a href="https://formsubmit.co/exemple">Form</a>')
        self.assertTrue(module.validate(self.root))

    def test_google_forms_shortlink_detecte(self):
        self.add("participer.html",'<a href="https://forms.gle/exemple">Form</a>')
        self.assertTrue(module.validate(self.root))

    def test_google_forms_embed_detecte(self):
        self.add("participer.html",'<iframe src="https://docs.google.com/forms/d/e/exemple/viewform"></iframe>')
        self.assertTrue(module.validate(self.root))

    def test_typeform_detecte(self):
        self.add("contact.html",'<a href="https://exemple.typeform.com/to/ABC">Form</a>')
        self.assertTrue(module.validate(self.root))

    def test_jotform_detecte(self):
        self.add("contact.html",'<a href="https://www.jotform.com/form/exemple">Form</a>')
        self.assertTrue(module.validate(self.root))

    def test_stripe_checkout_detecte(self):
        self.add("participer.html",'<a href="https://checkout.stripe.com/c/pay/exemple">Don</a>')
        self.assertTrue(module.validate(self.root))

    def test_stripe_payment_links_detecte(self):
        self.add("participer.html",'<a href="https://buy.stripe.com/exemple">Payer</a>')
        self.assertTrue(module.validate(self.root))

    def test_paypal_donate_detecte(self):
        self.add("recrutement.html",'<a href="https://www.paypal.com/donate?hosted_button_id=exemple">Don</a>')
        self.assertTrue(module.validate(self.root))

    def test_paypal_me_detecte(self):
        self.add("recrutement.html",'<a href="https://paypal.me/exemple">Payer</a>')
        self.assertTrue(module.validate(self.root))

    def test_mailto_commentaire_html_insuffisant(self):
        self.modify("contact.html","<!-- mailto:officiellenovaparti@gmail.com -->")
        self.assertTrue(module.validate(self.root))

    def test_mailto_in_text_only_insufficient(self):
        self.modify("contact.html","Veuillez écrire à mailto:officiellenovaparti@gmail.com")
        self.assertTrue(module.validate(self.root))

    def test_script_fournisseur_externe_detecte(self):
        self.add("contact.html",'<script>const destination="https://forms.gle/exemple";</script>')
        self.assertTrue(module.validate(self.root))

    def test_iframe_non_repertorie_bloque(self):
        self.add("recrutement.html",'<iframe src="https://inconnu.example.org/form"></iframe>')
        self.assertTrue(module.validate(self.root))

    def test_declaration_perimee_detectee(self):
        self.add("participer.html"," qui contient le formulaire intégré de soutien et de préadhésion")
        self.assertTrue(module.validate(self.root))

    def test_metadonnee_perimee_detectee(self):
        self.add("participer.html","Soutenir Projet Nova et accéder au formulaire de recrutement.")
        self.assertTrue(module.validate(self.root))

    def test_ancien_lien_pdf_detecte(self):
        self.add("participer.html",'<a href="visionneuse.html?doc=formulaire-soutien">Ancien PDF</a>')
        self.assertTrue(module.validate(self.root))

    def test_avis_legal_incomplet(self):
        self.modify("avis-legal.html", "Texte sans suspension")
        self.assertTrue(module.validate(self.root))

    def test_canal_contact_absent(self):
        self.modify("contact.html","contact absent")
        self.assertTrue(module.validate(self.root))

    def test_page_absente(self):
        (self.root/"recrutement.html").unlink()
        self.assertTrue(module.validate(self.root))

    def test_suspension_page_participer_absente(self):
        self.modify("participer.html",self.pages["participer.html"].replace("suspendus","ouverts"))
        self.assertTrue(module.validate(self.root))

    def test_commented_out_statut_does_not_count(self):
        self.modify("participer.html",
                    '<!-- contact volontaire, formulaires externes suspendus -->'
                    '<a href="recrutement.html">Participer</a>'
                    '<a href="confidentialite.html">Confidentialité</a>')
        self.assertTrue(module.validate(self.root))

    def test_hote_ressemblant_a_paypal_non_bloque(self):
        self.add("contact.html",'<a href="https://paypal.com.exemple.org/document">Lien neutre</a>')
        self.assertEqual(module.validate(self.root), [])

    def test_reseau_externe_neutre_non_bloque(self):
        self.add("contact.html",'<a href="https://www.electionsquebec.qc.ca">Source officielle</a>')
        self.assertEqual(module.validate(self.root), [])


if __name__=="__main__":
    unittest.main(verbosity=2)
