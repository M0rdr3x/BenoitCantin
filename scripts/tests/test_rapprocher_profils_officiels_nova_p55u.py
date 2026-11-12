"""Tests P55U : quatre profils de menages et PME officiels 2026."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import rapprocher_profils_officiels_nova_p55u as m

class TestP55U(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.load()
        cls.rows=cls.cfg['profils_menages_automne_2025']

    def test_01_schema(self):
        self.assertEqual(self.cfg['schema_version'],'P55U-1')

    def test_02_sources_autumn(self):
        self.assertEqual(self.cfg['sources']['mise_a_jour_2025']['date'],'2025-11-25')

    def test_03_source_table_households(self):
        self.assertEqual(self.cfg['sources']['mise_a_jour_2025']['table_menages'],'B.8')

    def test_04_source_page_households(self):
        self.assertEqual(self.cfg['sources']['mise_a_jour_2025']['page_menages'],'B.14')

    def test_05_source_table_sme(self):
        self.assertEqual(self.cfg['sources']['mise_a_jour_2025']['table_pme'],'B.14')

    def test_06_source_page_sme(self):
        self.assertEqual(self.cfg['sources']['mise_a_jour_2025']['page_pme'],'B.28')

    def test_07_june_2026(self):
        self.assertEqual(self.cfg['sources']['simulation_2026_actualisee']['date_mise_a_jour'],'2026-06-17')

    def test_08_four_households(self):
        self.assertEqual(len(self.cfg['profils_menages_automne_2025']),4)

    def test_09_first_household(self):
        self.assertEqual(self.rows[0]['gain_publie_cad'],217)

    def test_10_second_household(self):
        self.assertEqual(self.rows[1]['gain_publie_cad'],245)

    def test_11_single_parent(self):
        self.assertEqual(self.rows[2]['gain_publie_cad'],363)

    def test_12_couple(self):
        self.assertEqual(self.rows[3]['gain_publie_cad'],440)

    def test_13_singles_social_aid(self):
        self.assertEqual(self.rows[0]['montants']['prestations_aide_sociale'],192)

    def test_14_singles_solidarity(self):
        self.assertEqual(self.rows[0]['montants']['credit_solidarite'],25)

    def test_15_worker_tax(self):
        self.assertEqual(self.rows[1]['montants']['impot_revenu'],87)

    def test_16_worker_qpp(self):
        self.assertEqual(self.rows[1]['montants']['rrq'],47)

    def test_17_worker_qpip(self):
        self.assertEqual(self.rows[1]['montants']['rqap'],32)

    def test_18_single_parent_family_allowance(self):
        self.assertEqual(self.rows[2]['montants']['allocation_famille'],115)

    def test_19_two_income_total(self):
        self.assertEqual(self.rows[3]['revenu_travail_annuel_cad'],100000)

    def test_20_two_incomes(self):
        self.assertEqual(self.rows[3]['repartition_revenus_individuels_cad'],[50000,50000])

    def test_21_couple_allowance(self):
        self.assertEqual(self.rows[3]['montants']['allocation_famille'],168)

    def test_22_total_households_match(self):
        self.assertEqual([sum(v for v in r['montants'].values() if v is not None) for r in self.rows],[217,245,363,440])

    def test_23_sme_staff(self):
        self.assertEqual(self.cfg['cas_pme_automne_2025']['employes'],10)

    def test_24_sme_wages(self):
        self.assertEqual(self.cfg['cas_pme_automne_2025']['salaire_unitaire_annuel_cad'],55000)

    def test_25_sme_rrq(self):
        self.assertEqual(self.cfg['cas_pme_automne_2025']['rrq_variation_reduction_cad'],515)

    def test_26_sme_qpip(self):
        self.assertEqual(self.cfg['cas_pme_automne_2025']['rqap_variation_reduction_cad'],495)

    def test_27_sme_total(self):
        self.assertEqual(self.cfg['cas_pme_automne_2025']['reduction_cotisations_cad'],1010)

    def test_28_new_case_gain(self):
        self.assertEqual(self.cfg['temoin_plus_recent_2026']['gain_publie_cad'],847)

    def test_29_no_direct_comparison(self):
        self.assertEqual(self.cfg['temoin_plus_recent_2026']['comparable_directement_avec_U02'],False)

    def test_30_missing_incidence(self):
        self.assertEqual(self.cfg['couverture']['montants_incidence_p52d_inconnus'],720)

    def test_31_missing_finance(self):
        self.assertEqual(self.cfg['couverture']['postes_budgetaires_p52b_inconnus'],600)

    def test_32_score(self):
        self.assertEqual(self.cfg['couverture']['pourcentage_programme_estime_inchange'],53)

    def test_33_guard_count(self):
        self.assertEqual(len(m.REQUIRED_SAFE),26)

    def test_34_task_count(self):
        self.assertEqual(len(self.cfg['preuves_necessaires']),8)

    def test_35_report_four(self):
        self.assertEqual(m.report(self.cfg)['nombre_menages_illustres'],4)

    def test_36_report_firm(self):
        self.assertEqual(m.report(self.cfg)['pme_exemple_10_employes_reduction_cotisations_cad'],1010)

    def test_37_report_no_rate(self):
        self.assertEqual(m.report(self.cfg)['taux_nova_pct'],None)

    def test_38_report_no_go(self):
        self.assertEqual(m.report(self.cfg)['decision'],m.NO_GO)

    def test_39_reject_changed_benefit(self):
        d=copy.deepcopy(self.cfg)
        d['profils_menages_automne_2025'][0]['montants']['credit_solidarite']=26
        with self.assertRaises(ValueError):m.validate(d)

    def test_40_reject_misreported_total(self):
        d=copy.deepcopy(self.cfg)
        d['profils_menages_automne_2025'][2]['gain_publie_cad']=364
        with self.assertRaises(ValueError):m.validate(d)

    def test_41_reject_blended_case(self):
        d=copy.deepcopy(self.cfg)
        d['temoin_plus_recent_2026']['comparable_directement_avec_U02']=True
        with self.assertRaises(ValueError):m.validate(d)

    def test_42_reject_fabricated_new_policy(self):
        d=copy.deepcopy(self.cfg)
        d['couverture']['gains_nova_attribuables_cad']=100
        with self.assertRaises(ValueError):m.validate(d)

    def test_43_reject_pme_fiction(self):
        d=copy.deepcopy(self.cfg)
        d['cas_pme_automne_2025']['reduction_cotisations_cad']=2020
        with self.assertRaises(ValueError):m.validate(d)

    def test_44_reject_guard_off(self):
        d=copy.deepcopy(self.cfg)
        d['garde_fous']['p55n_53_pourcent_inchange']=False
        with self.assertRaises(ValueError):m.validate(d)

    def test_45_reject_closing_task(self):
        d=copy.deepcopy(self.cfg)
        d['preuves_necessaires'][0]['statut']='TERMINE'
        with self.assertRaises(ValueError):m.validate(d)

    def test_46_reject_false_year(self):
        d=copy.deepcopy(self.cfg)
        d['sources']['mise_a_jour_2025']['date']='2026-06-17'
        with self.assertRaises(ValueError):m.validate(d)

    def test_47_reject_zero_instead_of_missing(self):
        d=copy.deepcopy(self.cfg)
        d['profils_menages_automne_2025'][0]['montants']['rrq']=0
        with self.assertRaises(ValueError):m.validate(d)

    def test_48_cli_default(self):
        self.assertEqual(m.main([]),0)

    def test_49_cli_refuses_go(self):
        self.assertEqual(m.main(['--exiger-incidence-nova']),3)

    def test_50_cli_export(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'r.json'
            self.assertEqual(m.main(['--bilan-public',str(file)]),0)
            report=json.loads(file.read_text())
            self.assertEqual(report['temoin_plus_recent_personne_seule_50000_cad'],847)
            self.assertEqual(report['temoin_automne_2025_personne_seule_50000_cad'],245)
            self.assertFalse(report['comparaison_directe_des_deux_temoins_autorisee'])

    def test_51_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'r.json';file.write_text('protect')
            self.assertEqual(m.main(['--bilan-public',str(file)]),2)
            self.assertEqual(file.read_text(),'protect')

if __name__=='__main__':
    unittest.main()
