"""P56B : tests déterministes sur budget, préliminaire et comptes audités 2025-2026."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / 'scripts/rapprocher_versions_finances_nova_p56b.py'
ENTRY = ROOT / 'projets/projet-nova/etudes/P56B_SNAPSHOTS_FINANCES_2025_2026_SOURCES_OFFICIELLES.json'
spec=importlib.util.spec_from_file_location('p56b', CODE)
p56b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p56b)

class TestP56B(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(ENTRY.read_text(encoding="utf-8"))
        cls.base=p56b.audit(cls.data)
    def make(self):
        return copy.deepcopy(self.data)
    def rejette(self,d):
        with self.assertRaises(ValueError):p56b.audit(d)

    def test_01_version(self):
        self.assertEqual(self.base["schema_version"],"P56B-1")
    def test_02_trois_versions(self):
        self.assertEqual(self.base["nombre_snapshots"],3)
    def test_03_deux_sources(self):
        self.assertEqual(self.base["sources_officielles_distinctes"],2)
    def test_04_exercice_unique(self):
        self.assertEqual(self.base["exercice_compare"],"2025-2026")
    def test_05_revision_deficit_prelim_audite(self):
        self.assertEqual(self.base["rapprochement_preliminaire_vers_audite_mcad"]["variation_solde_comptable"],"-606")
    def test_06_revision_leb_prelim_audite(self):
        self.assertEqual(self.base["rapprochement_preliminaire_vers_audite_mcad"]["variation_solde_leb"],"-606")
    def test_07_revision_revenus(self):
        self.assertEqual(self.base["rapprochement_preliminaire_vers_audite_mcad"]["variation_revenus"],"-685")
    def test_08_revision_depenses(self):
        self.assertEqual(self.base["rapprochement_preliminaire_vers_audite_mcad"]["variation_depenses"],"-79")
    def test_09_revision_somme(self):
        r=self.base["rapprochement_preliminaire_vers_audite_mcad"]
        self.assertEqual(int(r["variation_revenus"])-int(r["variation_depenses"]),int(r["variation_solde_comptable"]))
    def test_10_budget_vs_audite_deficit(self):
        self.assertEqual(self.base["rapprochement_budget_initial_vers_audite_mcad"]["variation_solde_comptable"],"5928")
    def test_11_budget_vs_audite_leb(self):
        self.assertEqual(self.base["rapprochement_budget_initial_vers_audite_mcad"]["variation_solde_leb"],"5816")
    def test_12_budget_vs_audite_revenus(self):
        self.assertEqual(self.base["rapprochement_budget_initial_vers_audite_mcad"]["variation_revenus"],"4086")
    def test_13_budget_vs_audite_depenses(self):
        self.assertEqual(self.base["rapprochement_budget_initial_vers_audite_mcad"]["variation_depenses"],"158")
    def test_14_ratio_dette_en_points(self):
        self.assertEqual(self.base["variation_ratio_dette_nette_pib_points"],"0.1")
    def test_15_solde_comptable_audite(self):
        self.assertEqual(self.base["donnees_auditees_references_mcad"]["solde_comptable"],"-5502")
    def test_16_solde_leb_audite(self):
        self.assertEqual(self.base["donnees_auditees_references_mcad"]["solde_budgetaire_leb"],"-7791")
    def test_17_aucune_economie_nova(self):
        self.assertTrue(self.base["revisions_comptables_ne_sont_pas_des_economies_nova"])
        self.assertFalse(self.base["budget_nova_certifie"])
    def test_18_pas_de_transposition_2027_2036(self):
        self.assertFalse(self.base["transposition_automatique_aux_exercices_2027_2036"])
    def test_19_maturite_inchangee(self):
        self.assertEqual(self.base["score_p55n_estime"],53)
    def test_20_inconnues_restent_600(self):
        self.assertEqual(self.base["inconnues_p52b_conservees"],600)
    def test_21_non_adoption(self):
        self.assertEqual(self.base["decision"],"NO_GO_AUTOMATIQUE")
    def test_22_refuse_version_definitive_preliminaire(self):
        d=self.make();d["snapshots"]["PRELIMINAIRE_JUIN_2026"]["statut"]="RESULTAT_ANNUEL_COMPTES_PUBLICS_AUDITES"
        self.rejette(d)
    def test_23_refuse_cadre_souverain(self):
        d=self.make();d["territoire"]="QUEBEC_SOUVERAIN"
        self.rejette(d)
    def test_24_refuse_2026_2027(self):
        d=self.make();d["exercice"]="2026-2027"
        self.rejette(d)
    def test_25_refuse_changement_source(self):
        d=self.make();d["sources"]["COMPTES_PUBLICS_AUDITES_2025_2026"]["url"]="https://fake.example/audit.pdf"
        self.rejette(d)
    def test_26_refuse_changement_page(self):
        d=self.make();d["snapshots"]["COMPTES_AUDITES_JUILLET_2026"]["pages_par_metrique"]["solde_comptable_mcad"]=199
        self.rejette(d)
    def test_27_refuse_oubli_page(self):
        d=self.make();del d["snapshots"]["PRELIMINAIRE_JUIN_2026"]["pages_par_metrique"]["solde_comptable_mcad"]
        self.rejette(d)
    def test_28_refuse_montant_flot(self):
        d=self.make();d["snapshots"]["COMPTES_AUDITES_JUILLET_2026"]["donnees"]["revenus_totaux_mcad"]=160428.0
        self.rejette(d)
    def test_29_refuse_ecart_arithmetique(self):
        d=self.make();d["snapshots"]["COMPTES_AUDITES_JUILLET_2026"]["donnees"]["revenus_totaux_mcad"]="160429"
        self.rejette(d)
    def test_30_refuse_confusion_leb(self):
        d=self.make();d["snapshots"]["COMPTES_AUDITES_JUILLET_2026"]["donnees"]["solde_leb_mcad"]="-5502"
        self.rejette(d)
    def test_31_refuse_provision_budget_absente(self):
        d=self.make();d["snapshots"]["BUDGET_INITIAL_REPRIS_DANS_COMPTES_PUBLICS"]["donnees"]["provision_eventualites_mcad"]=None
        del d["snapshots"]["BUDGET_INITIAL_REPRIS_DANS_COMPTES_PUBLICS"]["pages_par_metrique"]["provision_eventualites_mcad"]
        self.rejette(d)
    def test_32_refuse_taux_dette_incorrect(self):
        d=self.make();d["snapshots"]["COMPTES_AUDITES_JUILLET_2026"]["donnees"]["ratio_dette_nette_pib_pct"]="100.01"
        self.rejette(d)
    def test_33_refuse_une_source_absente(self):
        d=self.make();del d["sources"]["COMPTES_PUBLICS_AUDITES_2025_2026"]
        self.rejette(d)
    def test_34_refuse_faux_go(self):
        d=self.make();d["validation_budget_nova"]=True
        self.rejette(d)
    def test_35_refuse_pourcentage_non_prouve(self):
        d=self.make();d["score_p55n_estime"]=99
        self.rejette(d)
    def test_36_refuse_faux_nombre_inconnues(self):
        d=self.make();d["inconnues_p52b_conservees"]=0
        self.rejette(d)
    def test_37_cli_json_sans_ecrasement(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"bilan.json"
            args=[sys.executable,str(CODE),"--entree",str(ENTRY),"--rapport",str(target)]
            first=subprocess.run(args,capture_output=True)
            self.assertEqual(first.returncode,0,first.stderr)
            self.assertEqual(json.loads(target.read_text())["rapprochement_preliminaire_vers_audite_mcad"]["variation_solde_comptable"],"-606")
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,2)
    def test_38_cli_refus_certification_code_3(self):
        args=[sys.executable,str(CODE),"--entree",str(ENTRY),"--exiger-budget-certifie"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)
    def test_39_cli_stdin_non_autorise(self):
        args=[sys.executable,str(CODE),"--entree",str(ENTRY)]
        out=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(out.returncode,0,out.stderr)
        self.assertEqual(json.loads(out.stdout)["budget_nova_certifie"],False)
    def test_40_pas_de_certification_de_competence(self):
        self.assertFalse(self.base["certification_independante_nova"])
if __name__ == "__main__":
    unittest.main()
