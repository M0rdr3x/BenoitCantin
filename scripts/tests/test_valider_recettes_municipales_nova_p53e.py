"""P53E: source MAMH 2024, 1094 comptes, 15 postes et double-compte."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"valider_recettes_municipales_nova_p53e.py"
spec=importlib.util.spec_from_file_location("p53e",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def documents():return {k:m.read(v) for k,v in m.FILES.items()}
def audit():
 rows,dictionary=m.load_snapshots()
 return m.audit(documents(),rows,dictionary)

class P53ETests(unittest.TestCase):
 def reject(self,fn):
  doc=documents()
  fn(doc)
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):m.audit(doc,rows,dic)
 def test_01_source_observations_no_go(self):
  self.assertEqual(audit()["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_exact_local_accounts(self):
  self.assertEqual(audit()["municipalites_locales_analysees"],1094)
 def test_03_real_property_tax_observation(self):
  self.assertEqual(audit()["taxes_foncieres_2024_observees_cad"],"15085531572")
 def test_04_one_blank_property_not_zero(self):
  self.assertEqual(audit()["municipalites_avec_taxe_fonciere_renseignee"],1093)
 def test_05_all_tax_revenues_include_property(self):
  s=audit()
  self.assertEqual(s["taxes_municipales_totales_2024_cad"],"17337284213")
  self.assertLess(int(s["taxes_foncieres_2024_observees_cad"]),int(s["taxes_municipales_totales_2024_cad"]))
 def test_06_general_tax_subset(self):
  self.assertEqual(m.compute(m.load_snapshots()[0])[0]["CRIIX00018"]["total_cad"],"13325713274")
 def test_07_total_municipal_revenues(self):
  self.assertEqual(audit()["revenus_municipaux_locaux_totaux_2024_cad"],"32367623561")
 def test_08_transfers_visible_separately(self):
  self.assertEqual(audit()["transferts_municipaux_2024_cad"],"5376508934")
 def test_09_other_funds_are_not_net_of_intergovernmental_flows(self):
  self.assertEqual(audit()["revenus_hors_taxes_et_transferts_2024_cad"],"9653830414")
 def test_10_total_disjoint_reconciliation(self):
  r=audit()
  self.assertEqual(sum(int(r[k]) for k in
    ("taxes_municipales_totales_2024_cad",
     "transferts_municipaux_2024_cad",
     "revenus_hors_taxes_et_transferts_2024_cad")),
     int(r["revenus_municipaux_locaux_totaux_2024_cad"]))
 def test_11_all_1094_single_account_reconcile(self):
  self.assertEqual(audit()["ecarts_rapprochements"],0)
 def test_12_local_geographies_unique(self):
  rows,_=m.load_snapshots()
  self.assertEqual(len({x["cod_geo"] for x in rows}),1094)
 def test_13_15_codes_documented(self):
  _,dict_=m.load_snapshots()
  self.assertEqual(len(dict_),15)
 def test_14_15_fields_in_selected_csv(self):
  rows,_=m.load_snapshots()
  self.assertEqual(list(rows[0]),m.COLUMNS)
 def test_15_archive_sha256_of_derived_source(self):
  import hashlib
  self.assertEqual(hashlib.sha256(m.CSV_SOURCE.read_bytes()).hexdigest(),m.EXPECTED_CSV_SHA)
 def test_16_archive_sha256_of_description(self):
  import hashlib
  self.assertEqual(hashlib.sha256(m.DESC_SOURCE.read_bytes()).hexdigest(),m.EXPECTED_DESC_SHA)
 def test_17_2024_not_2026_27(self):
  self.assertEqual(audit()["annee_comptable"],2024)
  self.assertFalse(audit()["montants_municipaux_2026_2027_certifies"])
 def test_18_not_consolidated_to_provincial(self):
  self.assertFalse(audit()["consolidation_interadministrations_certifiee"])
 def test_19_tax_fonciere_blank_code_is_preserved(self):
  rows,_=m.load_snapshots()
  self.assertEqual([x["cod_geo"] for x in rows if not x["CRIIX00016"].strip()],["45080"])
 def test_20_historic_sources_not_nova_adoption(self):
  r=audit()
  self.assertFalse(r["adoption_autorisee"])
  self.assertEqual((r["preuves_F01_F20_non_validees"],r["valeurs_nova_inconnues"]),(20,1320))
 def test_21_cli_regular_summary(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"r.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(json.loads(p.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_22_cli_strict_refuses_consolidation(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(m.main(["--exiger-consolidation","--rapport",str(Path(d)/"a.json")]),3)
 def test_23_cli_refuses_non_existing_original_subset(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(m.main(["--csv-selection",str(Path(d)/"missing.csv")]),2)
 def test_24_cli_does_not_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"r.json"
   self.assertEqual(m.main(["--rapport",str(path)]),0)
   self.assertEqual(m.main(["--rapport",str(path)]),2)
 def test_25_detect_modified_subset_blob(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"selected.csv"
   data=m.CSV_SOURCE.read_bytes()
   path.write_bytes(data[:-1]+bytes([data[-1]^1]))
   with self.assertRaises(ValueError):m.load_snapshots(path,m.DESC_SOURCE)
 def test_26_detect_modified_dictionary(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"dictionary.json"
   raw=m.DESC_SOURCE.read_bytes()
   path.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
   with self.assertRaises(ValueError):m.load_snapshots(m.CSV_SOURCE,path)
 def test_27_decimals_reject_floats(self):
  for s in (1.1,True,"nan","NaN","100 CAD",""):
   with self.assertRaises(ValueError):m.money(s)
 def test_28_report_only_public_aggregate_and_no_identifying_municipality(self):
  r=json.dumps(audit(),ensure_ascii=False)
  for forbidden in ("45080","Saint-Benoît","https://","@","taux_Nova"):
   self.assertNotIn(forbidden,r)
 def test_29_false_total_01(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][0]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_30_false_total_02(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][1]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_31_false_total_03(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][2]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_32_false_total_04(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][3]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_33_false_total_05(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][4]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_34_false_total_06(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][5]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_35_false_total_07(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][6]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_36_false_total_08(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][7]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_37_false_total_09(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][8]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_38_false_total_10(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][9]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_39_false_total_11(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][10]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_40_false_total_12(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][11]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_41_false_total_13(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][12]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_42_false_total_14(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][13]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_43_false_total_15(self):
  d=documents()
  d["p53e"]["champs_reconciliation"][14]["total_cad"]="0"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_44_false_guard_1(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["taxes_foncieres_incluses_dans_taxes_totales"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_45_false_guard_2(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["total_revenus_inclut_taxes_et_transferts"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_46_false_guard_3(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["autres_revenus_hors_taxes_et_transferts_inclut_possiblement_quotes_parts_interadmin"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_47_false_guard_4(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["transfer_comptable_pas_a_additionner_aux_comptes_provinciaux"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_48_false_guard_5(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["filtre_municipalites_locales_ne_vaut_pas_tout_secteur_municipal"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_49_false_guard_6(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["source_extraite_et_filtre_intermediaire_pas_archive_integrale"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_50_false_guard_7(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["fichier_brut_modifiable_journalierement_retelecharger_et_empreinter"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_51_false_guard_8(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["taux_taxe_Nova_non_derivable_des_comptes_2024"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_52_false_guard_9(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["exercice_2024_pas_exercice_2026_2027"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_53_false_guard_10(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["aucune_certification_externe_des_totaux"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_54_false_guard_11(self):
  d=documents()
  d["p53e"]["périmètre_et_risques"]["blanc_foncier_pas_recette_zero"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_55_certified_all_governments(self):
  d=documents()
  d["p53e"]["observations_de_reference"]["montant_net_sans_doublon_tous_paliers_2024_cad"]="50000000000"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_56_fabricated_2026_2027(self):
  d=documents()
  d["p53e"]["observations_de_reference"]["montant_comparable_budget_2026_2027_mcad"]="30000"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_57_fabricated_nova_yield(self):
  d=documents()
  d["p53e"]["observations_de_reference"]["revenus_du_systeme_nova_mcad"]="20000"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_58_missing_tax_code_removed(self):
  d=documents()
  d["p53e"]["observations_de_reference"]["codes_taxation_fonciere_sans_valeur"]=[]
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_59_fictitious_source_original_archived(self):
  d=documents()
  d["p53e"]["sources"]["donnees"]["original_brut_entier_archive_dans_depot"]=True
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_60_fictitious_dictionary_original_archived(self):
  d=documents()
  d["p53e"]["sources"]["dictionnaire"]["original_brut_entier_archive_dans_depot"]=True
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_61_modified_full_sha(self):
  d=documents()
  d["p53e"]["sources"]["donnees"]["sha256_original_telecharge"]="FFFFFFFF"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_62_modified_extract_sha(self):
  d=documents()
  d["p53e"]["sources"]["donnees"]["sha256_derive"]="000"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_63_modified_desc_sha(self):
  d=documents()
  d["p53e"]["sources"]["dictionnaire"]["sha256_description_retenue"]="abc"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_64_fake_independent_source_validation(self):
  d=documents()
  d["p53e"]["sources"]["donnees"]["avis_expert_independant_authentifie"]=True
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_65_fake_independent_dictionary_validation(self):
  d=documents()
  d["p53e"]["sources"]["dictionnaire"]["avis_expert_independant_authentifie"]=True
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_66_fake_source_legal_year(self):
  d=documents()
  d["p53e"]["methode"]["annee"]=2026
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_67_fake_extra_local_municipality(self):
  d=documents()
  d["p53e"]["methode"]["municipalites_locales_retenues"]=1095
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_68_fake_double_count_resolution(self):
  d=documents()
  d["p53e"]["methode"]["ecarts_de_rapprochement_individuels"]=1
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_69_fake_wrong_scope(self):
  d=documents()
  d["p53e"]["methode"]["n_inclut_pas_MRC_regies_organismes_transport"]=False
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_70_invented_legal_go(self):
  d=documents()
  d["p53e"]["bilan"]["publication_autorisee"]=True
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_71_invented_all_nova_fiscal_values(self):
  d=documents()
  d["p53e"]["bilan"]["valeurs_nova_inconnues"]=0
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_72_invented_f04_status(self):
  d=documents()
  d["p52a"]["required_evidence"][3]["statut"]="VALIDE"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_73_invented_f04_2026(self):
  d=documents()
  d["lacunes"]["dossiers"][3]["montant_mcad"]="15085.532"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_74_invented_E05_2026(self):
  d=documents()
  d["lacunes"]["dossiers"][4]["montant_mcad"]="9653.83"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_75_invalid_reference(self):
  d=documents()
  d["p53e"]["references"]["p53d"]="other.json"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_76_false_p53d_decoder(self):
  d=documents()
  d["p53d"]["sources"]["mamH"]["dictionnaire_38_champs_valide"]=True
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_77_false_p53c_consolidation(self):
  d=documents()
  d["p53c"]["donnees_quebec_2024"]["total_historique_millions_cad"]="32000"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_78_false_p53a_budget(self):
  d=documents()
  d["p53a"]["compartiments_non_additionner_aux_lignes"]["total_budget_quebec_mcad"]="150000"
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
 def test_79_false_p52a_go(self):
  d=documents()
  d["p52a"]["automatic_go"]=True
  rows,dic=m.load_snapshots()
  with self.assertRaises(ValueError):
   m.audit(d,rows,dic)
if __name__=='__main__':
 unittest.main()
