"""P56E : 38 tests de sources, millesime, contreparties et refus de certifications fictives."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "scripts/rapprocher_enveloppes_municipales_nova_p56e.py"
DATA = (ROOT / "projets/projet-nova/etudes/"
        "P56E_REGISTRE_TRANSFERTS_MUNICIPAUX_2027_ET_VERIFICATION_SOURCES.json")
spec = importlib.util.spec_from_file_location("p56e", SRC)
p56e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p56e)

class TestsP56E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.result = p56e.auditer(cls.data)

    def d(self):
        return copy.deepcopy(self.data)

    def program(self, d, id):
        return next(x for x in d["programmes"] if x["id"] == id)

    def reject(self, d):
        with self.assertRaises(ValueError):
            p56e.auditer(d)

    def test_01_schema(self):
        self.assertEqual(self.result["schema_version"], "P56E-1")
    def test_02_year(self):
        self.assertEqual(self.result["annee_civile_previsions"], 2027)
    def test_03_four_programmes(self):
        self.assertEqual(self.result["nombre_programmes_budgetaires_identifies"], 4)
    def test_04_sous_total(self):
        self.assertEqual(self.result["sous_total_quatre_enveloppes_previsionnelles_mcad"], "951.8")
    def test_05_not_all_transfers(self):
        self.assertFalse(self.result["sous_total_represente_total_transferts_publics"])
    def test_06_tvq_821(self):
        self.assertEqual(self.program(self.d(), "CROISSANCE_PARTIE_TVQ")["enveloppe_prevue_mcad"], "821.0")
    def test_07_terres_25_8(self):
        self.assertEqual(self.program(self.d(), "COMPENSATION_TERRES_PUBLIQUES")["enveloppe_prevue_mcad"], "25.8")
    def test_08_redevances_38(self):
        self.assertEqual(self.program(self.d(), "PARTAGE_REDEVANCES_RESSOURCES")["enveloppe_prevue_mcad"], "38.0")
    def test_09_perequation_67(self):
        self.assertEqual(self.program(self.d(), "PEREQUATION_MUNICIPALE")["enveloppe_prevue_mcad"], "67.0")
    def test_10_tvq_volet_un(self):
        self.assertEqual(self.result["tvq_volet_i_calcul_illustratif_mcad"], "767.635")
    def test_11_tvq_volet_deux(self):
        self.assertEqual(self.result["tvq_volet_ii_calcul_illustratif_mcad"], "53.365")
    def test_12_versements_non_constates(self):
        self.assertIsNone(self.result["subventions_reelles_2027_versees_mcad"])
    def test_13_no_reconciliation(self):
        self.assertFalse(self.result["rapprochement_depense_province_recette_municipale"])
    def test_14_pdf_2025_bloque(self):
        self.assertFalse(self.result["sommaire_historique_2025_valide"])
        self.assertTrue(self.result["source_2025_version_a_reverifier"])
    def test_15_no_nova_gain(self):
        self.assertIsNone(self.result["economie_obtenue_nova_mcad"])
    def test_16_no_nova_budget(self):
        self.assertFalse(self.result["budget_nova_certifie"])
    def test_17_p52b_600(self):
        self.assertEqual(self.result["inconnues_budget_p52b"], 600)
    def test_18_p52d_720(self):
        self.assertEqual(self.result["inconnues_incidence_p52d"], 720)
    def test_19_score_53(self):
        self.assertEqual(self.result["score_p55n_estimatif"], 53)
    def test_20_no_go(self):
        self.assertEqual(self.result["decision"], "NO_GO_AUTOMATIQUE")
    def test_21_pas_automatic_2027_2036(self):
        self.assertFalse(self.result["projections_2027_2036_modifiees"])
    def test_22_refuse_deux_taxes_adoptees(self):
        d=self.d();d["programme_fiscal_adopte"]=True;self.reject(d)
    def test_23_refuse_faux_gain(self):
        d=self.d();d["economies_projet_nova_certifiees_mcad"]="10.0";self.reject(d)
    def test_24_refuse_changement_taux_821(self):
        d=self.d();self.program(d,"CROISSANCE_PARTIE_TVQ")["enveloppe_prevue_mcad"]="822.0";self.reject(d)
    def test_25_refuse_statut_versement_paye(self):
        d=self.d();self.program(d,"CROISSANCE_PARTIE_TVQ")["statut"]="PAYE";self.reject(d)
    def test_26_refuse_importation_2027_28(self):
        d=self.d();self.program(d,"PEREQUATION_MUNICIPALE")["annee_debut_exercice_budget_p52b"]=2027;self.reject(d)
    def test_27_refuse_depense_provinciale_inventee(self):
        d=self.d();self.program(d,"PEREQUATION_MUNICIPALE")["depense_provinciale_reconciliee_mcad"]="67.0";self.reject(d)
    def test_28_refuse_recette_municipale_inventee(self):
        d=self.d();self.program(d,"PEREQUATION_MUNICIPALE")["recette_municipale_reconciliee_mcad"]="67.0";self.reject(d)
    def test_29_refuse_beneficiaire_invente(self):
        d=self.d();self.program(d,"PEREQUATION_MUNICIPALE")["identifiant_beneficiaire_municipal"]="DEMO-001";self.reject(d)
    def test_30_refuse_sommaire_non_verifie_2025(self):
        d=self.d();d["source_sommaire_2025"]["montants_importables"]="100.0";self.reject(d)
    def test_31_refuse_version_sommaire_resolue_sans_preuve(self):
        d=self.d();d["source_sommaire_2025"]["date_et_empreinte_binaire_originale_verifiees"]=True;self.reject(d)
    def test_32_refuse_contrefactuel_sommaire(self):
        d=self.d();d["source_sommaire_2025"]["controle_version"]="VERIFIE";self.reject(d)
    def test_33_refuse_faux_total_de_toutes_municipalites(self):
        d=self.d();d["somme_est_sous_ensemble_et_non_total_tous_transferts"]=False;self.reject(d)
    def test_34_refuse_proportions_alterees(self):
        d=self.d();d["ventilation_tvq_2027"]["volet_i_pourcent"]="90.0";self.reject(d)
    def test_35_refuse_source_modifiee(self):
        d=self.d();d["source_previsions"]["url"]="https://example.org/faux";self.reject(d)
    def test_36_refuse_annee_2026(self):
        d=self.d();self.program(d,"PARTAGE_REDEVANCES_RESSOURCES")["annee_civile"]=2026;self.reject(d)
    def test_37_cli_refuse_certification(self):
        r=subprocess.run([sys.executable,str(SRC),"--registre",str(DATA),
                          "--exiger-certification"],capture_output=True)
        self.assertEqual(r.returncode,3)
    def test_38_cli_refuse_ecrasement(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/"bilan.json"
            args=[sys.executable,str(SRC),"--registre",str(DATA),"--rapport",str(report)]
            r=subprocess.run(args,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["decision"],"NO_GO_AUTOMATIQUE")
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,2)

if __name__ == "__main__":
    unittest.main()
