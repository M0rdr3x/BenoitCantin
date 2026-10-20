"""P52W : tests contradictoires d'éligibilité, simulation et dépense fictive."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"preparer_selection_expert_nova_p52w.py"
sp=importlib.util.spec_from_file_location("nova_p52w",P)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)

def load():
 return {key:m.read(value) for key,value in m.FILES.items()}

def mock_offer(gates=None,notes=None):
 return {"fictif":True,"marqueur":"TEST_UNITAIRE_SYNTHETIQUE",
         "gates":gates or {k:True for k in m.GATES},
         "notes":notes or {k:100 for k in m.AXES}}

class QualificationTests(unittest.TestCase):
 def test_01_original_registry_passes_as_no_go(self):
  self.assertEqual(m.verify(load())["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_zero_received_offers(self):
  self.assertEqual(m.verify(load())["offres_recues"],0)
 def test_03_twelve_unchecked_gates(self):
  self.assertEqual(m.verify(load())["conditions_non_verifiees"],12)
 def test_04_five_unadopted_axes(self):
  self.assertEqual(m.verify(load())["axes_scores_non_adoptes"],5)
 def test_05_weights_sum_100_only_proposed(self):
  self.assertEqual(m.verify(load())["somme_ponderations_proposees"],100)
 def test_06_no_candidates_or_expenses(self):
  o=m.verify(load())
  self.assertEqual((o["experts_recrutes"],o["cout_engage_cad"]), (0,0))
 def test_07_no_independent_F09_signoffs(self):
  self.assertEqual(m.verify(load())["positions_F09_validees_par_humain"],0)
 def test_08_upstream_20_proofs_open(self):
  self.assertEqual(m.verify(load())["preuves_F01_F20_non_validees"],20)
 def test_09_missing_1320_values(self):
  self.assertEqual(m.verify(load())["valeurs_financieres_nova_inconnues"],1320)
 def test_10_export_blank_csv_header_only(self):
  self.assertEqual(len(list(csv.reader(io.StringIO(m.blank_csv())))),1)
 def test_11_export_no_private_candidate(self):
  self.assertNotIn("prenom",m.blank_csv())
 def test_12_fictitious_perfect_candidate_still_no_go(self):
  outcome=m.simulation_synthetique(mock_offer())
  self.assertEqual(outcome["score_indicatif_fictif"],100)
  self.assertEqual(outcome["decision"],"NO_GO_AUTOMATIQUE")
 def test_13_conflict_gate_blocks_even_perfect_offer(self):
  s=mock_offer();s["gates"]["G07"]=False
  r=m.simulation_synthetique(s)
  self.assertFalse(r["admissibilite_fictive"])
  self.assertIsNone(r["score_indicatif_fictif"])
 def test_14_unverified_authority_blocks(self):
  s=mock_offer();s["gates"]["G01"]=False
  self.assertIsNone(m.simulation_synthetique(s)["score_indicatif_fictif"])
 def test_15_valid_zero_score_still_no_mandate(self):
  s=mock_offer(notes={key:0 for key in m.AXES})
  r=m.simulation_synthetique(s)
  self.assertEqual(r["score_indicatif_fictif"],0)
  self.assertFalse(r["mandat_autorise"])
 def test_16_reject_non_fictional_prospect(self):
  s=mock_offer();s["fictif"]=False
  with self.assertRaises(ValueError):m.simulation_synthetique(s)
 def test_17_reject_personal_field_even_in_simulation(self):
  s=mock_offer();s["courriel"]="person@example.com"
  with self.assertRaises(ValueError):m.simulation_synthetique(s)
 def test_18_reject_missing_gate_in_simulation(self):
  s=mock_offer();s["gates"].pop("G07")
  with self.assertRaises(ValueError):m.simulation_synthetique(s)
 def test_19_reject_string_not_bool(self):
  s=mock_offer();s["gates"]["G07"]="true"
  with self.assertRaises(ValueError):m.simulation_synthetique(s)
 def test_20_reject_score_outside_100(self):
  s=mock_offer();s["notes"]["S05"]=101
  with self.assertRaises(ValueError):m.simulation_synthetique(s)
 def test_21_cli_zero_receipts(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"bilan.json"
   self.assertEqual(m.main(["--rapport",str(f)]),0)
   self.assertEqual(json.loads(f.read_text())["offres_recues"],0)
 def test_22_cli_blank_csv_export(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"grille.csv"
   self.assertEqual(m.main(["--export-csv",str(f)]),0)
   self.assertEqual(len(list(csv.reader(f.open(encoding="utf-8")))),1)
 def test_23_cli_strict_requires_real_mandate(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(m.main(["--exiger-mandat","--rapport",str(Path(d)/"r.json")]),3)
 def test_24_cli_missing_reference_fails(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(m.main(["--selection",str(Path(d)/"missing.json")]),2)
 def test_25_cli_never_overwrites(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"out.json"
   self.assertEqual(m.main(["--rapport",str(f)]),0)
   self.assertEqual(m.main(["--rapport",str(f)]),2)
 def test_26_cli_refuses_same_report_and_csv_path(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"same.json"
   self.assertEqual(m.main(["--rapport",str(f),"--export-csv",str(f)]),2)
 def test_27_cli_explicit_synthetic_only(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"fake.json";f.write_text(json.dumps(mock_offer()),encoding="utf-8")
   out=Path(d)/"result.json"
   self.assertEqual(m.main(["--simulation",str(f),"--rapport",str(out)]),0)
   self.assertFalse(json.loads(out.read_text())["simulation_fictive"]["mandat_autorise"])
 def test_28_summary_leaks_no_url_or_identity(self):
  result=json.dumps(m.verify(load()),ensure_ascii=False)
  for secret in ("https://","@", "cf89d3d8","numéro_de_permis"):
   self.assertNotIn(secret,result)
 def test_29_gate_01(self):
  data=load()
  data["selection"]["conditions"][0]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_30_gate_02(self):
  data=load()
  data["selection"]["conditions"][1]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_31_gate_03(self):
  data=load()
  data["selection"]["conditions"][2]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_32_gate_04(self):
  data=load()
  data["selection"]["conditions"][3]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_33_gate_05(self):
  data=load()
  data["selection"]["conditions"][4]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_34_gate_06(self):
  data=load()
  data["selection"]["conditions"][5]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_35_gate_07(self):
  data=load()
  data["selection"]["conditions"][6]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_36_gate_08(self):
  data=load()
  data["selection"]["conditions"][7]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_37_gate_09(self):
  data=load()
  data["selection"]["conditions"][8]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_38_gate_10(self):
  data=load()
  data["selection"]["conditions"][9]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_39_gate_11(self):
  data=load()
  data["selection"]["conditions"][10]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_40_gate_12(self):
  data=load()
  data["selection"]["conditions"][11]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_41_axis_01(self):
  data=load()
  data["selection"]["axes_proposes"][0]["adopte"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_42_axis_02(self):
  data=load()
  data["selection"]["axes_proposes"][1]["adopte"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_43_axis_03(self):
  data=load()
  data["selection"]["axes_proposes"][2]["adopte"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_44_axis_04(self):
  data=load()
  data["selection"]["axes_proposes"][3]["adopte"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_45_axis_05(self):
  data=load()
  data["selection"]["axes_proposes"][4]["adopte"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_46_fictional_offer_recieved(self):
  data=load()
  data["reception"]["offres"]=[{"id":"SIM01"}]
  with self.assertRaises(ValueError):m.verify(data)
 def test_47_fake_reception_total(self):
  data=load()
  data["reception"]["etat"]["receptions_authentifiees"]=1
  with self.assertRaises(ValueError):m.verify(data)
 def test_48_fake_legal_mandant(self):
  data=load()
  data["selection"]["parametres_non_adoptes"]["organisme_mandant_legalement_identifie"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_49_false_accepted_score(self):
  data=load()
  data["selection"]["parametres_non_adoptes"]["criteres_adoptes"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_50_false_budget(self):
  data=load()
  data["selection"]["parametres_non_adoptes"]["budget_max_autorise_cad"]=100000
  with self.assertRaises(ValueError):m.verify(data)
 def test_51_false_recruitment(self):
  data=load()
  data["selection"]["garde"]["experts_F09_mandates"]=1
  with self.assertRaises(ValueError):m.verify(data)
 def test_52_false_spending(self):
  data=load()
  data["selection"]["garde"]["fonds_engages_cad"]=5
  with self.assertRaises(ValueError):m.verify(data)
 def test_53_false_go(self):
  data=load()
  data["selection"]["garde"]["adoption_autorisee"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_54_false_cpa_verification(self):
  data=load()
  data["selection"]["sources"][0]["verification_reelle_effectuee"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_55_false_privacy(self):
  data=load()
  data["selection"]["donnees_confidentielles"]["aucune_sortie_de_personnes_dans_CI"]=False
  with self.assertRaises(ValueError):m.verify(data)
 def test_56_changed_cpa_url(self):
  data=load()
  data["selection"]["sources"][0]["url"]="https://example.invalid"
  with self.assertRaises(ValueError):m.verify(data)
 def test_57_changed_references(self):
  data=load()
  data["selection"]["references"]["p52v"]="wrong-path"
  with self.assertRaises(ValueError):m.verify(data)
 def test_58_changed_score_weight(self):
  data=load()
  data["selection"]["axes_proposes"][0]["poids"]=99
  with self.assertRaises(ValueError):m.verify(data)
 def test_59_false_p52v_signed(self):
  data=load()
  data["p52v"]["selection_candidat"]["contrat_signe"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_60_false_p52n_mandate(self):
  data=load()
  data["p52n"]["mandats"][8]["expert_mandate"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_61_false_p52q_expert(self):
  data=load()
  data["p52q"]["dossiers"][5]["expert_reel_mandate"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_62_false_p52u_signoff(self):
  data=load()
  data["p52u"]["relecture_humaine"]["avis_independant_signe"]=True
  with self.assertRaises(ValueError):m.verify(data)
 def test_63_false_p52a_validation(self):
  data=load()
  data["p52a"]["required_evidence"][8]["statut"]="VALIDE"
  with self.assertRaises(ValueError):m.verify(data)
if __name__=="__main__":
 unittest.main()
