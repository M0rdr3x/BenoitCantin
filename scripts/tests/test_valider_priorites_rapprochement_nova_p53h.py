"""P53H: 1343 municipal receipts, signed ranking, strict no false pairings."""
import csv,copy,importlib.util,io,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"valider_priorites_rapprochement_nova_p53h.py"
spec=importlib.util.spec_from_file_location("p53h",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def docs():return {k:m.read(v) for k,v in m.FILES.items()}
def inputs():return m.source_rows()
def audited():
 local,other=inputs()
 return m.validate(docs(),local,other)

class PrioritizationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.local,cls.other=inputs()
 def attack(self,callback):
  d=docs()
  callback(d)
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_01_real_primary_source_passes(self):
  self.assertEqual(audited()["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_1343_all_organisms_checked(self):
  self.assertEqual(audited()["organismes_2024_controles"],1343)
 def test_03_25_priorities(self):
  self.assertEqual(audited()["organismes_priorises"],25)
 def test_04_five_categories_of_organisms(self):
  self.assertEqual(audited()["groupes"],5)
 def test_05_signed_10864_million_candidate_receipts(self):
  self.assertEqual(audited()["exposition_brute_signee_a_etudier_CAD"],10864282201)
 def test_06_top25_sum_signed_7069_million(self):
  self.assertEqual(audited()["exposition_signee_top25_CAD"],7069371200)
 def test_07_priority_coverage_not_claimed_saving(self):
  self.assertEqual(audited()["concentration_top25_pourcent_approx"],"65.07")
 def test_08_no_pairs_proven(self):
  self.assertEqual(audited()["appariements_reciproques_documentes"],0)
 def test_09_no_certified_eliminations_not_false_zero(self):
  self.assertIsNone(audited()["eliminations_certifiees_CAD"])
 def test_10_no_2026_budget_appropriation(self):
  self.assertFalse(audited()["credits_budgetaires_2026_2027_justifies"])
 def test_11_twenty_unvalidated_proofs(self):
  self.assertEqual(audited()["preuves_fiscales_validees"],0)
 def test_12_1320_unknown_nova_values(self):
  self.assertEqual(audited()["parametres_financiers_Nova_inconnus"],1320)
 def test_13_taxes_not_added_to_candidate_receipts(self):
  gs,top,all_items=m.priorities(self.local+self.other)
  self.assertEqual(sum(int(g["quotes_parts_cad"]) for g in gs),3148209097)
  self.assertEqual(sum(int(g["transferts_cad"]) for g in gs),7716073104)
 def test_14_all_orgs_have_different_codes(self):
  g,t,items=m.priorities(self.local+self.other)
  self.assertEqual(len({r["code_organisme"] for r in items}),1343)
 def test_15_pri_order_starts_montreal(self):
  g,t,items=m.priorities(self.local+self.other)
  self.assertEqual((t[0]["code_organisme"],t[0]["flux_candidats_signes_cad"]),("66023","2058550000"))
 def test_16_transport_can_be_high_priority(self):
  g,t,items=m.priorities(self.local+self.other)
  self.assertEqual((t[1]["code_organisme"],t[1]["type_org"]),("T1025","Organisme public de transport"))
 def test_17_missing_raw_not_written_as_zero(self):
  g,t,items=m.priorities(self.local+self.other)
  self.assertTrue(any(r["quotes_parts_cad"] is None for r in items))
 def test_18_negative_signed_receipts_kept(self):
  g,t,items=m.priorities(self.local+self.other)
  self.assertTrue(any(int(r["flux_candidats_signes_cad"])<0 for r in items))
 def test_19_two_blanks_recorded_per_group(self):
  g,t,items=m.priorities(self.local+self.other)
  self.assertEqual(sum(x["organismes_deux_champs_vides"] for x in g),17)
 def test_20_no_org_with_fictitious_counterparty(self):
  g,t,items=m.priorities(self.local+self.other)
  self.assertTrue(all(r["contrepartie_payeur_identifiee"] is False and
                      r["piece_originale_correspondante"] is None and
                      r["appariement_reciproque_confirme"] is False for r in items))
 def test_21_export_all_1343_plus_header(self):
  items=m.priorities(self.local+self.other)[2]
  rows=list(csv.reader(io.StringIO(m.export_csv(items))))
  self.assertEqual(len(rows),1344)
  self.assertTrue(all(r[-4:]==["","","",""] for r in rows[1:]))
 def test_22_export_priority_first_montreal(self):
  items=m.priorities(self.local+self.other)[2]
  rows=list(csv.reader(io.StringIO(m.export_csv(items))))
  self.assertEqual(rows[1][1],"66023")
 def test_23_regular_cli_outputs_no_go(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(path)]),0)
   self.assertEqual(json.loads(path.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_24_strict_cli_blocks_uncertified_pairings(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"report.json"
   self.assertEqual(m.main(["--exiger-appariement","--rapport",str(path)]),3)
 def test_25_cli_csv_can_be_exported(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"full.csv"
   self.assertEqual(m.main(["--export-csv",str(path)]),0)
   with path.open(encoding="utf-8") as f:rows=list(csv.reader(f))
   self.assertEqual(len(rows),1344)
 def test_26_cli_missing_local_file_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--csv-local",str(Path(td)/"missing.csv")]),2)
 def test_27_cli_missing_other_file_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--csv-complementaire",str(Path(td)/"missing.csv")]),2)
 def test_28_cli_refuses_existing_report(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(path)]),0)
   self.assertEqual(m.main(["--rapport",str(path)]),2)
 def test_29_cli_refuses_same_output_destination(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"one"
   self.assertEqual(m.main(["--rapport",str(path),"--export-csv",str(path)]),2)
 def test_30_wrong_number_of_organisms_rejected(self):
  with self.assertRaises(ValueError):m.priorities((self.local+self.other)[:1342])
 def test_31_type_1_false_exposure(self):
  d=docs()
  d["p53h"]["groupes"][0]["exposition_signee_cad"]="100"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_32_type_2_false_exposure(self):
  d=docs()
  d["p53h"]["groupes"][1]["exposition_signee_cad"]="100"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_33_type_3_false_exposure(self):
  d=docs()
  d["p53h"]["groupes"][2]["exposition_signee_cad"]="100"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_34_type_4_false_exposure(self):
  d=docs()
  d["p53h"]["groupes"][3]["exposition_signee_cad"]="100"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_35_type_5_false_exposure(self):
  d=docs()
  d["p53h"]["groupes"][4]["exposition_signee_cad"]="100"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_36_priority_1_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][0]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_37_priority_2_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][1]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_38_priority_3_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][2]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_39_priority_4_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][3]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_40_priority_5_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][4]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_41_priority_6_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][5]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_42_priority_7_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][6]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_43_priority_8_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][7]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_44_priority_9_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][8]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_45_priority_10_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][9]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_46_priority_11_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][10]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_47_priority_12_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][11]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_48_priority_13_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][12]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_49_priority_14_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][13]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_50_priority_15_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][14]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_51_priority_16_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][15]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_52_priority_17_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][16]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_53_priority_18_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][17]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_54_priority_19_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][18]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_55_priority_20_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][19]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_56_priority_21_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][20]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_57_priority_22_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][21]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_58_priority_23_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][22]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_59_priority_24_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][23]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_60_priority_25_false_amount(self):
  d=docs()
  d["p53h"]["priorites_relecture"][24]["flux_candidats_signes_cad"]="1"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_61_guard_1_removed(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["tri_descendant_puis_code_org_ascendant"]=False
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_62_guard_2_removed(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["blancs_sont_non_renseignes_pas_zero_constate"]=False
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_63_guard_3_removed(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["montants_negatifs_conserves"]=False
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_64_guard_4_removed(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["revenu_recipient_ne_prouve_pas_depense_du_payeur"]=False
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_65_guard_5_removed(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["organismes_priorises_pas_coupables_d_erreur"]=False
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_66_guard_6_removed(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["rang_ne_signifie_pas_montant_eliminable"]=False
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_67_guard_7_removed(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["exercice_2024_pas_projection_2026_2027"]=False
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_68_guard_8_removed(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["exclusion_du_budget_federal_et_quebec_incompatible"]=False
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_69_fake_counterparty(self):
  d=docs()
  d["p53h"]["priorites_relecture"][0]["contrepartie_payeur_identifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_70_fake_matching_evidence(self):
  d=docs()
  d["p53h"]["priorites_relecture"][0]["piece_originale_correspondante"]="MATCHED"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_71_fake_pair_verified(self):
  d=docs()
  d["p53h"]["priorites_relecture"][1]["appariement_reciproque_confirme"]=True
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_72_fake_all_pair_count(self):
  d=docs()
  d["p53h"]["bilan"]["operations_reciproques_demontrees"]=25
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_73_fake_total_elimination(self):
  d=docs()
  d["p53h"]["chiffres_controle"]["montant_eliminable_preuve_cad"]="7069371200"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_74_fake_nova_yield(self):
  d=docs()
  d["p53h"]["chiffres_controle"]["montant_projet_nova_2026_2027_cad"]="999999"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_75_fake_fiscal_adoption(self):
  d=docs()
  d["p53h"]["bilan"]["taux_nova_adoptes"]=1
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_76_fake_all_certified(self):
  d=docs()
  d["p53h"]["bilan"]["preuves_F01_F20_validees"]=20
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_77_false_external_signatures(self):
  d=docs()
  d["p53h"]["bilan"]["avis_comptables_independants_signes"]=1
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_78_false_go(self):
  d=docs()
  d["p53h"]["bilan"]["publication_autorisee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_79_false_merge(self):
  d=docs()
  d["p53h"]["bilan"]["fusion_autorisee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_80_false_wrong_year(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["annee"]=2025
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_81_false_population(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["population_complete"]=1094
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_82_false_top_count(self):
  d=docs()
  d["p53h"]["regles_priorisation"]["nombre_cibles_prioritaires"]=20
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_83_altered_reference(self):
  d=docs()
  d["p53h"]["references"]["p53g"]="elsewhere.json"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_84_altered_requirements(self):
  d=docs()
  d["p53h"]["instructions_de_verification"][0]="ALREADY_APPROVED"
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_85_fake_upstream_complete(self):
  d=docs()
  d["p53g"]["bilan"]["eliminations_certifiees"]=20
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_86_fake_p53f_certification(self):
  d=docs()
  d["p53f"]["bilan"]["appariements_confirmes"]=1
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_87_fake_p52a_approved(self):
  d=docs()
  d["p52a"]["automatic_go"]=True
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
 def test_88_fake_p53e_revenue(self):
  d=docs()
  d["p53e"]["bilan"]["municipalites_locales_retenues"]=1000
  with self.assertRaises(ValueError):
   m.validate(d,self.local,self.other)
if __name__=="__main__":
 unittest.main()
