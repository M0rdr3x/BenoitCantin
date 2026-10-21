"""P53A: rapprochements, périmètres et refus des montants fictifs."""
import csv,importlib.util,io,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/"scripts"/"auditer_inventaire_recettes_nova_p53a.py"
spec=importlib.util.spec_from_file_location("p53a",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixtures():return {key:m.read(value) for key,value in m.FILES.items()}
class AuditTests(unittest.TestCase):
 def test_01_valid_real_reconciliation(self):
  self.assertEqual(m.validate(fixtures())["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_totals_are_official(self):
  r=m.validate(fixtures())
  self.assertEqual(r["recettes_gouvernement_quebec_mcad"],166492)
  self.assertEqual(r["recettes_autonomes_quebec_mcad"],134361)
  self.assertEqual(r["transferts_federaux_dans_budget_mcad"],32131)
 def test_03_partition_disjoint(self):
  r=m.validate(fixtures())
  self.assertEqual(sum(r[x] for x in
    ("impots_revenu_existant_quebec_mcad","autres_prelevements_a_instruire_mcad",
     "revenus_entreprises_droits_divers_mcad","transferts_federaux_dans_budget_mcad")),166492)
 def test_04_four_partition_expected(self):
  r=m.validate(fixtures())
  self.assertEqual([r[k] for k in (
    "impots_revenu_existant_quebec_mcad","autres_prelevements_a_instruire_mcad",
    "revenus_entreprises_droits_divers_mcad")],[65327,40731,28303])
 def test_05_accounts_balanced(self):
  r=m.validate(fixtures())
  self.assertEqual((r["depenses_totales_avec_service_dette_mcad"],
                    r["deficit_comptable_mcad"],r["solde_loi_equilibre_mcad"]),
                   (170757,-6265,-8612))
 def test_06_twenty_one_rows_nine_gaps(self):
  r=m.validate(fixtures())
  self.assertEqual((r["lignes_recettes_budget"],r["lacunes_sans_montant"]),(21,9))
 def test_07_no_independent_expert_or_go(self):
  r=m.validate(fixtures())
  self.assertFalse(r["revenus_du_projet_nova_certifies"])
  self.assertFalse(r["consolidation_intergouvernementale_obtenue"])
 def test_08_tax_revenue_not_sole_tvq(self):
  self.assertTrue(fixtures()["registre"]["regles"]["ventes_aggregat_pas_tvq_seule"])
 def test_09_federal_transfer_not_sovereign_guarantee(self):
  self.assertTrue(fixtures()["registre"]["regles"]["transferts_non_garantis_souverainete"])
 def test_10_false_municipal_zero_not_assumed(self):
  self.assertTrue(all(x["montant_mcad"] is None for x in fixtures()["lacunes"]["dossiers"]))
 def test_11_twenty_proofs_and_1320_unknown(self):
  r=m.validate(fixtures())
  self.assertEqual((r["preuves_F01_F20_non_validees"],r["valeurs_nova_inconnues"]),(20,1320))
 def test_12_csv_rows_and_amount_gaps(self):
  rows=list(csv.reader(io.StringIO(m.csv_export(fixtures()))))
  self.assertEqual(len(rows),31)
  self.assertEqual(rows[1][0],"impot_particuliers")
  self.assertEqual(rows[-1][0],"E09")
  self.assertTrue(all(row[4]=="" for row in rows[22:]))
 def test_13_csv_no_fictitious_human_review(self):
  rows=list(csv.reader(io.StringIO(m.csv_export(fixtures()))))
  self.assertTrue(all(row[-1]=="" for row in rows[1:]))
 def test_14_amount_strict_integer(self):
  for value in ("1 000","1.0",1000,"$1000"):
   with self.assertRaises(ValueError):m.number(value)
 def test_15_valid_negative_number(self):
  self.assertEqual(m.number("-8612"),-8612)
 def test_16_cli_incomplete_go_is_three(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"r.json"
   self.assertEqual(m.main(["--exiger-completude","--rapport",str(f)]),3)
   self.assertEqual(json.loads(f.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_17_cli_missing_source_returns_two(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(m.main(["--registre",str(Path(d)/"missing.json")]),2)
 def test_18_cli_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"r.json"
   self.assertEqual(m.main(["--rapport",str(f)]),0)
   self.assertEqual(m.main(["--rapport",str(f)]),2)
 def test_19_cli_report_and_csv_distinct(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"r.json"
   self.assertEqual(m.main(["--rapport",str(p),"--export-csv",str(p)]),2)
 def test_20_cli_30_line_export(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"rows.csv"
   self.assertEqual(m.main(["--export-csv",str(f)]),0)
   self.assertEqual(len(list(csv.reader(f.open(encoding="utf-8")))),31)
 def test_21_budget_line_01_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][0]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_22_budget_line_02_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][1]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_23_budget_line_03_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][2]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_24_budget_line_04_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][3]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_25_budget_line_05_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][4]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_26_budget_line_06_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][5]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_27_budget_line_07_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][6]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_28_budget_line_08_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][7]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_29_budget_line_09_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][8]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_30_budget_line_10_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][9]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_31_budget_line_11_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][10]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_32_budget_line_12_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][11]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_33_budget_line_13_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][12]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_34_budget_line_14_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][13]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_35_budget_line_15_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][14]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_36_budget_line_16_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][15]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_37_budget_line_17_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][16]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_38_budget_line_18_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][17]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_39_budget_line_19_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][18]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_40_budget_line_20_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][19]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_41_budget_line_21_tampered(self):
  d=fixtures()
  d["registre"]["lignes"][20]["montant_mcad"]="999999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_42_external_gap_1_fabricated(self):
  d=fixtures()
  d["lacunes"]["dossiers"][0]["montant_mcad"]="100"
  with self.assertRaises(ValueError):m.validate(d)
 def test_43_external_gap_2_fabricated(self):
  d=fixtures()
  d["lacunes"]["dossiers"][1]["montant_mcad"]="100"
  with self.assertRaises(ValueError):m.validate(d)
 def test_44_external_gap_3_fabricated(self):
  d=fixtures()
  d["lacunes"]["dossiers"][2]["montant_mcad"]="100"
  with self.assertRaises(ValueError):m.validate(d)
 def test_45_external_gap_4_fabricated(self):
  d=fixtures()
  d["lacunes"]["dossiers"][3]["montant_mcad"]="100"
  with self.assertRaises(ValueError):m.validate(d)
 def test_46_external_gap_5_fabricated(self):
  d=fixtures()
  d["lacunes"]["dossiers"][4]["montant_mcad"]="100"
  with self.assertRaises(ValueError):m.validate(d)
 def test_47_external_gap_6_fabricated(self):
  d=fixtures()
  d["lacunes"]["dossiers"][5]["montant_mcad"]="100"
  with self.assertRaises(ValueError):m.validate(d)
 def test_48_external_gap_7_fabricated(self):
  d=fixtures()
  d["lacunes"]["dossiers"][6]["montant_mcad"]="100"
  with self.assertRaises(ValueError):m.validate(d)
 def test_49_external_gap_8_fabricated(self):
  d=fixtures()
  d["lacunes"]["dossiers"][7]["montant_mcad"]="100"
  with self.assertRaises(ValueError):m.validate(d)
 def test_50_external_gap_9_fabricated(self):
  d=fixtures()
  d["lacunes"]["dossiers"][8]["montant_mcad"]="100"
  with self.assertRaises(ValueError):m.validate(d)
 def test_51_disabled_ventes_aggregat_pas_tvq_seule(self):
  d=fixtures()
  d["registre"]["regles"]["ventes_aggregat_pas_tvq_seule"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_52_disabled_cotisations_pas_automatiquement_abolies(self):
  d=fixtures()
  d["registre"]["regles"]["cotisations_pas_automatiquement_abolies"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_53_disabled_entreprises_publiques_pas_impots(self):
  d=fixtures()
  d["registre"]["regles"]["entreprises_publiques_pas_impots"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_54_disabled_droits_et_redevances_a_ventiler(self):
  d=fixtures()
  d["registre"]["regles"]["droits_et_redevances_a_ventiler"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_55_disabled_transferts_federaux_pas_taxes_provinciales(self):
  d=fixtures()
  d["registre"]["regles"]["transferts_federaux_pas_taxes_provinciales"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_56_disabled_transferts_non_garantis_souverainete(self):
  d=fixtures()
  d["registre"]["regles"]["transferts_non_garantis_souverainete"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_57_disabled_ne_pas_double_compter_sous_totaux(self):
  d=fixtures()
  d["registre"]["regles"]["ne_pas_double_compter_sous_totaux"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_58_disabled_service_dette_dans_depenses_totales(self):
  d=fixtures()
  d["registre"]["regles"]["service_dette_dans_depenses_totales"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_59_disabled_provision_et_fonds_generations_distincts(self):
  d=fixtures()
  d["registre"]["regles"]["provision_et_fonds_generations_distincts"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_60_disabled_taux_nova_non_deductible_des_chiffres_actuels(self):
  d=fixtures()
  d["registre"]["regles"]["taux_nova_non_deductible_des_chiffres_actuels"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_61_fake_sov_tax(self):
  d=fixtures()
  d["registre"]["lignes"][0]["recette_nova_mcad"]="1500"
  with self.assertRaises(ValueError):m.validate(d)
 def test_62_fake_elimination(self):
  d=fixtures()
  d["registre"]["lignes"][1]["reforme_adoptee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_63_fake_expert(self):
  d=fixtures()
  d["registre"]["lignes"][2]["avis_signe"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_64_fake_federal_transfer_as_tax(self):
  d=fixtures()
  d["registre"]["lignes"][17]["juridiction"]="BUDGET_QUEBEC"
  with self.assertRaises(ValueError):m.validate(d)
 def test_65_falsified_expense(self):
  d=fixtures()
  d["registre"]["depenses_officielles_mcad"]["service_dette"]="0"
  with self.assertRaises(ValueError):m.validate(d)
 def test_66_falsified_revenues(self):
  d=fixtures()
  d["registre"]["sous_totaux_officiels_mcad"]["revenus_totaux"]="200000"
  with self.assertRaises(ValueError):m.validate(d)
 def test_67_falsified_partition(self):
  d=fixtures()
  d["registre"]["compartiments_non_additionner_aux_lignes"]["impots_revenu_quebec_existants_mcad"]="99999"
  with self.assertRaises(ValueError):m.validate(d)
 def test_68_no_federal_exclusions(self):
  d=fixtures()
  d["registre"]["perimetre"]["taxes_federales_hors_perimetre"]=False
  with self.assertRaises(ValueError):m.validate(d)
 def test_69_invented_consolidation(self):
  d=fixtures()
  d["lacunes"]["bilan"]["consolidation_tous_niveaux"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_70_invented_municipal_import(self):
  d=fixtures()
  d["lacunes"]["source_municipale_candidate"]["selection_geographie_annee_et_nature_reelle"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_71_fake_p52a_go(self):
  d=fixtures()
  d["p52a"]["automatic_go"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_72_fake_p52z_certification(self):
  d=fixtures()
  d["p52z"]["bilan"]["decision"]="GO"
  with self.assertRaises(ValueError):m.validate(d)
 def test_73_fake_p52c_total(self):
  d=fixtures()
  d["p52c"]["lignes_revenus"][0]["valeur_mcad"]="0"
  with self.assertRaises(ValueError):m.validate(d)
 def test_74_fake_p52j_f09(self):
  d=fixtures()
  d["p52j"]["validation_de_nature"]["preuve_F09_independamment_attestee"]=True
  with self.assertRaises(ValueError):m.validate(d)
 def test_75_fake_completeness(self):
  d=fixtures()
  d["registre"]["bilan"]["montants_nova_inconnus"]=0
  with self.assertRaises(ValueError):m.validate(d)
if __name__=="__main__":
 unittest.main()
