"""P53F: 2024 signed municipal flows, candidates not matched eliminations."""
import csv,importlib.util,io,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"auditer_flux_interadministrations_nova_p53f.py"
spec=importlib.util.spec_from_file_location("p53f",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def docs():return {k:m.load(v) for k,v in m.FILES.items()}
def result():return m.validate(docs(),m.parse_source())
class F53FTests(unittest.TestCase):
 def test_01_real_totals_reconciled(self):
  self.assertEqual(result()["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_1094_local_accounts(self):
  self.assertEqual(result()["municipalites_locales"],1094)
 def test_03_sum_all_revenues_2024(self):
  self.assertEqual(result()["revenus_bruts_CAD"],32367623561)
 def test_04_tax_total(self):
  self.assertEqual(result()["taxes_CAD"],17337284213)
 def test_05_quotes_part_and_transfers_distinct(self):
  r=result()
  self.assertEqual((r["quotes_parts_CAD"],r["transferts_CAD"]),(846987123,5376508934))
 def test_06_candidates_are_sum_of_signed_categories(self):
  r=result()
  self.assertEqual(r["exposition_susceptible_appariement_CAD"],
   r["quotes_parts_CAD"]+r["transferts_CAD"])
 def test_07_2024_remaining_categories(self):
  r=result()
  self.assertEqual(r["reste_hors_taxes_quotes_transferts_CAD"],8806843291)
 def test_08_all_four_categories_disjoint(self):
  r=result()
  self.assertEqual(
   sum(r[k] for k in ("taxes_CAD","quotes_parts_CAD","transferts_CAD",
    "reste_hors_taxes_quotes_transferts_CAD")),r["revenus_bruts_CAD"])
 def test_09_nothing_matched(self):
  self.assertEqual(result()["transactions_appariees"],0)
 def test_10_no_zero_claim_for_unknown_eliminations(self):
  self.assertIsNone(result()["eliminations_confirmees_CAD"])
 def test_11_independent_consolidation_missing(self):
  self.assertFalse(result()["consolidation_interadministrations_certifiee"])
 def test_12_fiscal_projection_not_certified(self):
  self.assertFalse(result()["montants_2026_2027_verifies"])
 def test_13_20_unknown_fiscal_proofs(self):
  self.assertEqual(result()["preuves_F01_F20_non_validees"],20)
 def test_14_1320_unknown_nova_parameters(self):
  self.assertEqual(result()["parametres_Nova_inconnus"],1320)
 def test_15_quotes_have_39_negatives(self):
  self.assertEqual(m.aggregate(m.parse_source())[0]["CRIIX00408"]["negatifs"],39)
 def test_16_quotes_have_298_declared_zeros(self):
  self.assertEqual(m.aggregate(m.parse_source())[0]["CRIIX00408"]["zeros"],298)
 def test_17_quotes_have_627_unreported(self):
  self.assertEqual(m.aggregate(m.parse_source())[0]["CRIIX00408"]["blancs"],627)
 def test_18_transfers_one_negative_and_nine_blanks(self):
  r=m.aggregate(m.parse_source())[0]["CRIIX00409"]
  self.assertEqual((r["negatifs"],r["blancs"]),(1,9))
 def test_19_1094_ledger_rows(self):
  data=list(csv.reader(io.StringIO(m.export(m.parse_source()))))
  self.assertEqual(len(data),1095)
 def test_20_ledger_counterparties_blank(self):
  rows=list(csv.reader(io.StringIO(m.export(m.parse_source()))))
  self.assertTrue(all(row[-3:]==["","","NON"] for row in rows[1:]))
 def test_21_blank_quote_stays_blank_in_export(self):
  rows=list(csv.reader(io.StringIO(m.export(m.parse_source()))))
  self.assertTrue(any(x[2]=="" for x in rows[1:]))
 def test_22_negative_quotes_preserved_in_export(self):
  rows=list(csv.reader(io.StringIO(m.export(m.parse_source()))))
  self.assertEqual(sum(int(x[2])<0 for x in rows[1:] if x[2]),39)
 def test_23_income_tax_rate_not_selected(self):
  self.assertIsNone(docs()["manifest"]["totaux"]["revenus_2026_2027"])
 def test_24_signed_allows_negative_integer(self):
  self.assertEqual(m.signed("-100"),-100)
 def test_25_empty_is_unknown(self):
  self.assertIsNone(m.signed(""))
 def test_26_decimal_float_rejected(self):
  for v in ("1.0","3,500","1e4","nan",3,True):
   with self.assertRaises(ValueError):m.signed(v)
 def test_27_csv_original_checksum(self):
  import hashlib
  self.assertEqual(hashlib.sha256(m.SOURCE.read_bytes()).hexdigest(),m.SOURCE_SHA)
 def test_28_tampered_csv_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"dirty.csv"
   raw=m.SOURCE.read_bytes()
   path.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
   with self.assertRaises(ValueError):m.parse_source(path)
 def test_29_missing_csv_returns_error(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):m.parse_source(Path(td)/"missing.csv")
 def test_30_cli_no_go_bilan(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"bilan.json"
   self.assertEqual(m.main(["--rapport",str(path)]),0)
   self.assertEqual(json.loads(path.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_31_cli_refuses_fictitious_certification(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"bilan.json"
   self.assertEqual(m.main(["--exiger-appariements","--rapport",str(path)]),3)
 def test_32_cli_generates_ledger(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"journal.csv"
   self.assertEqual(m.main(["--export-csv",str(path)]),0)
   self.assertEqual(len(list(csv.reader(path.open(encoding="utf-8")))),1095)
 def test_33_cli_missing_document_fails_two(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--manifest",str(Path(td)/"missing.json")]),2)
 def test_34_cli_preserves_previous_report(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"bilan.json"
   self.assertEqual(m.main(["--rapport",str(path)]),0)
   self.assertEqual(m.main(["--rapport",str(path)]),2)
 def test_35_cli_same_report_csv_file_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"same"
   self.assertEqual(m.main(["--rapport",str(path),"--export-csv",str(path)]),2)
 def test_36_no_personal_identification_in_aggregate_report(self):
  t=json.dumps(result(),ensure_ascii=False)
  for term in ("nom_organisme","@","45080","http"):
   self.assertNotIn(term,t)
 def test_37_guard_1(self):
  d=docs()
  d["manifest"]["regles"]["pas_eliminer_candidats_sans_appariement"]=False
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_38_guard_2(self):
  d=docs()
  d["manifest"]["regles"]["preserver_negatifs_et_blancs"]=False
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_39_guard_3(self):
  d=docs()
  d["manifest"]["regles"]["taxes_foncieres_incluses_dans_taxes"]=False
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_40_guard_4(self):
  d=docs()
  d["manifest"]["regles"]["revenus_incluent_transferts_et_quotes_parts"]=False
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_41_guard_5(self):
  d=docs()
  d["manifest"]["regles"]["services_compensations_a_verifier"]=False
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_42_guard_6(self):
  d=docs()
  d["manifest"]["regles"]["exclure_mrc_regies_transports"]=False
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_43_guard_7(self):
  d=docs()
  d["manifest"]["regles"]["2024_non_assimilable_budget_2026_2027"]=False
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_44_guard_8(self):
  d=docs()
  d["manifest"]["regles"]["pas_de_taux_nova_derive"]=False
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_45_synthetic_entry_1(self):
  d=docs()
  d["manifest"]["postes"][0]["montant_cad"]="123"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_46_synthetic_entry_2(self):
  d=docs()
  d["manifest"]["postes"][1]["montant_cad"]="123"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_47_synthetic_entry_3(self):
  d=docs()
  d["manifest"]["postes"][2]["montant_cad"]="123"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_48_synthetic_entry_4(self):
  d=docs()
  d["manifest"]["postes"][3]["montant_cad"]="123"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_49_synthetic_entry_5(self):
  d=docs()
  d["manifest"]["postes"][4]["montant_cad"]="123"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_50_fake_counterparty_1(self):
  d=docs()
  d["manifest"]["postes"][0]["contrepartie_certifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_51_fake_counterparty_2(self):
  d=docs()
  d["manifest"]["postes"][1]["contrepartie_certifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_52_fake_counterparty_3(self):
  d=docs()
  d["manifest"]["postes"][2]["contrepartie_certifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_53_fake_counterparty_4(self):
  d=docs()
  d["manifest"]["postes"][3]["contrepartie_certifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_54_fake_counterparty_5(self):
  d=docs()
  d["manifest"]["postes"][4]["contrepartie_certifiee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_55_invented_elimination(self):
  d=docs()
  d["manifest"]["totaux"]["montant_eliminations_certifiees"]="300000000"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_56_invented_appariement(self):
  d=docs()
  d["manifest"]["appariement"]["transactions_appariees"]=1
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_57_false_publication(self):
  d=docs()
  d["manifest"]["bilan"]["publication_autorisee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_58_false_rate(self):
  d=docs()
  d["manifest"]["totaux"]["revenus_2026_2027"]="30000"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_59_other_revenues_fabricated(self):
  d=docs()
  d["manifest"]["totaux"]["reste_non_taxes_ni_quotes_ni_transferts"]="100000"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_60_2024_relabelled_2026(self):
  d=docs()
  d["manifest"]["annee"]=2026
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_61_tax_scope_invented(self):
  d=docs()
  d["manifest"]["périmètre"]["nombre"]=1095
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_62_municipal_snapshot_sha_invalid(self):
  d=docs()
  d["manifest"]["périmètre"]["source_sha256"]="fake"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_63_source_path_modified(self):
  d=docs()
  d["manifest"]["ref"]["csv"]="bad-file.csv"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_64_exposure_treated_as_eliminated(self):
  d=docs()
  d["manifest"]["totaux"]["candidats_a_appariement_non_eliminables"]="0"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_65_false_audit(self):
  d=docs()
  d["manifest"]["appariement"]["publication_autorisee"]=True
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_66_fiscal_proofs_claimed(self):
  d=docs()
  d["manifest"]["bilan"]["preuves_F01_F20"]=20
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_67_no_unknown_nova(self):
  d=docs()
  d["manifest"]["bilan"]["inconnues_nova"]=0
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_68_wrong_source_revenue(self):
  d=docs()
  d["p53e"]["observations_de_reference"]["revenus_totaux_municipalites_locales_2024_cad"]="100000"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_69_source_go_fabricated(self):
  d=docs()
  d["p53d"]["bilan"]["decision"]="GO"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_70_budget_qc_wrong_year(self):
  d=docs()
  d["p53a"]["compartiments_non_additionner_aux_lignes"]["total_budget_quebec_mcad"]="50000"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_71_fabricated_gap_f04(self):
  d=docs()
  d["lacunes"]["dossiers"][3]["montant_mcad"]="15085"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_72_p52a_f04_fabricated(self):
  d=docs()
  d["p52a"]["required_evidence"][3]["statut"]="VALIDE"
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
 def test_73_selected_go(self):
  d=docs()
  d["p52a"]["automatic_go"]=True
  with self.assertRaises(ValueError):
   m.validate(d,m.parse_source())
if __name__=='__main__':
 unittest.main()
