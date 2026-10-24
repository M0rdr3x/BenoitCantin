"""P53B: sources publiées, barèmes 2026, années et montants inconnus."""
import csv,importlib.util,io,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/"scripts"/"valider_sources_recettes_nova_p53b.py"
spec=importlib.util.spec_from_file_location("p53b",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def source():return {k:m.read(path) for k,path in m.FILES.items()}
class P53BTests(unittest.TestCase):
 def test_01_register_valid_no_go(self):
  self.assertEqual(m.verify(source())["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_nine_official_sources(self):
  self.assertEqual(m.verify(source())["sources_officielles_reperees"],9)
 def test_03_nine_rate_parameters(self):
  self.assertEqual(m.verify(source())["taux_contributifs_2026_releves"],9)
 def test_04_nine_unpriced_gaps(self):
  self.assertEqual(m.verify(source())["lacunes_hors_budget_chiffrees"],0)
 def test_05_twenty_unvalidated_proofs(self):
  self.assertEqual(m.verify(source())["preuves_F01_F20_non_validees"],20)
 def test_06_1320_unknown_financial_model(self):
  self.assertEqual(m.verify(source())["donnees_nova_inconnues"],1320)
 def test_07_calendar_year_separated(self):
  d=source()["p53b"]["dossiers"]
  self.assertEqual(d[0]["comparabilite"],"ANNEE_IMPOSITION_2024")
  self.assertEqual(d[3]["comparabilite"],"EXERCICE_ANNUEL_JUSQU_A_2024")
 def test_08_non_tax_social_rights(self):
  self.assertTrue(source()["p53b"]["règles_non_additivité"]["cotisations_régimes_ne_sont_pas_impôts_sur_revenu"])
 def test_09_rrq_ceiling_math(self):
  s=m.verify(source())
  self.assertTrue(s["plafonds_rrq_et_ae_reconcilies"])
 def test_10_rrq_second_tranche_not_percent_whole_salary(self):
  caps=source()["p53b"]["plafonds_2026"]
  self.assertEqual((m.dec(caps["rrq_max_supplement_cad"])-m.dec(caps["rrq_max_gains_base_cad"]))*m.dec("4.00")/100,m.dec("416.00"))
 def test_11_AE_employee_rate(self):
  self.assertEqual(m.RATES["AE_SALARIE_QUEBEC_2026"][2],"1.30")
 def test_12_AE_employer_rate(self):
  self.assertEqual(m.RATES["AE_EMPLOYEUR_QUEBEC_2026"][2],"1.82")
 def test_13_RQAP_three_distinct_rates(self):
  self.assertEqual([m.RATES[k][2] for k in list(m.RATES)[-3:]],["0.430","0.602","0.764"])
 def test_14_csv_gap_export_ten_rows(self):
  r=list(csv.reader(io.StringIO(m.csv_gaps(source()["p53b"]))))
  self.assertEqual(len(r),10)
  self.assertTrue(all(v[4]=="" for v in r[1:]))
 def test_15_csv_rate_export_ten_rows(self):
  r=list(csv.reader(io.StringIO(m.csv_rates(source()["p53b"]))))
  self.assertEqual(len(r),10)
  self.assertTrue(all(v[-1]=="" for v in r[1:]))
 def test_16_strict_decimal_type(self):
  for v in (100,"1 200","2,40","-1.00"):
   with self.assertRaises(ValueError):m.dec(v)
 def test_17_cli_three_exports_no_go(self):
  with tempfile.TemporaryDirectory() as td:
   base=Path(td)
   self.assertEqual(m.main(["--rapport",str(base/"report.json"),"--export-csv",str(base/"gaps.csv"),"--export-baremes-csv",str(base/"rates.csv")]),0)
   self.assertEqual(json.loads((base/"report.json").read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_18_cli_require_consolidation_code_three(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--exiger-consolidation","--rapport",str(Path(td)/"report.json")]),3)
 def test_19_cli_missing_json_code_two(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--p53b",str(Path(td)/"missing.json")]),2)
 def test_20_cli_refuses_overwrite(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(path)]),0)
   self.assertEqual(m.main(["--rapport",str(path)]),2)
 def test_21_cli_paths_cannot_clash(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(path),"--export-csv",str(path)]),2)
 def test_22_summary_has_no_fake_rates_or_names(self):
  summary=json.dumps(m.verify(source()))
  for text in ("https://","contact_prive","taux_nova_propose","@"):
   self.assertNotIn(text,summary)
 def test_23_source_1_fake_sha(self):
  d=source()
  d["p53b"]["sources"][0]["extraction_structurée_et_SHA256_verifies"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_24_source_2_fake_sha(self):
  d=source()
  d["p53b"]["sources"][1]["extraction_structurée_et_SHA256_verifies"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_25_source_3_fake_sha(self):
  d=source()
  d["p53b"]["sources"][2]["extraction_structurée_et_SHA256_verifies"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_26_source_4_fake_sha(self):
  d=source()
  d["p53b"]["sources"][3]["extraction_structurée_et_SHA256_verifies"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_27_source_5_fake_sha(self):
  d=source()
  d["p53b"]["sources"][4]["extraction_structurée_et_SHA256_verifies"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_28_source_6_fake_sha(self):
  d=source()
  d["p53b"]["sources"][5]["extraction_structurée_et_SHA256_verifies"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_29_source_7_fake_sha(self):
  d=source()
  d["p53b"]["sources"][6]["extraction_structurée_et_SHA256_verifies"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_30_source_8_fake_sha(self):
  d=source()
  d["p53b"]["sources"][7]["extraction_structurée_et_SHA256_verifies"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_31_source_9_fake_sha(self):
  d=source()
  d["p53b"]["sources"][8]["extraction_structurée_et_SHA256_verifies"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_32_gap_1_fabricated_millions(self):
  d=source()
  d["p53b"]["dossiers"][0]["montant_annuel_reel_quebec_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_33_gap_2_fabricated_millions(self):
  d=source()
  d["p53b"]["dossiers"][1]["montant_annuel_reel_quebec_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_34_gap_3_fabricated_millions(self):
  d=source()
  d["p53b"]["dossiers"][2]["montant_annuel_reel_quebec_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_35_gap_4_fabricated_millions(self):
  d=source()
  d["p53b"]["dossiers"][3]["montant_annuel_reel_quebec_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_36_gap_5_fabricated_millions(self):
  d=source()
  d["p53b"]["dossiers"][4]["montant_annuel_reel_quebec_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_37_gap_6_fabricated_millions(self):
  d=source()
  d["p53b"]["dossiers"][5]["montant_annuel_reel_quebec_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_38_gap_7_fabricated_millions(self):
  d=source()
  d["p53b"]["dossiers"][6]["montant_annuel_reel_quebec_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_39_gap_8_fabricated_millions(self):
  d=source()
  d["p53b"]["dossiers"][7]["montant_annuel_reel_quebec_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_40_gap_9_fabricated_millions(self):
  d=source()
  d["p53b"]["dossiers"][8]["montant_annuel_reel_quebec_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_41_rate_1_false_total(self):
  d=source()
  d["p53b"]["barèmes_2026"][0]["montant_agrege_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_42_rate_2_false_total(self):
  d=source()
  d["p53b"]["barèmes_2026"][1]["montant_agrege_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_43_rate_3_false_total(self):
  d=source()
  d["p53b"]["barèmes_2026"][2]["montant_agrege_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_44_rate_4_false_total(self):
  d=source()
  d["p53b"]["barèmes_2026"][3]["montant_agrege_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_45_rate_5_false_total(self):
  d=source()
  d["p53b"]["barèmes_2026"][4]["montant_agrege_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_46_rate_6_false_total(self):
  d=source()
  d["p53b"]["barèmes_2026"][5]["montant_agrege_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_47_rate_7_false_total(self):
  d=source()
  d["p53b"]["barèmes_2026"][6]["montant_agrege_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_48_rate_8_false_total(self):
  d=source()
  d["p53b"]["barèmes_2026"][7]["montant_agrege_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_49_rate_9_false_total(self):
  d=source()
  d["p53b"]["barèmes_2026"][8]["montant_agrege_mcad"]="100"
  with self.assertRaises(ValueError):m.verify(d)
 def test_50_rate_changed_rrq(self):
  d=source()
  d["p53b"]["barèmes_2026"][0]["valeur"]="7.20"
  with self.assertRaises(ValueError):m.verify(d)
 def test_51_rate_changed_AE(self):
  d=source()
  d["p53b"]["barèmes_2026"][4]["valeur"]="2.00"
  with self.assertRaises(ValueError):m.verify(d)
 def test_52_rate_changed_RQAP(self):
  d=source()
  d["p53b"]["barèmes_2026"][6]["valeur"]="0.999"
  with self.assertRaises(ValueError):m.verify(d)
 def test_53_RRQ_max_false(self):
  d=source()
  d["p53b"]["plafonds_2026"]["rrq_base_max_salarie_cad"]="5000.00"
  with self.assertRaises(ValueError):m.verify(d)
 def test_54_AE_max_false(self):
  d=source()
  d["p53b"]["plafonds_2026"]["ae_max_employeur_cad"]="5000.00"
  with self.assertRaises(ValueError):m.verify(d)
 def test_55_social_rights_rule_removed(self):
  d=source()
  d["p53b"]["règles_non_additivité"]["deux_taxes_n_abolissent_pas_les_droits_a_prestations"]=False
  with self.assertRaises(ValueError):m.verify(d)
 def test_56_federal_budget_mismatch_suppressed(self):
  d=source()
  d["p53b"]["règles_non_additivité"]["source_T1_2024_n_est_pas_budget_2026_2027"]=False
  with self.assertRaises(ValueError):m.verify(d)
 def test_57_fake_federal_inclusion(self):
  d=source()
  d["p53a"]["perimetre"]["taxes_federales_hors_perimetre"]=False
  with self.assertRaises(ValueError):m.verify(d)
 def test_58_fake_local_nine_millions(self):
  d=source()
  d["lacunes"]["dossiers"][3]["montant_mcad"]="99999"
  with self.assertRaises(ValueError):m.verify(d)
 def test_59_fake_p52z_legal(self):
  d=source()
  d["p52z"]["bilan"]["decision"]="GO"
  with self.assertRaises(ValueError):m.verify(d)
 def test_60_fake_fiscal_go(self):
  d=source()
  d["p52a"]["automatic_go"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_61_false_consolidation(self):
  d=source()
  d["p53b"]["bilan"]["années_comparables_validées"]=9
  with self.assertRaises(ValueError):m.verify(d)
 def test_62_false_nova_adoption(self):
  d=source()
  d["p53b"]["bilan"]["adoption_autorisée"]=True
  with self.assertRaises(ValueError):m.verify(d)
 def test_63_wrong_link(self):
  d=source()
  d["p53b"]["references"]["p53a"]="not-the-file.json"
  with self.assertRaises(ValueError):m.verify(d)
 def test_64_wrong_source(self):
  d=source()
  d["p53b"]["sources"][0]["url"]="https://example.invalid"
  with self.assertRaises(ValueError):m.verify(d)
if __name__=="__main__":
 unittest.main()
