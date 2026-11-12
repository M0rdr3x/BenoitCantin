"""P56U : cohérence rédactionnelle avec les scénarios et les services à financer."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/verifier_concordance_chapitre_finances_nova_p56u.py"
DOC=ROOT/"projets/projet-nova/programme/P56U_CHAPITRE_CANDIDAT_FINANCES_FISCALITE_ET_CONTINUITE_SERVICES.md"
P56S=ROOT/"projets/projet-nova/etudes/P56S_TROIS_OPTIONS_FISCALES_2027_2031_ET_CONDITIONS_PROTECTION.json"
P56T=ROOT/"projets/projet-nova/etudes/P56T_BASE_OFFICIELLE_DEPENSES_PORTEFEUILLES_2025_2029_PROTECTION_SERVICES.json"
P56O=ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json"
P55N=ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
spec=importlib.util.spec_from_file_location("p56u",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestP56U(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.txt=DOC.read_text(encoding="utf-8")
        cls.data=[json.loads(p.read_text(encoding="utf-8")) for p in (P56S,P56T,P56O,P55N)]
        cls.result=m.evaluer(cls.txt,*cls.data)
    def altered(self,n=0):return copy.deepcopy(self.data[n])
    def reject_doc(self,txt):
        with self.assertRaises(ValueError):m.evaluer(txt,*self.data)
    def reject_data(self,changed,index=0):
        args=list(self.data);args[index]=changed
        with self.assertRaises(ValueError):m.evaluer(self.txt,*args)
    def test_01_name(self):self.assertEqual(self.result["jalon"],"P56U")
    def test_02_sixteen_articles(self):self.assertEqual(self.result["articles"],16)
    def test_03_53_percent(self):self.assertEqual(self.result["score_interne_estime"],53)
    def test_04_services_core(self):self.assertEqual(self.result["services_2027_2028_pivot_mcad"],"120433")
    def test_05_spending_total(self):self.assertEqual(self.result["depenses_totales_portefeuilles_2027_2028_mcad"],"165049")
    def test_06_recettes_risque(self):self.assertEqual(self.result["recettes_a_remplacer_2027_2028_mcad"],"42875")
    def test_07_deficit_risque(self):self.assertEqual(self.result["deficit_test_2027_2028_mcad"],"-48570")
    def test_08_not_adopted(self):self.assertFalse(self.result["textes_officiellement_adoptes"])
    def test_09_budget_not_certified(self):self.assertFalse(self.result["budget_reforme_certifie"])
    def test_10_programme_not_done(self):self.assertFalse(self.result["programme_termine"])
    def test_11_no_go(self):self.assertEqual(self.result["decision"],"NO_GO_AUTOMATIQUE")
    def test_12_wrong_number_of_articles(self):
        self.reject_doc(self.txt.replace("### Article 16 —","### Section 16 —"))
    def test_13_duplicates_article(self):
        self.reject_doc(self.txt.replace("### Article 15 —","### Article 14 —"))
    def test_14_invalid_headline(self):
        self.reject_doc(self.txt.replace("# Projet Nova — Chapitre candidat P56U","# Programme appliqué"))
    def test_15_maturity_claim_missing(self):
        self.reject_doc(self.txt.replace("53 % estimés","100 % certifiés"))
    def test_16_no_explicit_nonadoption(self):
        self.reject_doc(self.txt.replace("non adopté","déjà adopté"))
    def test_17_wrong_loss_in_chapter(self):
        self.reject_doc(self.txt.replace("42,875 G$","52,875 G$"))
    def test_18_wrong_deficit_in_chapter(self):
        self.reject_doc(self.txt.replace("48,570 G$","58,570 G$"))
    def test_19_wrong_health_budget_in_chapter(self):
        self.reject_doc(self.txt.replace("120,433 G$","111,433 G$"))
    def test_20_wrong_total_in_chapter(self):
        self.reject_doc(self.txt.replace("165,049 G$","135,049 G$"))
    def test_21_missing_federal_legal_limit(self):
        self.reject_doc(self.txt.replace("Québec dans le Canada","Province imaginaire"))
    def test_22_missing_no_countertariff(self):
        self.reject_doc(self.txt.replace("contre-tarifs","tarifs réciproques"))
    def test_23_no_evidence_requirement(self):
        self.reject_doc(self.txt.replace("600 montants P52B","0 montant P52B"))
    def test_24_source_p56t_fabrication(self):
        x=self.altered(1);x["annees"][2]["noyau_sante_education_superieur_famille_mcad"]="130000"
        self.reject_data(x,1)
    def test_25_source_p56s_fabrication(self):
        x=self.altered(0);x["options"][2]["resultats_par_exercice"][0]["recettes_retirees_uniquement_dans_le_test_mcad"]="50000.00"
        self.reject_data(x,0)
    def test_26_source_p55n_fabrication(self):
        x=self.altered(3);x["score_estimatif"]=100;self.reject_data(x,3)
    def test_27_cli_and_no_overwrite(self):
        args=[sys.executable,str(SCRIPT),"--chapitre",str(DOC),"--p56s",str(P56S),
              "--p56t",str(P56T),"--p56o",str(P56O),"--barometre",str(P55N)]
        r=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["articles"],16)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"report.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,2)
    def test_28_cli_reject_adoption(self):
        args=[sys.executable,str(SCRIPT),"--chapitre",str(DOC),"--p56s",str(P56S),
              "--p56t",str(P56T),"--p56o",str(P56O),"--barometre",str(P55N),
              "--exiger-programme-adopte"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":unittest.main()
