"""P52U : scenarios contradictoires, schema, preuves fictives et texte PDF."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
p=ROOT/"scripts"/"valider_pages_budget_nova_p52u.py"
spec=importlib.util.spec_from_file_location("nova_p52u",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def load():
 return {k:m.read_json(path) for k,path in m.FILES.items()}
def list_values(doc):
 return " ".join(str(int(x["valeur_mcad"])) for x in doc["valeurs_attendues"])
def sample_text(doc):
 return doc["titre_tableau"]+" 2026-2027 Revenus\n"+list_values(doc).replace(" ", "\n")
class P52UPDFTests(unittest.TestCase):
 def reject(self,change):
  d=load()
  change(d)
  with self.assertRaises(ValueError):m.validate(d)
 def test_01_schema_has_two_sources(self):
  self.assertEqual(len(m.validate(load())),2)
 def test_02_29_discours_expected(self):
  self.assertEqual(len(m.validate(load())[0]["valeurs_attendues"]),29)
 def test_03_10_f2_expected(self):
  self.assertEqual(len(m.validate(load())[1]["valeurs_attendues"]),10)
 def test_04_39_total_expected(self):
  self.assertEqual(sum(len(x["valeurs_attendues"]) for x in m.validate(load())),39)
 def test_05_2026_pdf_page_numbers(self):
  self.assertEqual([x["pages_attendues"] for x in m.validate(load())],[34,426])
 def test_06_expected_page_indices(self):
  self.assertEqual([x["page_tableau_pdf_zero"] for x in m.validate(load())],[29,277])
 def test_07_reference_sha_unchanged(self):
  self.assertEqual(m.validate(load())[0]["sha256_attendu_octets_recus"],
   "cf89d3d8d448cfa4155e2370be8226a904d393205f64962d23f45a40749acbfa")
 def test_08_audit_offline_does_not_claim_pdf_parsing(self):
  out=m.audit(load())
  self.assertEqual(out["documents_controles"],0)
  self.assertEqual(out["mode"],"schema_seul")
 def test_09_offline_no_go(self):
  self.assertEqual(m.audit(load())["decision"],"NO_GO_AUTOMATIQUE")
 def test_10_no_human_expert_claimed(self):
  self.assertFalse(m.audit(load())["expert_independant_mandate"])
 def test_11_tokens_normalize_french_separator(self):
  vals,_=m.tokens("Total 166 492 32\u00a0131 et 134\u202f361")
  self.assertTrue({"166492","32131","134361"}<=vals)
 def test_12_negative_sign_kept(self):
  vals,_=m.tokens("Déficit \u2212 8 612 et dépenses −170 757")
  self.assertTrue({"-8612","-170757"}<=vals)
 def test_13_discours_all_29_synthetic_values(self):
  doc=m.validate(load())[0]
  out=m.check_text(sample_text(doc),doc)
  self.assertEqual(out["lignes_retrouvees"],29)
  self.assertEqual(out["lignes_absentes"],[])
 def test_14_plan_all_10_synthetic_values(self):
  doc=m.validate(load())[1]
  out=m.check_text(sample_text(doc),doc)
  self.assertEqual(out["lignes_retrouvees"],10)
 def test_15_table_heading_missing_rejected(self):
  doc=m.validate(load())[0]
  with self.assertRaises(ValueError):
   m.check_text("2026-2027 revenus "+list_values(doc),doc)
 def test_16_year_missing_rejected(self):
  doc=m.validate(load())[0]
  with self.assertRaises(ValueError):
   m.check_text(doc["titre_tableau"]+" revenus "+list_values(doc),doc)
 def test_17_missing_specific_value_detected(self):
  doc=m.validate(load())[0]
  text=sample_text(doc).replace("50800","")
  out=m.check_text(text,doc)
  self.assertIn("impot_particuliers",out["lignes_absentes"])
 def test_18_signed_negative_missing_detected(self):
  doc=m.validate(load())[1]
  text=sample_text(doc).replace("-8612","8612")
  self.assertIn("solde_budgetaire_loi_equilibre",
                m.check_text(text,doc)["lignes_absentes"])
 def test_19_repeated_values_are_not_proof_of_line_alignment(self):
  doc=m.validate(load())[1]
  self.assertFalse(m.check_text(sample_text(doc),doc)["relecture_humaine_independante"])
 def test_20_wrong_manifest_hash_rejected(self):
  self.reject(lambda x:x["manifest"]["documents"][0].update(sha256_attendu_octets_recus="a"*64))
 def test_21_wrong_manifest_size_rejected(self):
  self.reject(lambda x:x["manifest"]["documents"][1].update(taille_attendue_octets=1))
 def test_22_fake_signoff_rejected(self):
  self.reject(lambda x:x["manifest"]["relecture_humaine"].update(avis_independant_signe=True))
 def test_23_fake_expert_name_rejected(self):
  self.reject(lambda x:x["manifest"]["relecture_humaine"].update(nom_du_relecteur="Fictif"))
 def test_24_false_mandate_rejected(self):
  self.reject(lambda x:x["manifest"]["relecture_humaine"].update(mandat_reel_verifie=True))
 def test_25_fake_adoption_rejected(self):
  self.reject(lambda x:x["manifest"]["autorisations"].update(adoption=True))
 def test_26_fake_P52J_attestation_rejected(self):
  self.reject(lambda x:x["p52j"]["validation_de_nature"].update(preuve_F09_independamment_attestee=True))
 def test_27_fake_P52K_original_hash_rejected(self):
  self.reject(lambda x:x["p52k"]["fichiers_source"][0].update(empreinte_sha256_pdf_original="f"*64))
 def test_28_fake_P52A_preuve_rejected(self):
  self.reject(lambda x:x["p52a"]["required_evidence"][8].update(statut="VALIDE"))
 def test_29_fake_P52T_human_review_rejected(self):
  self.reject(lambda x:x["p52t"]["etat"].update(avis_signes=1))
 def test_30_source_url_not_authorized(self):
  with self.assertRaises(ValueError):m.fetch_pdf("https://evil.example/document.pdf")
 def test_31_pdf_wrong_size_rejected_before_parser(self):
  doc=m.validate(load())[0]
  with self.assertRaises(ValueError):m.inspect_octets(b"%PDF-1.7\n%%EOF",doc)
 def test_32_pdf_empty_input_rejected(self):
  doc=m.validate(load())[1]
  with self.assertRaises(ValueError):m.inspect_octets(b"",doc)
 def test_33_pdf_wrong_hash_rejected(self):
  doc=m.validate(load())[0].copy()
  data=b"%PDF-1.7\nsome data %%EOF"
  doc["taille_attendue_octets"]=len(data)
  with self.assertRaises(ValueError):m.inspect_octets(data,doc)
 def test_34_cli_offline_report_no_go(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/"report.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(json.loads(p.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_35_cli_exiger_expertise_code3(self):
  with tempfile.TemporaryDirectory() as temp:
   self.assertEqual(m.main(["--exiger-expertise","--rapport",str(Path(temp)/"r.json")]),3)
 def test_36_cli_missing_manifest_code2(self):
  with tempfile.TemporaryDirectory() as temp:
   self.assertEqual(m.main(["--manifest",str(Path(temp)/"absent.json")]),2)
 def test_37_cli_no_overwrite(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/"r.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(m.main(["--rapport",str(p)]),2)
 def test_38_no_sensitive_full_text_in_report(self):
  s=json.dumps(m.audit(load()),ensure_ascii=False)
  for value in ("https://","tableau F.2", "cf89d3d8", "50800","166492"):
   self.assertNotIn(value,s)
if __name__=="__main__":
 unittest.main()
