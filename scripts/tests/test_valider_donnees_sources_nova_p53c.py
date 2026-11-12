"""P53C: authentic CRA source bytes, 2024 historical values and missing municipal ZIP."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"valider_donnees_sources_nova_p53c.py"
spec=importlib.util.spec_from_file_location("p53c",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def documents():
 return {key:m.read(path) for key,path in m.FILES.items()}

def verified(d=None):
 return m.verify(d or documents(),m.read_original(m.SOURCE))

class P53CDataTests(unittest.TestCase):
 def rejected(self,edit):
  d=documents();edit(d)
  with self.assertRaises(ValueError):
   verified(d)
 def test_01_source_bytes_authentic(self):
  source=m.read_original(m.SOURCE)
  self.assertEqual(source["source_sha256"],m.EXPECTED_SHA)
 def test_02_source_1059_bytes(self):
  self.assertEqual(m.SOURCE.stat().st_size,1059)
 def test_03_line_count_original(self):
  self.assertEqual(m.read_original(m.SOURCE)["lignes_csv_incluant_entete"],16)
 def test_04_historic_quebec_total(self):
  self.assertEqual(verified()["impot_federal_net_particuliers_quebec_2024_milliers_cad"],43549895)
 def test_05_decimal_millions_precise(self):
  self.assertEqual(verified()["impot_federal_net_particuliers_quebec_2024_millions_cad"],"43549.895")
 def test_06_arithmetic_rounding_one_thousand(self):
  self.assertEqual(verified()["difference_arrondis_5_tranches_milliers_cad"],1)
 def test_07_original_five_brackets(self):
  self.assertEqual(m.read_original(m.SOURCE)["montants_quebec_milliers_cad"][:5],
   ["5564856","16863643","7303699","3310900","10506796"])
 def test_08_canada_total_cross_check(self):
  self.assertEqual(m.read_original(m.SOURCE)["montant_canada_milliers_cad"],"222652101")
 def test_09_calendar_tax_year_not_budget_year(self):
  self.assertEqual(verified()["annee_impot_ARC"],2024)
  self.assertFalse(verified()["recettes_federales_quebec_2026_2027_certifiees"])
 def test_10_no_municipal_archive_acquired(self):
  self.assertFalse(verified()["source_zip_municipale_acquise"])
 def test_11_no_municipal_revenue(self):
  self.assertEqual(verified()["recettes_municipales_2024_et_2026_2027_chiffrees"],0)
 def test_12_unvalidated_twenty_evidence(self):
  self.assertEqual(verified()["preuves_F01_F20_non_validees"],20)
 def test_13_unvalidated_1320_figures(self):
  self.assertEqual(verified()["valeurs_nova_inconnues"],1320)
 def test_14_no_municipal_fabrication(self):
  self.assertIsNone(documents()["registre"]["municipal"]["montant_taxes_foncieres_mcad"])
 def test_15_no_tax_rate_inference(self):
  self.assertIsNone(documents()["registre"]["donnees_quebec_2024"]["rendement_impot_nova_mcad"])
 def test_16_no_revenue_as_2026(self):
  self.assertIsNone(documents()["registre"]["donnees_quebec_2024"]["montant_pour_exercice_2026_2027_mcad"])
 def test_17_export_has_six_data_rows(self):
  export=list(csv.reader(io.StringIO(m.export_csv(documents()))))
  self.assertEqual(len(export),7)
 def test_18_export_total_row_not_sum_of_buckets(self):
  export=list(csv.reader(io.StringIO(m.export_csv(documents()))))
  self.assertEqual(export[-1][4],"43549895")
 def test_19_export_separate_budget_year_and_no_certification(self):
  export=list(csv.reader(io.StringIO(m.export_csv(documents()))))
  self.assertTrue(all(row[5]=="2026-2027" and row[6]=="NON" for row in export[1:]))
 def test_20_source_not_as_utf8(self):
  with self.assertRaises(UnicodeDecodeError):
   m.SOURCE.read_bytes().decode("utf-8")
 def test_21_tampered_original_rejected(self):
  original=m.SOURCE.read_bytes()
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"source.csv"
   p.write_bytes(original[:-1]+bytes([original[-1]^1]))
   with self.assertRaises(ValueError):m.read_original(p)
 def test_22_missing_source_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):m.read_original(Path(td)/"no.csv")
 def test_23_cli_report_has_no_go(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(json.loads(p.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_24_cli_strict_exits_three(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"report.json"
   self.assertEqual(m.main(["--exiger-consolidation","--rapport",str(p)]),3)
 def test_25_cli_export_local_observation(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"quebec.csv"
   self.assertEqual(m.main(["--export-csv",str(p)]),0)
   self.assertEqual(len(list(csv.reader(p.open(encoding="utf-8")))),7)
 def test_26_cli_bad_missing_original_exits_two(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--csv-original",str(Path(td)/"nonexistent.csv")]),2)
 def test_27_cli_no_overwrite_existing(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(m.main(["--rapport",str(p)]),2)
 def test_28_cli_no_same_csv_and_report(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"same.json"
   self.assertEqual(m.main(["--rapport",str(p),"--export-csv",str(p)]),2)
 def test_29_csv_sha_is_binary_original_not_normalized(self):
  import hashlib
  self.assertEqual(hashlib.sha256(m.SOURCE.read_bytes()).hexdigest(),m.EXPECTED_SHA)
 def test_30_report_no_personal_data(self):
  s=json.dumps(verified())
  for forbidden in ("https://","@", "numero_assurance_sociale","nom_personnel"):
   self.assertNotIn(forbidden,s)
 def test_31_changed_bracket_1(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["tranche_55867_ou_moins_milliers_cad"]="0"
  with self.assertRaises(ValueError):
   verified(d)
 def test_32_changed_bracket_2(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["tranche_55867_111733_milliers_cad"]="0"
  with self.assertRaises(ValueError):
   verified(d)
 def test_33_changed_bracket_3(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["tranche_111733_173205_milliers_cad"]="0"
  with self.assertRaises(ValueError):
   verified(d)
 def test_34_changed_bracket_4(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["tranche_173205_246752_milliers_cad"]="0"
  with self.assertRaises(ValueError):
   verified(d)
 def test_35_changed_bracket_5(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["tranche_246752_et_plus_milliers_cad"]="0"
  with self.assertRaises(ValueError):
   verified(d)
 def test_36_removed_comparability_1(self):
  d=documents()
  d["registre"]["comparabilite"]["annee_imposition_2024_nequivaut_pas_budget_2026_2027"]=False
  with self.assertRaises(ValueError):
   verified(d)
 def test_37_removed_comparability_2(self):
  d=documents()
  d["registre"]["comparabilite"]["impots_federaux_particuliers_non_equivalents_recettes_federales_toutes_sources"]=False
  with self.assertRaises(ValueError):
   verified(d)
 def test_38_removed_comparability_3(self):
  d=documents()
  d["registre"]["comparabilite"]["recettes_M_2026_2027_du_Quebec_non_additives_directement_aux_impots_2024"]=False
  with self.assertRaises(ValueError):
   verified(d)
 def test_39_removed_comparability_4(self):
  d=documents()
  d["registre"]["comparabilite"]["somme_de_tranches_permet_ecart_arrondi_1_millier"]=False
  with self.assertRaises(ValueError):
   verified(d)
 def test_40_removed_comparability_5(self):
  d=documents()
  d["registre"]["comparabilite"]["transferts_intergouvernementaux_a_ne_pas_doubler"]=False
  with self.assertRaises(ValueError):
   verified(d)
 def test_41_removed_comparability_6(self):
  d=documents()
  d["registre"]["comparabilite"]["taxes_municipales_non_confondre_impot_scolaire_budget_Quebec"]=False
  with self.assertRaises(ValueError):
   verified(d)
 def test_42_removed_comparability_7(self):
  d=documents()
  d["registre"]["comparabilite"]["statut_F02_toujours_NON_VALIDE"]=False
  with self.assertRaises(ValueError):
   verified(d)
 def test_43_removed_comparability_8(self):
  d=documents()
  d["registre"]["comparabilite"]["aucune_validation_independante_inventee"]=False
  with self.assertRaises(ValueError):
   verified(d)
 def test_44_fake_2026_revenue(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["montant_pour_exercice_2026_2027_mcad"]="43549.895"
  with self.assertRaises(ValueError):
   verified(d)
 def test_45_fake_nova_rate_yield(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["rendement_impot_nova_mcad"]="1000"
  with self.assertRaises(ValueError):
   verified(d)
 def test_46_fake_consolidated_federal(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["montant_federal_toutes_taxes_2026_2027_mcad"]="90000"
  with self.assertRaises(ValueError):
   verified(d)
 def test_47_fake_pdf_hash(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["octets_pdf_originaux_archives_et_hashes"]=True
  with self.assertRaises(ValueError):
   verified(d)
 def test_48_fake_independent_expert(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["avis_expert_comptable_independant_signe"]=True
  with self.assertRaises(ValueError):
   verified(d)
 def test_49_wrong_arc_sha256(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["sha256_octets_originaux"]="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
  with self.assertRaises(ValueError):
   verified(d)
 def test_50_wrong_blob_id(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["git_blob_sha"]="not-a-blob"
  with self.assertRaises(ValueError):
   verified(d)
 def test_51_wrong_unit(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["unite_originale"]="DOLLARS"
  with self.assertRaises(ValueError):
   verified(d)
 def test_52_fake_source_bytes(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["taille_octets"]=1060
  with self.assertRaises(ValueError):
   verified(d)
 def test_53_fake_original_encoding(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["encodage_original"]="utf-8"
  with self.assertRaises(ValueError):
   verified(d)
 def test_54_tampered_historical_total(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["total_quebec_officiel_milliers_cad"]="43549894"
  with self.assertRaises(ValueError):
   verified(d)
 def test_55_tampered_rounding_residual(self):
  d=documents()
  d["registre"]["donnees_quebec_2024"]["ecart_arrondis_total_moins_somme_milliers_cad"]="0"
  with self.assertRaises(ValueError):
   verified(d)
 def test_56_false_2024_2027_link(self):
  d=documents()
  d["registre"]["reference_exercice_budget_quebec"]="2024-2025"
  with self.assertRaises(ValueError):
   verified(d)
 def test_57_municipal_zip_falsely_received(self):
  d=documents()
  d["registre"]["municipal"]["source_zip_original_recue"]=True
  with self.assertRaises(ValueError):
   verified(d)
 def test_58_municipal_zip_fictitious_sha(self):
  d=documents()
  d["registre"]["municipal"]["source_zip_SHA256"]="123"
  with self.assertRaises(ValueError):
   verified(d)
 def test_59_municipal_properties_fictitious(self):
  d=documents()
  d["registre"]["municipal"]["montant_taxes_foncieres_mcad"]="3000"
  with self.assertRaises(ValueError):
   verified(d)
 def test_60_municipal_tax_services_fictitious(self):
  d=documents()
  d["registre"]["municipal"]["montant_autres_recettes_mcad"]="1000"
  with self.assertRaises(ValueError):
   verified(d)
 def test_61_municipal_verification_fictitious(self):
  d=documents()
  d["registre"]["municipal"]["geographie_quebec_et_finances_classifiees_verifiees"]=True
  with self.assertRaises(ValueError):
   verified(d)
 def test_62_false_municipal_link(self):
  d=documents()
  d["registre"]["municipal"]["source"]="https://no.example/municipal"
  with self.assertRaises(ValueError):
   verified(d)
 def test_63_false_reform_certification(self):
  d=documents()
  d["registre"]["bilan"]["preuves_F01_F20_validees"]=1
  with self.assertRaises(ValueError):
   verified(d)
 def test_64_false_publication(self):
  d=documents()
  d["registre"]["bilan"]["publication_autorisee"]=True
  with self.assertRaises(ValueError):
   verified(d)
 def test_65_fake_2026_federal(self):
  d=documents()
  d["registre"]["bilan"]["recettes_2026_2027_federales_certifiees"]=1
  with self.assertRaises(ValueError):
   verified(d)
 def test_66_false_gov_access(self):
  d=documents()
  d["registre"]["bilan"]["source_originale_archivee_et_sha256_reproductible"]=0
  with self.assertRaises(ValueError):
   verified(d)
 def test_67_fictitious_2026_p53a(self):
  d=documents()
  d["p53a"]["compartiments_non_additionner_aux_lignes"]["total_budget_quebec_mcad"]="200000"
  with self.assertRaises(ValueError):
   verified(d)
 def test_68_fictitious_p53a_E01(self):
  d=documents()
  d["lacunes"]["dossiers"][0]["montant_mcad"]="43549.895"
  with self.assertRaises(ValueError):
   verified(d)
 def test_69_fictitious_p53b_annual(self):
  d=documents()
  d["p53b"]["dossiers"][0]["montant_annuel_reel_quebec_mcad"]="43549.895"
  with self.assertRaises(ValueError):
   verified(d)
 def test_70_fictitious_p52a_F02(self):
  d=documents()
  d["p52a"]["required_evidence"][1]["statut"]="VALIDE"
  with self.assertRaises(ValueError):
   verified(d)
 def test_71_fictitious_go(self):
  d=documents()
  d["p52a"]["automatic_go"]=True
  with self.assertRaises(ValueError):
   verified(d)
 def test_72_wrong_catalogue(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["catalogue"]="https://invalid.example"
  with self.assertRaises(ValueError):
   verified(d)
 def test_73_wrong_original_path(self):
  d=documents()
  d["registre"]["chainage_documents"]["document_original_archetype"]="a.csv"
  with self.assertRaises(ValueError):
   verified(d)
 def test_74_wrong_publication_date(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["date_publication_catalogue"]="2027-01-01"
  with self.assertRaises(ValueError):
   verified(d)
 def test_75_fake_asof_2026(self):
  d=documents()
  d["registre"]["source_fiscale_ARC"]["date_donnees_arrete"]="2026-12-31"
  with self.assertRaises(ValueError):
   verified(d)
if __name__=="__main__":
 unittest.main()
