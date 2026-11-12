"""P52S : conservation de la provenance des deux empreintes reçues en GHA."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/"scripts"/"valider_constats_transports_nova_p52s.py"
spec=importlib.util.spec_from_file_location("p52s_constats",FILE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def fixtures():
    d={k:m.read(v) for k,v in m.FILES.items()}
    return d,m.verify(d)
def captured(sources):
    return {
      "schema_version":"P52S-1","mode":"sonde","sources_attendues":2,
      "archives_officielles_certifiees":0,
      "avis_independants_F09_obtenus":0,"adoption_autorisee":False,
      "decision":"NO_GO_AUTOMATIQUE",
      "reçus_techniques":[{
       "id":x["id"],"statut":"OCTETS_PDF_RECUS_HTTPS_NON_AUTHENTIFIES",
       "sha256_octets_recus":x["sha256_octets_recus"],
       "taille_octets":x["taille_octets"],
       "archive_permanente_obtenue":False,
       "signature_ministerielle_verifiee":False} for x in sources]}

class BaselineP52S(unittest.TestCase):
    def refuse(self,change):
        data,s=fixtures();change(data)
        with self.assertRaises(ValueError):m.verify(data)
    def test_01_two_real_snapshots(self):
        d,x=fixtures();self.assertEqual(len(x),2)
    def test_02_real_sha_consistent(self):
        d,x=fixtures();self.assertEqual(len(x[0]["sha256_octets_recus"]),64)
    def test_03_origin_record_linked(self):
        d,x=fixtures();self.assertIn("actions/runs/39491881661",d["recu"]["run_url"])
    def test_04_no_official_signing(self):
        d,x=fixtures();self.assertEqual(m.comparison(x)["copies_permanentes_archives"],0)
    def test_05_baseline_without_today_not_reproducible(self):
        d,x=fixtures();self.assertEqual(m.comparison(x)["flux_aujourdhui_identiques_a_octets_observes"],0)
    def test_06_match_with_new_bytes(self):
        d,x=fixtures();r=m.comparison(x,captured(x))
        self.assertEqual(r["flux_aujourdhui_identiques_a_octets_observes"],2)
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_07_new_bytes_hash_difference(self):
        d,x=fixtures();now=captured(x)
        now["reçus_techniques"][0]["sha256_octets_recus"]="0"*64
        self.assertEqual(m.comparison(x,now)["flux_aujourdhui_identiques_a_octets_observes"],1)
    def test_08_new_bytes_size_difference(self):
        d,x=fixtures();now=captured(x)
        now["reçus_techniques"][1]["taille_octets"]+=1
        self.assertEqual(m.comparison(x,now)["flux_aujourdhui_identiques_a_octets_observes"],1)
    def test_09_no_acquisition_never_certifies(self):
        d,x=fixtures();now=captured(x)
        now["reçus_techniques"][1].update(statut="SOURCE_NON_RECUPEREE",
          sha256_octets_recus=None,taille_octets=None)
        self.assertEqual(m.comparison(x,now)["flux_aujourdhui_identiques_a_octets_observes"],1)
    def test_10_fake_adoption_rejected(self):
        d,x=fixtures();now=captured(x);now["adoption_autorisee"]=True
        with self.assertRaises(ValueError):m.comparison(x,now)
    def test_11_fake_signature_rejected(self):
        d,x=fixtures();now=captured(x)
        now["reçus_techniques"][0]["signature_ministerielle_verifiee"]=True
        with self.assertRaises(ValueError):m.comparison(x,now)
    def test_12_unknown_baseline_hash_rejected(self):
        self.refuse(lambda d:d["recu"]["sources"][0].update(sha256_octets_recus="f"*64))
    def test_13_unknown_baseline_length_rejected(self):
        self.refuse(lambda d:d["recu"]["sources"][0].update(taille_octets=12))
    def test_14_fake_original_archive_rejected(self):
        self.refuse(lambda d:d["recu"]["sources"][0].update(archivage_permanent_obtenu=True))
    def test_15_fake_p52k_archive_rejected(self):
        self.refuse(lambda d:d["p52k"]["fichiers_source"][0].update(empreinte_sha256_pdf_original="f"*64))
    def test_16_fake_p52a_certification_rejected(self):
        self.refuse(lambda d:d["p52a"]["required_evidence"][8].update(statut="VALIDE"))
    def test_17_wrong_github_run_rejected(self):
        self.refuse(lambda d:d["recu"].update(run_id=99999))
    def test_18_clipped_timestamp_rejected(self):
        self.refuse(lambda d:d["recu"]["sources"][0].update(date_utc_tentative="2026-10-19T12:00:00+00:00"))
    def test_19_cli_baseline_NO_GO(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"report.json"
            self.assertEqual(m.main(["--rapport",str(p)]),0)
            self.assertFalse(json.loads(p.read_text())["adoption_autorisee"])
    def test_20_cli_exige_attestation_code_3(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--exiger-attestation","--rapport",str(Path(td)/"r.json")]),3)
    def test_21_cli_exige_reproductibilite_no_capture(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--exiger-reproductibilite","--rapport",str(Path(td)/"r.json")]),3)
    def test_22_cli_missing_snapshot_code_2(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--recu",str(Path(td)/"missing.json")]),2)
    def test_23_new_capture_cli_match(self):
        with tempfile.TemporaryDirectory() as td:
            d,x=fixtures()
            f=Path(td)/"now.json";f.write_text(json.dumps(captured(x)))
            out=Path(td)/"report.json"
            self.assertEqual(m.main(["--capture",str(f),"--exiger-reproductibilite","--rapport",str(out)]),0)
            self.assertEqual(json.loads(out.read_text())["flux_aujourdhui_identiques_a_octets_observes"],2)
    def test_24_new_capture_cli_drift(self):
        with tempfile.TemporaryDirectory() as td:
            d,x=fixtures();now=captured(x)
            now["reçus_techniques"][0]["sha256_octets_recus"]="0"*64
            f=Path(td)/"now.json";f.write_text(json.dumps(now))
            self.assertEqual(m.main(["--capture",str(f),"--exiger-reproductibilite"]),3)
    def test_25_report_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"r.json"
            self.assertEqual(m.main(["--rapport",str(out)]),0)
            self.assertEqual(m.main(["--rapport",str(out)]),2)
    def test_26_no_raw_source_url_report(self):
        d,x=fixtures()
        txt=json.dumps(m.comparison(x))
        self.assertNotIn("https://www.finances",txt)
if __name__=="__main__":
    unittest.main()
