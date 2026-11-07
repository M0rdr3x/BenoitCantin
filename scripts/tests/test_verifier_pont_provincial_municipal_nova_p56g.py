"""P56G : 36 tests des pièces réelles, millésimes et fausses contreparties."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
CODE=ROOT/"scripts/verifier_pont_provincial_municipal_nova_p56g.py"
ENTRY=ROOT/"projets/projet-nova/etudes/P56G_PREMIER_PONT_PROVINCIAL_MUNICIPAL_ALMA_2024.json"
spec=importlib.util.spec_from_file_location("p56g",CODE)
p56g=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p56g)

class TestP56G(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads(ENTRY.read_text(encoding="utf-8"))
        cls.result=p56g.verifier(cls.base)
    def c(self):
        return copy.deepcopy(self.base)
    def reject(self,d):
        with self.assertRaises(ValueError):
            p56g.verifier(d)
    def mun(self,d,id):
        return next(x for x in d["donnees_municipales"] if x["id"]==id)
    def prov(self,d,id):
        return next(x for x in d["donnees_provinciales"] if x["id"]==id)
    def hyp(self,d,id):
        return next(x for x in d["hypotheses_appariement"] if x["id"]==id)

    def test_01_schema(self):
        self.assertEqual(self.result["schema_version"],"P56G-1")
    def test_02_municipalite(self):
        self.assertEqual(self.result["municipalite"],"Alma")
    def test_03_annee_municipale(self):
        self.assertEqual(self.result["annee_civile_comptes"],2024)
    def test_04_annee_provinciale(self):
        self.assertEqual(self.result["exercice_provincial"],"2024-2025")
    def test_05_compensations_reelles(self):
        self.assertEqual(self.result["compensations_municipales_2024_cad"],"5514445")
    def test_06_transferts_reels(self):
        self.assertEqual(self.result["transferts_municipaux_2024_cad"],"5578416")
    def test_07_engagement_40350(self):
        self.assertEqual(self.result["engagement_provincial_40350_cad"],"3320039")
    def test_08_engagement_40561(self):
        self.assertEqual(self.result["engagement_provincial_40561_cad"],"1665580")
    def test_09_revenus_municipaux(self):
        self.assertEqual(self.result["revenus_municipaux_consolides_cad"],"93994134")
    def test_10_charges_municipales(self):
        self.assertEqual(self.result["charges_municipales_consolidees_cad"],"89364728")
    def test_11_excedent_comptable_et_non_budget_fonctionnement(self):
        self.assertEqual(self.result["excedent_comptable_municipal_cad"],"4629406")
    def test_12_deux_hypotheses(self):
        self.assertEqual(self.result["nombre_liens_appariemement_candidats"],2)
    def test_13_aucun_lien_certifie(self):
        self.assertEqual(self.result["liens_apparies_avec_preuves"],0)
    def test_14_total_apparie_inconnu(self):
        self.assertIsNone(self.result["montant_apparie_cad"])
    def test_15_ecart_non_calcule(self):
        self.assertIsNone(self.result["ecart_de_contreparties_cad"])
    def test_16_pas_importation_budget_nova(self):
        self.assertEqual(self.result["montants_disponibles_pour_projection_nova_2027_2036"],0)
    def test_17_cinq_preuves(self):
        self.assertEqual(self.result["besoin_pieces_independantes"],5)
    def test_18_53_pourcent(self):
        self.assertEqual(self.result["p55n_maturite_estimee_pourcent"],53)
    def test_19_no_go(self):
        self.assertEqual(self.result["decision"],"NO_GO_AUTOMATIQUE")
    def test_20_aucun_audit_visuel_du_binaire(self):
        self.assertFalse(self.result["examen_original_pdf_visuel_confirme"])
    def test_21_compensations_changees(self):
        d=self.c();self.mun(d,"MUN_2024_COMPENSATIONS")["montant_cad"]="5514446";self.reject(d)
    def test_22_transferts_changees(self):
        d=self.c();self.mun(d,"MUN_2024_TRANSFERTS")["montant_cad"]="0";self.reject(d)
    def test_23_source_provinciale_tampered(self):
        d=self.c();self.prov(d,"PROV_2024_40350")["montant_cad"]="3320040";self.reject(d)
    def test_24_autre_programme(self):
        d=self.c();self.prov(d,"PROV_2024_40561")["programme"]="40350";self.reject(d)
    def test_25_mauvais_millesime(self):
        d=self.c();self.prov(d,"PROV_2024_40350")["exercice_fin"]="2024-12-31";self.reject(d)
    def test_26_fausse_date_paiement(self):
        d=self.c();self.hyp(d,"H01")["preuve_date_paiement"]="2024-07-02";self.reject(d)
    def test_27_fausse_piece_comptable(self):
        d=self.c();self.hyp(d,"H01")["preuve_piece_comptable_municipale"]="piece";self.reject(d)
    def test_28_faux_montant_apparie(self):
        d=self.c();self.hyp(d,"H01")["montant_rapproche_cad"]="3320039";self.reject(d)
    def test_29_faux_ecart_residuel(self):
        d=self.c();self.hyp(d,"H01")["montant_non_explique_cad"]="2194406";self.reject(d)
    def test_30_fausse_certification(self):
        d=self.c();self.hyp(d,"H02")["appariement_confirme"]=True;self.reject(d)
    def test_31_importation_p52b_interdite(self):
        d=self.c();d["autorisation_importation_p52b"]=True;self.reject(d)
    def test_32_reforme_adoptee_interdite(self):
        d=self.c();d["reforme_fiscale_adoptee"]=True;self.reject(d)
    def test_33_score_non_falsifiable(self):
        d=self.c();d["score_p55n_estime"]=100;self.reject(d)
    def test_34_cli_json(self):
        r=subprocess.run([sys.executable,str(CODE),"--dossier",str(ENTRY)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIsNone(json.loads(r.stdout)["montant_apparie_cad"])
    def test_35_cli_refuse_certification(self):
        args=[sys.executable,str(CODE),"--dossier",str(ENTRY),"--exiger-appariement-certifie"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)
    def test_36_refus_ecraser_fichier(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"result.json"
            args=[sys.executable,str(CODE),"--dossier",str(ENTRY),"--rapport",str(path)]
            r=subprocess.run(args,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,2)

if __name__=="__main__":
    unittest.main()
