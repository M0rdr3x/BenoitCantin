"""P53I: source version drift, expense-side MAMH codes, no unsupported netting."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"auditer_revision_et_charges_municipales_nova_p53i.py"
spec=importlib.util.spec_from_file_location("p53i",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RevisionsEtChargesTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.old,cls.new,cls.desc=m.get_sources()
  cls.data={k:m.load_json(p) for k,p in m.FILES.items()}
 @classmethod
 def stats(cls):
  return m.audit(copy.deepcopy(cls.data),cls.old,cls.new,cls.desc)
 def reject(self,fn):
  d=copy.deepcopy(self.data);fn(d)
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_01_baseline_no_go(self):
  self.assertEqual(self.stats()["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_previous_1343_retained(self):
  self.assertEqual(self.stats()["ancienne_version_organismes"],1343)
 def test_03_new_1344_current(self):
  self.assertEqual(self.stats()["nouvelle_version_organismes"],1344)
 def test_04_sole_new_code(self):
  self.assertEqual(self.stats()["organisme_ajoute"],"39135")
 def test_05_no_old_shared_field_changed(self):
  self.assertEqual(self.stats()["anciens_organismes_modifies_sur_18_champs"],0)
 def test_06_current_2024_total(self):
  self.assertEqual(self.stats()["revenus_bruts_nouvelle_version_cad"],41666627807)
 def test_07_current_2024_taxes(self):
  self.assertEqual(self.stats()["taxes_municipales_brutes_cad"],17339561033)
 def test_08_current_2024_quotes_parts(self):
  self.assertEqual(self.stats()["quotes_parts_recues_cad"],3148209097)
 def test_09_payer_contributions_not_netting(self):
  self.assertEqual(self.stats()["charges_quotes_parts_organismes_municipaux_cad"],2526339827)
 def test_10_non_net_gap_not_savings(self):
  self.assertEqual(self.stats()["ecart_quotes_recues_moins_charges_cad"],621869270)
 def test_11_no_pairs_or_deductions(self):
  r=self.stats()
  self.assertEqual(r["appariements_transactionnels_confirmes"],0)
  self.assertIsNone(r["eliminations_certifiees_cad"])
 def test_12_no_independent_reform_certification(self):
  r=self.stats()
  self.assertEqual(r["preuves_F01_F20_non_validees"],20)
  self.assertEqual(r["parametres_Nova_inconnus"],1320)
 def test_13_old_sources_integrity(self):
  self.assertEqual(len(self.old),1343)
  self.assertEqual(len(self.new),1344)
  self.assertEqual(len(self.desc),5)
 def test_14_existing_18_fields_equal(self):
  old={r["cod_geo"]:r for r in self.old}
  new={r["cod_geo"]:r for r in self.new}
  self.assertEqual(set(new)-set(old),{"39135"})
  self.assertTrue(all([r[k] for k in m.OLD_COLUMNS]==
                       [new[code][k] for k in m.OLD_COLUMNS]
                       for code,r in old.items()))
 def test_15_added_Saint_Valere(self):
  added=m.compare(self.old,self.new)
  self.assertEqual(added["nom_organisme"],"Saint-Valère")
  self.assertEqual(added["CRIIX00405"],"2951221")
 def test_16_dictionary_codes(self):
  self.assertEqual([x["Code de postes"] for x in self.desc],m.CODES)
 def test_17_expense_quotes_by_payee_class(self):
  stats,_=m.calculate(self.new)
  self.assertEqual(stats["CRIIX00681"]["montant_signe_cad"],"2526339827")
 def test_18_expense_transfers_by_class(self):
  stats,_=m.calculate(self.new)
  self.assertEqual(stats["CRIIX00682"]["montant_signe_cad"],"53587714")
 def test_19_two_other_municipal_charge_categories(self):
  stats,_=m.calculate(self.new)
  self.assertEqual(stats["CRIIX00683"]["montant_signe_cad"],"254824938")
  self.assertEqual(stats["CRIIX00685"]["montant_signe_cad"],"386907793")
 def test_20_other_org_charges(self):
  stats,_=m.calculate(self.new)
  self.assertEqual(stats["CRIIX00686"]["montant_signe_cad"],"816798326")
 def test_21_preserve_negative_values(self):
  st,_=m.calculate(self.new)
  self.assertEqual([st[k]["negatifs"] for k in m.CODES],[0,0,1,1,1])
 def test_22_preserve_blanks(self):
  st,_=m.calculate(self.new)
  self.assertEqual([st[k]["blancs"] for k in m.CODES],[246,1267,1010,1131,718])
 def test_23_new_local_record_count(self):
  self.assertEqual(sum(x["type_org"]=="Municipalité locale" for x in self.new),1095)
 def test_24_new_complementary_count(self):
  self.assertEqual(sum(x["type_org"]!="Municipalité locale" for x in self.new),249)
 def test_25_2024_not_budget_2026_27(self):
  self.assertTrue(self.data["p53i"]["garde_fous"]["annee_financiere_2024_pas_budget_2026_2027"])
 def test_26_no_gains_from_difference(self):
  self.assertTrue(self.data["p53i"]["garde_fous"]["difference_621869270_n_est_pas_economie"])
 def test_27_old_snapshot_stable(self):
  self.assertEqual(self.data["p53g"]["totaux_bruts_cad"]["revenus"],"41663676586")
 def test_28_new_snapshot_bytes(self):
  self.assertEqual(m.NEW.stat().st_size,188879)
 def test_29_new_dictionary_bytes(self):
  self.assertEqual(m.DESC.stat().st_size,1634)
 def test_30_cli_report_no_go(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/"summary.json"
   self.assertEqual(m.main(["--rapport",str(out)]),0)
   self.assertEqual(json.loads(out.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_31_cli_strict_refuses_pairs(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/"summary.json"
   self.assertEqual(m.main(["--rapport",str(out),"--exiger-appariements"]),3)
 def test_32_cli_missing_snapshot_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(m.main(["--nouveau",str(Path(d)/"missing.csv")]),2)
 def test_33_cli_refuses_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/"summary.json"
   self.assertEqual(m.main(["--rapport",str(out)]),0)
   self.assertEqual(m.main(["--rapport",str(out)]),2)
 def test_34_snapshot_tampering_detected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"s.csv"
   raw=m.NEW.read_bytes()
   p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
   with self.assertRaises(ValueError):
    m.get_sources(new_path=p)
 def test_35_dictionary_tampering_detected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"des.json"
   raw=m.DESC.read_bytes()
   p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
   with self.assertRaises(ValueError):
    m.get_sources(desc_path=p)
 def test_36_actual_old_revenue_gap_matches_one_added_municipality(self):
  new_sum=sum(int(x["CRIIX00405"]) for x in self.new)
  old_sum=sum(int(x["CRIIX00405"]) for x in self.old)
  self.assertEqual(new_sum-old_sum,2951221)
 def test_37_report_not_personal_data(self):
  r=json.dumps(self.stats(),ensure_ascii=False)
  for bad in ("https://","@","adresse_postale","numero_assurance_sociale"):
   self.assertNotIn(bad,r)
 def test_38_guard_1_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["versions_anciennes_maintenues_sans_recriture"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_39_guard_2_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["nouvelle_archive_derivee_non_equivalente_original_integral"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_40_guard_3_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["annee_financiere_2024_pas_budget_2026_2027"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_41_guard_4_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["nouvel_organisme_ne_prouve_pas_hausse_economique_2024"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_42_guard_5_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["identite_codes_ne_prouve_pas_identite_transactionnelle"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_43_guard_6_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["montants_recus_ne_sont_pas_eliminations"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_44_guard_7_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["montants_depenses_ne_sont_pas_eliminations"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_45_guard_8_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["difference_621869270_n_est_pas_economie"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_46_guard_9_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["champs_vides_distincts_de_zero"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_47_guard_10_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["charges_negatives_preservees"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_48_guard_11_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["pas_de_double_cumul_niveaux_de_gouvernement"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_49_guard_12_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["pas_de_taux_fiscal_Nova_inferé"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_50_guard_13_disabled(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["garde_fous"]["pas_de_preuve_F01_F20_auto_validée"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_51_expense_1_falsified(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["charges_reelles_comptables"][0]["montant_signe_cad"]="0"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_52_expense_2_falsified(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["charges_reelles_comptables"][1]["montant_signe_cad"]="0"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_53_expense_3_falsified(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["charges_reelles_comptables"][2]["montant_signe_cad"]="0"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_54_expense_4_falsified(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["charges_reelles_comptables"][3]["montant_signe_cad"]="0"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_55_expense_5_falsified(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["charges_reelles_comptables"][4]["montant_signe_cad"]="0"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_56_fake_source_original_archived(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["historique_provenance"]["originaux_complets_archives_dans_git"]=True
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_57_fake_accountant_signed(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["historique_provenance"]["avis_comptable_independant_signé_obtenu"]=True
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_58_new_raw_source_hash_wrong(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["historique_provenance"]["nouvelle_source_2026_10_22_sha256"]="fff"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_59_new_csv_sha_wrong(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["archives_derivées"]["nouvelle_selection_sha256"]="bbb"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_60_new_dict_sha_wrong(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["archives_derivées"]["dictionnaire_5_charges_sha256"]="zzz"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_61_pretend_extra_revisions(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["variation_et_population"]["anciens_codes_avec_revision_sur_18_colonnes"]=1
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_62_pretend_other_columns_audited(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["variation_et_population"]["exhaustivite_revision_autres_colonnes_non_extraite"]=False
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_63_fake_new_code(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["variation_et_population"]["nouveaux_codes"]=["39200"]
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_64_fake_current_total(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["totaux_recettes_2024_mis_a_jour"]["total_revenus_tous_organismes_cad"]="41000000000"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_65_fake_nova_yield(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["totaux_recettes_2024_mis_a_jour"]["projection_budget_2026_2027_mcad"]="90000"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_66_fake_2024_adjusted_net(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["totaux_recettes_2024_mis_a_jour"]["montant_net_apres_elimination_cad"]="100"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_67_fake_consolidated_2024_amount(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["totaux_recettes_2024_mis_a_jour"]["montant_apparemment_double_compte_certifie_cad"]="621869270"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_68_claimed_pairing(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["confrontation_non_transactionnelle"]["exactitude_appariement_transactionnel_etablie"]=True
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_69_gap_as_savings(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["confrontation_non_transactionnelle"]["montant_eliminable_deduit_de_l_ecart_cad"]="621869270"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_70_false_new_added(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["nouvelle_ligne_municipale"]["revenus_totaux_cad"]="0"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_71_false_saint_code(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["nouvelle_ligne_municipale"]["code"]="99999"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_72_fake_eliminations(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["etat"]["eliminations_certifiees"]=1
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_73_fake_politic_adoption(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["etat"]["adoption_autorisee"]=True
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_74_fake_fiscal_rate(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["etat"]["taux_Nova_adoptes"]=1
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_75_fake_p53g_coverage(self):
  d=copy.deepcopy(self.data)
  d["p53g"]["totaux_bruts_cad"]["revenus"]="1500"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_76_fake_p53h_go(self):
  d=copy.deepcopy(self.data)
  d["p53h"]["bilan"]["decision"]="GO"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_77_fake_p53e_go(self):
  d=copy.deepcopy(self.data)
  d["p53e"]["bilan"]["decision"]="GO"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_78_fake_p52a_validated(self):
  d=copy.deepcopy(self.data)
  d["p52a"]["required_evidence"][3]["statut"]="VALIDE"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_79_fake_source_path(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["archives_derivées"]["nouvelle_selection"]="fake.csv"
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_80_fake_zero_unknowns(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["etat"]["montants_Nova_inconnus"]=0
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)
 def test_81_fake_extra_experts(self):
  d=copy.deepcopy(self.data)
  d["p53i"]["etat"]["appariements_transactionnels_confirmes"]=1
  with self.assertRaises(ValueError):
   m.audit(d,self.old,self.new,self.desc)

if __name__=="__main__":
 unittest.main()
