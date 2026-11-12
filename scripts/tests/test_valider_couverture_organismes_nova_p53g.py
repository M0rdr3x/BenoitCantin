"""P53G: 1343 municipal bodies, historical gross not consolidated, SHA-256 coverage."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"valider_couverture_organismes_nova_p53g.py"
spec=importlib.util.spec_from_file_location("p53g",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def data():return {k:m.read(v) for k,v in m.FILES.items()}
def snapshot():return m.csv_source(m.LOCAL,m.SHA_LOCAL,1094),m.csv_source(m.OTHER,m.SHA_OTHER,249)
def audited(d=None,local=None,other=None):
 a,b=snapshot()
 return m.validate(data() if d is None else d,a if local is None else local,b if other is None else other)

class P53GTests(unittest.TestCase):
 def test_01_archive_is_consistent(self):
  self.assertEqual(audited()["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_all_entities_1343(self):
  self.assertEqual(audited()["organismes_denombrables"],1343)
 def test_03_local_entities_1094(self):
  self.assertEqual(audited()["municipalites_locales"],1094)
 def test_04_other_entities_249(self):
  self.assertEqual(audited()["mrc_regies_transport_communautes"],249)
 def test_05_five_groups(self):
  self.assertEqual(audited()["familles_organismes"],5)
 def test_06_gross_revenues_2024(self):
  self.assertEqual(audited()["enveloppe_recettes_brutes_CAD"],41663676586)
 def test_07_incremental_non_local_gross(self):
  self.assertEqual(audited()["enveloppe_additionnelle_non_locale_CAD"],9296053025)
 def test_08_totals_quotes(self):
  self.assertEqual(audited()["quotes_parts_recues_brutes_CAD"],3148209097)
 def test_09_totals_transfers(self):
  self.assertEqual(audited()["transferts_recus_bruts_CAD"],7716073104)
 def test_10_combined_exposure_not_savings(self):
  self.assertEqual(audited()["quotes_et_transferts_exposition_brute_CAD"],10864282201)
 def test_11_total_with_no_duplication_among_geo_codes(self):
  a,b=snapshot()
  self.assertEqual(len({r["cod_geo"] for r in a+b}),1343)
 def test_12_each_entity_12_revenues_reconcile(self):
  self.assertEqual(audited()["reconciliations_des_12_postes_par_organisme"],1343)
 def test_13_mrc_gross(self):
  self.assertEqual(data()["p53g"]["types_organismes"][2]["revenus"],"1417481157")
 def test_14_regies_gross(self):
  self.assertEqual(data()["p53g"]["types_organismes"][4]["revenus"],"636013686")
 def test_15_transit_gross(self):
  self.assertEqual(data()["p53g"]["types_organismes"][3]["revenus"],"7122045861")
 def test_16_communities_gross(self):
  self.assertEqual(data()["p53g"]["types_organismes"][1]["revenus"],"120512321")
 def test_17_no_provincial_2026_revenue_projection(self):
  self.assertIsNone(data()["p53g"]["recettes_equivalentes_budget_2026_2027_mcad"])
 def test_18_original_not_saved_in_git(self):
  self.assertFalse(data()["p53g"]["provenance"]["original_integral_archive_dans_git"])
 def test_19_intergovernmental_consolidation_not_attested(self):
  self.assertFalse(audited()["recettes_consolidees_interorganismes_certifiees"])
 def test_20_no_known_eliminations(self):
  self.assertEqual(audited()["eliminations_transactionnelles_documentees"],0)
  self.assertIsNone(data()["p53g"]["eliminations_interorganismes_certifiees_cad"])
 def test_21_evidence_gate_no_go(self):
  self.assertEqual((audited()["preuves_F01_F20_non_validees"],
                    audited()["parametres_Nova_inconnus"]),(20,1320))
 def test_22_regie_has_signed_negative_revenues(self):
  _,other=snapshot()
  self.assertTrue(any(m.dollars(x["CRIIX00405"])<0 for x in other if x["type_org"]=="Régie intermunicipale"))
 def test_23_gap_not_reinterpreted_as_zero(self):
  _,other=snapshot()
  self.assertTrue(any(x["CRIIX00406"]=="" for x in other))
 def test_24_csv_has_five_rows_plus_header(self):
  rows=list(csv.reader(io.StringIO(m.csv_summary(data()["p53g"]["types_organismes"]))))
  self.assertEqual(len(rows),6)
  self.assertTrue(all(r[-1]=="" for r in rows[1:]))
 def test_25_cli_standard_outputs_no_go(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(f)]),0)
   self.assertEqual(json.loads(f.read_text(encoding="utf-8"))["decision"],"NO_GO_AUTOMATIQUE")
 def test_26_cli_strict_returns_three(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--exiger-consolidation","--rapport",str(Path(td)/"report.json")]),3)
 def test_27_cli_csv_exports_separate_summary(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"coverage.csv"
   self.assertEqual(m.main(["--export-csv",str(p)]),0)
   self.assertEqual(len(list(csv.reader(p.open(encoding="utf-8")))),6)
 def test_28_cli_fails_missing_source(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(m.main(["--selection-complementaire",str(Path(td)/"missing.csv")]),2)
 def test_29_cli_no_overwrite_existing_report(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"report.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(m.main(["--rapport",str(p)]),2)
 def test_30_cli_no_identical_report_csv_dest(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"same.csv"
   self.assertEqual(m.main(["--rapport",str(p),"--export-csv",str(p)]),2)
 def test_31_modified_other_csv_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"altered.csv"
   raw=m.OTHER.read_bytes()
   p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
   with self.assertRaises(ValueError):m.csv_source(p,m.SHA_OTHER,249)
 def test_32_changed_money_rejected(self):
  local,other=snapshot()
  other[0]["CRIIX00405"]="900000000"
  with self.assertRaises(ValueError):m.validate(data(),local,other)
 def test_33_cross_source_duplicate_geo_rejected(self):
  local,other=snapshot()
  other[0]["cod_geo"]=local[0]["cod_geo"]
  with self.assertRaises(ValueError):m.validate(data(),local,other)
 def test_34_float_argument_refused(self):
  for s in ("$100","nan",True,"1 000","1e4"):
   with self.assertRaises(ValueError):m.dollars(s)
 def test_35_zero_vs_blank_preserved(self):
  self.assertIsNone(m.dollars(""))
  self.assertEqual(m.dollars("0"),0)
 def test_36_false_timestamp_not_in_public_aggregate(self):
  text=json.dumps(audited(),ensure_ascii=False)
  self.assertNotIn("https://",text)
  self.assertNotIn("@",text)
 def test_37_guard_1_disabled(self):
  d=data()
  d["p53g"]["controles"]["categories_405_406_a_417_reconciliees_ligne_par_ligne"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_38_guard_2_disabled(self):
  d=data()
  d["p53g"]["controles"]["identifiants_geo_distincts_1343"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_39_guard_3_disabled(self):
  d=data()
  d["p53g"]["controles"]["aucun_appariement_payeurs_beneficiaires_etabli"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_40_guard_4_disabled(self):
  d=data()
  d["p53g"]["controles"]["les_sommes_de_recettes_sont_brutes_non_consolidees"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_41_guard_5_disabled(self):
  d=data()
  d["p53g"]["controles"]["certains_organismes_deja_consolides_dans_leurs_rapports"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_42_guard_6_disabled(self):
  d=data()
  d["p53g"]["controles"]["blancs_non_equivalents_a_recettes_nulles"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_43_guard_7_disabled(self):
  d=data()
  d["p53g"]["controles"]["valeurs_negatives_conservees"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_44_guard_8_disabled(self):
  d=data()
  d["p53g"]["controles"]["transferts_non_ajoutes_au_budget_quebec"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_45_guard_9_disabled(self):
  d=data()
  d["p53g"]["controles"]["annees_2024_et_2026_2027_non_assimilables"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_46_guard_10_disabled(self):
  d=data()
  d["p53g"]["controles"]["pas_d_elimination_sans_preuve_transactionnelle"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_47_guard_11_disabled(self):
  d=data()
  d["p53g"]["controles"]["aucun_taux_Nova_calcule"]=False
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_48_gross_group_1_false(self):
  d=data()
  d["p53g"]["types_organismes"][0]["revenus"]="9999999"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_49_gross_group_2_false(self):
  d=data()
  d["p53g"]["types_organismes"][1]["revenus"]="9999999"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_50_gross_group_3_false(self):
  d=data()
  d["p53g"]["types_organismes"][2]["revenus"]="9999999"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_51_gross_group_4_false(self):
  d=data()
  d["p53g"]["types_organismes"][3]["revenus"]="9999999"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_52_gross_group_5_false(self):
  d=data()
  d["p53g"]["types_organismes"][4]["revenus"]="9999999"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_53_group_1_count_false(self):
  d=data()
  d["p53g"]["types_organismes"][0]["effectif"]=0
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_54_group_2_count_false(self):
  d=data()
  d["p53g"]["types_organismes"][1]["effectif"]=0
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_55_group_3_count_false(self):
  d=data()
  d["p53g"]["types_organismes"][2]["effectif"]=0
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_56_group_4_count_false(self):
  d=data()
  d["p53g"]["types_organismes"][3]["effectif"]=0
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_57_group_5_count_false(self):
  d=data()
  d["p53g"]["types_organismes"][4]["effectif"]=0
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_58_group_1_transfers_false(self):
  d=data()
  d["p53g"]["types_organismes"][0]["transferts"]="0"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_59_group_2_transfers_false(self):
  d=data()
  d["p53g"]["types_organismes"][1]["transferts"]="0"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_60_group_3_transfers_false(self):
  d=data()
  d["p53g"]["types_organismes"][2]["transferts"]="0"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_61_group_4_transfers_false(self):
  d=data()
  d["p53g"]["types_organismes"][3]["transferts"]="0"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_62_group_5_transfers_false(self):
  d=data()
  d["p53g"]["types_organismes"][4]["transferts"]="0"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_63_fake_local_revenues(self):
  d=data()
  d["p53g"]["totaux_bruts_cad"]["revenus"]="0"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_64_fake_quotes(self):
  d=data()
  d["p53g"]["totaux_bruts_cad"]["quotes_parts"]="0"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_65_fake_transfers(self):
  d=data()
  d["p53g"]["totaux_bruts_cad"]["transferts"]="0"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_66_fake_original_archived(self):
  d=data()
  d["p53g"]["provenance"]["original_integral_archive_dans_git"]=True
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_67_fake_original_sha(self):
  d=data()
  d["p53g"]["provenance"]["original_sha256_observe"]="ffffffff"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_68_fake_selected_sha(self):
  d=data()
  d["p53g"]["provenance"]["selection_complementaire_sha256"]="ffffffff"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_69_fake_local_selected_sha(self):
  d=data()
  d["p53g"]["provenance"]["selection_locale_sha256"]="ffffffff"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_70_fake_blob_sha(self):
  d=data()
  d["p53g"]["provenance"]["selection_complementaire_git_blob"]="ffffffff"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_71_fake_source_octets(self):
  d=data()
  d["p53g"]["provenance"]["original_octets_observes"]=1
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_72_fake_more_columns(self):
  d=data()
  d["p53g"]["provenance"]["colonnes_originales"]=123
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_73_fake_source_license(self):
  d=data()
  d["p53g"]["provenance"]["licence_affichee"]="PRIVATE"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_74_fake_eliminations(self):
  d=data()
  d["p53g"]["eliminations_interorganismes_certifiees_cad"]="9999"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_75_fake_consolidation(self):
  d=data()
  d["p53g"]["recettes_consolidees_tous_organismes_cad"]="40000000000"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_76_fake_revenues_2026(self):
  d=data()
  d["p53g"]["recettes_equivalentes_budget_2026_2027_mcad"]="40000"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_77_fake_nova_yield(self):
  d=data()
  d["p53g"]["reforme_Nova_rendement_mcad"]="888"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_78_fake_additional_count(self):
  d=data()
  d["p53g"]["bilan"]["organismes_complementaires_ajoutes"]=250
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_79_fake_certified_reciprocal(self):
  d=data()
  d["p53g"]["bilan"]["appariements_reciproques_recus"]=1
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_80_fake_certified_elimination_count(self):
  d=data()
  d["p53g"]["bilan"]["eliminations_certifiees"]=1
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_81_fake_Nova_rate(self):
  d=data()
  d["p53g"]["bilan"]["taux_Nova_adoptes"]=1
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_82_fake_publication(self):
  d=data()
  d["p53g"]["bilan"]["publication_autorisee"]=True
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_83_fake_P53F_match(self):
  d=data()
  d["p53f"]["bilan"]["appariements_confirmes"]=1
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_84_fake_P53E_revenues(self):
  d=data()
  d["p53e"]["observations_de_reference"]["revenus_totaux_municipalites_locales_2024_cad"]="0"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_85_fake_P52A_statut(self):
  d=data()
  d["p52a"]["required_evidence"][3]["statut"]="VALIDE"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_86_fake_P52A_GO(self):
  d=data()
  d["p52a"]["automatic_go"]=True
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
 def test_87_wrong_P53F_reference(self):
  d=data()
  d["p53g"]["sources"]["p53f"]="other.json"
  local,other=snapshot()
  with self.assertRaises(ValueError):
   m.validate(d,local,other)
if __name__=='__main__':
 unittest.main()
