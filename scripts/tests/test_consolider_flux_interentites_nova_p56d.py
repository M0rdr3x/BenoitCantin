"""P56D : 32 controles des transferts, emprunts, fonds, perimetres et refus de GO."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"scripts/consolider_flux_interentites_nova_p56d.py"
CASE=ROOT/"projets/projet-nova/etudes/P56D_EXEMPLE_FICTIF_FLUX_INTERENTITES_2026_2027.json"
spec=importlib.util.spec_from_file_location("p56d",SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class P56DTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(CASE.read_text(encoding="utf-8"))
        cls.result=m.analyser(cls.data)
        cls.p=cls.result["vues"]["ETAT_QUEBEC_FICTIF_NON_OFFICIEL"]
        cls.g=cls.result["vues"]["SECTEUR_PUBLIC_QC_ELARGI_FICTIF_NON_OFFICIEL"]
    def data_copy(self):
        return copy.deepcopy(self.data)
    def flow(self,d,i):
        return next(f for f in d["flux"] if f["id"]==i)
    def rejette(self,d):
        with self.assertRaises(ValueError):
            m.analyser(d)

    def test_01_schema(self):self.assertEqual(self.result["schema_version"],"P56D-1")
    def test_02_territoire(self):self.assertEqual(self.result["territoire"],"QUEBEC_DANS_CANADA")
    def test_03_revenus_province(self):self.assertEqual(self.p["revenus_externes_fictifs_mcad"],"40.00")
    def test_04_depenses_province(self):self.assertEqual(self.p["depenses_externes_fictives_mcad"],"155.00")
    def test_05_solde_province(self):self.assertEqual(self.p["solde_arithmetique_fictif_mcad"],"-115.00")
    def test_06_transferts_interne_province(self):self.assertEqual(self.p["transferts_internes_elimines_fictifs_mcad"],"30.00")
    def test_07_revenus_public_elargi(self):self.assertEqual(self.g["revenus_externes_fictifs_mcad"],"250.00")
    def test_08_depenses_public_elargi(self):self.assertEqual(self.g["depenses_externes_fictives_mcad"],"167.00")
    def test_09_solde_public_elargi(self):self.assertEqual(self.g["solde_arithmetique_fictif_mcad"],"83.00")
    def test_10_eliminations_public_elargi(self):self.assertEqual(self.g["transferts_internes_elimines_fictifs_mcad"],"142.00")
    def test_11_emprunt_financement_province(self):self.assertEqual(self.p["financement_par_emprunt_hors_revenus_mcad"],"20.00")
    def test_12_emprunt_financement_public(self):self.assertEqual(self.g["financement_par_emprunt_hors_revenus_mcad"],"20.00")
    def test_13_transfert_100_charge_etat(self):
        line=next(x for x in self.p["lignes"] if x["id"]=="F02")
        self.assertEqual(line["classification"],"DEPENSE_EXTERNE_DE_LA_VUE")
    def test_14_transfert_100_elimine_elargi(self):
        line=next(x for x in self.g["lignes"] if x["id"]=="F02")
        self.assertEqual(line["classification"],"ELIMINE_INTERNE_POUR_CETTE_VUE")
    def test_15_fonds_affecte_interne_non_economie(self):
        self.assertFalse(self.result["fonds_affecte_automatiquement_disponible"])
    def test_16_impot_municipal_reconnu(self):
        self.assertEqual(next(x for x in self.g["lignes"] if x["id"]=="F06")["classification"],"REVENU_EXTERNE_DE_LA_VUE")
    def test_17_preuve_economies_manquante(self):
        self.assertIsNone(self.g["economies_reelles_certifiees_mcad"])
    def test_18_dette_non_recette(self):self.assertFalse(self.result["financement_dette_traite_comme_recette"])
    def test_19_aucune_projection(self):self.assertFalse(self.result["transposition_aux_exercices_p52b"])
    def test_20_maturite_53(self):self.assertEqual(self.result["p55n_maturite_estimee_pourcent"],53)
    def test_21_no_go(self):self.assertEqual(self.result["decision"],"NO_GO_AUTOMATIQUE")
    def test_22_refuse_taux_souverain(self):
        d=self.data_copy();d["territoire"]="QUEBEC_SOUVERAIN";self.rejette(d)
    def test_23_refuse_nature_auditee(self):
        d=self.data_copy();d["nature"]="AUDITE";self.rejette(d)
    def test_24_refuse_suppression_du_transfert_municipal(self):
        d=self.data_copy();d["flux"]=[f for f in d["flux"] if f["id"]!="F02"];self.rejette(d)
    def test_25_refuse_double_transfert(self):
        d=self.data_copy();d["flux"][1]["id"]="F01";self.rejette(d)
    def test_26_refuse_contournement_de_competence(self):
        d=self.data_copy();self.flow(d,"F02")["destination"]="ORGANISME_QC";self.rejette(d)
    def test_27_refuse_impot_local_rebaptise(self):
        d=self.data_copy();self.flow(d,"F06")["nature"]="REDEVANCE";self.rejette(d)
    def test_28_refuse_emploi_zero_fictif_non_prouve(self):
        d=self.data_copy();self.flow(d,"F05")["provenance"]="RAPPORT_OFFICIEL";self.rejette(d)
    def test_29_refuse_fonds_non_protege(self):
        d=self.data_copy();next(e for e in d["entites"] if e["id"]=="FONDS_ETAT_AFFECTE")["affectation_protegee"]=False;self.rejette(d)
    def test_30_null_propage_sans_zero(self):
        d=self.data_copy();self.flow(d,"F02")["montant_mcad"]=None
        r=m.analyser(d)
        self.assertIsNone(r["vues"]["ETAT_QUEBEC_FICTIF_NON_OFFICIEL"]["solde_arithmetique_fictif_mcad"])
        self.assertIsNone(r["vues"]["SECTEUR_PUBLIC_QC_ELARGI_FICTIF_NON_OFFICIEL"]["solde_arithmetique_fictif_mcad"])
    def test_31_refuse_certification_cli(self):
        r=subprocess.run([sys.executable,str(SRC),"--entree",str(CASE),"--exiger-faisabilite"],capture_output=True)
        self.assertEqual(r.returncode,3)
    def test_32_cli_success_et_refus_ecrasement(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/"rapport.json"
            args=[sys.executable,str(SRC),"--entree",str(CASE),"--rapport",str(report)]
            r=subprocess.run(args,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["decision"],"NO_GO_AUTOMATIQUE")
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,2)

if __name__=="__main__":
    unittest.main()
