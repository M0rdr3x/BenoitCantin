"""P53D: municipal profile textual capture, zero fiscal amounts, all NO_GO."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"auditer_donnees_municipales_nova_p53d.py"
spec=importlib.util.spec_from_file_location("p53d",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def docs():return {k:m.read(v) for k,v in m.FILES.items()}
def passed(d=None):return m.verify(d if d is not None else docs(),m.capture())
class MunicipalIntegrity(unittest.TestCase):
 def test_01_all_checks_pass_no_go(self):
  self.assertEqual(passed()["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_git_blob_matches(self):
  self.assertEqual(m.capture()["git_blob"],m.SHA)
 def test_03_exact_two_csv_lines(self):
  self.assertEqual(len(m.SOURCE.read_text().strip().splitlines()),2)
 def test_04_reconciles_three_ids(self):
  self.assertEqual(m.capture()["values"][:3],["2024","2024","PROV"])
 def test_05_38_numeric_columns(self):
  self.assertEqual(len(m.capture()["header"][3:]),38)
 def test_06_codes_look_like_codes(self):
  self.assertTrue(all(m.CODE.fullmatch(k) for k in m.capture()["header"][3:]))
 def test_07_not_original_archive(self):
  self.assertFalse(docs()["manifest"]["sources"]["mamH"]["octets_source_origine_authentifies"])
 def test_08_sha_original_remains_unknown(self):
  self.assertIsNone(docs()["manifest"]["sources"]["mamH"]["sha256_fichier_original"])
 def test_09_zip_statcan_not_acquired(self):
  self.assertFalse(passed()["statcan_zip_acquis"])
 def test_10_no_municipal_income_fabricated(self):
  self.assertEqual(passed()["montants_municipaux_certifies"],0)
 def test_11_20_evidences_missing(self):
  self.assertEqual(passed()["preuves_F01_F20_non_validees"],20)
 def test_12_1320_nova_unknowns(self):
  self.assertEqual(passed()["valeurs_nova_inconnues"],1320)
 def test_13_export_has_38_rows_plus_header(self):
  rows=list(csv.reader(io.StringIO(m.export_csv(m.capture()))))
  self.assertEqual(len(rows),39)
  self.assertTrue(all(r[4]=="" for r in rows[1:]))
 def test_14_export_never_labels_amounts(self):
  lines=list(csv.reader(io.StringIO(m.export_csv(m.capture()))))
  self.assertTrue(all(r[1]=="PROV" and r[0]=="2024" for r in lines[1:]))
 def test_15_corrupt_source_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/"source.csv"
   f.write_bytes(m.SOURCE.read_bytes().replace(b"PROV",b"FAKE"))
   with self.assertRaises(ValueError):m.capture(f)
 def test_16_missing_source_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ValueError):m.capture(Path(t)/"missing.csv")
 def test_17_cli_success_no_go(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"s.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(json.loads(p.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_18_cli_strict_refusal_three(self):
  with tempfile.TemporaryDirectory() as t:
   self.assertEqual(m.main(["--exiger-recettes-municipales","--rapport",str(Path(t)/"s.json")]),3)
 def test_19_cli_export_38_unlabelled(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"s.csv"
   self.assertEqual(m.main(["--export-csv",str(p)]),0)
   self.assertEqual(len(list(csv.reader(p.open(encoding="utf-8")))),39)
 def test_20_cli_missing_manifest_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   self.assertEqual(m.main(["--manifest",str(Path(t)/"missing.json")]),2)
 def test_21_cli_never_overwrites(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"s.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(m.main(["--rapport",str(p)]),2)
 def test_22_cli_rejects_same_output_path(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"same"
   self.assertEqual(m.main(["--rapport",str(p),"--export-csv",str(p)]),2)
 def test_23_guard_1_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["code_PROV_ne_demontre_pas_recettes_consolidees"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_24_guard_2_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["champs_CIALC_CIAIC_CIIIC_sans_dictionnaire_pas_taxes"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_25_guard_3_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["fichier_mamh_2024_pas_memes_definitions_que_statcan"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_26_guard_4_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["source_capture_non_equivalente_a_archive_octets_originaux"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_27_guard_5_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["absence_SHA256_original_doit_rester_visible"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_28_guard_6_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["annee_municipale_2024_distincte_budget_quebec_2026_2027"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_29_guard_7_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["transferts_entre_paliers_a_exclure_du_cumul"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_30_guard_8_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["taxe_scolaire_budget_Quebec_pas_taxe_municipale"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_31_guard_9_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["impot_federal_net_2024_pas_taxe_municipale"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_32_guard_10_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["pas_d_imputation_depuis_taux_ou_ratios"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_33_guard_11_false(self):
  d=docs()
  d["manifest"]["garde_fous"]["donnees_provisoires_pas_certification_independante"]=False
  with self.assertRaises(ValueError):passed(d)
 def test_34_fake_tax_foncier(self):
  d=docs()
  d["manifest"]["lignes_ciblees"][0]["montant_mcad"]="1000"
  with self.assertRaises(ValueError):passed(d)
 def test_35_fake_other_revenues(self):
  d=docs()
  d["manifest"]["lignes_ciblees"][1]["montant_mcad"]="1000"
  with self.assertRaises(ValueError):passed(d)
 def test_36_fake_e04_decoding(self):
  d=docs()
  d["manifest"]["lignes_ciblees"][0]["donnee_mamh_convertible_en_montant_fiscal"]=True
  with self.assertRaises(ValueError):passed(d)
 def test_37_fake_e05_statcan(self):
  d=docs()
  d["manifest"]["lignes_ciblees"][1]["source_agregat_statcan_certifiee"]=True
  with self.assertRaises(ValueError):passed(d)
 def test_38_fake_zip(self):
  d=docs()
  d["manifest"]["sources"]["statcan"]["octets_zip_authentifies"]=True
  with self.assertRaises(ValueError):passed(d)
 def test_39_fake_sha_statcan(self):
  d=docs()
  d["manifest"]["sources"]["statcan"]["sha256_zip_original"]="not-sha"
  with self.assertRaises(ValueError):passed(d)
 def test_40_fake_mamh_sha(self):
  d=docs()
  d["manifest"]["sources"]["mamH"]["sha256_fichier_original"]="not-sha"
  with self.assertRaises(ValueError):passed(d)
 def test_41_fake_original_mamh(self):
  d=docs()
  d["manifest"]["sources"]["mamH"]["octets_source_origine_authentifies"]=True
  with self.assertRaises(ValueError):passed(d)
 def test_42_fake_decoded_fields(self):
  d=docs()
  d["manifest"]["sources"]["mamH"]["dictionnaire_38_champs_valide"]=True
  with self.assertRaises(ValueError):passed(d)
 def test_43_incorrect_license(self):
  d=docs()
  d["manifest"]["sources"]["mamH"]["licence_fiche"]="all-rights-reserved"
  with self.assertRaises(ValueError):passed(d)
 def test_44_incorrect_source(self):
  d=docs()
  d["manifest"]["sources"]["mamH"]["url_csv"]="https://false.example"
  with self.assertRaises(ValueError):passed(d)
 def test_45_changed_blob(self):
  d=docs()
  d["manifest"]["sources"]["mamH"]["sha_git_du_texte_capture"]="not-sha"
  with self.assertRaises(ValueError):passed(d)
 def test_46_changed_period(self):
  d=docs()
  d["manifest"]["sources"]["mamH"]["annee_donnee"]=2025
  with self.assertRaises(ValueError):passed(d)
 def test_47_false_global_total(self):
  d=docs()
  d["manifest"]["bilan"]["montants_municipaux_foncier_reels_certifies"]=1
  with self.assertRaises(ValueError):passed(d)
 def test_48_false_go(self):
  d=docs()
  d["manifest"]["bilan"]["publication_autorisee"]=True
  with self.assertRaises(ValueError):passed(d)
 def test_49_fake_2024_prov_gov_total(self):
  d=docs()
  d["p53a"]["compartiments_non_additionner_aux_lignes"]["total_budget_quebec_mcad"]="999999"
  with self.assertRaises(ValueError):passed(d)
 def test_50_fake_p53a_e04(self):
  d=docs()
  d["lacunes"]["dossiers"][3]["montant_mcad"]="2000"
  with self.assertRaises(ValueError):passed(d)
 def test_51_fake_p53b_amount(self):
  d=docs()
  d["p53b"]["bilan"]["montants_hors_budget_certifiés"]=1
  with self.assertRaises(ValueError):passed(d)
 def test_52_fake_p53c_zip(self):
  d=docs()
  d["p53c"]["municipal"]["source_zip_original_recue"]=True
  with self.assertRaises(ValueError):passed(d)
 def test_53_fake_p52a_proof(self):
  d=docs()
  d["p52a"]["required_evidence"][3]["statut"]="VALIDE"
  with self.assertRaises(ValueError):passed(d)
 def test_54_broken_upstream_ref(self):
  d=docs()
  d["manifest"]["references"]["p53c"]="bogus.json"
  with self.assertRaises(ValueError):passed(d)
 def test_55_changing_38_count(self):
  d=docs()
  d["manifest"]["bilan"]["champs_numeriques_codes_a_qualifier"]=37
  with self.assertRaises(ValueError):passed(d)
if __name__=="__main__":
 unittest.main()
