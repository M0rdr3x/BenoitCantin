"""P50I : tests de non-contournement, sans réseau et sans publication."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/validate_nova_qualification_p50i.py"
REGISTRY_PATH = ROOT / "projets/projet-nova/controles/P50I_REGISTRE_PUBLIC_QUALIFICATION.json"
spec = importlib.util.spec_from_file_location("p50i", MODULE_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
MODEL = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

class TestP50I(unittest.TestCase):
    def fresh(self):
        return copy.deepcopy(MODEL)

    def test_public_template_is_structurally_valid(self):
        report = validator.inspect(self.fresh())
        self.assertEqual(report["structure"], "VALIDE_MODELE_SEULEMENT")
        self.assertEqual(report["preuves_presentes"], 9)

    def test_never_authorizes_publication(self):
        report = validator.inspect(self.fresh())
        self.assertEqual(report["decision"], "NO_GO_AUTOMATIQUE")
        self.assertEqual(report["preuves_authentifiees"], 0)

    def test_marking_opaque_evidence_does_not_grant_go(self):
        data = self.fresh()
        data["preuves"][0].update(statut="VERIFIE_HORS_DEPOT",
            reference_opaque="EV-ABCDEFG123",date_verification="2026-10-14")
        report = validator.inspect(data)
        self.assertEqual(report["structure"], "VALIDE_MODELE_SEULEMENT")
        self.assertFalse(report["habilitations_confirmees"])
        self.assertEqual(report["decision"], "NO_GO_AUTOMATIQUE")

    def test_cannot_mark_as_authorized_party(self):
        data = self.fresh(); data["autorisation_electorale"] = "OUI"
        self.assertIn("AFFIRMATION_INCOMPATIBLE_AUTORISATION_ELECTORALE",
                      validator.inspect(data)["anomalies"])

    def test_cannot_claim_go(self):
        data = self.fresh(); data["decision"]["statut"] = "GO"
        self.assertIn("DECISION_INCOMPATIBLE", validator.inspect(data)["anomalies"])

    def test_cannot_claim_collecting_signatures(self):
        data = self.fresh(); data["verrous"].remove("AUCUNE_COLLECTE_DE_SIGNATURES_PAR_CE_JALON")
        self.assertIn("VERROUS_INCOMPLETS", validator.inspect(data)["anomalies"])

    def test_cannot_authorize_fundraising(self):
        data = self.fresh(); data["financement_officiel"]="AUTORISE"
        self.assertEqual(validator.inspect(data)["structure"], "INVALIDE")

    def test_cannot_turn_on_forms(self):
        data=self.fresh(); data["collecte_formulaires"]="ACTIVE"
        self.assertIn("AFFIRMATION_INCOMPATIBLE_COLLECTE_FORMULAIRES",
                      validator.inspect(data)["anomalies"])

    def test_missing_proof_is_rejected(self):
        data=self.fresh();data["preuves"].pop()
        self.assertIn("NEUF_PREUVES_INCOMPLETES",validator.inspect(data)["anomalies"])

    def test_duplicate_proof_is_rejected(self):
        data=self.fresh();data["preuves"][0]["id"]="Q02"
        self.assertIn("ID_INVALIDE_OU_DOUBLE",validator.inspect(data)["anomalies"])

    def test_real_person_fields_are_prohibited(self):
        data=self.fresh();data["preuves"][0]["date_naissance"]="2000-01-01"
        self.assertIn("CHAMP_SENSIBLE_INTERDIT",validator.inspect(data)["anomalies"])

    def test_external_fake_source_is_rejected(self):
        data=self.fresh();data["sources_officielles"][0]["url"]="https://example.com/autorisation"
        self.assertIn("URL_SOURCE_INVALIDE",validator.inspect(data)["anomalies"])

    def test_verification_without_reference_rejected(self):
        data=self.fresh();data["preuves"][0]["statut"]="VERIFIE_HORS_DEPOT"
        anomalies=validator.inspect(data)["anomalies"]
        self.assertIn("REFERENCE_NON_VALIDABLE_Q01",anomalies)
        self.assertIn("DATE_INVALIDE_Q01",anomalies)

    def test_unproven_scenario_cannot_be_declared_real(self):
        data=self.fresh();data["scenarios"][3]["fait_etabli"]=True
        self.assertIn("SCENARIOS_NON_PROBANTS",validator.inspect(data)["anomalies"])

    def test_explicit_action_is_blocked(self):
        data=self.fresh();data["actes_autorises_par_ce_modele"]=["SOLLICITER"]
        self.assertIn("ACTE_AUTORISE_INTERDIT",validator.inspect(data)["anomalies"])

    def test_missing_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            missing=Path(folder)/"not-here.json"
            output=Path(folder)/"output.json"
            self.assertEqual(validator.main(["--registre",str(missing),"--rapport",str(output)]),2)
            self.assertEqual(json.loads(output.read_text())["decision"],"NO_GO_AUTOMATIQUE")

if __name__ == "__main__":
    unittest.main()
