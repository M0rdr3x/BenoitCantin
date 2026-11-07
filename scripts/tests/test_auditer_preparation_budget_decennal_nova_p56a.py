"""P56A : audit reproductible et tests des inconnues, schémas, et faux GO."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/auditer_preparation_budget_decennal_nova_p56a.py'
TEMPLATE = ROOT / 'projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json'
REGISTER = ROOT / 'projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json'
spec=importlib.util.spec_from_file_location('p56a',SOURCE)
p56a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p56a)

class TestP56A(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template=json.loads(TEMPLATE.read_text(encoding='utf-8'))
        cls.registry=json.loads(REGISTER.read_text(encoding='utf-8'))
        cls.baseline=p56a.auditer(cls.template,cls.registry)

    def mutated(self):
        return copy.deepcopy(self.template)

    def run_case(self, d):
        return p56a.auditer(d,self.registry)

    def test_01_schema(self):
        self.assertEqual(self.baseline['schema_version'],'P56A-1')
    def test_02_60_scenarios(self):
        self.assertEqual(self.baseline['nombre_lignes'],60)
    def test_03_deux_regimes(self):
        self.assertEqual(len(self.baseline['regimes_distincts']),2)
    def test_04_trois_trajectoires(self):
        self.assertEqual(len(self.baseline['trajectoires_distinctes']),3)
    def test_05_dix_ans(self):
        self.assertEqual(self.baseline['horizon_exercices_debut'],list(range(2027,2037)))
    def test_06_660_postes(self):
        self.assertEqual(self.baseline['nombre_champs_monetaires_theoriques'],660)
    def test_07_600_manquants(self):
        self.assertEqual(self.baseline['nombre_champs_monetaires_inconnus'],600)
    def test_08_60_zeros_prudents_pas_recettes(self):
        self.assertEqual(self.baseline['nombre_hypotheses_zero_anti_evasion'],60)
    def test_09_valeurs_non_authentifiees(self):
        self.assertEqual(self.baseline['nombre_valeurs_monetaires_presentes_non_authentifiees'],60)
    def test_10_aucune_annee_remplie(self):
        self.assertEqual(self.baseline['annees_scenarios_entierement_renseignees'],0)
    def test_11_annees_toutes_60_manquants(self):
        self.assertTrue(all(v==60 for v in self.baseline['inconnues_par_annee'].values()))
    def test_12_regimes_separes_300_manquants(self):
        self.assertEqual(set(self.baseline['inconnues_par_regime'].values()),{300})
    def test_13_attestations_non_validees_240(self):
        self.assertEqual(self.baseline['attestations_p52b_non_validees'],240)
    def test_14_garde_fous_budget_120(self):
        self.assertEqual(self.baseline['conditions_budget_precedent_dette_inconnues'],120)
    def test_15_preuves_p52a_20(self):
        self.assertEqual(self.baseline['preuves_fiscales_p52a_non_validees'],20)
    def test_16_ecart_arithmetique_non_officiel(self):
        r=self.baseline['reference_nova_non_certifiee_2026_2027']
        self.assertEqual(r['difference_arithmetique_gcad'],'-4.265')
        self.assertFalse(r['difference_est_solde_budgetaire_officiel'])
    def test_17_interdit_double_service_dette(self):
        r=self.baseline['reference_nova_non_certifiee_2026_2027']
        self.assertTrue(r['service_dette_indicatif_deja_inclus_dans_depenses'])
        self.assertFalse(r['service_dette_ajoute_une_deuxieme_fois'])
    def test_18_decision_no_go(self):
        self.assertEqual(self.baseline['decision'],'NO_GO_AUTOMATIQUE')
    def test_19_53_pourcent_non_modifie(self):
        self.assertEqual(self.baseline['pourcentage_maturite_p55n_estimatif'],53)
    def test_20_pas_de_budget_certifie(self):
        self.assertFalse(self.baseline['budget_decennal_certifie'])
    def test_21_municipal_non_concilie(self):
        self.assertFalse(self.baseline['comptes_municipaux_consolides_et_rapproches'])
    def test_22_pas_avis_professionnel(self):
        self.assertFalse(self.baseline['certification_independante'])
    def test_23_abandon_annee(self):
        d=self.mutated()
        del d['regimes']['QUEBEC_DANS_CANADA']['trajectoires']['central'][0]
        with self.assertRaises(ValueError):self.run_case(d)
    def test_24_refuse_valeur_non_decimale(self):
        d=self.mutated()
        d['regimes']['QUEBEC_DANS_CANADA']['trajectoires']['central'][0]['recettes']['impot_revenu_net']=42.0
        with self.assertRaises(ValueError):self.run_case(d)
    def test_25_refuse_source_absente(self):
        d=self.mutated()
        d['regimes']['QUEBEC_DANS_CANADA']['trajectoires']['central'][0]['recettes']['impot_revenu_net']='1.0'
        with self.assertRaises(ValueError):self.run_case(d)
    def test_26_refuse_revenu_anti_evasion_invente(self):
        d=self.mutated()
        d['regimes']['QUEBEC_DANS_CANADA']['trajectoires']['central'][0]['recettes']['anti_evasion_additionnelle_nette']='1'
        with self.assertRaises(ValueError):self.run_case(d)
    def test_27_refuse_deux_regimes_identiques_ecrases(self):
        d=self.mutated()
        del d['regimes']['QUEBEC_SOUVERAIN']
        with self.assertRaises(ValueError):self.run_case(d)
    def test_28_refuse_attestation_type_incorrect(self):
        d=self.mutated()
        d['regimes']['QUEBEC_DANS_CANADA']['trajectoires']['central'][0]['perimetre_reconcilie']='oui'
        with self.assertRaises(ValueError):self.run_case(d)
    def test_29_cli_json_documente(self):
        proc=subprocess.run([sys.executable,str(SOURCE),'--gabarit',str(TEMPLATE),
                             '--registre',str(REGISTER)],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['nombre_champs_monetaires_inconnus'],600)
    def test_30_refuse_certification_en_cli(self):
        proc=subprocess.run([sys.executable,str(SOURCE),'--gabarit',str(TEMPLATE),
                             '--registre',str(REGISTER),'--exiger-budget-certifie'],capture_output=True)
        self.assertEqual(proc.returncode,3)
    def test_31_refuse_ecrasement_rapport(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'rapport.json'
            cmd=[sys.executable,str(SOURCE),'--gabarit',str(TEMPLATE),
                 '--registre',str(REGISTER),'--rapport',str(out)]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
    def test_32_retient_null_sur_chaque_ligne(self):
        self.assertTrue(all(s['solde_simule_gcad'] is None for s in self.baseline['annees_scenarios']))
    def test_33_ligne_individualisee(self):
        self.assertEqual(self.baseline['annees_scenarios'][0]['exercice_debut'],2027)
        self.assertEqual(self.baseline['annees_scenarios'][0]['nombre_valeurs_financieres_absentes'],10)
    def test_34_pas_de_transfert_intra_gouvernemental_fictif(self):
        self.assertFalse(self.baseline['transferts_intragouvernementaux_elimines_et_verifies'])

if __name__=='__main__':
    unittest.main()
