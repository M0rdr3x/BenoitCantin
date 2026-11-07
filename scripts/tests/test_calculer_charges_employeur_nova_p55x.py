"""Tests synthétiques P55X : arithmétique, inconnues et non-adoption."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'calculer_charges_employeur_nova_p55x.py'
spec = importlib.util.spec_from_file_location('p55x', SRC)
p55x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p55x)

class ChargesEmployeurP55X(unittest.TestCase):
    def test_reference_10_salaries_50k_general(self):
        r = p55x.calculer('50000.00', 10, 'general')
        c = r['calculs_conditionnels']
        self.assertEqual(c['masse_salariale_cad'], '500000.00')
        self.assertEqual(c['trois_cotisations_p55w_cad'], '41405.00')
        self.assertEqual(c['fonds_services_sante_cad'], '8250.00')
        self.assertEqual(c['cotisation_normes_travail_cad'], '300.00')
        self.assertEqual(c['somme_charges_partielles_cad'], '49955.00')
    def test_manufacturier_non_exonere(self):
        r=p55x.calculer('50000',10,'primaire_manufacturier')
        self.assertEqual(r['calculs_conditionnels']['fonds_services_sante_cad'],'6250.00')
        self.assertEqual(r['calculs_conditionnels']['somme_charges_partielles_cad'],'47955.00')
    def test_secteur_public(self):
        self.assertEqual(p55x.taux_fss(Decimal('500000'),'public'),Decimal('4.26'))
    def test_fss_1m_general(self):
        self.assertEqual(p55x.taux_fss(Decimal('1000000'),'general'), Decimal('1.65'))
    def test_fss_1m_manufacturier(self):
        self.assertEqual(p55x.taux_fss(Decimal('1000000'),'primaire_manufacturier'), Decimal('1.25'))
    def test_fss_7800000(self):
        self.assertEqual(p55x.taux_fss(Decimal('7800000'),'general'), Decimal('4.26'))
    def test_fss_intermediaire_general(self):
        self.assertEqual(p55x.taux_fss(Decimal('2000000'),'general'), Decimal('2.0338'))
    def test_fss_intermediaire_manufacturier(self):
        self.assertEqual(p55x.taux_fss(Decimal('2000000'),'primaire_manufacturier'), Decimal('1.6926'))
    def test_normes_plafond(self):
        self.assertEqual(p55x.calculer('200000',1,'general')['calculs_conditionnels']['cotisation_normes_travail_cad'], '61.80')
    def test_rrq_plafond(self):
        self.assertEqual(p55x.calculer('100000',1,'general')['calculs_conditionnels']['rrq_employeur_cad'], '4895.30')
    def test_non_imputation_cnesst(self):
        r=p55x.calculer('50000',10,'general')
        self.assertIsNone(r['calculs_conditionnels']['prime_cnesst_sst_cad'])
        self.assertIsNone(r['calculs_conditionnels']['cout_complet_employeur_cad'])
        self.assertIsNone(r['calculs_conditionnels']['variation_nova_cad'])
        self.assertEqual(r['decision'],'NO_GO_AUTOMATIQUE')
        self.assertFalse(r['faisabilite_nova_certifiee'])
    def test_invalid_money(self):
        for val in ('-1','1e4','1.234','NaN','Infinity','1000,00',''):
            with self.subTest(val=val),self.assertRaises(ValueError):p55x.montant(val)
    def test_invalid_effectif(self):
        for val in (0,-2,True,100001):
            with self.subTest(val=val),self.assertRaises(ValueError):p55x.calculer('50000',val,'general')
    def test_invalid_sector(self):
        with self.assertRaises(ValueError):p55x.calculer('50000',10,'une_fausse_categorie')
    def test_cli_refus_sans_hypotheses(self):
        x=subprocess.run([sys.executable,str(SRC),'--salaire','50000','--effectif','10','--secteur','general'],capture_output=True,text=True)
        self.assertEqual(x.returncode,2)
    def test_cli_refus_go(self):
        x=subprocess.run([sys.executable,str(SRC),'--salaire','50000','--effectif','10','--secteur','general','--hypotheses-confirmees','--exiger-faisabilite'],capture_output=True,text=True)
        self.assertEqual(x.returncode,3)
    def test_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bilan.json'
            cmd=[sys.executable,str(SRC),'--salaire','50000','--effectif','10','--secteur','general','--hypotheses-confirmees','--bilan-public',str(p)]
            a=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(a.returncode,0)
            self.assertIsNone(json.loads(p.read_text())['calculs_conditionnels']['prime_cnesst_sst_cad'])
            b=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(b.returncode,2)
    def test_zero_salary_is_not_savings(self):
        r=p55x.calculer('0',1,'general')
        self.assertEqual(r['calculs_conditionnels']['somme_charges_partielles_cad'],'0.00')
        self.assertEqual(r['decision'],'NO_GO_AUTOMATIQUE')

if __name__ == '__main__':
    unittest.main()
