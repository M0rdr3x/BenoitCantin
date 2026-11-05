"""Tests P55N : grille éditoriale et refus de complétude auto-proclamée."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import evaluer_completude_programme_nova_p55n as m

class TestP55N(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.load()

    def test_01_config_schema(self):
        self.assertEqual(self.cfg['schema_version'],'P55N-1')

    def test_02_date(self):
        self.assertEqual(self.cfg['date_evaluation'],'2026-11-05')

    def test_03_score_53(self):
        self.assertEqual(m.validate(self.cfg)['score'],53)

    def test_04_max_100(self):
        self.assertEqual(m.validate(self.cfg)['maximum'],100)

    def test_05_eight_axes(self):
        self.assertEqual(len(self.cfg['axes']),8)

    def test_06_unique_axes(self):
        self.assertEqual(len({a['id'] for a in self.cfg['axes']}),8)

    def test_07_fiscal_score(self):
        self.assertEqual(next(a for a in self.cfg['axes'] if a['id']=='FISCALITE')['points_estimes'],5)

    def test_08_external_zero(self):
        self.assertEqual(next(a for a in self.cfg['axes'] if a['id']=='EXPERTISE')['points_estimes'],0)

    def test_09_adoption_zero(self):
        self.assertEqual(next(a for a in self.cfg['axes'] if a['id']=='ADOPTION')['points_estimes'],0)

    def test_10_estimate_interval(self):
        self.assertEqual(self.cfg['fourchette_prudente'],[45,60])

    def test_11_gates_ten(self):
        self.assertEqual(m.validate(self.cfg)['portes_non_demontrees'],10)

    def test_12_all_gates_open(self):
        self.assertTrue(all(g['statut']=='NON_DEMONTRE' for g in self.cfg['portes_de_completion']))

    def test_13_twelve_priorities(self):
        self.assertEqual(m.validate(self.cfg)['priorites_ouvertes'],12)

    def test_14_all_priorities_open(self):
        self.assertTrue(all(p['statut']=='OUVERT' for p in self.cfg['priorites']))

    def test_15_first_priority(self):
        self.assertEqual(self.cfg['priorites'][0]['id'],'N01')

    def test_16_fiscal_unknowns_600(self):
        self.assertEqual(self.cfg['constats_non_ambigus']['entrees_financieres_p52b_inconnues'],600)

    def test_17_incidence_unknowns_720(self):
        self.assertEqual(self.cfg['constats_non_ambigus']['montants_incidence_p52d_inconnus'],720)

    def test_18_fiscal_evidence_20(self):
        self.assertEqual(self.cfg['constats_non_ambigus']['dossiers_preuves_fiscales_p52a_ouverts'],20)

    def test_19_not_authorized_assumed(self):
        self.assertFalse(self.cfg['constats_non_ambigus']['autorisation_legale_parti_verifiee'])

    def test_20_not_adopted(self):
        self.assertTrue(self.cfg['constats_non_ambigus']['programme_public_non_adopte'])

    def test_21_savings_unknown(self):
        self.assertIsNone(self.cfg['constats_non_ambigus']['economies_certifiees_cad'])

    def test_22_no_pass_due_to_tests(self):
        self.assertFalse(m.report(self.cfg)['evaluation_basee_sur_nombre_de_commits'])

    def test_23_status_no_go(self):
        self.assertEqual(m.report(self.cfg)['decision'],m.NO_GO)

    def test_24_public_range(self):
        self.assertEqual(m.report(self.cfg)['fourchette_prudente_pourcent'],[45,60])

    def test_25_public_detail(self):
        self.assertEqual(len(m.table(self.cfg)['portes_de_completion']),10)

    def test_26_score_tamper_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['score_estimatif']=99
        with self.assertRaises(ValueError):m.validate(cfg,check_files=False)

    def test_27_axis_inflation_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['axes'][0]['points_estimes']=11
        with self.assertRaises(ValueError):m.validate(cfg,check_files=False)

    def test_28_axis_bool_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['axes'][0]['points_estimes']=True
        with self.assertRaises(ValueError):m.validate(cfg,check_files=False)

    def test_29_gate_fake_close_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['portes_de_completion'][0]['statut']='DEMONTRÉ'
        with self.assertRaises(ValueError):m.validate(cfg,check_files=False)

    def test_30_source_forged_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['axes'][0]['preuve_documentaire']=['../outside.txt']
        with self.assertRaises(ValueError):m.validate(cfg,check_files=False)

    def test_31_guard_off_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['protections']['pas_de_scores_a_partir_nombre_commits']=False
        with self.assertRaises(ValueError):m.validate(cfg,check_files=False)

    def test_32_priority_done_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['priorites'][0]['statut']='TERMINE'
        with self.assertRaises(ValueError):m.validate(cfg,check_files=False)

    def test_33_pending_sources_locally_absent_rejected(self):
        with patch.object(m,'ROOT',Path('/this/is/an/intentionally/nonexistent/path')):
            with self.assertRaises(ValueError):m.validate(self.cfg)

    def test_34_cli_default(self):
        self.assertEqual(m.main([]),0)

    def test_35_cli_no_full(self):
        self.assertEqual(m.main(['--exiger-complet']),3)

    def test_36_cli_no_implementation(self):
        self.assertEqual(m.main(['--exiger-pret-a-appliquer']),3)

    def test_37_cli_two_outputs(self):
        with tempfile.TemporaryDirectory() as root:
            first=Path(root)/'bilan.json';second=Path(root)/'table.json'
            self.assertEqual(m.main(['--bilan-public',str(first),'--table-public',str(second)]),0)
            self.assertEqual(json.loads(first.read_text())['pourcentage_estimatif'],53)
            self.assertEqual(len(json.loads(second.read_text())['priorites']),12)

    def test_38_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/'bilan.json';f.write_text('garder')
            self.assertEqual(m.main(['--bilan-public',str(f)]),2)
            self.assertEqual(f.read_text(),'garder')

    def test_39_cli_no_duplicate(self):
        with tempfile.TemporaryDirectory() as root:
            f=str(Path(root)/'bilan.json')
            self.assertEqual(m.main(['--bilan-public',f,'--table-public',f]),2)

    def test_40_no_private_hash_public(self):
        self.assertNotIn('sha256',json.dumps(m.report(self.cfg)))

    def test_41_safeguards_count(self):
        self.assertEqual(len(m.EXPECTED_PROTECTIONS),19)

if __name__=='__main__':
    unittest.main()
