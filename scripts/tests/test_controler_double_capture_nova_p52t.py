"""P52T: captures synthétiques A et B, frontières NO_GO et chaîne de provenance."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"controler_double_capture_nova_p52t.py"
spec=importlib.util.spec_from_file_location("p52t",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def source():
 return {k:m.read(path) for k,path in m.FILES.items()}
def baseline():
 return m.baseline_check(source())
def captured(src=None):
 src=src or baseline()
 return {
  "jalon":"P52S","schema_version":"P52S-1","mode":"sonde",
  "sources_attendues":2,"tentatives_reseau_effectuees":2,
  "flux_pdf_recus_non_authentifies":2,"sources_non_recuperees":0,
  "reçus_techniques":[{
    "id":a["id"],"statut":"OCTETS_PDF_RECUS_HTTPS_NON_AUTHENTIFIES",
    "sha256_octets_recus":a["sha256_octets_recus"],
    "taille_octets":a["taille_octets"],
    "date_utc_tentative":"2026-10-20T21:00:00+00:00",
    "categorie_echec":None,
    "archive_permanente_obtenue":False,
    "signature_ministerielle_verifiee":False,
    "type_mime_recu":"application/pdf",
    "validation_tls_client_standard":True,
    "controle_structurel_pdf_complet":False,
  } for a in src],
  "archives_officielles_certifiees":0,
  "avis_independants_F09_obtenus":0,
  "preuves_F01_F20_validees":0,
  "publication_autorisee":False,
  "fusion_autorisee":False,
  "adoption_autorisee":False,
  "decision":"NO_GO_AUTOMATIQUE"
 }
def env(role="A",run="1234",sha="a"*40):
 return {"GITHUB_RUN_ID":run,"GITHUB_RUN_ATTEMPT":"1",
         "GITHUB_SHA":sha,"GITHUB_JOB":f"capture-{role.lower()}",
         "RUNNER_OS":"Linux"}
def wraps():
 cap=captured()
 return m.wrap("A",cap,env("A")),m.wrap("B",cap,env("B"))
class DoubleCaptureTest(unittest.TestCase):
 def rejects_plan(self,edit):
  d=source();edit(d)
  with self.assertRaises(ValueError):m.baseline_check(d)
 def rejects_capture(self,edit):
  c=captured();edit(c)
  with self.assertRaises(ValueError):m.check_capture(c)
 def rejects_pair(self,edit):
  a,b=wraps();edit(a,b)
  with self.assertRaises(ValueError):m.compare(baseline(),a,b)
 def test_01_two_official_reference_ids(self):
  self.assertEqual(tuple(x["id"] for x in baseline()),m.IDS)
 def test_02_fixed_p52s_hashes(self):
  self.assertEqual(baseline()[0]["sha256_octets_recus"],m.EXPECTED["DISC2026_T3"][0])
 def test_03_p52s_pdf_sizes(self):
  self.assertEqual(baseline()[1]["taille_octets"],5341975)
 def test_04_default_plan_no_human(self):
  self.assertFalse(source()["plan"]["procedures"][0]["humain_independant"])
 def test_05_no_source_archive(self):
  self.assertEqual(source()["plan"]["etat"]["originaux_pdf_archives"],0)
 def test_06_capture_fixtures_synthetic_two(self):
  self.assertEqual(len(m.check_capture(captured())),2)
 def test_07_agreement_with_both_jobs_and_baseline(self):
  a,b=wraps()
  v=m.compare(baseline(),a,b)
  self.assertTrue(v["integrite_binaire_triple_confirmee"])
  self.assertEqual(v["concordances_trois_references"],2)
 def test_08_no_legal_adoption_even_two_match(self):
  a,b=wraps()
  v=m.compare(baseline(),a,b)
  self.assertFalse(v["adoption_autorisee"])
  self.assertFalse(v["verification_independante_humaine_obtenue"])
 def test_09_distinct_jobs(self):
  a,b=wraps()
  self.assertNotEqual(a["github_job"],b["github_job"])
 def test_10_detect_different_hash_between_jobs(self):
  a,b=wraps()
  b["capture"]["reçus_techniques"][0]["sha256_octets_recus"]="0"*64
  result=m.compare(baseline(),a,b)
  self.assertEqual(result["resultats"][0]["etat"],"DIVERGENCE_ENTRE_TACHES")
 def test_11_detect_different_size_between_jobs(self):
  a,b=wraps();b["capture"]["reçus_techniques"][1]["taille_octets"]+=1
  self.assertEqual(m.compare(baseline(),a,b)["incoherences_techniques"],1)
 def test_12_detect_both_changed_since_P52S(self):
  a,b=wraps()
  for w in (a,b):w["capture"]["reçus_techniques"][0]["sha256_octets_recus"]="1"*64
  self.assertEqual(m.compare(baseline(),a,b)["resultats"][0]["etat"],"DERIVE_DEPUIS_P52S")
 def test_13_detect_one_failed_capture(self):
  a,b=wraps()
  obj=b["capture"]["reçus_techniques"][0]
  obj["statut"]="SOURCE_NON_RECUPEREE"
  obj["sha256_octets_recus"]=None
  obj["taille_octets"]=None
  obj["categorie_echec"]="URLError"
  for field in m.SUCCESS:obj.pop(field)
  b["capture"]["flux_pdf_recus_non_authentifies"]=1
  b["capture"]["sources_non_recuperees"]=1
  self.assertEqual(m.compare(baseline(),a,b)["resultats"][0]["etat"],"CAPTURE_MANQUANTE")
 def test_14_fail_if_same_github_job(self):
  self.rejects_pair(lambda a,b:b.update(github_job="capture-a"))
 def test_15_fail_if_different_run_id(self):
  self.rejects_pair(lambda a,b:b.update(github_run_id=2))
 def test_16_fail_if_different_attempt(self):
  self.rejects_pair(lambda a,b:b.update(github_run_attempt=2))
 def test_17_fail_if_different_commit(self):
  self.rejects_pair(lambda a,b:b.update(github_sha="f"*40))
 def test_18_fail_fake_human_reviewer(self):
  self.rejects_pair(lambda a,b:a.update(reviewer_human=True))
 def test_19_fail_fake_official_signature(self):
  self.rejects_pair(lambda a,b:a.update(publisher_signature_verified=True))
 def test_20_fail_fake_archive(self):
  self.rejects_pair(lambda a,b:b.update(archive_permanent=True))
 def test_21_fail_personal_extra_field(self):
  self.rejects_pair(lambda a,b:a.update(telephone_personnel="privé"))
 def test_22_capture_wrong_source_order(self):
  self.rejects_capture(lambda c:c["reçus_techniques"].reverse())
 def test_23_capture_short_sha(self):
  self.rejects_capture(lambda c:c["reçus_techniques"][0].update(sha256_octets_recus="xxx"))
 def test_24_capture_forged_signature(self):
  self.rejects_capture(lambda c:c["reçus_techniques"][0].update(signature_ministerielle_verifiee=True))
 def test_25_capture_unexpected_pii(self):
  self.rejects_capture(lambda c:c["reçus_techniques"][0].update(citoyen="inconnu"))
 def test_26_capture_wrong_mimetype(self):
  self.rejects_capture(lambda c:c["reçus_techniques"][0].update(type_mime_recu="text/html"))
 def test_27_capture_missing_utc(self):
  self.rejects_capture(lambda c:c["reçus_techniques"][0].update(date_utc_tentative="2026-10-20T12:00:00"))
 def test_28_capture_wrong_time_format(self):
  self.rejects_capture(lambda c:c["reçus_techniques"][0].update(date_utc_tentative="yesterday"))
 def test_29_capture_size_over_cap(self):
  self.rejects_capture(lambda c:c["reçus_techniques"][0].update(taille_octets=50_000_001))
 def test_30_capture_bad_success_count(self):
  self.rejects_capture(lambda c:c.update(flux_pdf_recus_non_authentifies=1))
 def test_31_capture_false_f09_proof(self):
  self.rejects_capture(lambda c:c.update(avis_independants_F09_obtenus=1))
 def test_32_capture_any_adoption_refused(self):
  self.rejects_capture(lambda c:c.update(adoption_autorisee=True))
 def test_33_without_github_environment_refused(self):
  with self.assertRaises(ValueError):m.wrap("A",captured(),{})
 def test_34_wrong_github_job_label_refused(self):
  with self.assertRaises(ValueError):m.wrap("A",captured(),env("B"))
 def test_35_wrong_sha_refused(self):
  with self.assertRaises(ValueError):m.wrap("A",captured(),env("A",sha="a"))
 def test_36_env_run_not_number_refused(self):
  with self.assertRaises(ValueError):m.wrap("A",captured(),env("A",run="not-a-number"))
 def test_37_source_plan_go_refused(self):
  self.rejects_plan(lambda d:d["plan"]["etat"].update(adoption_autorisee=True))
 def test_38_source_p52k_fake_hash_refused(self):
  self.rejects_plan(lambda d:d["p52k"]["fichiers_source"][0].update(empreinte_sha256_pdf_original="a"*64))
 def test_39_source_p52a_fake_expert_refused(self):
  self.rejects_plan(lambda d:d["p52a"]["required_evidence"][8].update(preuve_independante_obtenue=True))
 def test_40_source_baseline_tampered_refused(self):
  self.rejects_plan(lambda d:d["baseline"]["sources"][0].update(sha256_octets_recus="0"*64))
 def test_41_source_required_guard_refused(self):
  self.rejects_plan(lambda d:d["plan"]["controles"].update(aucune_transformation_automatique_de_F09=False))
 def test_42_report_no_private_urls_or_pdf_data(self):
  a,b=wraps();o=json.dumps(m.compare(baseline(),a,b))
  for x in ("https://","%PDF","a"*64,"@example.com","cf89d3d8"):
   self.assertNotIn(x,o)
 def test_43_cli_audit_no_go(self):
  with tempfile.TemporaryDirectory() as tmp:
   target=Path(tmp)/"r.json"
   self.assertEqual(m.main(["audit","--rapport",str(target)]),0)
   self.assertEqual(json.loads(target.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_44_cli_expert_strict_refuses(self):
  with tempfile.TemporaryDirectory() as tmp:
   self.assertEqual(m.main(["audit","--exiger-expertise","--rapport",str(Path(tmp)/"r.json")]),3)
 def test_45_cli_missing_baseline_returns_two(self):
  with tempfile.TemporaryDirectory() as tmp:
   self.assertEqual(m.main(["audit","--baseline",str(Path(tmp)/"no.json")]),2)
 def test_46_cli_reports_not_overwritten(self):
  with tempfile.TemporaryDirectory() as tmp:
   target=Path(tmp)/"r.json"
   self.assertEqual(m.main(["audit","--rapport",str(target)]),0)
   self.assertEqual(m.main(["audit","--rapport",str(target)]),2)
 def test_47_cli_comparison_match_exits_zero(self):
  with tempfile.TemporaryDirectory() as tmp:
   a,b=wraps()
   ap=Path(tmp)/"a.json";bp=Path(tmp)/"b.json"
   ap.write_text(json.dumps(a));bp.write_text(json.dumps(b))
   out=Path(tmp)/"decision.json"
   self.assertEqual(m.main(["comparer","--a",str(ap),"--b",str(bp),
                            "--exiger-coherence","--rapport",str(out)]),0)
   self.assertTrue(json.loads(out.read_text())["integrite_binaire_triple_confirmee"])
 def test_48_cli_comparison_drift_returns_four(self):
  with tempfile.TemporaryDirectory() as tmp:
   a,b=wraps();b["capture"]["reçus_techniques"][0]["sha256_octets_recus"]="0"*64
   ap=Path(tmp)/"a.json";bp=Path(tmp)/"b.json"
   ap.write_text(json.dumps(a));bp.write_text(json.dumps(b))
   self.assertEqual(m.main(["comparer","--a",str(ap),"--b",str(bp),
                            "--exiger-coherence"]),4)
 def test_49_cli_without_two_capture_files_returns_two(self):
  self.assertEqual(m.main(["comparer"]),2)
 def test_50_cli_envelopper_requires_Github_environment(self):
  with tempfile.TemporaryDirectory() as tmp:
   cap=Path(tmp)/"raw.json";cap.write_text(json.dumps(captured()))
   self.assertEqual(m.main(["envelopper","--role","A","--capture",str(cap),
                            "--sortie",str(Path(tmp)/"a.json")]),2)
if __name__=="__main__":
 unittest.main()
