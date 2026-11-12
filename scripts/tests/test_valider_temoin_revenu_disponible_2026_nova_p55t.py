"""P55T : témoin officiel du revenu disponible 2026 et seuils de barèmes."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import valider_temoin_revenu_disponible_2026_nova_p55t as m

class TestP55T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.load()
        cls.b=cls.cfg['cas_officiel_2026']

    def test_01_schema(self):
        self.assertEqual(self.cfg['schema_version'],'P55T-1')

    def test_02_date(self):
        self.assertEqual(self.cfg['date_reference'],'2026-11-07')

    def test_03_source_page(self):
        self.assertEqual(self.cfg['source_principale']['url'],m.SOURCES['quebec'])

    def test_04_source_revision(self):
        self.assertEqual(self.cfg['source_principale']['derniere_mise_a_jour_publiee'],'2026-06-17')

    def test_05_single_case(self):
        self.assertEqual(self.b['profil'],'PERSONNE_VIVANT_SEULE')

    def test_06_income_50000(self):
        self.assertEqual(self.b['revenu_annuel_indique_cad'],50000)

    def test_07_reference_2025(self):
        self.assertEqual(self.b['annee_reference'],2025)

    def test_08_comparison_2026(self):
        self.assertEqual(self.b['annee_comparee'],2026)

    def test_09_published_gain_847(self):
        self.assertEqual(self.b['variation_revenu_disponible_publiee_cad'],847)

    def test_10_displayed_sum_846(self):
        self.assertEqual(self.b['somme_composantes_affichees_cad'],846)

    def test_11_unexplained_one(self):
        self.assertEqual(self.b['ecart_avec_total_publie_cad'],1)

    def test_12_source_component_sum(self):
        self.assertEqual(sum(x['montant_cad'] for x in self.b['composantes_de_variation_affichees_cad']),846)

    def test_13_component_count(self):
        self.assertEqual(len(self.b['composantes_de_variation_affichees_cad']),5)

    def test_14_one_time_grocery(self):
        self.assertEqual(self.b['composantes_de_variation_affichees_cad'][0]['montant_cad'],100)

    def test_15_federal_grocery(self):
        self.assertEqual(self.b['composantes_de_variation_affichees_cad'][1]['montant_cad'],358)

    def test_16_social_contribution(self):
        self.assertEqual(self.b['composantes_de_variation_affichees_cad'][2]['montant_cad'],72)

    def test_17_quebec_indexation(self):
        self.assertEqual(self.b['composantes_de_variation_affichees_cad'][3]['montant_cad'],166)

    def test_18_federal_indexation(self):
        self.assertEqual(self.b['composantes_de_variation_affichees_cad'][4]['montant_cad'],150)

    def test_19_no_absolute_income_2026(self):
        self.assertEqual(self.b['revenu_disponible_2026_total_cad'],None)

    def test_20_no_absolute_income_2025(self):
        self.assertEqual(self.b['revenu_disponible_2025_total_cad'],None)

    def test_21_no_nova_amount(self):
        self.assertEqual(self.b['resultat_nova_cad'],None)

    def test_22_brackets_quebec(self):
        self.assertEqual(len(m.BRACKETS_Q),4)

    def test_23_brackets_federal(self):
        self.assertEqual(len(m.BRACKETS_F),5)

    def test_24_qe_54345(self):
        self.assertEqual(self.cfg['baremes_marginaux_2026']['quebec']['paliers'][0]['plafond_revenu_imposable_cad'],54345)

    def test_25_f_58523(self):
        self.assertEqual(self.cfg['baremes_marginaux_2026']['federal']['paliers'][0]['plafond_revenu_imposable_cad'],58523)

    def test_26_base_credit_amount(self):
        self.assertEqual(self.cfg['baremes_marginaux_2026']['quebec']['montant_personnel_base_2026_cad'],18952)

    def test_27_abatement_rate(self):
        self.assertEqual(self.cfg['baremes_marginaux_2026']['federal']['abattement_quebec_base_federale_pct'],'16.5')

    def test_28_guard_total(self):
        self.assertEqual(len(self.cfg['protections']),24)

    def test_29_unresolved_questions(self):
        self.assertEqual(len(self.cfg['questions_requises']),8)

    def test_30_score(self):
        self.assertEqual(m.report(self.cfg)['p55n_score_estime_inchange_pct'],53)

    def test_31_unknown_finance(self):
        self.assertEqual(m.report(self.cfg)['p52b_montants_inconnus'],600)

    def test_32_unknown_people(self):
        self.assertEqual(m.report(self.cfg)['p52d_montants_inconnus'],720)

    def test_33_no_go(self):
        self.assertEqual(m.report(self.cfg)['decision'],m.NO_GO)

    def test_34_no_p52d_mapping(self):
        self.assertFalse(self.b['mapping_p52d_certifie'])

    def test_35_no_reform_simulated(self):
        self.assertFalse(m.report(self.cfg)['comparaison_nova_vs_actuel_calculee'])

    def test_36_no_new_rate(self):
        self.assertEqual(m.report(self.cfg)['taux_propose_deux_prelevements_pct'],None)

    def test_37_precredit_q_50000(self):
        self.assertEqual(m.progressive_before_credits('50000','quebec'),'7000.00')

    def test_38_precredit_f_50000(self):
        self.assertEqual(m.progressive_before_credits('50000','federal'),'7000.00')

    def test_39_precredit_q_54345(self):
        self.assertEqual(m.progressive_before_credits('54345','quebec'),'7608.30')

    def test_40_precredit_q_54346(self):
        self.assertEqual(m.progressive_before_credits('54346','quebec'),'7608.49')

    def test_41_precredit_f_58523(self):
        self.assertEqual(m.progressive_before_credits('58523','federal'),'8193.22')

    def test_42_precredit_f_58524(self):
        self.assertEqual(m.progressive_before_credits('58524','federal'),'8193.43')

    def test_43_zero_case(self):
        self.assertEqual(m.progressive_before_credits('0','quebec'),'0.00')

    def test_44_reject_negative(self):
        with self.assertRaises(ValueError):m.progressive_before_credits('-5','quebec')

    def test_45_reject_bad_jurisdiction(self):
        with self.assertRaises(ValueError):m.progressive_before_credits('50000','nova')

    def test_46_reject_float_input(self):
        with self.assertRaises(ValueError):m.progressive_before_credits(50000.0,'quebec')

    def test_47_reject_exponent_input(self):
        with self.assertRaises(ValueError):m.progressive_before_credits('5e4','quebec')

    def test_48_reject_giant_input(self):
        with self.assertRaises(ValueError):m.progressive_before_credits('100000001','quebec')

    def test_49_reject_modified_published_total(self):
        c=copy.deepcopy(self.cfg)
        c['cas_officiel_2026']['variation_revenu_disponible_publiee_cad']=846
        with self.assertRaises(ValueError):m.check(c)

    def test_50_reject_modified_component(self):
        c=copy.deepcopy(self.cfg)
        c['cas_officiel_2026']['composantes_de_variation_affichees_cad'][1]['montant_cad']=359
        with self.assertRaises(ValueError):m.check(c)

    def test_51_reject_invented_full_income(self):
        c=copy.deepcopy(self.cfg)
        c['cas_officiel_2026']['revenu_disponible_2026_total_cad']=40000
        with self.assertRaises(ValueError):m.check(c)

    def test_52_reject_fake_p52d_fill(self):
        c=copy.deepcopy(self.cfg)
        c['population_et_incidence']['p52d_montants_inconnus']=719
        with self.assertRaises(ValueError):m.check(c)

    def test_53_reject_marginal_rate(self):
        c=copy.deepcopy(self.cfg)
        c['baremes_marginaux_2026']['quebec']['paliers'][0]['taux_pct']='16'
        with self.assertRaises(ValueError):m.check(c)

    def test_54_reject_fake_nova_tax(self):
        c=copy.deepcopy(self.cfg)
        c['baremes_marginaux_2026']['calcul_impot_nova_autorise']=True
        with self.assertRaises(ValueError):m.check(c)

    def test_55_reject_missing_guard(self):
        c=copy.deepcopy(self.cfg)
        c['protections']['abattement_federal_quebec_ne_pas_omettre']=False
        with self.assertRaises(ValueError):m.check(c)

    def test_56_reject_closed_evidence(self):
        c=copy.deepcopy(self.cfg)
        c['questions_requises'][0]['statut']='TERMINE'
        with self.assertRaises(ValueError):m.check(c)

    def test_57_cli_plain(self):
        self.assertEqual(m.main([]),0)

    def test_58_cli_no_approval(self):
        self.assertEqual(m.main(['--exiger-simulation-nova']),3)

    def test_59_cli_export(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'p55t.json'
            self.assertEqual(m.main(['--bilan-public',str(path)]),0)
            obj=json.loads(path.read_text())
            self.assertEqual(obj['variation_revenu_disponible_2025_2026_publiee_cad'],847)
            self.assertEqual(obj['ecart_de_presentation_inexplique_cad'],1)

    def test_60_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'p55t.json';path.write_text('sauvegarder')
            self.assertEqual(m.main(['--bilan-public',str(path)]),2)
            self.assertEqual(path.read_text(),'sauvegarder')

if __name__=='__main__':
    unittest.main()
