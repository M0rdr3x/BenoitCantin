"""P50J — tests à données strictement fictives, sans réseau ni collecte réelle."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "scripts/validate_nova_preuves_p50j.py"
MODEL = ROOT / "projets/projet-nova/controles/P50J_MODELE_PUBLIC_PREUVES.json"
spec = importlib.util.spec_from_file_location("nova_p50j", TOOL)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FIXTURE = json.loads(MODEL.read_text(encoding="utf-8"))


class TestP50J(unittest.TestCase):
    def clean(self):
        return copy.deepcopy(FIXTURE)

    def check(self, v):
        return module.inspect_public_template(v)

    def test_clean_public_model_valid(self):
        self.assertEqual(self.check(self.clean())["structure"], "VALIDE_MODELE_SEULEMENT")

    def test_nine_empty_families(self):
        model = self.clean()
        self.assertEqual(len(model["preuves"]), 9)
        self.assertTrue(all(x["statut"] == "NON_RECU" for x in model["preuves"]))

    def test_no_go_even_if_model_valid(self):
        self.assertEqual(self.check(self.clean())["decision"], "NO_GO_AUTOMATIQUE")

    def test_go_forgery_rejected(self):
        m = self.clean(); m["decision"] = "GO"
        self.assertIn("DECISION_PUBLIQUE_NON_AUTORISEE", self.check(m)["problemes"])

    def test_cannot_claim_repository_holds_evidence(self):
        m = self.clean(); m["pieces_recues"] = 1
        self.assertIn("PIECES_DECLAREES_RECUES", self.check(m)["problemes"])

    def test_cannot_claim_verified_proofs(self):
        m = self.clean(); m["pieces_verifiees"] = 9
        self.assertIn("PIECES_DECLAREES_VERIFIEES", self.check(m)["problemes"])

    def test_cannot_enable_vault_without_authority(self):
        m = self.clean(); m["coffre_prive_deploye"] = True
        self.assertIn("ACTIVATION_OU_ATTESTATION_INTERDITE", self.check(m)["problemes"])

    def test_cannot_enable_form(self):
        m = self.clean(); m["formulaires_externes_actifs"] = True
        self.assertEqual(self.check(m)["structure"], "INVALIDE")

    def test_cannot_claim_party_authorization(self):
        m = self.clean(); m["autorisation_electorale_attestee"] = True
        self.assertEqual(self.check(m)["structure"], "INVALIDE")

    def test_pr640_guard_required(self):
        m = self.clean(); m["verrous"].remove("PR_640_NE_PAS_FUSIONNER")
        self.assertIn("VERROUS_INCOMPLETS", self.check(m)["problemes"])

    def test_no_public_private_reference(self):
        m = self.clean(); m["preuves"][0]["reference_privee"] = "EV-EXAMPLE987"
        self.assertIn("PREUVE_PUBLIQUE_NON_VIDE_Q01", self.check(m)["problemes"])

    def test_reject_real_person_field_in_model(self):
        m = self.clean(); m["preuves"][0]["courriel_personnel"] = "test@example.com"
        self.assertIn("PREUVE_PUBLIQUE_NON_VIDE_Q01", self.check(m)["problemes"])

    def test_extra_root_key_rejected(self):
        m = self.clean(); m["raw_file"] = "sensitive.zip"
        self.assertIn("CHAMPS_RACINE_NON_CONFORMES", self.check(m)["problemes"])

    def test_duplicate_family_rejected(self):
        m = self.clean(); m["preuves"][1] = dict(m["preuves"][0])
        self.assertIn("CODE_DUPLIQUE_OU_INCONNU", self.check(m)["problemes"])

    def test_missing_family_rejected(self):
        m = self.clean(); m["preuves"].pop()
        self.assertIn("FAMILLES_MANQUANTES", self.check(m)["problemes"])

    def test_initial_receipt_requires_all_guards(self):
        r = module.simulate_transition("NON_RECU", "RECU_ISOLE", {})
        self.assertEqual(r["transition_theorique"], "REFUSEE")
        self.assertEqual(r["decision"], "NO_GO_AUTOMATIQUE")

    def test_qualified_synthetic_receipt_not_real_approval(self):
        r = module.simulate_transition("NON_RECU", "RECU_ISOLE", {
            "canal_reel_autorise": True, "qualification_juridique_confirmee": True,
            "mandat_reception_verifie": True,
        })
        self.assertEqual(r["transition_theorique"], "AUTORISEE_SUR_DONNEES_FICTIVES")
        self.assertFalse(r["preuve_authentifiee"])
        self.assertEqual(r["decision"], "NO_GO_AUTOMATIQUE")

    def test_verification_cannot_skip_two_independent_reviews(self):
        guards = dict.fromkeys(module.REQUIRED_GUARDS[("EN_VERIFICATION", "VERIFIE_HORS_DEPOT")], True)
        guards["deux_revues_independantes"] = False
        self.assertEqual(
            module.simulate_transition("EN_VERIFICATION", "VERIFIE_HORS_DEPOT", guards)["transition_theorique"],
            "REFUSEE",
        )

    def test_valid_synthetic_verification_still_no_go(self):
        guards = dict.fromkeys(module.REQUIRED_GUARDS[("EN_VERIFICATION", "VERIFIE_HORS_DEPOT")], True)
        r = module.simulate_transition("EN_VERIFICATION", "VERIFIE_HORS_DEPOT", guards)
        self.assertEqual(r["transition_theorique"], "AUTORISEE_SUR_DONNEES_FICTIVES")
        self.assertFalse(r["preuve_authentifiee"])

    def test_expired_evidence_cannot_reactivate(self):
        r = module.simulate_transition("EXPIRE", "EN_VERIFICATION",
                                       {"incident_resolu": True})
        self.assertIn("ETAT_TERMINAL_NOUVELLE_REFERENCE", r["problemes"])
        self.assertEqual(r["transition_theorique"], "REFUSEE")

    def test_revoked_evidence_cannot_reactivate(self):
        r = module.simulate_transition("REVOQUE", "VERIFIE_HORS_DEPOT", {})
        self.assertEqual(r["transition_theorique"], "REFUSEE")

    def test_rejected_evidence_cannot_self_approve(self):
        r = module.simulate_transition("REJETE", "VERIFIE_HORS_DEPOT", {})
        self.assertEqual(r["transition_theorique"], "REFUSEE")

    def test_suspended_evidence_requires_documented_recovery(self):
        r = module.simulate_transition("SUSPENDU", "EN_VERIFICATION", {
            "incident_resolu": True, "mandat_valide": True,
        })
        self.assertEqual(r["transition_theorique"], "REFUSEE")

    def test_missing_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/"missing.json"
            result = Path(tmp)/"result.json"
            self.assertEqual(module.main(["--registre", str(src), "--rapport", str(result)]), 2)
            self.assertEqual(json.loads(result.read_text())["decision"], "NO_GO_AUTOMATIQUE")


if __name__ == "__main__":
    unittest.main()
