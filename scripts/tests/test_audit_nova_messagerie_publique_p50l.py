"""P50L: tests documentaires sans réseau, sans messagerie ni données personnelles."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "scripts/audit_nova_messagerie_publique_p50l.py"
MODEL_FILE = ROOT / "projets/projet-nova/controles/P50L_REGISTRE_PUBLIC_12_VERIFICATIONS.json"
s = importlib.util.spec_from_file_location("p50l", PY)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
MODEL = json.loads(MODEL_FILE.read_text(encoding="utf-8"))

def basic(content, links=""):
    return "<!DOCTYPE html><html><body><main>" + content + links + "</main></body></html>"

class TestP50L(unittest.TestCase):
    def template(self):
        return copy.deepcopy(MODEL)

    def test_model_initially_valid_and_empty(self):
        self.assertEqual(m.inspect_model(self.template()), [])
        self.assertEqual(len(MODEL["requirements"]), 12)

    def test_cannot_claim_mailbox_access(self):
        x = self.template(); x["constraints"]["inbox_read"] = True
        self.assertIn("PREUVE_OU_ACCES_REEL_FAUSSEMENT_ATTESTE", m.inspect_model(x))

    def test_cannot_claim_emails_exported(self):
        x = self.template(); x["constraints"]["messages_collected"] = 1
        self.assertIn("PREUVE_OU_ACCES_REEL_FAUSSEMENT_ATTESTE", m.inspect_model(x))

    def test_cannot_claim_legal_efvp(self):
        x = self.template(); x["constraints"]["formal_efvp_signed"] = True
        self.assertIn("PREUVE_OU_ACCES_REEL_FAUSSEMENT_ATTESTE", m.inspect_model(x))

    def test_cannot_claim_deployment(self):
        x = self.template(); x["constraints"]["deployment_proven"] = True
        self.assertIn("PREUVE_OU_ACCES_REEL_FAUSSEMENT_ATTESTE", m.inspect_model(x))

    def test_cannot_change_no_go(self):
        x = self.template(); x["decision"] = "GO"
        self.assertIn("AUTORISATION_INTERDITE", m.inspect_model(x))

    def test_cannot_delete_pr640_guard(self):
        x = self.template(); x["frozen_guards"].remove("NE_PAS_FUSIONNER_PR_640")
        self.assertIn("GARDE_FOU_MANQUANT", m.inspect_model(x))

    def test_cannot_fake_requirement(self):
        x = self.template(); x["requirements"][0]["state"] = "VALIDE"
        self.assertIn("EXIGENCE_FAUSSEMENT_ATTESTEE_M01", m.inspect_model(x))

    def test_missing_requirement_detected(self):
        x = self.template(); x["requirements"].pop()
        self.assertIn("EXIGENCES_INCOMPLETES", m.inspect_model(x))

    def test_mailto_count_but_address_never_returned(self):
        html = basic("Contact", '<a href="mailto:exemple@example.invalid">Écrire</a>')
        r = m.inspect_page("contact.html", html)
        self.assertEqual(r["liens_courriel_compte"], 1)
        self.assertNotIn("exemple", json.dumps(r))
        self.assertFalse(r["preuve_de_fonctionnement_messagerie"])

    def test_legacy_preadhesion_is_editorial_alert_not_a_form(self):
        html = basic("Participation citoyenne, formulaire intégré de soutien et de préadhésion")
        r = m.inspect_page("participer.html", html)
        self.assertTrue(r["alerte_redactionnelle"])
        self.assertFalse(r["alerte_surface_technique"])
        self.assertEqual(r["balises_formulaire_compte"], 0)

    def test_legal_legacy_copy(self):
        html = basic("Projet Nova. Les formulaires servent uniquement à communiquer avec le Projet Nova")
        self.assertTrue(m.inspect_page("avis-legal.html", html)["alerte_redactionnelle"])

    def test_form_tag_detected(self):
        html = basic("Contact", '<form action="/post"></form>')
        r = m.inspect_page("contact.html", html)
        self.assertTrue(r["alerte_surface_technique"])
        self.assertEqual(r["balises_formulaire_compte"], 1)

    def test_external_form_detected(self):
        html = basic("Contact", '<a href="https://formspree.io/f/sample">Cliquez</a>')
        r = m.inspect_page("contact.html", html)
        self.assertEqual(r["liens_vers_formulaires_externes_compte"], 1)

    def test_payment_link_detected(self):
        html = basic("Contact", '<a href="https://checkout.stripe.com/example">Payez</a>')
        self.assertTrue(m.inspect_page("contact.html", html)["alerte_surface_technique"])

    def test_read_only_report_always_no_go_even_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "projets/projet-nova"
            p.mkdir(parents=True)
            for name in m.PAGES:
                (p / name).write_text(basic(m.REQUIRED[name][0]), encoding="utf-8")
            out = m.run(tmp, self.template())
            self.assertEqual(out["verification_executable"], "OK_LECTURE_SEULE")
            self.assertEqual(out["decision"], "NO_GO_AUTOMATIQUE")
            self.assertFalse(out["messagerie_effectivement_auditee"])

    def test_missing_public_page_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = m.run(tmp, self.template())
            self.assertEqual(out["verification_executable"], "INCOMPLETE_OU_INVALIDE")
            self.assertEqual(len(out["pages_absentes"]), 5)
            self.assertEqual(out["decision"], "NO_GO_AUTOMATIQUE")

    def test_missing_model_fails_closed(self):
        self.assertEqual(m.inspect_model(None), ["MODELE_ABSENT_OU_INVALIDE"])


if __name__ == "__main__":
    unittest.main()
