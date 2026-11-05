"""P55M — tests sur réserves affectées et engagements groupés, sans téléchargement."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import qualifier_reserves_et_obligations_somhac_nova_p55m as m

class TestP55M(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()

    def test_01_schema(self):
        self.assertEqual(self.cfg['schema_version'],'P55M-1')

    def test_02_year(self):
        self.assertEqual(self.cfg['exercice_source'],2024)

    def test_03_date(self):
        self.assertEqual(self.cfg['reference_date'],'2026-11-05')

    def test_04_two_sources(self):
        self.assertEqual(len(self.cfg['sources']),2)

    def test_05_source_2024(self):
        self.assertEqual(self.cfg['sources'][0]['id'],'VILLE_FINANCES_2024')

    def test_06_source_omhq(self):
        self.assertEqual(self.cfg['sources'][1]['id'],'OMHQ_SOMHAC_MANDAT')

    def test_07_source_pdf_caveat(self):
        self.assertTrue('SANS_SCREENSHOT' in m.SOURCE_VILLE['type_verification'])

    def test_08_guards_40(self):
        self.assertEqual(len(m.GUARDS),40)

    def test_09_all_guards(self):
        self.assertTrue(all(self.cfg['protections'].values()))

    def test_10_forbidden_10(self):
        self.assertEqual(len(m.FORBIDDEN),10)

    def test_11_open_tasks_6(self):
        self.assertEqual(len(m.review_tasks()),6)

    def test_12_reserve_2024(self):
        self.assertEqual(m.RESERVE['placements_affectes_reparations_majeures_cad'],4689663)

    def test_13_reserve_2023(self):
        self.assertEqual(m.RESERVE['comparatif_2023_cad'],4676844)

    def test_14_reserve_change(self):
        self.assertEqual(m.RESERVE['variation_2024_moins_2023_cad'],12819)

    def test_15_reserve_rate(self):
        self.assertEqual(m.percent(12819,4676844),'0.3')

    def test_16_reserve_no_free_cash(self):
        self.assertEqual(m.RESERVE['fonds_libres_disponibles_cad'],None)

    def test_17_convention_end(self):
        self.assertEqual(m.CONVENTION['annee_fin_indiquee'],2039)

    def test_18_convention_amount_unknown(self):
        self.assertEqual(m.CONVENTION['montant_annuel_cad'],None)

    def test_19_convention_termination_unknown(self):
        self.assertEqual(m.CONVENTION['peut_etre_resilie_sans_frais'],None)

    def test_20_schedule_6(self):
        self.assertEqual(len(m.DEBTS['annees']),6)

    def test_21_schedule_total(self):
        self.assertEqual(sum(x['organismes_controles_et_partenariats_cad'] for x in m.DEBTS['annees']),41856000)

    def test_22_schedule_consol(self):
        self.assertEqual(sum(x['total_consolide_cad'] for x in m.DEBTS['annees']),629684000)

    def test_23_schedule_2025(self):
        self.assertEqual(m.DEBTS['annees'][0]['organismes_controles_et_partenariats_cad'],10961000)

    def test_24_schedule_2026(self):
        self.assertEqual(m.DEBTS['annees'][1]['organismes_controles_et_partenariats_cad'],10301000)

    def test_25_schedule_2027(self):
        self.assertEqual(m.DEBTS['annees'][2]['organismes_controles_et_partenariats_cad'],9806000)

    def test_26_schedule_2028(self):
        self.assertEqual(m.DEBTS['annees'][3]['organismes_controles_et_partenariats_cad'],9124000)

    def test_27_schedule_2029(self):
        self.assertEqual(m.DEBTS['annees'][4]['organismes_controles_et_partenariats_cad'],1331000)

    def test_28_schedule_2030plus(self):
        self.assertEqual(m.DEBTS['annees'][5]['organismes_controles_et_partenariats_cad'],333000)

    def test_29_rights_group(self):
        self.assertEqual(m.RIGHTS['montant_groupe_cad'],8591000)

    def test_30_rights_somhac_unknown(self):
        self.assertEqual(m.RIGHTS['attribution_somhac_cad'],None)

    def test_31_obligations_somhac_unknown(self):
        self.assertEqual(m.DEBTS['attribution_somhac_cad'],None)

    def test_32_financial_validation(self):
        self.assertTrue(m.validate_financials(m.RESERVE,m.CONVENTION,m.DEBTS,m.RIGHTS))

    def test_33_public_report_schema(self):
        self.assertEqual(m.public_report()['schema_version'],'P55M-BILAN-PUBLIC-1')

    def test_34_public_table_schema(self):
        self.assertEqual(m.public_table()['schema_version'],'P55M-TABLE-PUBLIQUE-1')

    def test_35_no_free_cash(self):
        self.assertFalse(m.public_report()['reserve_somhac_est_tresorerie_libre'])

    def test_36_no_exclusive_obligations(self):
        self.assertFalse(m.public_report()['obligations_groupe_sont_somhac_seulement'])

    def test_37_no_exclusive_rights(self):
        self.assertFalse(m.public_report()['droits_groupe_sont_somhac_seulement'])

    def test_38_no_somhac_balance_sheet(self):
        self.assertFalse(m.public_report()['bilan_somhac_autonome_obtenu'])

    def test_39_no_reciprocal_journals(self):
        self.assertFalse(m.public_report()['ecritures_interorganismes_obtenues'])

    def test_40_no_pdf_hash(self):
        self.assertEqual(m.public_report()['pdf_originaux_verifies_par_sha_actuel'],0)

    def test_41_no_savings(self):
        self.assertEqual(m.public_report()['economies_certifiees_cad'],None)

    def test_42_no_go(self):
        self.assertEqual(m.public_report()['decision'],m.NO_GO)

    def test_43_no_merge(self):
        self.assertFalse(m.public_report()['fusion_main_autorisee'])

    def test_44_no_external_send(self):
        self.assertFalse(m.public_report()['transmission_externe_autorisee'])

    def test_45_open_p54e(self):
        self.assertEqual(m.public_report()['dossiers_p54e_ouverts'],4)

    def test_46_open_p54o(self):
        self.assertEqual(m.public_report()['blocages_p54o_non_leves'],10)

    def test_47_open_p54n(self):
        self.assertEqual(m.public_report()['taches_p54n_non_attestees'],40)

    def test_48_open_p54b(self):
        self.assertEqual(m.public_report()['controles_p54b_non_attestes'],96)

    def test_49_open_p54c(self):
        self.assertEqual(m.public_report()['controles_p54c_non_attestes'],8)

    def test_50_refuse_mutated_reserve(self):
        d=dict(m.RESERVE)
        d['placements_affectes_reparations_majeures_cad']+=1
        with self.assertRaises(ValueError):m.validate_financials(d,m.CONVENTION,m.DEBTS,m.RIGHTS)

    def test_51_refuse_mutated_period(self):
        d=copy.deepcopy(m.DEBTS)
        d['annees'][0]['organismes_controles_et_partenariats_cad']+=1
        with self.assertRaises(ValueError):m.validate_financials(m.RESERVE,m.CONVENTION,d,m.RIGHTS)

    def test_52_refuse_claimed_somhac(self):
        d=copy.deepcopy(m.DEBTS)
        d['attribution_somhac_cad']=41856000
        with self.assertRaises(ValueError):m.validate_financials(m.RESERVE,m.CONVENTION,d,m.RIGHTS)

    def test_53_refuse_claimed_rights(self):
        d=dict(m.RIGHTS)
        d['attribution_somhac_cad']=8591000
        with self.assertRaises(ValueError):m.validate_financials(m.RESERVE,m.CONVENTION,m.DEBTS,d)

    def test_54_refuse_changed_convention(self):
        d=dict(m.CONVENTION)
        d['peut_etre_resilie_sans_frais']=True
        with self.assertRaises(ValueError):m.validate_financials(m.RESERVE,d,m.DEBTS,m.RIGHTS)

    def test_55_refuse_modified_guard(self):
        data=copy.deepcopy(self.cfg)
        data['protections']['aucun_etat_individuel_somhac_certifie']=False
        with patch.object(m.p54z,'read_json',return_value=data):
            with self.assertRaises(ValueError):m.configuration()

    def test_56_refuse_modified_source(self):
        data=copy.deepcopy(self.cfg)
        data['sources'][1]['url']='https://wrong.example.org/'
        with patch.object(m.p54z,'read_json',return_value=data):
            with self.assertRaises(ValueError):m.configuration()

    def test_57_reject_zero_percent(self):
        with self.assertRaises(ValueError):m.percent(1,0)

    def test_58_reject_bool_percent(self):
        with self.assertRaises(ValueError):m.percent(True,5)

    def test_59_cli_no_network(self):
        self.assertEqual(m.main([]),0)

    def test_60_cli_certification_code_3(self):
        self.assertEqual(m.main(['--exiger-certification']),3)

    def test_61_cli_public_outputs(self):
        with tempfile.TemporaryDirectory() as root:
            a=Path(root)/'report.json';b=Path(root)/'table.json'
            self.assertEqual(m.main(['--bilan-public',str(a),'--table-public',str(b)]),0)
            self.assertEqual(json.loads(a.read_text())['reserve_somhac_affectee_cad'],4689663)
            self.assertEqual(json.loads(b.read_text())['obligations_groupe']['total_groupe_cad'],41856000)

    def test_62_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            a=Path(root)/'report.json';a.write_text('{}')
            self.assertEqual(m.main(['--bilan-public',str(a)]),2)

    def test_63_cli_no_duplicate(self):
        with tempfile.TemporaryDirectory() as root:
            a=str(Path(root)/'report.json')
            self.assertEqual(m.main(['--bilan-public',a,'--table-public',a]),2)

    def test_64_report_no_secrets(self):
        self.assertNotIn('sha256',json.dumps(m.public_report()))

if __name__=='__main__':
    unittest.main()
