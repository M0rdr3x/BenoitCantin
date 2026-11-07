"""P55V : tests d'un comparateur fiscal conditionnel sans passage GO."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import comparer_cas_fiscaux_nova_p55v as m

class TestP55V(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demo=m.p55s.read(m.DEMO)
        cls.partial=m.p55s.read(m.BASE/'P55V_CAS_PARTIEL_OFFICIEL_2026_A_COMPLETER.json')
        cls.diagnosis=m.validate_jeu(cls.demo)
        cls.part_diag=m.validate_jeu(cls.partial)

    def test_01_demo_mode(self):
        self.assertEqual(self.demo['type_jeu'],'SYNTHESE_FICTIVE_DEMONSTRATION')

    def test_02_candidate_mode(self):
        self.assertEqual(self.partial['type_jeu'],'CANDIDAT_DOCUMENTE_NON_AUDITE')

    def test_03_two_demo_cases(self):
        self.assertEqual(len(self.demo['cas']),2)

    def test_04_demo_two_complete(self):
        self.assertEqual(self.diagnosis['cas_arithmetiquement_complets'],2)

    def test_05_demo_none_incomplete(self):
        self.assertEqual(self.diagnosis['cas_incomplets'],0)

    def test_06_demo_none_unknown(self):
        self.assertEqual(self.diagnosis['montants_manquants_du_jeu'],0)

    def test_07_partial_one_case(self):
        self.assertEqual(self.part_diag['nombre_cas'],1)

    def test_08_partial_none_calculable(self):
        self.assertEqual(self.part_diag['cas_arithmetiquement_complets'],0)

    def test_09_partial_fifteen_unknown(self):
        self.assertEqual(self.part_diag['montants_manquants_du_jeu'],15)

    def test_10_partial_no_arithmetic(self):
        self.assertEqual(len(self.part_diag['resultats_conditionnels']),0)

    def test_11_demo_household_delta(self):
        self.assertEqual(self.diagnosis['resultats_conditionnels'][0]['variation_flux_partiel_cad'],'300.00')

    def test_12_demo_household_after_tax_delta(self):
        self.assertEqual(self.diagnosis['resultats_conditionnels'][0]['variation_apres_taxes_supportees_illustrative_cad'],'800.00')

    def test_13_demo_company_delta(self):
        self.assertEqual(self.diagnosis['resultats_conditionnels'][1]['variation_flux_partiel_cad'],'1500.00')

    def test_14_demo_household_current(self):
        self.assertEqual(self.diagnosis['resultats_conditionnels'][0]['flux_partiel_actuel_cad'],'28700.00')

    def test_15_demo_company_current(self):
        self.assertEqual(self.diagnosis['resultats_conditionnels'][1]['flux_partiel_actuel_cad'],'26000.00')

    def test_16_company_no_after_taxes(self):
        self.assertEqual(self.diagnosis['resultats_conditionnels'][1]['variation_apres_taxes_supportees_illustrative_cad'],None)

    def test_17_demo_result_label(self):
        self.assertEqual(self.diagnosis['resultats_conditionnels'][0]['type_source'],'SYNTHESE_FICTIVE_DEMONSTRATION')

    def test_18_public_no_numeric_cases(self):
        self.assertEqual('resultats_conditionnels' in m.public_report(self.diagnosis),False)

    def test_19_public_score(self):
        self.assertEqual(m.public_report(self.diagnosis)['score_programme_estime_pct'],53)

    def test_20_public_p52d_unknown(self):
        self.assertEqual(m.public_report(self.diagnosis)['p52d_valeurs_inconnues'],720)

    def test_21_public_p52b_unknown(self):
        self.assertEqual(m.public_report(self.diagnosis)['p52b_valeurs_inconnues'],600)

    def test_22_public_no_certification(self):
        self.assertEqual(m.public_report(self.diagnosis)['decision'],m.NO_GO)

    def test_23_public_no_tax_rate(self):
        self.assertEqual(m.public_report(self.diagnosis)['taux_nova_propose_pct'],None)

    def test_24_public_partial(self):
        self.assertEqual(m.public_report(self.part_diag)['cas_incomplets'],1)

    def test_25_public_no_online_validation(self):
        self.assertEqual(m.public_report(self.part_diag)['verification_sources_en_ligne_realisee'],False)

    def test_26_technical_no_go(self):
        self.assertEqual(m.technical_report(self.diagnosis)['decision'],m.NO_GO)

    def test_27_technical_result_two(self):
        self.assertEqual(len(m.technical_report(self.diagnosis)['resultats']),2)

    def test_28_max_cases(self):
        self.assertEqual(m.LIMIT,32)

    def test_29_max_id_format(self):
        self.assertEqual(m.CASE_ID.fullmatch('cas-a01') is not None,True)

    def test_30_reject_duplicate_id(self):
        data=copy.deepcopy(self.demo)
        data['cas'][1]['id']=data['cas'][0]['id']
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_31_reject_unapproved_flag(self):
        data=copy.deepcopy(self.demo)
        data['avis_independant_obtenu']=True
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_32_reject_fake_tax_adoption(self):
        data=copy.deepcopy(self.demo)
        data['version_programme_adoptee']=True
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_33_reject_unknown_extra_field(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['nom']='personne privee'
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_34_reject_unknown_regime(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['regime']='SOUVERAIN_DEJA_ADOPTE'
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_35_reject_wrong_year(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['annee']=2027
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_36_reject_wrong_category(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['categorie']='GRANDE_ENTREPRISE'
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_37_reject_missing_source_numeric(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['sources']['actuel']['revenu_brut']=None
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_38_reject_unjustified_source_null(self):
        data=copy.deepcopy(self.partial)
        data['cas'][0]['sources']['propose']['revenu_brut']='https://example.org/claimed'
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_39_reject_missing_demo_value(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['actuel']['revenu_brut']=None
        data['cas'][0]['sources']['actuel']['revenu_brut']=None
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_40_reject_negative_number(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['actuel']['revenu_brut']='-100'
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_41_reject_boolean_number(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['actuel']['revenu_brut']=True
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_42_reject_float_number(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['actuel']['revenu_brut']=30000.0
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_43_reject_more_than_two_decimals(self):
        data=copy.deepcopy(self.demo)
        data['cas'][0]['actuel']['revenu_brut']='30000.123'
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_44_reject_bad_source_candidate(self):
        data=copy.deepcopy(self.partial)
        data['cas'][0]['sources']['actuel']['revenu_brut']='SOURCE_LOCALE'
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_45_reject_candidate_no_warning(self):
        data=copy.deepcopy(self.partial)
        data['cas'][0]['avertissement']='CERTIFIE'
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_46_reject_thirtythree_cases(self):
        data=copy.deepcopy(self.demo)
        data['cas']=[copy.deepcopy(self.demo['cas'][0]) for _ in range(33)]
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_47_reject_invalid_non_2026_dataset(self):
        data=copy.deepcopy(self.demo)
        data['date_reference']='2026-10-10'
        with self.assertRaises(ValueError):m.validate_jeu(data)

    def test_48_candidate_complete_still_no_go(self):
        data=copy.deepcopy(self.demo)
        data['type_jeu']='CANDIDAT_DOCUMENTE_NON_AUDITE'
        for case in data['cas']:
            case['avertissement']='SOURCES_DECLAREES_NON_CONTROLEES_EXTERNEMENT'
            for status in ('actuel','propose'):
                for key in case['sources'][status]:
                    case['sources'][status][key]='https://example.org/fake-unverified-study'
        r=m.validate_jeu(data)
        self.assertEqual(r['cas_arithmetiquement_complets'],2)
        self.assertEqual(m.public_report(r)['decision'],m.NO_GO)
        self.assertFalse(r['resultats_conditionnels'][0]['sources_independamment_validees'])

    def test_49_federated_scenario_allowed(self):
        data=copy.deepcopy(self.demo)
        for case in data['cas']:
            case['regime']='QUEBEC_SOUVERAIN'
        r=m.validate_jeu(data)
        self.assertEqual(r['resultats_conditionnels'][0]['regime'],'QUEBEC_SOUVERAIN')

    def test_50_cli_default(self):
        self.assertEqual(m.main([]),0)

    def test_51_cli_no_go(self):
        self.assertEqual(m.main(['--exiger-faisabilite']),3)

    def test_52_cli_partial(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(m.main(['--jeu',str(m.BASE/'P55V_CAS_PARTIEL_OFFICIEL_2026_A_COMPLETER.json')]),0)

    def test_53_cli_export(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'public.json';b=Path(temp)/'technique.json'
            self.assertEqual(m.main(['--bilan-public',str(a),'--rapport-technique',str(b)]),0)
            x=json.loads(a.read_text());y=json.loads(b.read_text())
            self.assertNotIn('resultats',x)
            self.assertEqual(len(y['resultats']),2)
            self.assertEqual(x['score_programme_estime_pct'],53)

    def test_54_cli_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'public.json';a.write_text('ne pas ecraser')
            self.assertEqual(m.main(['--bilan-public',str(a)]),2)
            self.assertEqual(a.read_text(),'ne pas ecraser')

    def test_55_cli_refuses_same_output_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            a=str(Path(temp)/'resultat.json')
            self.assertEqual(m.main(['--bilan-public',a,'--rapport-technique',a]),2)

if __name__=='__main__':
    unittest.main()
