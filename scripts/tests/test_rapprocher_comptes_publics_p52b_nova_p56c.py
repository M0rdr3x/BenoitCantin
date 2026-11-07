"""P56C : contrôle de la ventilation de 2025-2026 et refus de la projection Nova."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"scripts/rapprocher_comptes_publics_p52b_nova_p56c.py"
D_TABLE=ROOT/"projets/projet-nova/etudes/P56C_TABLE_PASSAGE_COMPTES_PUBLICS_VERS_P52B_2025_2026.json"
D_SOURCE=ROOT/"projets/projet-nova/etudes/P56B_SNAPSHOTS_FINANCES_2025_2026_SOURCES_OFFICIELLES.json"
D_TEMPLATE=ROOT/"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json"
D_EVIDENCE=ROOT/"projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json"

spec=importlib.util.spec_from_file_location("p56c",SRC)
p56c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p56c)

class TestsP56C(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(D_TABLE.read_text(encoding="utf-8"))
        cls.s=json.loads(D_SOURCE.read_text(encoding="utf-8"))
        cls.m=json.loads(D_TEMPLATE.read_text(encoding="utf-8"))
        cls.e=json.loads(D_EVIDENCE.read_text(encoding="utf-8"))
        cls.r=p56c.verifier(cls.d,cls.s,cls.m,cls.e)
    def dcopy(self):
        return copy.deepcopy(self.d)
    def verify(self,d):
        return p56c.verifier(d,self.s,self.m,self.e)
    def reject(self,d):
        with self.assertRaises(ValueError):
            self.verify(d)
    def item(self,d,name):
        return next(x for x in d["poste_sources"] if x["id"]==name)

    def test_01_schema(self):self.assertEqual(self.r["schema_version"],"P56C-1")
    def test_02_exercice(self):self.assertEqual(self.r["exercice_historique"],"2025-2026")
    def test_03_11_postes(self):self.assertEqual(self.r["nb_postes_source_audites"],11)
    def test_04_9_revenus(self):self.assertEqual(self.r["nb_postes_de_recettes"],9)
    def test_05_2_depenses(self):self.assertEqual(self.r["nb_postes_de_depenses"],2)
    def test_06_recettes(self):self.assertEqual(self.r["revenus_audites_mcad"],"160428")
    def test_07_depenses(self):self.assertEqual(self.r["depenses_auditees_mcad"],"165930")
    def test_08_deficit(self):self.assertEqual(self.r["solde_comptable_audite_mcad"],"-5502")
    def test_09_impot_groupe(self):self.assertEqual(self.r["regroupement_impot_sur_revenu_et_biens_mcad"],"74115")
    def test_10_impots_personnes_societes(self):
        self.assertEqual(self.r["impots_particuliers_et_societes_historiques_mcad"],"63568")
    def test_11_pas_impot_nova(self):self.assertTrue(self.r["ce_sous_total_ne_vaut_pas_recette_nova"])
    def test_12_service_dette_inclus(self):
        self.assertEqual(self.r["service_dette_deja_inclus_dans_depenses_mcad"],"10148")
        self.assertTrue(self.r["aucun_double_compte_service_dette"])
    def test_13_municipalites_non_ventilees(self):
        self.assertTrue(self.r["ventilation_services_municipalites_encore_requise"])
    def test_14_zero_importation_automatique(self):
        self.assertEqual(self.r["chiffres_historiques_importables_directement_p52b"],0)
        self.assertEqual(self.r["montants_p52b_2027_2036_renseignes_par_ce_jalon"],0)
    def test_15_600_inconnues(self):self.assertEqual(self.r["montants_p52b_manquants"],600)
    def test_16_720_incidences(self):self.assertEqual(self.r["incidences_p52d_manquantes"],720)
    def test_17_20_preuves(self):self.assertEqual(self.r["preuves_p52a_manquantes"],20)
    def test_18_score_53(self):self.assertEqual(self.r["maturite_p55n_estimative_pourcent"],53)
    def test_19_no_go(self):self.assertEqual(self.r["decision"],"NO_GO_AUTOMATIQUE")
    def test_20_aucun_solde_projection(self):self.assertIsNone(self.r["solde_previsionnel_nova_2036"])
    def test_21_aucune_economie(self):self.assertIsNone(self.r["economies_publiques_nova_certifiees"])
    def test_22_refus_montant_altere(self):
        d=self.dcopy();self.item(d,"impot_particuliers")["montant_audite_mcad"]="48970";self.reject(d)
    def test_23_refus_double_compte_categories(self):
        d=self.dcopy();d["poste_sources"].append(copy.deepcopy(d["poste_sources"][0]));self.reject(d)
    def test_24_refus_retrait_taxes_consommation(self):
        d=self.dcopy();d["poste_sources"]=[x for x in d["poste_sources"] if x["id"]!="taxes_consommation"];self.reject(d)
    def test_25_refus_page_erronee(self):
        d=self.dcopy();self.item(d,"impots_societes")["page_pdf_zero_index"]=11;self.reject(d)
    def test_26_refus_fausse_source(self):
        d=self.dcopy();d["source"]["url"]="https://example.com";self.reject(d)
    def test_27_refus_regime_souverain(self):
        d=self.dcopy();d["territoire"]="QUEBEC_SOUVERAIN";self.reject(d)
    def test_28_refus_exercice_projeté(self):
        d=self.dcopy();d["exercice"]="2027-2028";self.reject(d)
    def test_29_refus_mauvaise_unite(self):
        d=self.dcopy();d["unite_montant"]="G_CAD";self.reject(d)
    def test_30_refus_mappage_fss_revenu(self):
        d=self.dcopy();self.item(d,"cotisations_services_sante")["postes_candidats_p52b"]=["impot_revenu_net"];self.reject(d)
    def test_31_refus_mappage_dette_services(self):
        d=self.dcopy();self.item(d,"service_dette")["postes_candidats_p52b"]=["services_existants_hors_dette_et_municipal_nets"];self.reject(d)
    def test_32_refus_transfert_autorise(self):
        d=self.dcopy();self.item(d,"transferts_gouvernement_federal")["transposition_directe_autorisee"]=True;self.reject(d)
    def test_33_refus_transfert_2027(self):
        d=self.dcopy();self.item(d,"impot_particuliers")["exercice_cible_p52b_2027_2036"]=2027;self.reject(d)
    def test_34_refus_faux_go(self):
        d=self.dcopy();d["decision"]="GO";self.reject(d)
    def test_35_refus_score_fictif(self):
        d=self.dcopy();d["p55n_maturite_estimee"]=100;self.reject(d)
    def test_36_refus_montants_p52b_modifies(self):
        d=self.dcopy();d["postes_budgetaires_p52b_inconnus_maintenus"]=0;self.reject(d)
    def test_37_refus_zero_p52b_artificiel(self):
        m=copy.deepcopy(self.m)
        row=m["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0]
        row["recettes"]["impot_revenu_net"]="0"
        row["sources"]["impot_revenu_net"]="HYPOTHESE_SANS_SOURCE"
        with self.assertRaises(ValueError):
            p56c.verifier(self.d,self.s,m,self.e)
    def test_38_closure_sources_non_certification(self):
        self.assertFalse(self.r["validation_independante_nova"])
        self.assertIsNone(self.r["effets_emplois_services_menages"])
    def test_39_cli_json(self):
        cmd=[sys.executable,str(SRC),"--table",str(D_TABLE),"--snapshots",str(D_SOURCE),
             "--gabarit",str(D_TEMPLATE),"--registre",str(D_EVIDENCE)]
        p=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)["revenus_audites_mcad"],"160428")
    def test_40_cli_refus_certification(self):
        cmd=[sys.executable,str(SRC),"--table",str(D_TABLE),"--snapshots",str(D_SOURCE),
             "--gabarit",str(D_TEMPLATE),"--registre",str(D_EVIDENCE),"--exiger-budget-certifie"]
        p=subprocess.run(cmd,capture_output=True)
        self.assertEqual(p.returncode,3)
    def test_41_cli_refus_ecraser_rapport(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"rapport.json"
            cmd=[sys.executable,str(SRC),"--table",str(D_TABLE),"--snapshots",str(D_SOURCE),
                 "--gabarit",str(D_TEMPLATE),"--registre",str(D_EVIDENCE),"--rapport",str(out)]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
    def test_42_refus_rapprochement_p56b_modifie(self):
        s=copy.deepcopy(self.s)
        v=s["snapshots"]["COMPTES_AUDITES_JUILLET_2026"]["donnees"]
        v["revenus_totaux_mcad"]="160429"
        with self.assertRaises(ValueError):
            p56c.verifier(self.d,s,self.m,self.e)

if __name__=="__main__":
    unittest.main()
