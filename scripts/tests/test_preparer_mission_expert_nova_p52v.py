"""P52V: epreuves adversariales du cahier F09, de ses 39 lignes et de l'export."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"preparer_mission_expert_nova_p52v.py"
spec=importlib.util.spec_from_file_location("p52v",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def docs():return {key:m.read(path) for key,path in m.FILES.items()}
class P52VMissionTests(unittest.TestCase):
 def reject(self,change):
  d=docs();change(d)
  with self.assertRaises(ValueError):m.verify(d)
 def test_01_original_mission_validated(self):
  self.assertEqual(m.verify(docs())["decision"],"NO_GO_AUTOMATIQUE")
 def test_02_39_review_positions(self):
  self.assertEqual(m.verify(docs())["positions_de_relecture_pret_a_transmettre"],39)
 def test_03_discours_29(self):
  self.assertEqual(m.verify(docs())["positions_discours"],29)
 def test_04_plan_ten(self):
  self.assertEqual(m.verify(docs())["positions_plan"],10)
 def test_05_three_inter_tables(self):
  self.assertEqual(m.verify(docs())["croisements_inter_tableaux_a_verifier"],3)
 def test_06_twelve_control_tasks(self):
  self.assertEqual(m.verify(docs())["controles_humains_non_executes"],12)
 def test_07_eight_deliverables(self):
  self.assertEqual(m.verify(docs())["livrables_experts_non_recus"],8)
 def test_08_no_candidate(self):
  self.assertEqual(m.verify(docs())["candidats_identifies_et_verifies"],0)
 def test_09_no_expert_signed(self):
  self.assertEqual(m.verify(docs())["avis_humains_reellement_signes"],0)
 def test_10_twenty_unvalidated_evidences(self):
  self.assertEqual(m.verify(docs())["preuves_F01_F20_non_validees"],20)
 def test_11_1320_values_unknown(self):
  self.assertEqual(m.verify(docs())["donnees_financieres_inconnues"],1320)
 def test_12_csv_40_rows_including_header(self):
  data=list(csv.reader(io.StringIO(m.csv_rows(docs()))))
  self.assertEqual(len(data),40)
 def test_13_csv_containing_only_blank_human_columns(self):
  rows=list(csv.reader(io.StringIO(m.csv_rows(docs()))))
  self.assertTrue(all(not any(cell for cell in row[5:]) for row in rows[1:]))
 def test_14_csv_last_position(self):
  self.assertEqual(list(csv.reader(io.StringIO(m.csv_rows(docs()))))[-1][0],"PLAN-10")
 def test_15_three_shared_values_twice(self):
  r=docs()["mission"]["points_de_relecture"]
  for name in ("revenus_autonomes","transferts_federaux","revenus_totaux"):
   self.assertEqual(sum(x["identifiant_ligne_P52J"]==name for x in r),2)
 def test_16_repeated_non_unique_revenues_divers(self):
  self.assertEqual(sum(x["identifiant_ligne_P52J"]=="revenus_divers"
                       for x in docs()["mission"]["points_de_relecture"]),2)
 def test_17_assembly_source_link(self):
  self.assertEqual(docs()["mission"]["references_officielles_a_consulter"][1]["url"],m.URLS[1])
 def test_18_CPA_register_link(self):
  self.assertEqual(docs()["mission"]["references_officielles_a_consulter"][2]["url"],m.URLS[2])
 def test_19_false_review_status_rejected(self):
  self.reject(lambda d:d["mission"]["points_de_relecture"][0].update(statut_relecture_humaine="ATTESTE"))
 def test_20_false_expert_amount_rejected(self):
  self.reject(lambda d:d["mission"]["points_de_relecture"][1].update(montant_confirme_par_expert="9412"))
 def test_21_fake_signature_rejected(self):
  self.reject(lambda d:d["mission"]["points_de_relecture"][2].update(signature_humaine_authentifiee=True))
 def test_22_modified_original_amount_rejected(self):
  self.reject(lambda d:d["mission"]["points_de_relecture"][6].update(valeur_attendue_lecture_non_certifiee="9999"))
 def test_23_renamed_row_rejected(self):
  self.reject(lambda d:d["mission"]["points_de_relecture"][8].update(identifiant_ligne_P52J="TVQ"))
 def test_24_missing_position_rejected(self):
  self.reject(lambda d:d["mission"]["points_de_relecture"].pop())
 def test_25_reordered_lines_rejected(self):
  self.reject(lambda d:d["mission"]["points_de_relecture"].reverse())
 def test_26_insert_personal_field_rejected(self):
  self.reject(lambda d:d["mission"]["points_de_relecture"][0].update(nom="identite interdite"))
 def test_27_fake_human_control_rejected(self):
  self.reject(lambda d:d["mission"]["controles_contradictoires"][0].update(statut="EXECUTE"))
 def test_28_fake_received_deliverable_rejected(self):
  self.reject(lambda d:d["mission"]["livrables_au_mandat"][0].update(etat="RECU"))
 def test_29_fake_candidate_rejected(self):
  self.reject(lambda d:d["mission"]["selection_candidat"].update(nom_candidat="Expert imaginaire"))
 def test_30_fake_CPA_verified_rejected(self):
  self.reject(lambda d:d["mission"]["selection_candidat"].update(qualification_verifiee=True))
 def test_31_fake_signed_contract_rejected(self):
  self.reject(lambda d:d["mission"]["selection_candidat"].update(contrat_signe=True))
 def test_32_fictitious_budget_rejected(self):
  self.reject(lambda d:d["mission"]["selection_candidat"].update(budget_mandat_autorise_cad=10000))
 def test_33_fake_expense_rejected(self):
  self.reject(lambda d:d["mission"]["selection_candidat"].update(fonds_engages_cad=1))
 def test_34_fake_official_source_verification_rejected(self):
  self.reject(lambda d:d["mission"]["references_officielles_a_consulter"][1].update(verification_edition_sous_mandat=True))
 def test_35_fake_independent_archive_rejected(self):
  self.reject(lambda d:d["mission"]["audit_et_protection"].update(copie_originale_archivée_hors_depot=True))
 def test_36_fake_go_rejected(self):
  self.reject(lambda d:d["mission"]["audit_et_protection"].update(adoption_autorisee=True))
 def test_37_fake_p52a_evidence_rejected(self):
  self.reject(lambda d:d["p52a"]["required_evidence"][8].update(statut="VALIDE"))
 def test_38_fake_p52n_mandate_rejected(self):
  self.reject(lambda d:d["p52n"]["mandats"][8].update(expert_mandate=True))
 def test_39_fake_p52q_expert_rejected(self):
  self.reject(lambda d:d["p52q"]["dossiers"][5].update(expert_reel_mandate=True))
 def test_40_fake_p52u_signed_report_rejected(self):
  self.reject(lambda d:d["p52u"]["relecture_humaine"].update(avis_independant_signe=True))
 def test_41_false_p52j_proof_rejected(self):
  self.reject(lambda d:d["p52j"]["validation_de_nature"].update(preuve_F09_independamment_attestee=True))
 def test_42_corrupt_upstream_figure_rejected(self):
  self.reject(lambda d:d["p52u"]["documents"][0]["valeurs_attendues"][0].update(valeur_mcad="999"))
 def test_43_cli_audit_no_go(self):
  with tempfile.TemporaryDirectory() as temp:
   out=Path(temp)/"audit.json"
   self.assertEqual(m.main(["--rapport",str(out)]),0)
   self.assertEqual(json.loads(out.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_44_cli_export_csv_readable(self):
  with tempfile.TemporaryDirectory() as temp:
   out=Path(temp)/"grille.csv"
   self.assertEqual(m.main(["--export-csv",str(out)]),0)
   self.assertEqual(len(list(csv.reader(out.open(encoding="utf-8")))),40)
 def test_45_cli_exiger_expert_code_three(self):
  with tempfile.TemporaryDirectory() as temp:
   out=Path(temp)/"audit.json"
   self.assertEqual(m.main(["--exiger-expertise","--rapport",str(out)]),3)
 def test_46_cli_missing_schema_code_two(self):
  with tempfile.TemporaryDirectory() as temp:
   self.assertEqual(m.main(["--mission",str(Path(temp)/"missing.json")]),2)
 def test_47_cli_never_overwrites(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/"audit.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(m.main(["--rapport",str(p)]),2)
 def test_48_cli_same_report_csv_path_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/"same.json"
   self.assertEqual(m.main(["--rapport",str(p),"--export-csv",str(p)]),2)
 def test_49_summary_excludes_urls_and_data_lines(self):
  s=json.dumps(m.verify(docs()))
  for forbidden in ("https://","50800","166492","cf89d3d8","@example"):
   self.assertNotIn(forbidden,s)
 def test_50_csv_no_private_identity(self):
  t=m.csv_rows(docs())
  self.assertNotIn("nom_candidat",t)
  self.assertNotIn("signature_humaine",t)
if __name__=="__main__":
 unittest.main()
