"""P55W - taux officiels RRQ RQAP AE 2026, sans gains politiques inventes."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import calculer_cotisations_salariales_nova_p55w as m

class TestP55W(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.load()
        cls.calc=m.payroll('50000.00')

    def test_01_schema(self):
        self.assertEqual(self.cfg['schema_version'],'P55W-1')

    def test_02_date(self):
        self.assertEqual(self.cfg['date_reference'],'2026-11-07')

    def test_03_decision(self):
        self.assertEqual(self.cfg['decision'],m.NO_GO)

    def test_04_rrq_exemption(self):
        self.assertEqual(self.cfg['parametres']['rrq']['exemption_annuelle_cad'],'3500.00')

    def test_05_rrq_primary_cap(self):
        self.assertEqual(self.cfg['parametres']['rrq']['max_gains_premier_palier_cad'],'74600.00')

    def test_06_rrq_second_cap(self):
        self.assertEqual(self.cfg['parametres']['rrq']['max_gains_supplementaires_cad'],'85000.00')

    def test_07_rrq_primary_rate(self):
        self.assertEqual(self.cfg['parametres']['rrq']['taux_premier_palier_salarie_pct'],'6.30')

    def test_08_rrq_secondary_rate(self):
        self.assertEqual(self.cfg['parametres']['rrq']['taux_second_palier_salarie_pct'],'4.00')

    def test_09_qpip_employee_rate(self):
        self.assertEqual(self.cfg['parametres']['rqap']['taux_salarie_pct'],'0.430')

    def test_10_qpip_employer_rate(self):
        self.assertEqual(self.cfg['parametres']['rqap']['taux_employeur_pct'],'0.602')

    def test_11_ei_employee_rate(self):
        self.assertEqual(self.cfg['parametres']['ae']['taux_salarie_quebec_pct'],'1.30')

    def test_12_ei_employer_rate(self):
        self.assertEqual(self.cfg['parametres']['ae']['taux_employeur_quebec_pct'],'1.82')

    def test_13_ei_max_wage(self):
        self.assertEqual(self.cfg['parametres']['ae']['max_salaire_assurable_cad'],'68900.00')

    def test_14_qpip_max_wage(self):
        self.assertEqual(self.cfg['parametres']['rqap']['max_salaire_assurable_cad'],'103000.00')

    def test_15_rrq_employee_50000(self):
        self.assertEqual(self.calc['rrq_salarie_cad'],'2929.50')

    def test_16_qpip_employee_50000(self):
        self.assertEqual(self.calc['rqap_salarie_cad'],'215.00')

    def test_17_ei_employee_50000(self):
        self.assertEqual(self.calc['ae_salarie_cad'],'650.00')

    def test_18_employee_total_50000(self):
        self.assertEqual(self.calc['total_salarie_trois_regimes_cad'],'3794.50')

    def test_19_rrq_employer_50000(self):
        self.assertEqual(self.calc['rrq_employeur_cad'],'2929.50')

    def test_20_qpip_employer_50000(self):
        self.assertEqual(self.calc['rqap_employeur_cad'],'301.00')

    def test_21_ei_employer_50000(self):
        self.assertEqual(self.calc['ae_employeur_cad'],'910.00')

    def test_22_employer_total_50000(self):
        self.assertEqual(self.calc['total_employeur_trois_regimes_cad'],'4140.50')

    def test_23_wage_zero_rrq(self):
        self.assertEqual(m.payroll('0.00')['rrq_salarie_cad'],'0.00')

    def test_24_wage_zero_total(self):
        self.assertEqual(m.payroll('0.00')['total_salarie_trois_regimes_cad'],'0.00')

    def test_25_wage_3500_no_rrq(self):
        self.assertEqual(m.payroll('3500.00')['rrq_salarie_cad'],'0.00')

    def test_26_wage_3500_ei(self):
        self.assertEqual(m.payroll('3500.00')['ae_salarie_cad'],'45.50')

    def test_27_rrq_below_exemption(self):
        self.assertEqual(m.payroll('3499.00')['rrq_salarie_cad'],'0.00')

    def test_28_rrq_first_cap(self):
        self.assertEqual(m.payroll('74600.00')['rrq_salarie_cad'],'4479.30')

    def test_29_rrq_second_tier_1(self):
        self.assertEqual(m.payroll('74601.00')['rrq_salarie_cad'],'4479.34')

    def test_30_rrq_second_cap(self):
        self.assertEqual(m.payroll('85000.00')['rrq_salarie_cad'],'4895.30')

    def test_31_rrq_above_cap(self):
        self.assertEqual(m.payroll('200000.00')['rrq_salarie_cad'],'4895.30')

    def test_32_ei_above_cap(self):
        self.assertEqual(m.payroll('200000.00')['ae_salarie_cad'],'895.70')

    def test_33_ei_employer_above_cap(self):
        self.assertEqual(m.payroll('200000.00')['ae_employeur_cad'],'1253.98')

    def test_34_qpip_above_cap(self):
        self.assertEqual(m.payroll('200000.00')['rqap_salarie_cad'],'442.90')

    def test_35_qpip_employer_above_cap(self):
        self.assertEqual(m.payroll('200000.00')['rqap_employeur_cad'],'620.06')

    def test_36_employee_max_three(self):
        self.assertEqual(m.payroll('200000.00')['total_salarie_trois_regimes_cad'],'6233.90')

    def test_37_employer_max_three(self):
        self.assertEqual(m.payroll('200000.00')['total_employeur_trois_regimes_cad'],'6769.34')

    def test_38_assumptions_count(self):
        self.assertEqual(len(self.cfg['hypotheses_obligatoires']),12)

    def test_39_protections_count(self):
        self.assertEqual(len(self.cfg['protections']),22)

    def test_40_actions_count(self):
        self.assertEqual(len(self.cfg['actions']),8)

    def test_41_unknown_p52d(self):
        self.assertEqual(m.public_report(self.cfg,'50000.00')['p52d_montants_inconnus'],720)

    def test_42_unknown_p52b(self):
        self.assertEqual(m.public_report(self.cfg,'50000.00')['p52b_montants_inconnus'],600)

    def test_43_score_unchanged(self):
        self.assertEqual(m.public_report(self.cfg,'50000.00')['score_completude_estime_pct'],53)

    def test_44_not_nova_rate(self):
        self.assertEqual(m.public_report(self.cfg,'50000.00')['taux_nova_propose_pct'],None)

    def test_45_not_nova(self):
        self.assertFalse(self.calc['montants_reels_garantis'])

    def test_46_not_all_employer_charges(self):
        self.assertFalse(self.calc['fss_et_autres_cotisations_employeur_inclus'])

    def test_47_not_household_net(self):
        self.assertFalse(self.calc['impot_revenu_et_prestations_inclus'])

    def test_48_no_go_funding(self):
        self.assertFalse(self.calc['ressources_de_remplacement_identifiees'])

    def test_49_reject_income_float(self):
        with self.assertRaises(ValueError):m.payroll(50000.0)

    def test_50_reject_income_negative(self):
        with self.assertRaises(ValueError):m.payroll('-1.00')

    def test_51_reject_income_scientific(self):
        with self.assertRaises(ValueError):m.payroll('5e4')

    def test_52_reject_income_3_decimal(self):
        with self.assertRaises(ValueError):m.payroll('50000.001')

    def test_53_reject_income_leading_zero(self):
        with self.assertRaises(ValueError):m.payroll('050000')

    def test_54_reject_income_huge(self):
        with self.assertRaises(ValueError):m.payroll('10000000.01')

    def test_55_reject_false_source_rate(self):
        c=copy.deepcopy(self.cfg)
        c['parametres']['rrq']['taux_premier_palier_salarie_pct']='7.00'
        with self.assertRaises(ValueError):m.check(c)

    def test_56_reject_false_employer_rate(self):
        c=copy.deepcopy(self.cfg)
        c['parametres']['ae']['taux_employeur_quebec_pct']='1.30'
        with self.assertRaises(ValueError):m.check(c)

    def test_57_reject_fake_rqap_cap(self):
        c=copy.deepcopy(self.cfg)
        c['parametres']['rqap']['max_salaire_assurable_cad']='50000.00'
        with self.assertRaises(ValueError):m.check(c)

    def test_58_reject_invented_example(self):
        c=copy.deepcopy(self.cfg)
        c['temoin_analytique_50000_cad']['total_salarie_trois_regimes_cad']='100.00'
        with self.assertRaises(ValueError):m.check(c)

    def test_59_reject_removed_exclusions(self):
        c=copy.deepcopy(self.cfg)
        c['hypotheses_obligatoires']['non_inclus_FSS_employeur_normes_travail_CNESST_et_autres_charges']=False
        with self.assertRaises(ValueError):m.check(c)

    def test_60_reject_missing_nogo(self):
        c=copy.deepcopy(self.cfg)
        c['protections']['no_go_automatique']=False
        with self.assertRaises(ValueError):m.check(c)

    def test_61_reject_fake_approval(self):
        c=copy.deepcopy(self.cfg)
        c['actions'][0]['statut']='TERMINE'
        with self.assertRaises(ValueError):m.check(c)

    def test_62_cli_default(self):
        self.assertEqual(m.main([]),0)

    def test_63_cli_gated(self):
        self.assertEqual(m.main(['--exiger-faisabilite']),3)

    def test_64_cli_wage(self):
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/'report.json'
            self.assertEqual(m.main(['--salaire','3500.00','--bilan-public',str(target)]),0)
            obj=json.loads(target.read_text())
            self.assertEqual(obj['cotisations_conditionnelles']['rrq_salarie_cad'],'0.00')
            self.assertFalse(obj['protection_et_financement_regimes_demontres'])

    def test_65_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/'report.json';target.write_text('conserver')
            self.assertEqual(m.main(['--bilan-public',str(target)]),2)
            self.assertEqual(target.read_text(),'conserver')

if __name__=='__main__':
    unittest.main()
