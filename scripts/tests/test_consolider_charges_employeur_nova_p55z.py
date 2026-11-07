"""P55Z : tests synthétiques de concordance et refus des fausses certifications."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'consolider_charges_employeur_nova_p55z.py'
spec = importlib.util.spec_from_file_location('p55z', SRC)
p55z = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p55z)

BASE = {
    'schema_version': 'P55Z-1', 'annee': 2026,
    'territoire': 'QUEBEC_DANS_LE_CANADA', 'nature': 'FICTIF',
    'scenario_id': 'SCENARIO-2026-TEST',
    'attestation_meme_population_fictive': True,
    'assiettes_salariales_fictives_concordantes': True,
    'hypotheses_p55x': {
        'salaire_annuel_fictif_cad': '50000.00',
        'effectif_fictif': 10,
        'secteur_fss': 'general'
    },
    'hypotheses_p55y': {
        'unites': [
            {'code':'UNIT-A', 'taux_prime_par_100_cad':'1.5000',
             'salaires_assurables_cad':'300000.00','origine_taux':'HYPOTHESE_FICTIVE'},
            {'code':'UNIT-B', 'taux_prime_par_100_cad':'3.0000',
             'salaires_assurables_cad':'200000.00','origine_taux':'HYPOTHESE_FICTIVE'}
        ]
    }
}

class TestP55Z(unittest.TestCase):
    def exemple(self):
        return copy.deepcopy(BASE)

    def c(self, d=None):
        return p55z.rapprocher(self.exemple() if d is None else d)

    def test_01_rapprochement_dans_un_meme_exemple(self):
        self.assertTrue(self.c()['rapprochement']['assiettes_fictives_concordantes'])

    def test_02_sous_total_p55x(self):
        self.assertEqual(self.c()['rapprochement']['charges_partielles_p55x_cad'],'49955.00')

    def test_03_prime_fictive_cnesst(self):
        self.assertEqual(self.c()['rapprochement']['prime_cnesst_hypothetique_p55y_cad'],'10500.00')

    def test_04_sous_total_six_charges(self):
        self.assertEqual(self.c()['rapprochement']['charges_partielles_six_postes_cad'],'60455.00')

    def test_05_salaire_plus_charges_partielles(self):
        self.assertEqual(self.c()['rapprochement']['salaire_plus_six_charges_partielles_cad'],'560455.00')

    def test_06_pas_de_cout_employeur_complet(self):
        self.assertIsNone(self.c()['rapprochement']['cout_employeur_complet_cad'])

    def test_07_aucune_economie_publique(self):
        self.assertIsNone(self.c()['rapprochement']['economie_budgetaire_publique_cad'])

    def test_08_aucun_gain_nova(self):
        self.assertIsNone(self.c()['rapprochement']['comparaison_avant_apres_nova_cad'])

    def test_09_maturite_inchangee(self):
        self.assertEqual(self.c()['score_p55n_estime_pourcent'],53)

    def test_10_bloquage_no_go(self):
        result=self.c()
        self.assertEqual(result['decision'],'NO_GO_AUTOMATIQUE')
        self.assertFalse(result['certification_independante'])

    def test_11_incoherence_assiette_bloque_somme(self):
        d=self.exemple()
        d['hypotheses_p55y']['unites'][1]['salaires_assurables_cad']='150000.00'
        result=self.c(d)['rapprochement']
        self.assertFalse(result['assiettes_fictives_concordantes'])
        self.assertIsNone(result['charges_partielles_six_postes_cad'])

    def test_12_incoherence_assiette_bloque_total_salaire(self):
        d=self.exemple()
        d['hypotheses_p55y']['unites'][1]['salaires_assurables_cad']='150000.00'
        self.assertIsNone(self.c(d)['rapprochement']['salaire_plus_six_charges_partielles_cad'])

    def test_13_taux_inconnu_bloque_total(self):
        d=self.exemple()
        d['hypotheses_p55y']['unites'][0]['taux_prime_par_100_cad']=None
        self.assertIsNone(self.c(d)['rapprochement']['charges_partielles_six_postes_cad'])

    def test_14_salaires_inconnus_bloquent_total(self):
        d=self.exemple()
        d['hypotheses_p55y']['unites'][0]['salaires_assurables_cad']=None
        self.assertIsNone(self.c(d)['rapprochement']['charges_partielles_six_postes_cad'])

    def test_15_incompatibilite_annee(self):
        d=self.exemple();d['annee']=2027
        with self.assertRaises(ValueError):self.c(d)

    def test_16_annee_booleenne(self):
        d=self.exemple();d['annee']=True
        with self.assertRaises(ValueError):self.c(d)

    def test_17_pas_de_souverainete_automatique(self):
        d=self.exemple();d['territoire']='QUEBEC_SOUVERAIN_HYPOTHETIQUE'
        with self.assertRaises(ValueError):self.c(d)

    def test_18_pas_de_preuve_declaree(self):
        d=self.exemple();d['nature']='DECLARATION_NON_AUTHENTIFIEE'
        with self.assertRaises(ValueError):self.c(d)

    def test_19_attestation_hypothese_obligatoire(self):
        d=self.exemple();d['attestation_meme_population_fictive']=False
        with self.assertRaises(ValueError):self.c(d)

    def test_20_attestation_strictement_booleenne(self):
        d=self.exemple();d['attestation_meme_population_fictive']=1
        with self.assertRaises(ValueError):self.c(d)

    def test_21_concordance_assiettes_obligatoire(self):
        d=self.exemple();d['assiettes_salariales_fictives_concordantes']=False
        with self.assertRaises(ValueError):self.c(d)

    def test_22_reference_conforme(self):
        d=self.exemple();d['scenario_id']='!x'
        with self.assertRaises(ValueError):self.c(d)

    def test_23_entree_p55x_incomplete(self):
        d=self.exemple();del d['hypotheses_p55x']['effectif_fictif']
        with self.assertRaises(ValueError):self.c(d)

    def test_24_p55y_duplicats(self):
        d=self.exemple();d['hypotheses_p55y']['unites'][1]['code']='UNIT-A'
        with self.assertRaises(ValueError):self.c(d)

    def test_25_p55y_taux_invalide(self):
        d=self.exemple();d['hypotheses_p55y']['unites'][1]['taux_prime_par_100_cad']='-3'
        with self.assertRaises(ValueError):self.c(d)

    def test_26_p55x_effectif_invalide(self):
        d=self.exemple();d['hypotheses_p55x']['effectif_fictif']=0
        with self.assertRaises(ValueError):self.c(d)

    def test_27_p55y_origine_taux_fictive_obligatoire(self):
        d=self.exemple();d['hypotheses_p55y']['unites'][1]['origine_taux']='DECISION_CNESST_DECLARATION_NON_VERIFIEE'
        with self.assertRaises(ValueError):self.c(d)

    def test_28_refus_cli_certification_code_3(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'entree.json';path.write_text(json.dumps(BASE))
            proc=subprocess.run([sys.executable,str(SRC),'--entree',str(path),'--exiger-faisabilite'],capture_output=True,text=True)
            self.assertEqual(proc.returncode,3)

    def test_29_cli_sortie_json(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'entree.json';path.write_text(json.dumps(BASE))
            proc=subprocess.run([sys.executable,str(SRC),'--entree',str(path)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['rapprochement']['charges_partielles_six_postes_cad'],'60455.00')

    def test_30_refus_ecrasement_fichier(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'entree.json';path.write_text(json.dumps(BASE))
            out=Path(td)/'bilan.json'
            args=[sys.executable,str(SRC),'--entree',str(path),'--bilan-public',str(out)]
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,2)

if __name__ == '__main__':
    unittest.main()
