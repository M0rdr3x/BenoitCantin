"""P52X: controles adversariaux precontractuels; ni candidat ni signature."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"controler_habilitation_mandat_nova_p52x.py"
spec=importlib.util.spec_from_file_location("nova_p52x",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def upstream():
 return {key:m.read(path) for key,path in m.FILES.items()}
def simulated(path="ENTITE_PRIVEE_AUTRE",positive=True):
 return {
  "synthetique":True,"marqueur":"TEST_HYPOTHETIQUE_SANS_IDENTITE",
  "hypothese_juridique":path,
  "preconditions_fictives":{id_:positive for id_ in m.GATES}
 }
class PrioritesLegalesTests(unittest.TestCase):
 def rejected(self,mutation):
  docs=upstream()
  mutation(docs)
  with self.assertRaises(ValueError):m.validate(docs)
 def test_01_manifest_current_no_go(self):
  self.assertEqual(m.validate(upstream())["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_twelve_gates_undocumented(self):
  self.assertEqual(m.validate(upstream())["preconditions_sans_decision_humaine"],12)
 def test_03_four_status_unconfirmed(self):
  self.assertEqual(m.validate(upstream())["regimes_non_qualifies"],4)
 def test_04_upstream_gates_not_verified(self):
  self.assertEqual(m.validate(upstream())["gates_p52w_restes_non_verifies"],12)
 def test_05_no_channel(self):
  self.assertEqual(m.validate(upstream())["canaux_confidentiels_actifs"],0)
 def test_06_no_budget(self):
  self.assertIs(m.validate(upstream())["budget_autorise"],False)
 def test_07_no_candidates(self):
  self.assertEqual(m.validate(upstream())["candidatures_recues"],0)
 def test_08_no_independent_review(self):
  self.assertEqual(m.validate(upstream())["expertises_F09_independantes_obtenues"],0)
 def test_09_twenty_proofs(self):
  self.assertEqual(m.validate(upstream())["preuves_f01_f20_non_validees"],20)
 def test_10_missing_1320_values(self):
  self.assertEqual(m.validate(upstream())["variables_financieres_nova_inconnues"],1320)
 def test_11_csv_twelve_rows_and_header(self):
  self.assertEqual(len(list(csv.reader(io.StringIO(m.blank_csv(upstream()["plan"]))))),13)
 def test_12_csv_private_fields_initially_blank(self):
  rows=list(csv.reader(io.StringIO(m.blank_csv(upstream()["plan"]))))
  self.assertTrue(all(row[5:]==["","","","",""] for row in rows[1:]))
 def test_13_csv_first_gate(self):
  rows=list(csv.reader(io.StringIO(m.blank_csv(upstream()["plan"]))))
  self.assertEqual(rows[1][0],"X01")
 def test_14_csv_last_gate(self):
  rows=list(csv.reader(io.StringIO(m.blank_csv(upstream()["plan"]))))
  self.assertEqual(rows[-1][0],"X12")
 def test_15_all_fictionally_completed_always_no_go(self):
  r=m.scenario_fictif(simulated())
  self.assertEqual(r["preconditions_fictivement_positives"],12)
  self.assertFalse(r["sollicitation_autorisee"])
  self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
 def test_16_partial_fiction_still_non_authorizing(self):
  s=simulated();s["preconditions_fictives"]["X07"]=False
  r=m.scenario_fictif(s)
  self.assertEqual(r["preconditions_fictivement_positives"],11)
  self.assertTrue(r["inadmissibilite_simulee"])
 def test_17_no_fictional_gates_succeeds_only_hypothetically(self):
  r=m.scenario_fictif(simulated(positive=False))
  self.assertFalse(r["decision_contractuelle_reelle"])
 def test_18_unlisted_pathway_rejected(self):
  s=simulated();s["hypothese_juridique"]="ROYAUME_INCONNU"
  with self.assertRaises(ValueError):m.scenario_fictif(s)
 def test_19_missing_gate_rejected(self):
  s=simulated();s["preconditions_fictives"].pop("X01")
  with self.assertRaises(ValueError):m.scenario_fictif(s)
 def test_20_str_boolean_instead_of_bool_rejected(self):
  s=simulated();s["preconditions_fictives"]["X09"]="true"
  with self.assertRaises(ValueError):m.scenario_fictif(s)
 def test_21_private_personal_field_rejected(self):
  s=simulated();s["courriel"]="person@example.invalid"
  with self.assertRaises(ValueError):m.scenario_fictif(s)
 def test_22_real_record_disguised_as_simulation_rejected(self):
  s=simulated();s["synthetique"]=False
  with self.assertRaises(ValueError):m.scenario_fictif(s)
 def test_23_cli_normal_no_go(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"summary.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(json.loads(p.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_24_cli_strict_habilitation_refused(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(m.main(["--exiger-habilitation","--rapport",str(Path(d)/"summary.json")]),3)
 def test_25_cli_csv_export_only_template(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"template.csv"
   self.assertEqual(m.main(["--export-csv",str(p)]),0)
   self.assertEqual(len(list(csv.reader(p.open(encoding="utf-8")))),13)
 def test_26_cli_missing_json_code_two(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(m.main(["--plan",str(Path(d)/"absent.json")]),2)
 def test_27_cli_refuses_existing_report(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"summary.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(m.main(["--rapport",str(p)]),2)
 def test_28_cli_same_csv_and_report_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"same.json"
   self.assertEqual(m.main(["--rapport",str(p),"--export-csv",str(p)]),2)
 def test_29_cli_simulation_never_authorizes_contact(self):
  with tempfile.TemporaryDirectory() as d:
   s=Path(d)/"scenario.json";s.write_text(json.dumps(simulated()))
   out=Path(d)/"summary.json"
   self.assertEqual(m.main(["--simulation",str(s),"--rapport",str(out)]),0)
   r=json.loads(out.read_text())
   self.assertIs(r["hypothese_synthetique"]["sollicitation_autorisee"],False)
 def test_30_summary_does_not_leak_urls_or_personal_data(self):
  s=json.dumps(m.validate(upstream()),ensure_ascii=False)
  for forbidden in ("https://","@", "F09", "nom_du_candidat","cv"):
   self.assertNotIn(forbidden,s)
 def test_31_false_gate_1(self):
  documents=upstream()
  documents["plan"]["preconditions"][0]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_32_false_gate_2(self):
  documents=upstream()
  documents["plan"]["preconditions"][1]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_33_false_gate_3(self):
  documents=upstream()
  documents["plan"]["preconditions"][2]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_34_false_gate_4(self):
  documents=upstream()
  documents["plan"]["preconditions"][3]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_35_false_gate_5(self):
  documents=upstream()
  documents["plan"]["preconditions"][4]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_36_false_gate_6(self):
  documents=upstream()
  documents["plan"]["preconditions"][5]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_37_false_gate_7(self):
  documents=upstream()
  documents["plan"]["preconditions"][6]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_38_false_gate_8(self):
  documents=upstream()
  documents["plan"]["preconditions"][7]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_39_false_gate_9(self):
  documents=upstream()
  documents["plan"]["preconditions"][8]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_40_false_gate_10(self):
  documents=upstream()
  documents["plan"]["preconditions"][9]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_41_false_gate_11(self):
  documents=upstream()
  documents["plan"]["preconditions"][10]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_42_false_gate_12(self):
  documents=upstream()
  documents["plan"]["preconditions"][11]["decision_humaine_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_43_false_mandant(self):
  documents=upstream()
  documents["plan"]["decision_precontractuelle"]["mandant_legal_identifie"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_44_false_delegation(self):
  documents=upstream()
  documents["plan"]["decision_precontractuelle"]["delegation_signature_authentifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_45_invented_spending(self):
  documents=upstream()
  documents["plan"]["decision_precontractuelle"]["fonds_engages_cad"]=100
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_46_invented_budget(self):
  documents=upstream()
  documents["plan"]["decision_precontractuelle"]["budget_total_autorise_cad"]=5000
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_47_fake_private_channel(self):
  documents=upstream()
  documents["plan"]["securite_reception"]["canal_de_reception_operationnel"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_48_fake_privacy_notice(self):
  documents=upstream()
  documents["plan"]["securite_reception"]["avis_confidentialite_approuve"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_49_fake_collected_candidates(self):
  documents=upstream()
  documents["plan"]["securite_reception"]["aucune_collecte_reelle_en_cours"]=False
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_50_fake_party_status(self):
  documents=upstream()
  documents["plan"]["hypotheses_statut_mandant"][1]["retenue_juridiquement"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_51_fake_elections_qc_source_verification(self):
  documents=upstream()
  documents["plan"]["sources_officielles_a_verifier"][0]["verification_statut_effectuee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_52_replaced_electoral_url(self):
  documents=upstream()
  documents["plan"]["sources_officielles_a_verifier"][0]["url"]="https://invalid.example"
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_53_faked_contract(self):
  documents=upstream()
  documents["plan"]["decision_precontractuelle"]["contrat_signe"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_54_faked_expert(self):
  documents=upstream()
  documents["plan"]["decision_precontractuelle"]["relecteur_humain_mandate"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_55_faked_go(self):
  documents=upstream()
  documents["plan"]["decision_precontractuelle"]["adoption_autorisee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_56_unknown_gate_name(self):
  documents=upstream()
  documents["plan"]["preconditions"][0]["id"]="X99"
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_57_changed_p52w_link(self):
  documents=upstream()
  documents["plan"]["preconditions"][0]["correspondance_p52w"]="G77"
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_58_pathway_removed(self):
  documents=upstream()
  documents["plan"]["hypotheses_statut_mandant"][0]["description"]="x"
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_59_fake_p52w_authority(self):
  documents=upstream()
  documents["p52w"]["parametres_non_adoptes"]["organisme_mandant_legalement_identifie"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_60_fake_p52w_receipt(self):
  documents=upstream()
  documents["reception_p52w"]["offres"]=[{"fake":true}]
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_61_fake_p52v_contract(self):
  documents=upstream()
  documents["p52v"]["selection_candidat"]["contrat_signe"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_62_fake_p52n_money(self):
  documents=upstream()
  documents["p52n"]["controles_transversaux"]["contrat_ou_depense_non_engage"]=False
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_63_fake_p52q_decision(self):
  documents=upstream()
  documents["p52q"]["gouvernance"]["decision"]="GO"
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_64_fake_p52a_approval(self):
  documents=upstream()
  documents["p52a"]["automatic_go"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_65_fake_p52a_f09(self):
  documents=upstream()
  documents["p52a"]["required_evidence"][8]["statut"]="VALIDE"
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_66_fake_stat_resolved(self):
  documents=upstream()
  documents["plan"]["bilan"]["preconditions_a_documenter"]=0
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_67_fake_financial_model_completeness(self):
  documents=upstream()
  documents["plan"]["bilan"]["valeurs_nova_inconnues"]=0
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_68_fake_receiving_under_git(self):
  documents=upstream()
  documents["plan"]["securite_reception"]["aucun_candidat_nominal_sur_github"]=False
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_69_fake_authority_named(self):
  documents=upstream()
  documents["plan"]["decision_precontractuelle"]["responsable_financier_nomme"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_70_fake_publication(self):
  documents=upstream()
  documents["plan"]["decision_precontractuelle"]["publication_autorisee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_71_fake_elector_privacy_verification(self):
  documents=upstream()
  documents["plan"]["sources_officielles_a_verifier"][2]["verification_applicabilite_effectuee"]=True
  with self.assertRaises(ValueError):
   m.validate(documents)
 def test_72_change_proof_path(self):
  documents=upstream()
  documents["plan"]["references"]["p52w"]="unverified.json"
  with self.assertRaises(ValueError):
   m.validate(documents)
if __name__=="__main__":
 unittest.main()
