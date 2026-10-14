"""P50K — Contrôles du modèle public, tests synthétiques uniquement."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate_nova_pre_efvp_p50k.py"
MODEL = ROOT / "projets/projet-nova/controles/P50K_REGISTRE_PUBLIC_PRE_EFVP.json"
spec = importlib.util.spec_from_file_location("p50k", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BASE = json.loads(MODEL.read_text(encoding="utf-8"))


class TestP50K(unittest.TestCase):
    def fresh(self):
        return copy.deepcopy(BASE)

    def check(self, model):
        return module.inspect(model)

    def assert_invalid(self, model, expected):
        r = self.check(model)
        self.assertEqual(r["statut_structure"], "INVALIDE")
        self.assertIn(expected, r["anomalies"])
        self.assertEqual(r["decision"], "NO_GO_AUTOMATIQUE")

    def test_template_syntax(self):
        r = self.check(self.fresh())
        self.assertEqual(r["statut_structure"], "MODELE_VALIDE_SANS_PREUVE")

    def test_four_flows(self):
        self.assertEqual(len(self.fresh()["flux"]), 4)

    def test_fourteen_unknown_risks(self):
        risks = self.fresh()["risques"]
        self.assertEqual(len(risks), 14)
        self.assertTrue(all(r["risque_residuel"] == "INCONNU" for r in risks))

    def test_twelve_vendor_gates_unevaluated(self):
        c = self.fresh()["prestataires"]["criteres"]
        self.assertEqual(len(c), 12)
        self.assertTrue(all(x["etat"] == "NON_EVALUE" for x in c))

    def test_no_go_even_when_valid(self):
        r = self.check(self.fresh())
        self.assertEqual(r["decision"], "NO_GO_AUTOMATIQUE")
        self.assertFalse(r["efvp_reellement_realisee"])

    def test_cannot_claim_completed_efvp(self):
        m = self.fresh(); m["evaluation_efvp"] = "REALISEE"
        self.assert_invalid(m, "VALEUR_INTERDITE_EVALUATION_EFVP")

    def test_cannot_claim_legal_review(self):
        m = self.fresh(); m["revision_juridique"] = "ATTESTEE"
        self.assert_invalid(m, "VALEUR_INTERDITE_REVISION_JURIDIQUE")

    def test_cannot_claim_compliance_officer(self):
        m = self.fresh(); m["responsable_habilite"] = "NOMME"
        self.assert_invalid(m, "VALEUR_INTERDITE_RESPONSABLE_HABILITE")

    def test_cannot_turn_on_vault(self):
        m = self.fresh(); m["coffre"] = "ACTIF"
        self.assert_invalid(m, "VALEUR_INTERDITE_COFFRE")

    def test_cannot_claim_mail_audited(self):
        m = self.fresh(); m["courriel_existant"] = "CONFORME"
        self.assert_invalid(m, "VALEUR_INTERDITE_COURRIEL_EXISTANT")

    def test_cannot_claim_mail_flow_verified(self):
        m = self.fresh(); m["flux"][0]["traitements_reels_verifies"] = True
        self.assert_invalid(m, "FLUX_FAUSSEMENT_CERTIFIE_F01")

    def test_cannot_pretend_vault_live(self):
        m = self.fresh(); m["flux"][1]["statut"] = "ACTIF"
        self.assert_invalid(m, "FLUX_FAUSSEMENT_CERTIFIE_F02")

    def test_cannot_score_inherent_risk_without_evidence(self):
        m = self.fresh(); m["risques"][0]["probabilite"] = "FAIBLE"
        self.assert_invalid(m, "RISQUE_FAUSSEMENT_EVALUE_R01")

    def test_cannot_accept_residual_risk_automatically(self):
        m = self.fresh(); m["risques"][1]["risque_residuel"] = "ACCEPTABLE"
        self.assert_invalid(m, "RISQUE_FAUSSEMENT_EVALUE_R02")

    def test_cannot_claim_control_implemented(self):
        m = self.fresh(); m["risques"][3]["controle_effectif_atteste"] = True
        self.assert_invalid(m, "RISQUE_FAUSSEMENT_EVALUE_R04")

    def test_cannot_insert_real_evidence_reference(self):
        m = self.fresh(); m["risques"][0]["preuve_publique"] = "real-person-dossier"
        self.assert_invalid(m, "RISQUE_FAUSSEMENT_EVALUE_R01")

    def test_cannot_select_vendor(self):
        m = self.fresh(); m["prestataires"]["selection_effectuee"] = True
        self.assert_invalid(m, "PRESTATAIRE_FAUSSEMENT_VALIDE")

    def test_cannot_insert_vendor_name(self):
        m = self.fresh(); m["prestataires"]["nom_prestataire"] = "exemple fournisseur"
        self.assert_invalid(m, "PRESTATAIRE_FAUSSEMENT_VALIDE")

    def test_cannot_mark_criterion_valid(self):
        m = self.fresh(); m["prestataires"]["criteres"][0]["etat"] = "DEMONTRÉ_HORS_DEPOT"
        self.assert_invalid(m, "CRITERE_FAUSSEMENT_VALIDE_V01")

    def test_missing_criterion(self):
        m = self.fresh(); m["prestataires"]["criteres"].pop()
        self.assert_invalid(m, "CRITERES_INCOMPLETS")

    def test_duplicate_risk(self):
        m = self.fresh(); m["risques"][1]["id"] = "R01"
        self.assert_invalid(m, "RISQUE_DOUBLE_OU_INCONNU")

    def test_pr640_guard_immutable(self):
        m = self.fresh(); m["blocs"].remove("NE_PAS_FUSIONNER_PR_640")
        self.assert_invalid(m, "VERROUS_MODIFIES")

    def test_cannot_forge_go(self):
        m = self.fresh(); m["decision"]["statut"] = "GO"
        self.assert_invalid(m, "FAUSSE_DECISION")

    def test_cannot_claim_assessment_signoff(self):
        m = self.fresh(); m["decision"]["efvp_signee"] = True
        self.assert_invalid(m, "FAUSSE_DECISION")

    def test_extra_personal_key_rejected(self):
        m = self.fresh(); m["proprietaire_nom"] = "TEST"
        self.assert_invalid(m, "CHAMPS_INATTENDUS_OU_MANQUANTS")

    def test_wrong_status_no_go(self):
        self.assertEqual(self.check([])["decision"], "NO_GO_AUTOMATIQUE")

    def test_missing_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "does-not-exist.json"
            report = Path(d) / "report.json"
            status = module.main(["--registre", str(source), "--rapport", str(report)])
            self.assertEqual(status, 2)
            self.assertEqual(json.loads(report.read_text())["decision"], "NO_GO_AUTOMATIQUE")


if __name__ == "__main__":
    unittest.main()
