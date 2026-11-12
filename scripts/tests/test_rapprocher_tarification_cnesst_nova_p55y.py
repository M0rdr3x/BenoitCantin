"""Tests P55Y : non-confusion salaires, taux, origine, GO et absence de données."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from decimal import Decimal

SRC = Path(__file__).resolve().parents[1] / 'rapprocher_tarification_cnesst_nova_p55y.py'
spec = importlib.util.spec_from_file_location('p55y', SRC)
p55y = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p55y)

EXAMPLE = {
    'schema_version': 'P55Y-1', 'annee': 2026,
    'territoire': 'QUEBEC_DANS_LE_CANADA', 'nature': 'FICTIF',
    'unites': [
        {'code': 'UNIT-A', 'taux_prime_par_100_cad': '1.5000',
         'salaires_assurables_cad': '300000.00', 'origine_taux': 'HYPOTHESE_FICTIVE'},
        {'code': 'UNIT-B', 'taux_prime_par_100_cad': '3.0000',
         'salaires_assurables_cad': '200000.00', 'origine_taux': 'HYPOTHESE_FICTIVE'}
    ]
}

class TestsP55Y(unittest.TestCase):
    def example(self):
        return copy.deepcopy(EXAMPLE)
    def test_01_calcule_deux_unites(self):
        r = p55y.rapprocher(self.example())
        self.assertEqual(r['prime_cnesst_conditionnelle_totale_cad'],'10500.00')
        self.assertEqual(r['salaires_assurables_totaux_cad'],'500000.00')
    def test_02_calcul_unitaire(self):
        r=p55y.rapprocher(self.example())
        self.assertEqual([i['cotisation_conditionnelle_cad'] for i in r['unites']],['4500.00','6000.00'])
    def test_03_total_employeur_inconnu(self):
        self.assertIsNone(p55y.rapprocher(self.example())['cout_total_employeur_cad'])
    def test_04_nova_inconnu(self):
        self.assertIsNone(p55y.rapprocher(self.example())['gain_nova_cad'])
    def test_05_statut_no_go(self):
        r=p55y.rapprocher(self.example())
        self.assertEqual(r['decision'],'NO_GO_AUTOMATIQUE')
        self.assertFalse(r['avis_professionnel_authentifie'])
    def test_06_taux_absent_propage_null(self):
        d=self.example();d['unites'][0]['taux_prime_par_100_cad']=None
        r=p55y.rapprocher(d)
        self.assertEqual(r['nombre_unites_incompletes'],1)
        self.assertIsNone(r['prime_cnesst_conditionnelle_totale_cad'])
    def test_07_salaires_absents_propage_null(self):
        d=self.example();d['unites'][1]['salaires_assurables_cad']=None
        self.assertIsNone(p55y.rapprocher(d)['salaires_assurables_totaux_cad'])
    def test_08_ne_remplace_pas_null_par_zero(self):
        d=self.example();d['unites'][0]['taux_prime_par_100_cad']=None
        self.assertIsNone(p55y.rapprocher(d)['unites'][0]['cotisation_conditionnelle_cad'])
    def test_09_refuse_taux_negatif(self):
        d=self.example();d['unites'][0]['taux_prime_par_100_cad']='-1'
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_10_refuse_valeur_exponentielle(self):
        d=self.example();d['unites'][0]['salaires_assurables_cad']='1e5'
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_11_refuse_taux_mille(self):
        d=self.example();d['unites'][0]['taux_prime_par_100_cad']='101'
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_12_refuse_code_duplique(self):
        d=self.example();d['unites'][1]['code']='UNIT-A'
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_13_refuse_nature_inconnue(self):
        d=self.example();d['nature']='CERTIFIE'
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_14_refuse_nature_documentaire_fictive(self):
        d=self.example();d['nature']='DECLARATION_NON_AUTHENTIFIEE'
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_15_documentaire_reste_non_certifie(self):
        d=self.example();d['nature']='DECLARATION_NON_AUTHENTIFIEE'
        for i in d['unites']:i['origine_taux']='DECISION_CNESST_DECLARATION_NON_VERIFIEE'
        r=p55y.rapprocher(d)
        self.assertEqual(r['statut'],'MODELE_CONDITIONNEL_NON_AUTHENTIFIE')
    def test_16_refuse_souverain_hypothetique(self):
        d=self.example();d['territoire']='QUEBEC_SOUVERAIN'
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_17_refuse_2027(self):
        d=self.example();d['annee']=2027
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_18_refuse_bool_annee(self):
        d=self.example();d['annee']=True
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_19_refuse_table_vide(self):
        d=self.example();d['unites']=[]
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_20_test_arrondi_monetaire(self):
        self.assertEqual(p55y.monnaie(Decimal('0.005')),'0.01')
    def test_21_rejet_decla_pas_source(self):
        d=self.example();d['nature']='DECLARATION_NON_AUTHENTIFIEE'
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_22_cli_non_autorisation(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'entree.json';p.write_text(json.dumps(EXAMPLE))
            r=subprocess.run([sys.executable,str(SRC),'--entree',str(p),'--exiger-faisabilite'],capture_output=True)
            self.assertEqual(r.returncode,3)
    def test_23_cli_refus_ecrasement(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'entree.json';p.write_text(json.dumps(EXAMPLE))
            output=Path(td)/'bilan.json'
            argv=[sys.executable,str(SRC),'--entree',str(p),'--bilan-public',str(output)]
            self.assertEqual(subprocess.run(argv,capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(argv,capture_output=True).returncode,2)
    def test_24_cli_valide_json(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'entree.json';p.write_text(json.dumps(EXAMPLE))
            r=subprocess.run([sys.executable,str(SRC),'--entree',str(p)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0)
            self.assertEqual(json.loads(r.stdout)['prime_cnesst_conditionnelle_totale_cad'],'10500.00')
    def test_25_refuse_precision_taux_excessive(self):
        d=self.example();d['unites'][1]['taux_prime_par_100_cad']='1.12345'
        with self.assertRaises(ValueError):p55y.rapprocher(d)
    def test_26_une_unite_valeur_zero_reelle(self):
        d=self.example();d['unites'][0]['salaires_assurables_cad']='0.00'
        r=p55y.rapprocher(d)
        self.assertEqual(r['unites'][0]['cotisation_conditionnelle_cad'],'0.00')
    def test_27_trop_unites(self):
        d=self.example();d['unites']=[dict(EXAMPLE['unites'][0],code=f'U-{i}') for i in range(31)]
        with self.assertRaises(ValueError):p55y.rapprocher(d)

if __name__=='__main__':unittest.main()
