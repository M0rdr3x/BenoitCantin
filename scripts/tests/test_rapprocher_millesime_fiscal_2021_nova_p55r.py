"""P55R - tests de statistiques fiscales 2021 pour deux assiettes distinctes."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import rapprocher_millesime_fiscal_2021_nova_p55r as m

class TestP55R(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=m.load()

    def test_01_schema(self):
        self.assertEqual(self.d['schema_version'],'P55R-1')

    def test_02_same_person_year(self):
        self.assertEqual(self.d['sources']['particuliers_2021']['annee_imposition'],2021)

    def test_03_same_corp_year(self):
        self.assertEqual(self.d['sources']['societes_2021']['annee_imposition'],2021)

    def test_04_individual_income(self):
        self.assertEqual(self.d['particuliers_2021']['revenu_imposable_mcad'],333898)

    def test_05_corporate_income(self):
        self.assertEqual(self.d['societes_2021']['revenu_imposable_quebec_mcad'],95784)

    def test_06_individual_tax(self):
        self.assertEqual(self.d['particuliers_2021']['impot_a_payer_mcad'],38503)

    def test_07_corp_tax(self):
        self.assertEqual(self.d['societes_2021']['impot_revenu_quebec_mcad'],10000)

    def test_08_individual_refundable(self):
        self.assertEqual(self.d['particuliers_2021']['credits_remboursables_mcad'],14118)

    def test_09_individual_net(self):
        self.assertEqual(self.d['particuliers_2021']['impot_apres_credits_remboursables_mcad'],24384)

    def test_10_exceptional_credit(self):
        self.assertEqual(self.d['particuliers_2021']['credit_exceptionnel_cout_vie_2021_mcad_approx'],7100)

    def test_11_total_corp_counts(self):
        self.assertEqual(self.d['societes_2021']['declarations'],564599)

    def test_12_corp_zero_income_tax(self):
        self.assertEqual(self.d['societes_2021']['societes_non_imposees_revenu'],322020)

    def test_13_corp_zero_both(self):
        self.assertEqual(self.d['societes_2021']['societes_sans_impot_ni_cotisation_fss'],239628)

    def test_14_corp_large_tax(self):
        self.assertEqual(self.d['societes_2021']['grandes_impots_cotisations_mcad'],8672)

    def test_15_pct_corp_large(self):
        self.assertEqual(round(100*8672/15327,1),56.6)

    def test_16_pct_corp_zero_tax(self):
        self.assertEqual(round(100*322020/564599,1),57.0)

    def test_17_pct_individual_zero_tax(self):
        self.assertEqual(round(100*2052/6975,1),29.4)

    def test_18_income_2023(self):
        self.assertEqual(self.d['rapprochements_autorises']['comparaison_2021_meme_annee']['particuliers_revenu_imposable_2023_mcad'],372261)

    def test_19_income_change(self):
        self.assertEqual(372261-333898,38363)

    def test_20_growth_pct(self):
        self.assertEqual(round(38363*100/333898,1),11.5)

    def test_21_guard_count(self):
        self.assertEqual(len(self.d['protections']),31)

    def test_22_actions_count(self):
        self.assertEqual(len(self.d['actions_preuves_humaines']),8)

    def test_23_report_score(self):
        self.assertEqual(m.report(self.d)['maturite_estimee_pct'],53)

    def test_24_report_unknown(self):
        self.assertEqual(m.report(self.d)['financement_p52b_montants_inconnus'],600)

    def test_25_report_no_go(self):
        self.assertEqual(m.report(self.d)['decision'],m.NO_GO)

    def test_26_report_no_rate(self):
        self.assertEqual(m.report(self.d)['taux_nova_pct'],None)

    def test_27_report_no_assiette(self):
        self.assertEqual(m.report(self.d)['assiette_nova_harmonisee_mcad'],None)

    def test_28_no_assiette_harmonisee(self):
        self.assertFalse(self.d['rapprochements_autorises']['comparaison_2021_meme_annee']['annee_commune_est_base_fiscale_harmonisee'])

    def test_29_reject_changed_person(self):
        d=copy.deepcopy(self.d)
        d['particuliers_2021']['revenu_imposable_mcad']=334000
        with self.assertRaises(ValueError):m.check(d)

    def test_30_reject_changed_corp(self):
        d=copy.deepcopy(self.d)
        d['societes_2021']['impot_revenu_quebec_mcad']+=1
        with self.assertRaises(ValueError):m.check(d)

    def test_31_reject_combined_tax_base(self):
        d=copy.deepcopy(self.d)
        d['rapprochements_autorises']['comparaison_2021_meme_annee']['assiette_combinee_validee_mcad']=429682
        with self.assertRaises(ValueError):m.check(d)

    def test_32_reject_fake_rate(self):
        d=copy.deepcopy(self.d)
        d['rapprochements_autorises']['comparaison_2021_meme_annee']['taux_nova_propose_pct']=15
        with self.assertRaises(ValueError):m.check(d)

    def test_33_reject_completed_action(self):
        d=copy.deepcopy(self.d)
        d['actions_preuves_humaines'][0]['statut']='TERMINE'
        with self.assertRaises(ValueError):m.check(d)

    def test_34_reject_guard_disabled(self):
        d=copy.deepcopy(self.d)
        d['protections']['SINJIRA_INCHANGE']=False
        with self.assertRaises(ValueError):m.check(d)

    def test_35_cli_default(self):
        self.assertEqual(m.main([]),0)

    def test_36_cli_certification_rejected(self):
        self.assertEqual(m.main(['--exiger-taux-certifie']),3)

    def test_37_cli_report(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'p55r.json'
            self.assertEqual(m.main(['--rapport-public',str(path)]),0)
            self.assertEqual(json.loads(path.read_text())['revenu_imposable_personnes_2021_mcad'],333898)

    def test_38_cli_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'p55r.json'
            path.write_text('conserver')
            self.assertEqual(m.main(['--rapport-public',str(path)]),2)
            self.assertEqual(path.read_text(),'conserver')

if __name__=='__main__':
    unittest.main()
