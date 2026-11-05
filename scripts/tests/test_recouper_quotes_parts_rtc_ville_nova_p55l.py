"""P55L — 63 tests déterministes de rapprochement RTC/Ville, sans téléchargement."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import recouper_quotes_parts_rtc_ville_nova_p55l as m

class TestP55L(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=m.configuration()

    def test_01_version(self):
        self.assertEqual(self.config['schema_version'],'P55L-1')

    def test_02_date(self):
        self.assertEqual(self.config['date_reference'],'2026-11-04')

    def test_03_year(self):
        self.assertEqual(self.config['exercice'],2024)

    def test_04_sources_two(self):
        self.assertEqual(len(m.SOURCES),2)

    def test_05_guards_39(self):
        self.assertEqual(len(m.GUARDS),39)

    def test_06_guards_all(self):
        self.assertTrue(all(self.config['protections'].values()))

    def test_07_matches_5(self):
        self.assertEqual(len(m.MATCHES),5)

    def test_08_forbidden_7(self):
        self.assertEqual(len(m.FORBIDDEN),7)

    def test_09_ville_s12(self):
        self.assertEqual(m.SOURCES['ville']['page_imprimee'],63)

    def test_10_rtc_note28(self):
        self.assertEqual(len(m.SOURCES['rtc']['rubriques']),3)

    def test_11_rtc_issuer(self):
        self.assertTrue('rtcquebec.ca' in m.SOURCES['rtc']['url'])

    def test_12_ville_issuer(self):
        self.assertTrue('ville.quebec.qc.ca' in m.SOURCES['ville']['url'])

    def test_13_rtc_deposit(self):
        self.assertEqual(m.SOURCES['rtc']['date_depot'],'2025-06')

    def test_14_rtc_source_no_visual(self):
        self.assertTrue('NI_CAPTURE_VISUELLE' in m.SOURCES['rtc']['qualification'])

    def test_15_rtc_q_2024(self):
        self.assertEqual(m.AMOUNTS['rtc_quotes_parts_realisees_2024_cad'],154047800)

    def test_16_rtc_q_budget(self):
        self.assertEqual(m.AMOUNTS['rtc_quotes_parts_budget_2024_cad'],154047800)

    def test_17_rtc_q_2023(self):
        self.assertEqual(m.AMOUNTS['rtc_quotes_parts_realisees_2023_cad'],143131000)

    def test_18_rtc_note28(self):
        self.assertEqual(m.AMOUNTS['rtc_note_28_contribution_agglomeration_2024_cad'],154047800)

    def test_19_ville_group_q(self):
        self.assertEqual(m.AMOUNTS['ville_s12_organismes_quotes_parts_2024_cad'],154047800)

    def test_20_ville_residue(self):
        self.assertEqual(m.AMOUNTS['ville_s12_residu_quotes_parts_2024_cad'],-154047800)

    def test_21_ville_admin_q(self):
        self.assertEqual(m.AMOUNTS['ville_s12_administration_quotes_parts_2024_cad'],47353223)

    def test_22_ville_consol_q(self):
        self.assertEqual(m.AMOUNTS['ville_s12_total_consolide_quotes_parts_2024_cad'],47353223)

    def test_23_rtc_revenues(self):
        self.assertEqual(m.AMOUNTS['rtc_total_revenus_realises_2024_cad'],428758065)

    def test_24_rtc_expenses(self):
        self.assertEqual(m.AMOUNTS['rtc_total_charges_realisees_2024_cad'],358727303)

    def test_25_rtc_surplus(self):
        self.assertEqual(m.AMOUNTS['rtc_excedent_activites_realise_2024_cad'],70030762)

    def test_26_change_rtc(self):
        self.assertEqual(m.AMOUNTS['variation_quotes_parts_rtc_2024_vs_2023_cad'],10916800)

    def test_27_pct_growth(self):
        self.assertEqual(m.pct(10916800,143131000),'7.6')

    def test_28_pct_share(self):
        self.assertEqual(m.pct(154047800,428758065),'35.9')

    def test_29_pct_zero(self):
        self.assertEqual(m.pct(0,100),'0.0')

    def test_30_pct_no_zero(self):
        with self.assertRaises(ValueError):m.pct(1,0)

    def test_31_pct_no_bool(self):
        with self.assertRaises(ValueError):m.pct(True,3)

    def test_32_pct_no_negative(self):
        with self.assertRaises(ValueError):m.pct(-1,3)

    def test_33_amounts_valid(self):
        self.assertTrue(m.verify_amounts(m.AMOUNTS))

    def test_34_approx_flag(self):
        self.assertTrue(m.AMOUNTS['rtc_note_28_part_ville_est_approximative'])

    def test_35_approx_pct(self):
        self.assertEqual(m.AMOUNTS['rtc_note_28_part_ville_approximative_pct'],93)

    def test_36_no_exact_municipal(self):
        self.assertFalse(m.public_report()['repartition_exacte_contribution_municipale_connue'])

    def test_37_no_signed_consolidation(self):
        self.assertFalse(m.public_report()['rapprochement_ecritures_comptables_independamment_verifie'])

    def test_38_no_somhac_split(self):
        self.assertFalse(m.public_report()['part_somhac_et_autres_ecarts_etablie'])

    def test_39_origins_no_sha(self):
        self.assertEqual(m.public_report()['copies_pdf_originales_sha_actuel_verifiees'],0)

    def test_40_no_cpa(self):
        self.assertEqual(m.public_report()['avis_professionnels_authentifies'],0)

    def test_41_no_contract(self):
        self.assertEqual(m.public_report()['mandats_signes'],0)

    def test_42_savings_none(self):
        self.assertEqual(m.public_report()['economies_certifiees_cad'],None)

    def test_43_no_go(self):
        self.assertEqual(m.public_report()['decision'],m.NO_GO)

    def test_44_no_merge(self):
        self.assertFalse(m.public_report()['fusion_main_autorisee'])

    def test_45_no_transfer(self):
        self.assertFalse(m.public_report()['transmission_externe_autorisee'])

    def test_46_public_references_count(self):
        self.assertEqual(len(m.public_table()['preuves_documentaires']),4)

    def test_47_table_no_cert(self):
        self.assertTrue(m.public_table()['montant_nouvelle_economie_demontre'] is None)

    def test_48_mutated_rtc(self):
        data=dict(m.AMOUNTS)
        data['rtc_quotes_parts_realisees_2024_cad']+=1
        with self.assertRaises(ValueError):m.verify_amounts(data)

    def test_49_mutated_note28(self):
        data=dict(m.AMOUNTS)
        data['rtc_note_28_contribution_agglomeration_2024_cad']-=1
        with self.assertRaises(ValueError):m.verify_amounts(data)

    def test_50_mutated_approx(self):
        data=dict(m.AMOUNTS)
        data['rtc_note_28_part_ville_est_approximative']=False
        with self.assertRaises(ValueError):m.verify_amounts(data)

    def test_51_mutated_2023(self):
        data=dict(m.AMOUNTS)
        data['rtc_quotes_parts_realisees_2023_cad']+=1
        with self.assertRaises(ValueError):m.verify_amounts(data)

    def test_52_mutated_budget(self):
        data=dict(m.AMOUNTS)
        data['rtc_quotes_parts_budget_2024_cad']+=1
        with self.assertRaises(ValueError):m.verify_amounts(data)

    def test_53_mutated_excedent(self):
        data=dict(m.AMOUNTS)
        data['rtc_excedent_activites_realise_2024_cad']+=1
        with self.assertRaises(ValueError):m.verify_amounts(data)

    def test_54_config_guard_changed(self):
        data=copy.deepcopy(self.config)
        data['protections']['aucun_double_compte_154m']=False
        with patch.object(m.p54z,'read_json',return_value=data):
            with self.assertRaises(ValueError):m.configuration()

    def test_55_config_source_changed(self):
        data=copy.deepcopy(self.config)
        data['sources']['rtc']['date_depot']='2024-06'
        with patch.object(m.p54z,'read_json',return_value=data):
            with self.assertRaises(ValueError):m.configuration()

    def test_56_cli_neutral(self):
        self.assertEqual(m.main([]),0)

    def test_57_cli_refuses_cert(self):
        self.assertEqual(m.main(['--exiger-certification']),3)

    def test_58_cli_outputs(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'bilan.json';q=Path(root)/'table.json'
            self.assertEqual(m.main(['--bilan-public',str(p),'--table-public',str(q)]),0)
            self.assertEqual(json.loads(p.read_text())['montant_quotes_parts_2024_cad'],154047800)
            self.assertEqual(len(json.loads(q.read_text())['preuves_documentaires']),4)

    def test_59_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'bilan.json';p.write_text('{}')
            self.assertEqual(m.main(['--bilan-public',str(p)]),2)

    def test_60_cli_duplicate(self):
        with tempfile.TemporaryDirectory() as root:
            p=str(Path(root)/'bilan.json')
            self.assertEqual(m.main(['--bilan-public',p,'--table-public',p]),2)

    def test_61_open_cases(self):
        report=m.public_report()
        self.assertEqual((report['dossiers_p54e_ouverts'],report['date_probable_non_certifiee'],report['taches_p54n_non_attestees'],report['blocages_p54o_non_leves']), (4,1,40,10))

    def test_62_open_checks(self):
        report=m.public_report()
        self.assertEqual((report['controles_p54b_non_attestes'],report['controles_p54c_non_attestes']), (96,8))

    def test_63_report_no_private_data(self):
        self.assertNotIn('sha256',json.dumps(m.public_report()))

if __name__=='__main__':
    unittest.main()
