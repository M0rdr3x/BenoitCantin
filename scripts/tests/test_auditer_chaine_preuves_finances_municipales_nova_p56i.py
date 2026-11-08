"""P56I : 37 tests de l'opinion avec réserve, S27 non auditée et absence de GO."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
CODE=ROOT/"scripts/auditer_chaine_preuves_finances_municipales_nova_p56i.py"
DOC=ROOT/"projets/projet-nova/etudes/P56I_REGISTRE_ASSURANCE_PREUVES_ET_RESERVES_ALMA_2024.json"
H=ROOT/"projets/projet-nova/etudes/P56H_DECOMPOSITION_REVENUS_ALMA_2024_CORRESPONDANCES_PROVINCIALES.json"
G=ROOT/"projets/projet-nova/etudes/P56G_PREMIER_PONT_PROVINCIAL_MUNICIPAL_ALMA_2024.json"
spec=importlib.util.spec_from_file_location("p56i",CODE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class P56ITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(DOC.read_text(encoding="utf-8"))
        cls.h=json.loads(H.read_text(encoding="utf-8"))
        cls.g=json.loads(G.read_text(encoding="utf-8"))
        cls.r=m.comparer(cls.d,cls.h,cls.g)
    def dcopy(self):
        return copy.deepcopy(self.d)
    def reject(self,d,h=None,g=None):
        with self.assertRaises(ValueError):
            m.comparer(d,h if h is not None else self.h,g if g is not None else self.g)
    def risk(self,d,id):
        return next(x for x in d["risques"] if x["id"]==id)
    def piece(self,d,id):
        return next(x for x in d["pieces_a_obtenir"] if x["id"]==id)

    def test_01_schema(self):self.assertEqual(self.r["schema_version"],"P56I-1")
    def test_02_neuf_controles(self):self.assertEqual(self.r["nombre_controles"],9)
    def test_03_deux_constats(self):self.assertEqual(self.r["constats_documentaires_verifies"],2)
    def test_04_sept_ouverts(self):self.assertEqual(self.r["chantiers_preuve_non_resolus"],7)
    def test_05_cinq_pieces(self):self.assertEqual(self.r["pieces_de_contrepartie_manquantes"],5)
    def test_06_audit_avec_reserve(self):self.assertTrue(self.r["rapport_municipal_audit_avec_reserve"])
    def test_07_s27_non_auditee(self):self.assertFalse(self.r["annexe_s27_auditee"])
    def test_08_concordances_numeriques(self):self.assertEqual(self.r["concordances_numeriques"],2)
    def test_09_ecart_numerique_40350(self):self.assertEqual(self.r["concordance_exacte_40350_cad"],"0")
    def test_10_ecart_40561(self):self.assertEqual(self.r["ecart_40561_non_explique_cad"],"-2")
    def test_11_zero_appariements(self):self.assertEqual(self.r["appariements_comptables_certifies"],0)
    def test_12_zero_sha(self):self.assertEqual(self.r["documents_binaires_originaux_authentifies"],0)
    def test_13_zero_economie(self):self.assertIsNone(self.r["nouvelles_economies_nova_certifiees_cad"])
    def test_14_zero_imputation(self):self.assertEqual(self.r["nouvelles_cellules_p52b_renseignees"],0)
    def test_15_p52b_inconnues(self):self.assertEqual(self.r["p52b_champs_inconnus"],600)
    def test_16_p52d_inconnues(self):self.assertEqual(self.r["p52d_incidences_inconnues"],720)
    def test_17_score_p55n(self):self.assertEqual(self.r["p55n_score_estimatif"],53)
    def test_18_no_go(self):self.assertEqual(self.r["decision"],"NO_GO_AUTOMATIQUE")
    def test_19_refuse_opinion_sans_reserve(self):
        d=self.dcopy();d["sources"]["RAPPORT_MUNICIPAL_S6"]["opinion_audit"]="SANS_RESERVE";self.reject(d)
    def test_20_refuse_reserve_SP3280_omise(self):
        d=self.dcopy();d["sources"]["RAPPORT_MUNICIPAL_S6"]["reserve"]="NON";self.reject(d)
    def test_21_refuse_annexe_s27_auditee(self):
        d=self.dcopy();d["sources"]["RAPPORT_MUNICIPAL_S27"]["type"]="ETATS_AUDITES";self.reject(d)
    def test_22_refuse_audit_nova(self):
        d=self.dcopy();d["sources"]["RAPPORT_MUNICIPAL_S6"]["audit_Nova"]=True;self.reject(d)
    def test_23_refuse_paiement_provincial_invente(self):
        d=self.dcopy();d["sources"]["MAMH_LISTES_2024"]["preuve_date_encaissement"]=True;self.reject(d)
    def test_24_refuse_paiement_40350_invente(self):
        d=self.dcopy();d["correspondances"]["PROGRAMME_40350"]["preuve_comptabilite_reciproque"]=True;self.reject(d)
    def test_25_refuse_paiement_40561_invente(self):
        d=self.dcopy();d["correspondances"]["PROGRAMME_40561"]["preuve_comptabilite_reciproque"]=True;self.reject(d)
    def test_26_refuse_cause_tvq_inventee(self):
        d=self.dcopy();d["correspondances"]["PROGRAMME_40561"]["cause_ecart_cad"]="ARRONDI";self.reject(d)
    def test_27_refuse_2_dollars_effaces(self):
        d=self.dcopy();d["correspondances"]["PROGRAMME_40561"]["difference_cad"]="0";self.reject(d)
    def test_28_refuse_modification_40350(self):
        d=self.dcopy();d["correspondances"]["PROGRAMME_40350"]["recette_s27_31_33_cad"]="3320040";self.reject(d)
    def test_29_refuse_avis_independant_suppose(self):
        d=self.dcopy();d["audit_contradictoire"]["avis_sur_projet_nova_signes"]=1;self.reject(d)
    def test_30_refuse_hash_suppose(self):
        d=self.dcopy();d["audit_contradictoire"]["empreintes_sha256_verifiees"]=3;self.reject(d)
    def test_31_refuse_modif_statut_critique(self):
        d=self.dcopy();self.risk(d,"I03")["etat"]="CONSTAT_PUBLIE";self.reject(d)
    def test_32_refuse_risque_duplique(self):
        d=self.dcopy();d["risques"][0]["id"]="I02";self.reject(d)
    def test_33_refuse_justification_trop_courte(self):
        d=self.dcopy();self.risk(d,"I04")["consequence"]="OK";self.reject(d)
    def test_34_refuse_piece_H04_fictive(self):
        d=self.dcopy();self.piece(d,"H04")["statut"]="OBTENUE";self.reject(d)
    def test_35_refuse_score_fictif(self):
        d=self.dcopy();d["score_p55n_estime"]=90;self.reject(d)
    def test_36_refuse_p56h_divergent(self):
        d=self.dcopy();h=copy.deepcopy(self.h);h["comparaisons"][0]["montant_municipal_agrege_cad"]="3320040"
        self.reject(d,h=h)
    def test_37_cli_and_certification_refused(self):
        args=[sys.executable,str(CODE),"--registre",str(DOC),"--p56h",str(H),"--p56g",str(G)]
        ok=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(ok.returncode,0,ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["p55n_score_estimatif"],53)
        refused=subprocess.run(args+["--exiger-certification"],capture_output=True)
        self.assertEqual(refused.returncode,3)
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"audit.json"
            save=subprocess.run(args+["--rapport",str(dest)],capture_output=True)
            self.assertEqual(save.returncode,0,save.stderr)
            self.assertEqual(subprocess.run(args+["--rapport",str(dest)],capture_output=True).returncode,2)

if __name__=="__main__":
    unittest.main()
