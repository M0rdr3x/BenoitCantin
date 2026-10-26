"""P52Z: limites réelles des deux régimes, sources officielles et refus GO."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"auditer_juridictions_fiscales_nova_p52z.py"
spec=importlib.util.spec_from_file_location("p52z",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def data():return {k:m.read(v) for k,v in m.FILES.items()}
class FiscJurisdictionTests(unittest.TestCase):
 def reject(self,change):
  d=data();change(d)
  with self.assertRaises(ValueError):m.check(d)
 def test_01_official_sources_eleven(self):
  self.assertEqual(m.check(data())["sources_primaires_reperes"],11)
 def test_02_twelve_questions(self):
  self.assertEqual(m.check(data())["questions_comparees"],12)
 def test_03_twenty_four_regime_evaluations(self):
  self.assertEqual(m.check(data())["scenarios_examens"],24)
 def test_04_no_independent_signed_legal_opinions(self):
  self.assertEqual(m.check(data())["analyses_fiscales_legalement_certifiees"],0)
 def test_05_sovereign_powers_not_acquired(self):
  self.assertEqual(m.check(data())["droits_souverains_reellement_acquis"],0)
 def test_06_no_tax_rates_selected(self):
  self.assertEqual(m.check(data())["taux_fiscaux_adoptes"],0)
 def test_07_no_go_even_sources_found(self):
  self.assertEqual(m.check(data())["decision"],"NO_GO_AUTOMATIQUE")
 def test_08_all_twenty_evidences_missing(self):
  self.assertEqual(m.check(data())["preuves_F01_F20_non_validees"],20)
 def test_09_missing_financial_values(self):
  self.assertEqual(m.check(data())["valeurs_financieres_inconnues"],1320)
 def test_10_four_federal_or_constitutional_blocks(self):
  self.assertEqual(m.check(data())["pouvoirs_federaux_ineliminables_unilateralement"],4)
 def test_11_provincial_income_and_federal_tax_separate(self):
  v=data()["matrice"]["evaluations"]
  self.assertEqual(v[0]["categorie_initiale"],"PROVINCIAL_REFORM_TO_VALIDATE")
  self.assertEqual(v[2]["categorie_initiale"],"FEDERAL_OUTSIDE_PROVINCIAL_UNILATERAL")
 def test_12_GST_federal(self):
  v=data()["matrice"]["evaluations"]
  self.assertEqual(v[6]["f_prioritaire"],"F02")
  self.assertEqual(v[6]["categorie_initiale"],"FEDERAL_OUTSIDE_PROVINCIAL_UNILATERAL")
 def test_13_TVQ_provincial(self):
  v=data()["matrice"]["evaluations"]
  self.assertEqual(v[4]["categorie_initiale"],"PROVINCIAL_REFORM_TO_VALIDATE")
 def test_14_customs_federal(self):
  self.assertEqual(data()["matrice"]["evaluations"][10]["categorie_initiale"],
                   "FEDERAL_OUTSIDE_PROVINCIAL_UNILATERAL")
 def test_15_schools_and_municipal_taxes_individual(self):
  v=data()["matrice"]["evaluations"]
  self.assertEqual(v[12]["f_prioritaire"],"F04")
  self.assertEqual(v[14]["f_prioritaire"],"F04")
 def test_16_all_sovereignty_analyses_conditional(self):
  v=data()["matrice"]["evaluations"]
  self.assertTrue(all(r["categorie_initiale"]=="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
                      for r in v[1::2]))
 def test_17_every_sovereignty_case_cites_clarity(self):
  v=data()["matrice"]["evaluations"]
  self.assertTrue(all("S11" in r["sources"] for r in v[1::2]))
 def test_18_anti_haven_levy_legally_undetermined(self):
  self.assertEqual(data()["matrice"]["evaluations"][8]["categorie_initiale"],
                   "LEGAL_QUALIFICATION_OPEN")
 def test_19_trade_policy_not_customs_repeal(self):
  self.assertEqual(data()["matrice"]["evaluations"][-2]["categorie_initiale"],
                   "LEGAL_QUALIFICATION_OPEN")
 def test_20_csv_25_rows_including_header(self):
  self.assertEqual(len(list(csv.reader(io.StringIO(m.export_csv(data()["matrice"]))))),25)
 def test_21_csv_last_scenario(self):
  self.assertEqual(list(csv.reader(io.StringIO(m.export_csv(data()["matrice"]))))[-1][0],
                   "T12-QC-SOUV")
 def test_22_csv_human_columns_blank(self):
  rows=list(csv.reader(io.StringIO(m.export_csv(data()["matrice"]))))
  self.assertTrue(all(x[6:]==["","","",""] for x in rows[1:]))
 def test_23_cli_normal_no_go(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(f)]),0)
   self.assertEqual(json.loads(f.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_24_cli_strict_no_expert_exit_three(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--exiger-avis-juridique","--rapport",str(Path(td)/"r.json")]),3)
 def test_25_cli_missing_upstream_exit_two(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--p52a",str(Path(td)/"missing.json")]),2)
 def test_26_cli_refuses_existing_report(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(f)]),0)
   self.assertEqual(m.main(["--rapport",str(f)]),2)
 def test_27_cli_same_report_csv_path_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/"same.json"
   self.assertEqual(m.main(["--rapport",str(f),"--export-csv",str(f)]),2)
 def test_28_cli_csv_export_no_personal_data(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/"comparison.csv"
   self.assertEqual(m.main(["--export-csv",str(f)]),0)
   self.assertEqual(len(list(csv.reader(f.open(encoding="utf-8")))),25)
 def test_29_aggregated_report_no_unapproved_juridical_judgment(self):
  summary=json.dumps(m.check(data()),ensure_ascii=False)
  for val in ("https://","T-0.1","prenom","@","166492","cf89d3d8"):
   self.assertNotIn(val,summary)
 def test_30_source_1_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][0]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_31_source_2_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][1]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_32_source_3_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][2]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_33_source_4_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][3]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_34_source_5_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][4]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_35_source_6_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][5]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_36_source_7_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][6]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_37_source_8_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][7]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_38_source_9_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][8]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_39_source_10_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][9]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_40_source_11_fake_certification(self):
  d=data()
  d["matrice"]["sources_primaires"][10]["avis_juridique_externe_independant_obtenu"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_41_topic_1_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][0]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_42_topic_2_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][2]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_43_topic_3_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][4]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_44_topic_4_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][6]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_45_topic_5_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][8]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_46_topic_6_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][10]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_47_topic_7_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][12]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_48_topic_8_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][14]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_49_topic_9_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][16]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_50_topic_10_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][18]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_51_topic_11_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][20]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_52_topic_12_wrong_fiscal_regime(self):
  d=data()
  d["matrice"]["evaluations"][22]["categorie_initiale"]="TRANSITION_CONDITIONNELLE_NON_ACQUISE"
  with self.assertRaises(ValueError):m.check(d)
 def test_53_sovereignty_1_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][1]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_54_sovereignty_2_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][3]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_55_sovereignty_3_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][5]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_56_sovereignty_4_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][7]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_57_sovereignty_5_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][9]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_58_sovereignty_6_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][11]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_59_sovereignty_7_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][13]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_60_sovereignty_8_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][15]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_61_sovereignty_9_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][17]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_62_sovereignty_10_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][19]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_63_sovereignty_11_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][21]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_64_sovereignty_12_claimed_legal_pow_er(self):
  d=data()
  d["matrice"]["evaluations"][23]["acquis_sans_reserve"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_65_false_certified_reference_archive(self):
  d=data()
  d["matrice"]["sources_primaires"][0]["copie_integrale_archivee_et_hash_certifie"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_66_dangerous_edited_constitution_url(self):
  d=data()
  d["matrice"]["sources_primaires"][0]["url"]="https://faux.example/constitutional-claim"
  with self.assertRaises(ValueError):m.check(d)
 def test_67_false_tax_rate(self):
  d=data()
  d["matrice"]["bilan"]["taux_fiscaux_fixes"]=4
  with self.assertRaises(ValueError):m.check(d)
 def test_68_false_go(self):
  d=data()
  d["matrice"]["bilan"]["adoption_autorisee"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_69_false_legal_opinion(self):
  d=data()
  d["matrice"]["evaluations"][0]["avis_juridique_independant"]="OK"
  with self.assertRaises(ValueError):m.check(d)
 def test_70_false_signed_review(self):
  d=data()
  d["matrice"]["evaluations"][1]["revue_humaine_signee"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_71_altered_school_tax_source(self):
  d=data()
  d["matrice"]["questions"][7]["sources"]=["S01"]
  with self.assertRaises(ValueError):m.check(d)
 def test_72_fake_federal_tax_removed(self):
  d=data()
  d["matrice"]["evaluations"][2]["conclusion_fiscale_approuvee"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_73_fake_P52A_validation(self):
  d=data()
  d["p52a"]["required_evidence"][0]["statut"]="VALIDE"
  with self.assertRaises(ValueError):m.check(d)
 def test_74_fake_P52X_contract(self):
  d=data()
  d["p52x"]["decision_precontractuelle"]["mandant_legal_identifie"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_75_fake_P52Y_reviewer(self):
  d=data()
  d["p52y"]["points_non_delegables"]["f09_avis_professionnel_independant_signe"]=True
  with self.assertRaises(ValueError):m.check(d)
 def test_76_fake_P52V_signoff(self):
  d=data()
  d["p52v"]["bilan"]["expertises_independantes_signees"]=1
  with self.assertRaises(ValueError):m.check(d)
 def test_77_broken_source_path(self):
  d=data()
  d["matrice"]["references"]["p52y"]="changed.json"
  with self.assertRaises(ValueError):m.check(d)
 def test_78_remove_reserve(self):
  d=data()
  d["matrice"]["notes_methode"]["aucune_preuve_F01_F20_approuvee"]=False
  with self.assertRaises(ValueError):m.check(d)
if __name__=="__main__":
 unittest.main()
