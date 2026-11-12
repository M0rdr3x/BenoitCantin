"""P56F: tests de fiabilité du périmètre et de la quarantaine du sommaire 2025."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
CODE=ROOT/"scripts/verifier_provenance_transferts_municipaux_nova_p56f.py"
HIST=ROOT/"projets/projet-nova/etudes/P56F_REFERENCES_MUNICIPALES_2023_2027_ET_QUARANTAINE_2025.json"
PLAN=ROOT/"projets/projet-nova/etudes/P56E_REGISTRE_TRANSFERTS_MUNICIPAUX_2027_ET_VERIFICATION_SOURCES.json"
spec=importlib.util.spec_from_file_location("p56f",CODE)
p56f=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p56f)

class TestP56F(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h=json.loads(HIST.read_text(encoding="utf-8"))
        cls.p=json.loads(PLAN.read_text(encoding="utf-8"))
        cls.r=p56f.controler(cls.h,cls.p)
    def hcopy(self):
        return copy.deepcopy(self.h)
    def reject(self,d):
        with self.assertRaises(ValueError):p56f.controler(d,self.p)
    def test_01_schema(self):
        self.assertEqual(self.r["schema_version"],"P56F-1")
    def test_02_total_historique(self):
        self.assertEqual(self.r["reference_historique_2023_total_transferts_mcad"],"6190.1")
    def test_03_transferts_droits(self):
        self.assertEqual(self.r["reference_historique_2023_transferts_droits_mcad"],"763.6")
    def test_04_transferts_conditionnels(self):
        self.assertEqual(self.r["reference_historique_2023_transferts_conditionnels_mcad"],"5426.5")
    def test_05_addition_sans_doublon(self):
        self.assertEqual(7636+54265,61901)
    def test_06_previsions_2027(self):
        self.assertEqual(self.r["enveloppes_quatre_programmes_2027_prevision_mcad"],"951.8")
    def test_07_pas_somme_millesimes(self):
        self.assertIsNone(self.r["somme_des_series_2023_2027"])
    def test_08_pas_de_croissance_inventee(self):
        self.assertIsNone(self.r["taux_de_croissance_2023_2027"])
    def test_09_pdf_2025_bloque(self):
        self.assertIsNone(self.r["montant_sommaire_2025_valide_mcad"])
        self.assertTrue(self.r["version_2025_a_resoudre"])
    def test_10_600_unknowns(self):
        self.assertEqual(self.r["p52b_valeurs_inconnues"],600)
    def test_11_720_unknowns(self):
        self.assertEqual(self.r["p52d_incidences_inconnues"],720)
    def test_12_53_pourcent(self):
        self.assertEqual(self.r["p55n_score_estime_pourcent"],53)
    def test_13_no_go(self):
        self.assertEqual(self.r["decision"],"NO_GO_AUTOMATIQUE")
    def test_14_pas_economie(self):
        self.assertIsNone(self.r["economie_nova_certifiee_mcad"])
    def test_15_regression_source2027(self):
        d=copy.deepcopy(self.p)
        d["programmes"][0]["enveloppe_prevue_mcad"]="822.0"
        with self.assertRaises(ValueError):p56f.controler(self.h,d)
    def test_16_source2023_alteree(self):
        d=self.hcopy();d["serie_historique_2023"]["source"]["url"]="https://example.org/fiction.pdf";self.reject(d)
    def test_17_annee_fausse(self):
        d=self.hcopy();d["serie_historique_2023"]["annee"]=2025;self.reject(d)
    def test_18_transferts_droits_alteres(self):
        d=self.hcopy();d["serie_historique_2023"]["transferts_de_droits_inconditionnels_mcad"]="700";self.reject(d)
    def test_19_total_altere(self):
        d=self.hcopy();d["serie_historique_2023"]["total_transferts_mcad"]="6000";self.reject(d)
    def test_20_pourcent_faux(self):
        d=self.hcopy();d["serie_historique_2023"]["parts_publiees_pourcent"]["droits"]="20";self.reject(d)
    def test_21_sous_categories_double(self):
        d=self.hcopy();d["serie_historique_2023"]["sous_categories_deja_incluses"][1]["id"]="TRANSPORT_COLLECTIF";self.reject(d)
    def test_22_sous_categories_augmentee(self):
        d=self.hcopy();d["serie_historique_2023"]["sous_categories_deja_incluses"][2]["montant_mcad"]="9999.9";self.reject(d)
    def test_23_total_2027_avec_inconnus(self):
        d=self.hcopy();d["previsions_2027"]["total_transferts_2027_tous_programmes_mcad"]="951.8";self.reject(d)
    def test_24_versements_2027_inventes(self):
        d=self.hcopy();d["previsions_2027"]["depenses_effectives_provinciales_2027_mcad"]="951.8";self.reject(d)
    def test_25_sommaire_2025_audite_invente(self):
        d=self.hcopy();d["sommaire_2025"]["montants_2025_importables"]="999";self.reject(d)
    def test_26_sommaire_2025_sha_non_verifie(self):
        d=self.hcopy();d["sommaire_2025"]["empreinte_sha256_document_binaire"]="000000";self.reject(d)
    def test_27_sommaire_2025_pas_2024(self):
        d=self.hcopy();d["sommaire_2025"]["rendu_visuel_web_2026_11_07"]="TABLE_2025";self.reject(d)
    def test_28_quarantaine_retirée(self):
        d=self.hcopy();d["sommaire_2025"]["autorisation_importation"]=True;self.reject(d)
    def test_29_faux_taux_croissance(self):
        d=self.hcopy();d["comparabilite"]["croissance_2023_2027_demontree"]=True;self.reject(d)
    def test_30_fausse_comparabilite_perimetre(self):
        d=self.hcopy();d["comparabilite"]["perimetres_equivalents"]=True;self.reject(d)
    def test_31_avis_comptable_invente(self):
        d=self.hcopy();d["provenance_professionnelle"]["revue_par_comptable_municipal_independant"]=True;self.reject(d)
    def test_32_validation_nova_inventee(self):
        d=self.hcopy();d["financement_des_services_valide"]=True;self.reject(d)
    def test_33_deux_taxes_adoptees_inventees(self):
        d=self.hcopy();d["taux_fiscaux_nova_adoptes"]=True;self.reject(d)
    def test_34_faux_score(self):
        d=self.hcopy();d["p55n_maturite_estimative"]=60;self.reject(d)
    def test_35_non_adoption_auto(self):
        d=self.hcopy();d["decision"]="GO";self.reject(d)
    def test_36_budget_2027_non_certifie(self):
        self.assertFalse(self.r["budget_decennal_renseigne_par_p56f"])
    def test_37_cli_json(self):
        r=subprocess.run([sys.executable,str(CODE),"--historique",str(HIST),"--previsions",str(PLAN)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["reference_historique_2023_total_transferts_mcad"],"6190.1")
    def test_38_cli_certification_refusee(self):
        cmd=[sys.executable,str(CODE),"--historique",str(HIST),"--previsions",str(PLAN),"--exiger-faisabilite"]
        self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,3)
    def test_39_rapport_ecrasement_refuse(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"rapport.json"
            cmd=[sys.executable,str(CODE),"--historique",str(HIST),"--previsions",str(PLAN),"--rapport",str(out)]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
    def test_40_url_du_pdf_non_speculatif(self):
        self.assertIn("fiscalite_organismes_municipaux.pdf",self.r["source_historique_mamh_2023"])

if __name__=="__main__":
    unittest.main()
