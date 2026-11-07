"""P55S : couverture de 720 valeurs et essais purement synthétiques de flux."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import mesurer_couverture_incidences_nova_p55s as m

class TestP55S(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.result=m.load()
        cls.source=m.read(m.P52D)
        cls.score=m.read(m.P55N)

    def synthetic_household(self):
        d={k:'0.00' for k in m.HH}
        d.update({'revenu_brut':'50000.00','prestations_federales':'2000.00',
                  'prestations_quebec_ou_etat':'1000.00',
                  'impot_revenu_federal':'6000.00',
                  'impot_revenu_quebec_ou_etat':'5000.00',
                  'cotisations_obligatoires':'3500.00',
                  'prelevements_municipaux_directs':'500.00',
                  'taxes_consommation_supportees':'1000.00'})
        return d

    def synthetic_firm(self):
        d={k:'0.00' for k in m.FIRMS}
        d.update({'chiffre_affaires':'200000.00',
                  'couts_exploitation_hors_salaires':'60000.00',
                  'masse_salariale':'90000.00',
                  'impot_entreprise_federal':'10000.00',
                  'impot_entreprise_quebec_ou_etat':'8000.00',
                  'cotisations_employeur':'4000.00',
                  'prelevements_municipaux':'2000.00',
                  'taxes_consommation_non_recouvrables':'1000.00',
                  'subventions_recues':'1000.00'})
        return d

    def test_01_schema(self):
        self.assertEqual(self.cfg['schema_version'],'P55S-1')

    def test_02_date(self):
        self.assertEqual(self.cfg['date_reference'],'2026-11-06')

    def test_03_regimes(self):
        self.assertEqual(len(m.REGIMES),2)

    def test_04_trajectories(self):
        self.assertEqual(len(m.SCENARIOS),3)

    def test_05_households(self):
        self.assertEqual(len(m.CATEGORIES_HH),5)

    def test_06_firms(self):
        self.assertEqual(len(m.CATEGORIES_FIRMS),2)

    def test_07_household_fields(self):
        self.assertEqual(len(m.HH),8)

    def test_08_firm_fields(self):
        self.assertEqual(len(m.FIRMS),10)

    def test_09_cases_household(self):
        self.assertEqual(self.result['menages'],30)

    def test_10_cases_firms(self):
        self.assertEqual(self.result['entreprises'],12)

    def test_11_missing_households(self):
        self.assertEqual(self.result['montants_menages_non_renseignes'],480)

    def test_12_missing_firms(self):
        self.assertEqual(self.result['montants_entreprises_non_renseignes'],240)

    def test_13_missing_total(self):
        self.assertEqual(self.result['total_montants_non_renseignes'],720)

    def test_14_safeguards(self):
        self.assertEqual(len(m.SAFE),29)

    def test_15_all_safeguards(self):
        self.assertEqual(all(self.cfg['protections'].values()),True)

    def test_16_evidence_tasks(self):
        self.assertEqual(len(self.cfg['actions_justificatifs']),12)

    def test_17_sources(self):
        self.assertEqual(len(self.cfg['sources']),5)

    def test_18_source_not_adopted(self):
        self.assertEqual(self.cfg['decision'],m.NO_GO)

    def test_19_score_same(self):
        self.assertEqual(m.public_report(self.cfg,self.result)['score_programme_estimatif_pourcent'],53)

    def test_20_no_safety_assumed(self):
        self.assertFalse(m.public_report(self.cfg,self.result)['gain_pouvoir_achat_certifie'])

    def test_21_no_tax_rates(self):
        self.assertFalse(m.public_report(self.cfg,self.result)['recettes_fiscales_deux_prelevements_demontrees'])

    def test_22_none_rate(self):
        self.assertEqual(m.public_report(self.cfg,self.result)['taux_fiscal_propose_pct'],None)

    def test_23_no_genuine_scenarios(self):
        self.assertEqual(m.public_report(self.cfg,self.result)['simulations_reelles_completes'],0)

    def test_24_no_scores_increment(self):
        self.assertEqual(m.public_report(self.cfg,self.result)['progression_score_demontree'],False)

    def test_25_synthetic_household(self):
        a=self.synthetic_household()
        b=dict(a)
        b['impot_revenu_quebec_ou_etat']='4000.00'
        b['taxes_consommation_supportees']='500.00'
        r=m.fixture_synthetic('personne_seule_revenu_modeste',a,b)
        self.assertEqual(r['direct_actuel_cad'],'38000.00')
        self.assertEqual(r['direct_propose_cad'],'39000.00')
        self.assertEqual(r['variation_directe_cad'],'1000.00')
        self.assertEqual(r['variation_apres_taxes_consommation_cad'],'1500.00')
        self.assertTrue(r['statut_non_representatif'])

    def test_26_synthetic_firm(self):
        a=self.synthetic_firm()
        b=dict(a)
        b['impot_entreprise_quebec_ou_etat']='7000.00'
        b['charge_additionnelle_anti_evasion']='500.00'
        r=m.fixture_synthetic('PME',a,b,'entreprise')
        self.assertEqual(r['direct_actuel_cad'],'26000.00')
        self.assertEqual(r['direct_propose_cad'],'26500.00')
        self.assertIsNone(r['variation_apres_taxes_consommation_cad'])

    def test_27_income_empty_zeros(self):
        a={k:'0' for k in m.HH}
        r=m.fixture_synthetic('personne_retraitee',a,a)
        self.assertEqual(r['variation_directe_cad'],'0.00')

    def test_28_income_single_decimal(self):
        a={k:'0.5' for k in m.HH}
        r=m.fixture_synthetic('personne_retraitee',a,a)
        self.assertEqual(r['variation_directe_cad'],'0.00')

    def test_29_reject_unknown_category(self):
        a=self.synthetic_household()
        with self.assertRaises(ValueError):m.fixture_synthetic('categorie_inconnue',a,a)

    def test_30_reject_unknown_kind(self):
        a=self.synthetic_household()
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a,'other')

    def test_31_reject_missing_field(self):
        a=self.synthetic_household();a.pop('cotisations_obligatoires')
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a)

    def test_32_reject_extra_field(self):
        a=self.synthetic_household();a['identifiant_personnel']='x'
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a)

    def test_33_reject_null(self):
        a=self.synthetic_household();a['revenu_brut']=None
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a)

    def test_34_reject_float(self):
        a=self.synthetic_household();a['revenu_brut']=50000.0
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a)

    def test_35_reject_negative(self):
        a=self.synthetic_household();a['revenu_brut']='-500'
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a)

    def test_36_reject_exponent(self):
        a=self.synthetic_household();a['revenu_brut']='5e4'
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a)

    def test_37_reject_3_decimal(self):
        a=self.synthetic_household();a['revenu_brut']='50000.001'
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a)

    def test_38_reject_leading_zero(self):
        a=self.synthetic_household();a['revenu_brut']='050000'
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a)

    def test_39_reject_above_limit(self):
        a=self.synthetic_household();a['revenu_brut']='100000001.00'
        with self.assertRaises(ValueError):m.fixture_synthetic('personne_retraitee',a,a)

    def test_40_reject_field_modified(self):
        c=copy.deepcopy(self.cfg)
        c['perimetre']['montants_inconnus_total']=719
        with self.assertRaises(ValueError):m.check_config(c)

    def test_41_reject_guard_false(self):
        c=copy.deepcopy(self.cfg)
        c['protections']['NE_PAS_REMPLACER_NULL_PAR_ZERO']=False
        with self.assertRaises(ValueError):m.check_config(c)

    def test_42_reject_fake_completion(self):
        c=copy.deepcopy(self.cfg)
        c['actions_justificatifs'][0]['statut']='TERMINE'
        with self.assertRaises(ValueError):m.check_config(c)

    def test_43_reject_public_claim(self):
        c=copy.deepcopy(self.cfg)
        c['methodes']['calcul_reel_autorise']=True
        with self.assertRaises(ValueError):m.check_config(c)

    def test_44_reject_real_data_changed(self):
        d=copy.deepcopy(self.source)
        d['regimes']['QUEBEC_DANS_CANADA']['scenarios']['central']['menages'][0]['actuel']['revenu_brut']='50000'
        with self.assertRaises(ValueError):m.inspect(self.cfg,d,self.score)

    def test_45_reject_source_claim(self):
        d=copy.deepcopy(self.source)
        d['regimes']['QUEBEC_DANS_CANADA']['scenarios']['central']['entreprises'][0]['classification_validee']=True
        with self.assertRaises(ValueError):m.inspect(self.cfg,d,self.score)

    def test_46_reject_score_change(self):
        d=copy.deepcopy(self.score);d['score_estimatif']=70
        with self.assertRaises(ValueError):m.inspect(self.cfg,self.source,d)

    def test_47_cli_default(self):
        self.assertEqual(m.main([]),0)

    def test_48_cli_no_approval(self):
        self.assertEqual(m.main(['--exiger-incidence-validee']),3)

    def test_49_cli_public(self):
        with tempfile.TemporaryDirectory() as root:
            out=Path(root)/'rapport.json'
            self.assertEqual(m.main(['--bilan-public',str(out)]),0)
            v=json.loads(out.read_text())
            self.assertEqual(v['montants_inconnus_total'],720)
            self.assertIsNone(v['taux_fiscal_propose_pct'])

    def test_50_cli_refuse_existing(self):
        with tempfile.TemporaryDirectory() as root:
            out=Path(root)/'rapport.json';out.write_text('ne pas ecraser')
            self.assertEqual(m.main(['--bilan-public',str(out)]),2)
            self.assertEqual(out.read_text(),'ne pas ecraser')

if __name__=='__main__':
    unittest.main()
