"""P56H — tests des deux correspondances numériques et refus du faux appariement."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
CODE=ROOT/"scripts/verifier_correspondances_revenus_municipaux_nova_p56h.py"
DOC=ROOT/"projets/projet-nova/etudes/P56H_DECOMPOSITION_REVENUS_ALMA_2024_CORRESPONDANCES_PROVINCIALES.json"
PILOT=ROOT/"projets/projet-nova/etudes/P56G_PREMIER_PONT_PROVINCIAL_MUNICIPAL_ALMA_2024.json"
spec=importlib.util.spec_from_file_location("p56h",CODE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestP56H(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(DOC.read_text(encoding="utf-8"))
        cls.g=json.loads(PILOT.read_text(encoding="utf-8"))
        cls.r=m.audit(cls.d,cls.g)
    def data(self):
        return copy.deepcopy(self.d)
    def reject(self,d,g=None):
        with self.assertRaises(ValueError):
            m.audit(d,self.g if g is None else g)
    def municipal(self,d,name):
        return next(r for r in d["rubriques_municipales_detaillees"] if r["id"]==name)
    def provincial(self,d,name):
        return next(r for r in d["lignes_provinciales"] if r["id"]==name)
    def comparison(self,d,name):
        return next(r for r in d["comparaisons"] if r["id"]==name)

    def test_01_schema(self):
        self.assertEqual(self.r["schema_version"],"P56H-1")
    def test_02_annee_municipale(self):
        self.assertEqual(self.r["annee_municipale"],"2024")
    def test_03_exercice_provincial(self):
        self.assertEqual(self.r["exercice_provincial"],"2024-2025")
    def test_04_montant_somme_sante_ecole(self):
        self.assertEqual(self.r["somme_sante_cegeps_ecoles_municipale_cad"],"3320039")
    def test_05_montant_provincial_40350(self):
        self.assertEqual(self.r["montant_provincial_programme_40350_cad"],"3320039")
    def test_06_difference_zero(self):
        self.assertEqual(self.r["difference_numerique_programme_40350_cad"],"0")
    def test_07_part_tvq_municipale(self):
        self.assertEqual(self.r["part_tvq_municipale_2024_cad"],"1665578")
    def test_08_programme_40561(self):
        self.assertEqual(self.r["montant_provincial_programme_40561_cad"],"1665580")
    def test_09_difference_moins_deux(self):
        self.assertEqual(self.r["difference_numerique_programme_40561_cad"],"-2")
    def test_10_deux_liens_numeriques(self):
        self.assertEqual(self.r["concordances_numeriques_documentees"],2)
    def test_11_zero_appairement_comptable(self):
        self.assertEqual(self.r["nombre_appariements_comptables_certifies"],0)
    def test_12_cause_ecart_tva_inconnue(self):
        self.assertIsNone(self.r["cause_ecart_tvq_2_cad"])
    def test_13_dates_paiement_non_verifiees(self):
        self.assertFalse(self.r["dates_encaissement_municipal_prouvees"])
    def test_14_original_pdf_non_verifie(self):
        self.assertFalse(self.r["documents_binaries_controles_visuellement"])
    def test_15_annexe_non_auditee(self):
        self.assertTrue(self.r["rubriques_s27_non_auditees"])
    def test_16_pas_economie_nova(self):
        self.assertIsNone(self.r["economies_nova_certifiees_cad"])
    def test_17_pas_cellules_p52b(self):
        self.assertEqual(self.r["nombre_nouvelles_cellules_p52b_certifiees"],0)
    def test_18_600_inconnues_p52b(self):
        self.assertEqual(self.r["inconnues_p52b"],600)
    def test_19_720_incidences(self):
        self.assertEqual(self.r["incidences_p52d_inconnues"],720)
    def test_20_53_pourcent_inchange(self):
        self.assertEqual(self.r["score_p55n_estime_pourcent"],53)
    def test_21_no_go(self):
        self.assertEqual(self.r["decision"],"NO_GO_AUTOMATIQUE")
    def test_22_valeur_sante_trompee(self):
        d=self.data();self.municipal(d,"M_SANTE_S27_31")["montant_realisation_2024_cad"]="1163326";self.reject(d)
    def test_23_valeur_cegep_trompee(self):
        d=self.data();self.municipal(d,"M_CEGEP_S27_32")["montant_realisation_2024_cad"]="576301";self.reject(d)
    def test_24_valeur_ecole_trompee(self):
        d=self.data();self.municipal(d,"M_ECOLES_S27_33")["montant_realisation_2024_cad"]="1580413";self.reject(d)
    def test_25_tvq_trompee(self):
        d=self.data();self.municipal(d,"M_TVQ_S27_136")["montant_realisation_2024_cad"]="1665580";self.reject(d)
    def test_26_programme_40350_trompe(self):
        d=self.data();self.provincial(d,"P_40350")["montant_publie_exercice_2024_2025_cad"]="3320040";self.reject(d)
    def test_27_programme_40561_trompe(self):
        d=self.data();self.provincial(d,"P_40561")["montant_publie_exercice_2024_2025_cad"]="1665578";self.reject(d)
    def test_28_fausse_audition_annexe(self):
        d=self.data();self.municipal(d,"M_CEGEP_S27_32")["comptes_annexe_statut"]="AUDITE";self.reject(d)
    def test_29_fausse_page_s27(self):
        d=self.data();self.municipal(d,"M_SANTE_S27_31")["page_imprimee"]=52;self.reject(d)
    def test_30_faux_programme_40350(self):
        d=self.data();self.provincial(d,"P_40350")["programme"]="40561";self.reject(d)
    def test_31_fausse_concordance_certifiee(self):
        d=self.data();self.comparison(d,"C_40350")["correspondance_comptable_confirmee"]=True;self.reject(d)
    def test_32_fausse_date_paiement(self):
        d=self.data();self.comparison(d,"C_40350")["preuve_date_paiement"]="2024-07-12";self.reject(d)
    def test_33_faux_ecart_zero_tvq(self):
        d=self.data();self.comparison(d,"C_40561")["ecart_municipal_moins_provincial_cad"]="0";self.reject(d)
    def test_34_faux_total_sante_ecoles(self):
        d=self.data();self.comparison(d,"C_40350")["montant_municipal_agrege_cad"]="3320038";self.reject(d)
    def test_35_faux_avis_independant(self):
        d=self.data();self.comparison(d,"C_40350")["avis_independant_signé"]="accepte";self.reject(d)
    def test_36_fausse_validation_p56g(self):
        d=self.data();g=copy.deepcopy(self.g);g["donnees_provinciales"][0]["montant_cad"]="3320040"
        self.reject(d,g)
    def test_37_faux_score(self):
        d=self.data();d["pourcentage_estime_p55n"]=57;self.reject(d)
    def test_38_faux_go(self):
        d=self.data();d["decision"]="GO";self.reject(d)
    def test_39_faux_cellules_budget(self):
        d=self.data();d["montants_p52b_modifies"]=3;self.reject(d)
    def test_40_fausse_preuve_pdf(self):
        d=self.data();d["sources"]["MUN_2024_S27"]["verification_du_binaire_original_et_sha256"]=True;self.reject(d)
    def test_41_cli_json(self):
        p=subprocess.run([sys.executable,str(CODE),"--decomposition",str(DOC),"--pilote-p56g",str(PILOT)],
                         capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)["difference_numerique_programme_40350_cad"],"0")
    def test_42_cli_refus_certification(self):
        p=subprocess.run([sys.executable,str(CODE),"--decomposition",str(DOC),
                          "--pilote-p56g",str(PILOT),"--exiger-appariement-certifie"],
                         capture_output=True)
        self.assertEqual(p.returncode,3)
    def test_43_cli_refus_ecrasement(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"rapport.json"
            args=[sys.executable,str(CODE),"--decomposition",str(DOC),
                  "--pilote-p56g",str(PILOT),"--rapport",str(out)]
            p=subprocess.run(args,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,2)
if __name__=="__main__":
    unittest.main()
