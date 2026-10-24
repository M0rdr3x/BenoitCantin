"""P52J: vingt-quatre tests contradictoires sur la transcription du budget."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"controler_relecture_budget_nova_p52j.py"
spec=importlib.util.spec_from_file_location("p52j_relecture",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def data():
    return {k:m.charge(p) for k,p in m.FILES.items()}

class AuditBudgetP52J(unittest.TestCase):
    def test_01_39_montants_concordants(self):
        self.assertEqual(m.comparer(data())["recoupements_numeriques_locaux"],39)
    def test_02_21_lignes_de_revenus(self):
        self.assertEqual(m.comparer(data())["lignes_revenus_concordantes"],21)
    def test_03_8_agregats(self):
        self.assertEqual(m.comparer(data())["agregats_revenus_concordants"],8)
    def test_04_10_lignes_de_plan(self):
        self.assertEqual(m.comparer(data())["lignes_plan_budgétaire_concordantes"],10)
    def test_05_pas_certification_independante(self):
        self.assertFalse(m.comparer(data())["relecture_humaine_independante"])
    def test_06_f09_reste_non_atteste(self):
        self.assertFalse(m.comparer(data())["f09_preuve_independante_obtenue"])
    def test_07_20_preuves_non_attestees(self):
        self.assertEqual(m.comparer(data())["preuves_P52A_encore_non_attestees"],20)
    def test_08_1320_inconnues_restant(self):
        self.assertEqual(m.comparer(data())["champs_financiers_P52H_encore_inconnus"],1320)
    def test_09_chiffre_recette_change_rejete(self):
        d=data()
        d["lecture"]["transcription_discours_tableau3"]["lignes_revenus"][0]["valeur_mcad"]="999"
        with self.assertRaises(ValueError):m.comparer(d)
    def test_10_identifiant_renomme_rejete(self):
        d=data()
        d["lecture"]["transcription_discours_tableau3"]["lignes_revenus"][0]["id"]="fake"
        with self.assertRaises(ValueError):m.comparer(d)
    def test_11_agregat_falsifie_rejete(self):
        d=data()
        d["lecture"]["transcription_discours_tableau3"]["sous_totaux_officiels_mcad"]["revenus_totaux"]="1"
        with self.assertRaises(ValueError):m.comparer(d)
    def test_12_depenses_positives_dans_source_rejetees(self):
        d=data()
        d["lecture"]["transcription_plan_budgetaire_f2"]["montants_signes_comme_affiches_mcad"]["service_dette"]="10268"
        with self.assertRaises(ValueError):m.comparer(d)
    def test_13_fonds_generation_change_rejete(self):
        d=data()
        d["lecture"]["transcription_plan_budgetaire_f2"]["montants_signes_comme_affiches_mcad"]["versements_fonds_generations"]="-1"
        with self.assertRaises(ValueError):m.comparer(d)
    def test_14_pdf_source_redirige_rejete(self):
        d=data()
        d["lecture"]["source_primaires"][0]["url"]="https://evil.example.org/faux.pdf"
        with self.assertRaises(ValueError):m.comparer(d)
    def test_15_fausse_signature_rejetee(self):
        d=data()
        d["lecture"]["validation_de_nature"]["validation_par_expert_independant"]=True
        with self.assertRaises(ValueError):m.comparer(d)
    def test_16_fausse_publication_rejetee(self):
        d=data()
        d["lecture"]["validation_de_nature"]["publication_autorisee"]=True
        with self.assertRaises(ValueError):m.comparer(d)
    def test_17_f09_faussement_validee_rejetee(self):
        d=data()
        d["preuves"]["required_evidence"][8]["statut"]="VALIDE"
        with self.assertRaises(ValueError):m.comparer(d)
    def test_18_fausse_certification_p52i_rejetee(self):
        d=data()
        d["pistes"]["donnees_extraites_certifiees"]=True
        with self.assertRaises(ValueError):m.comparer(d)
    def test_19_deficit_officiel_altere_rejete(self):
        d=data()
        d["budget"]["depenses_et_ajustements_officiels_mcad"]["solde_budgetaire_loi_equilibre"]="-4265"
        with self.assertRaises(ValueError):m.comparer(d)
    def test_20_source_budget_ambigue_rejetee(self):
        d=data()
        d["budget"]["sources"][1]["id"]="DISC2026_T3"
        with self.assertRaises(ValueError):m.comparer(d)
    def test_21_rapport_ne_contient_aucune_valeur_de_cas(self):
        d=data()
        d["lecture"]["transcription_discours_tableau3"]["note_taxes_de_vente"] += " CONFIDENTIEL_TEST_P52J"
        r=json.dumps(m.comparer(d),ensure_ascii=False)
        self.assertNotIn("CONFIDENTIEL_TEST_P52J",r)
        self.assertNotIn("https://",r)
        self.assertNotIn("valeur_mcad",r)
    def test_22_cli_normal_observation_seulement(self):
        with tempfile.TemporaryDirectory() as p:
            target=Path(p)/"res.json"
            self.assertEqual(m.main(["--rapport",str(target)]),0)
            self.assertFalse(json.loads(target.read_text("utf-8"))["fusion_autorisee"])
    def test_23_cli_strict_retourne_code_3(self):
        with tempfile.TemporaryDirectory() as p:
            self.assertEqual(m.main(["--exiger-attestation","--rapport",str(Path(p)/"r.json")]),3)
    def test_24_cli_fichier_absent_refuse(self):
        with tempfile.TemporaryDirectory() as p:
            target=Path(p)/"r.json"
            self.assertEqual(m.main(["--lecture",str(Path(p)/"absent.json"),"--rapport",str(target)]),2)
            self.assertEqual(json.loads(target.read_text("utf-8"))["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
