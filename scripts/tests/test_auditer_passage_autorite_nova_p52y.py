"""P52Y: validation de la transmission à des personnes réelles sans approbation fictive."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"auditer_passage_autorite_nova_p52y.py"
spec=importlib.util.spec_from_file_location("p52y",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def load():return {k:m.read(v) for k,v in m.FILES.items()}
def simulate(default=False):
 return {"synthetique":True,"code":"TEST_ORDONNANCEMENT_SEULEMENT",
         "actions_fictives":{k:default for k in m.ACTIONS}}
class DossierDecisions(unittest.TestCase):
 def reject(self,change):
  d=load()
  change(d)
  with self.assertRaises(ValueError):m.validate(d)
 def test_01_validate_reference(self):
  self.assertEqual(m.validate(load())["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_ten_pending(self):
  self.assertEqual(m.validate(load())["actions_pretes_pour_remise_non_executees"],10)
 def test_03_eight_mandating_actions(self):
  self.assertEqual(m.validate(load())["actions_mandat_non_executees"],8)
 def test_04_two_github_actions(self):
  self.assertEqual(m.validate(load())["actions_protection_github_non_executees"],2)
 def test_05_four_decisions(self):
  self.assertEqual(m.validate(load())["decisions_attendues"],4)
 def test_06_zero_humans_authorized(self):
  self.assertEqual(m.validate(load())["personnes_reellement_habilitees_identifiees"],0)
 def test_07_zero_spending(self):
  self.assertEqual(m.validate(load())["budget_engage_cad"],0)
 def test_08_twenty_proofs_still_unvalidated(self):
  self.assertEqual(m.validate(load())["preuves_F01_F20_non_validees"],20)
 def test_09_missing_financial_values(self):
  self.assertEqual(m.validate(load())["donnees_financieres_nova_inconnues"],1320)
 def test_10_main_unprotected_snapshot(self):
  self.assertFalse(m.validate(load())["main_protegee_au_constat"])
 def test_11_no_github_reviews_snapshot(self):
  self.assertEqual(m.validate(load())["revues_humaines_PR_673_au_constat"],0)
 def test_12_csv_has_ten_actions_plus_header(self):
  rows=list(csv.reader(io.StringIO(m.blank_csv(load()["plan"]["actions"]))))
  self.assertEqual(len(rows),11)
 def test_13_csv_privacy_fields_initially_blank(self):
  rows=list(csv.reader(io.StringIO(m.blank_csv(load()["plan"]["actions"]))))
  self.assertTrue(all(row[7:]==["","","","",""] for row in rows[1:]))
 def test_14_csv_shows_expected_last_action(self):
  rows=list(csv.reader(io.StringIO(m.blank_csv(load()["plan"]["actions"]))))
  self.assertEqual(rows[-1][0],"A10")
 def test_15_github_decision_links_both_controls(self):
  dossier=load()["plan"]["decisions"][3]
  self.assertEqual(dossier["actions_requises"],["A07","A08"])
 def test_16_dependencies_acyclic(self):
  for key,(_,_,requires,_) in m.ACTIONS.items():
   self.assertTrue(all(int(prereq[1:])<int(key[1:]) for prereq in requires))
 def test_17_simulated_none_is_not_real(self):
  result=m.simulation_fictive(simulate())
  self.assertEqual(result["actions_fictivement_accomplies"],0)
  self.assertFalse(result["fusion_autorisee"])
 def test_18_simulated_everything_is_still_no_go(self):
  result=m.simulation_fictive(simulate(True))
  self.assertEqual(result["actions_fictivement_accomplies"],10)
  self.assertEqual(result["decision"],"NO_GO_AUTOMATIQUE")
  self.assertFalse(result["protection_main_reellement_verifiee"])
 def test_19_fictitious_missing_dependency_flagged(self):
  case=simulate();case["actions_fictives"]["A09"]=True
  r=m.simulation_fictive(case)
  self.assertIn("A09",r["actions_avec_dependances_non_satisfaites"])
 def test_20_invented_real_candidate_in_simulation_rejected(self):
  case=simulate();case["courriel"]="user@example.org"
  with self.assertRaises(ValueError):m.simulation_fictive(case)
 def test_21_non_synthetic_data_rejected(self):
  case=simulate();case["synthetique"]=False
  with self.assertRaises(ValueError):m.simulation_fictive(case)
 def test_22_missing_action_in_simulation_rejected(self):
  case=simulate();del case["actions_fictives"]["A07"]
  with self.assertRaises(ValueError):m.simulation_fictive(case)
 def test_23_string_instead_of_boolean_rejected(self):
  case=simulate();case["actions_fictives"]["A07"]="true"
  with self.assertRaises(ValueError):m.simulation_fictive(case)
 def test_24_cli_summary_no_go(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"bilan.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(json.loads(p.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_25_cli_strict_authentication_exit_three(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"bilan.json"
   self.assertEqual(m.main(["--exiger-autorisations","--rapport",str(p)]),3)
 def test_26_cli_csv_export_has_no_human_signature(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"grille.csv"
   self.assertEqual(m.main(["--export-csv",str(p)]),0)
   rows=list(csv.reader(p.open(encoding="utf-8")))
   self.assertEqual(len(rows),11)
   self.assertFalse(any(row[7] for row in rows[1:]))
 def test_27_cli_missing_registry_exit_two(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--plan",str(Path(td)/"absent.json")]),2)
 def test_28_cli_never_overwrite_summary(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"a.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(m.main(["--rapport",str(p)]),2)
 def test_29_cli_same_csv_and_report_exit_two(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"same.json"
   self.assertEqual(m.main(["--rapport",str(p),"--export-csv",str(p)]),2)
 def test_30_cli_synthetic_simulation_no_real_permission(self):
  with tempfile.TemporaryDirectory() as td:
   s=Path(td)/"fiction.json"
   s.write_text(json.dumps(simulate(True)))
   out=Path(td)/"result.json"
   self.assertEqual(m.main(["--simulation",str(s),"--rapport",str(out)]),0)
   result=json.loads(out.read_text())
   self.assertEqual(result["simulation"]["decision"],"NO_GO_AUTOMATIQUE")
 def test_31_output_aggregate_without_sensitive_information(self):
  report=json.dumps(m.validate(load()))
  for forbidden in ("https://","@", "courriel_prive", "signature_scannee", "conflict_private_record"):
   self.assertNotIn(forbidden,report)
 def test_32_action_01_false_signoff(self):
  d=load()
  d["plan"]["actions"][0]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_33_action_02_false_signoff(self):
  d=load()
  d["plan"]["actions"][1]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_34_action_03_false_signoff(self):
  d=load()
  d["plan"]["actions"][2]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_35_action_04_false_signoff(self):
  d=load()
  d["plan"]["actions"][3]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_36_action_05_false_signoff(self):
  d=load()
  d["plan"]["actions"][4]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_37_action_06_false_signoff(self):
  d=load()
  d["plan"]["actions"][5]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_38_action_07_false_signoff(self):
  d=load()
  d["plan"]["actions"][6]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_39_action_08_false_signoff(self):
  d=load()
  d["plan"]["actions"][7]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_40_action_09_false_signoff(self):
  d=load()
  d["plan"]["actions"][8]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_41_action_10_false_signoff(self):
  d=load()
  d["plan"]["actions"][9]["signature_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_42_decision_1_false_signoff(self):
  d=load()
  d["plan"]["decisions"][0]["decision_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_43_decision_2_false_signoff(self):
  d=load()
  d["plan"]["decisions"][1]["decision_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_44_decision_3_false_signoff(self):
  d=load()
  d["plan"]["decisions"][2]["decision_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_45_decision_4_false_signoff(self):
  d=load()
  d["plan"]["decisions"][3]["decision_authentifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_46_fake_owner(self):
  d=load()
  d["plan"]["actions"][0]["responsable_reel_designe"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_47_fake_private_evidence(self):
  d=load()
  d["plan"]["actions"][3]["preuve_confidentielle_stockee_hors_git"]="secret"
  with self.assertRaises(ValueError):m.validate(d)
 def test_48_fake_completed_action(self):
  d=load()
  d["plan"]["actions"][4]["statut"]="TERMINE"
  with self.assertRaises(ValueError):m.validate(d)
 def test_49_alter_dependency(self):
  d=load()
  d["plan"]["actions"][9]["dependances"]=["A07"]
  with self.assertRaises(ValueError):m.validate(d)
 def test_50_fake_budget(self):
  d=load()
  d["plan"]["points_non_delegables"]["budget_cad_veritablement_accorde"]=3000
  with self.assertRaises(ValueError):m.validate(d)
 def test_51_fake_main_protection(self):
  d=load()
  d["plan"]["points_non_delegables"]["main_protegee_via_github"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_52_fake_human_review(self):
  d=load()
  d["plan"]["points_non_delegables"]["minimum_une_revue_reelle_requise_et_obtenue"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_53_fake_legal_mandant(self):
  d=load()
  d["plan"]["points_non_delegables"]["instance_mandante_legalement_qualifiee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_54_fake_real_offer(self):
  d=load()
  d["plan"]["points_non_delegables"]["candidatures_confidentielles_reellement_recues"]=1
  with self.assertRaises(ValueError):m.validate(d)
 def test_55_fake_go(self):
  d=load()
  d["plan"]["bilan"]["fusion_autorisee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_56_tampered_pr(self):
  d=load()
  d["plan"]["github_snapshot"]["pr_numero"]=999
  with self.assertRaises(ValueError):m.validate(d)
 def test_57_tampered_issue(self):
  d=load()
  d["plan"]["github_snapshot"]["issue_securite"]["numero"]=999
  with self.assertRaises(ValueError):m.validate(d)
 def test_58_fake_branch_protected_snapshot(self):
  d=load()
  d["plan"]["github_snapshot"]["main_protegee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_59_fake_branch_ruleset_snapshot(self):
  d=load()
  d["plan"]["github_snapshot"]["rulesets_nombre"]=1
  with self.assertRaises(ValueError):m.validate(d)
 def test_60_fake_real_reviews_snapshot(self):
  d=load()
  d["plan"]["github_snapshot"]["pr_relectures_humaines"]=1
  with self.assertRaises(ValueError):m.validate(d)
 def test_61_falsely_approved_journal(self):
  d=load()
  d["journal"]["actions_autorisees"]=1
  with self.assertRaises(ValueError):m.validate(d)
 def test_62_fake_journal_entry(self):
  d=load()
  d["journal"]["evenements"]=[{"id":"fake"}]
  with self.assertRaises(ValueError):m.validate(d)
 def test_63_fake_journal_approval(self):
  d=load()
  d["journal"]["decision"]="GO"
  with self.assertRaises(ValueError):m.validate(d)
 def test_64_fake_p52x_auth(self):
  d=load()
  d["p52x"]["decision_precontractuelle"]["mandant_legal_identifie"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_65_fake_p52x_x01(self):
  d=load()
  d["p52x"]["preconditions"][0]["etat"]="VALIDE"
  with self.assertRaises(ValueError):m.validate(d)
 def test_66_fake_p52w_gate(self):
  d=load()
  d["p52w"]["conditions"][0]["verification_humaine"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_67_fake_p52w_candidate(self):
  d=load()
  d["p52w"]["garde"]["candidats_reels_recus"]=1
  with self.assertRaises(ValueError):m.validate(d)
 def test_68_fake_p52v_signed(self):
  d=load()
  d["p52v"]["selection_candidat"]["contrat_signe"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_69_fake_p52n_signature(self):
  d=load()
  d["p52n"]["controles_transversaux"]["contrat_ou_depense_non_engage"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_70_fake_p52a_go(self):
  d=load()
  d["p52a"]["automatic_go"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_71_fake_p52a_f09(self):
  d=load()
  d["p52a"]["required_evidence"][8]["statut"]="VALIDE"
  with self.assertRaises(ValueError):m.validate(d)
 def test_72_mismatched_source_link(self):
  d=load()
  d["plan"]["references"]["p52x"]="other.json"
  with self.assertRaises(ValueError):m.validate(d)
 def test_73_wrong_action_count(self):
  d=load()
  d["plan"]["bilan"]["actions_humaines_non_executees"]=9
  with self.assertRaises(ValueError):m.validate(d)
 def test_74_fake_pii_upload(self):
  d=load()
  d["plan"]["points_non_delegables"]["aucun_document_personnel_dans_depot"]=False
  with self.assertRaises(ValueError):m.validate(d)
if __name__=="__main__":
 unittest.main()
