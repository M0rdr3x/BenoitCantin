"""P55H — tests uniquement sur faux PDF et objets HTTP simulés (aucun réseau)."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import acquerir_pdfs_publics_nova_p55h as m


class FakeHTTP(io.BytesIO):
    def __init__(self, url, data, status=200, content_type="application/pdf",
                 declared_length=None, final_url=None):
        super().__init__(data)
        self.status = status
        self._url = url if final_url is None else final_url
        self.headers = {"Content-Type":content_type}
        if declared_length is not None:
            self.headers["Content-Length"] = declared_length
    def geturl(self):
        return self._url


class TestP55H(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_config = m.configuration()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.orig_source_data = m.p55b.SOURCE_DATA
        self.bodies = {
            self.orig_source_data[0][2]: b"%PDF-1.7 test-ville-2024\n%%EOF",
            self.orig_source_data[1][2]: b"%PDF-1.7 test-mamh-2024\n%%EOF",
        }
        alt = []
        for row in self.orig_source_data:
            new = list(row)
            data = self.bodies[row[2]]
            new[5] = len(data)
            new[6] = hashlib.sha256(data).hexdigest()
            alt.append(tuple(new))
        self.fake_data = tuple(alt)
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        return FakeHTTP(url,self.bodies[url],declared_length=str(len(self.bodies[url])))

    def with_fake_rows(self):
        return patch.object(m.p55b, "SOURCE_DATA", self.fake_data)

    def simulate(self, args, fake_rows=True, fetch=None):
        with patch.object(m, "configuration", return_value=self.base_config):
            if fake_rows:
                with self.with_fake_rows(), patch.object(
                        m, "open_public_https",
                        side_effect=fetch if fetch is not None else self.fetch):
                    return m.main(args)
            with patch.object(m, "open_public_https",
                              side_effect=fetch if fetch is not None else self.fetch):
                return m.main(args)

    def folder(self, name="new-acquisition"):
        return self.base / name

    def do_acquire(self, folder=None, fake_rows=True, fetch=None):
        folder = folder or self.folder()
        code=self.simulate([
            "--autoriser-lecture-https-public",
            "--destination-privee",str(folder)
        ],fake_rows=fake_rows,fetch=fetch)
        return code, folder

    def do_verify(self, folder=None, fake_rows=True):
        folder = folder or self.folder()
        return self.simulate(
            ["--verifier-repertoire-prive",str(folder)],fake_rows=fake_rows)

    def test_01_schema_config(self):
        self.assertEqual(self.base_config["schema_version"],"P55H-1")
    def test_02_sources_deux(self):
        self.assertEqual(len(self.base_config["sources_requises"]),2)
    def test_03_urls_https(self):
        self.assertTrue(all(s["url_officielle"].startswith("https://")
                            for s in m.official_sources()))
    def test_04_sources_immuables(self):
        self.assertEqual(m.official_sources()[0]["taille_octets_historique"],8984919)
    def test_05_second_sha_reference(self):
        self.assertEqual(len(m.official_sources()[1]["sha256_historique"]),64)
    def test_06_config_p54q_et_p55g(self):
        self.assertEqual(self.base_config["sources"][0] if False else
                         self.base_config["etat_initial"]["decision"],m.NO_GO)
    def test_07_toutes_protections(self):
        self.assertTrue(all(self.base_config["protections"].values()))
    def test_08_gardes_35(self):
        self.assertEqual(len(m.GUARDS),35)
    def test_09_no_network_by_default(self):
        with patch.object(m,"open_public_https",side_effect=AssertionError):
            self.assertEqual(m.main([]),0)
    def test_10_plan_neutre_sources(self):
        self.assertEqual(len(m.public_plan()["sources_publiees_a_consulter"]),2)
    def test_11_plan_autorisation_manuel(self):
        self.assertFalse(m.public_plan()["activation_reseau_automatique"])
    def test_12_plan_pas_authentification(self):
        self.assertEqual(m.public_plan()["decision"],m.NO_GO)
    def test_13_bilan_neutre_zero_copies(self):
        self.assertEqual(m.public_report()["copies_locales_acquises_en_mode_volontaire"],0)
    def test_14_bilan_neutre_pas_reproduction(self):
        self.assertTrue(m.public_report()["reproduction_nfkc_non_effectuee"])
    def test_15_bilan_neutre_pas_certification(self):
        self.assertIsNone(m.public_report()["economies_certifiees_cad"])
    def test_16_bilan_neutre_pas_fusion(self):
        self.assertFalse(m.public_report()["fusion_main_autorisee"])
    def test_17_bilan_neutre_pas_transmission(self):
        self.assertFalse(m.public_report()["transmission_externe_autorisee"])
    def test_18_aucun_pdf_prive_dans_plan(self):
        raw=json.dumps(m.public_plan())
        self.assertNotIn("sha256",raw)
        self.assertNotIn(str(self.base),raw)
    def test_19_aucune_empreinte_actuelle_dans_bilan(self):
        self.assertNotIn("sha256",json.dumps(m.public_report()))
    def test_20_acces_auto_refuse_drapeau_sans_destination(self):
        self.assertEqual(m.main(["--autoriser-lecture-https-public"]),2)
    def test_21_acces_auto_refuse_destination_sans_drapeau(self):
        self.assertEqual(m.main(["--destination-privee",str(self.folder())]),2)
    def test_22_refus_authenticite(self):
        self.assertEqual(m.main(["--exiger-authenticite"]),3)
    def test_23_lien_arbitraire_non_autorise(self):
        with self.assertRaises(ValueError):
            m.open_public_https("https://example.org/finance.pdf")
    def test_24_http_non_autorise(self):
        with self.assertRaises(ValueError):
            m.open_public_https("http://www.ville.quebec.qc.ca/")
    def test_25_url_officielle_avec_query_refusee(self):
        with self.assertRaises(ValueError):
            m.open_public_https(m.official_sources()[0]["url_officielle"]+"?download=1")
    def test_26_redirect_refuse(self):
        with self.assertRaises(ValueError):
            m.RefuseRedirects().redirect_request(
                None,None,302,"redirect",{},"https://example.org")
    def test_27_aucun_appel_reseau_neutre(self):
        with patch.object(m,"open_public_https",side_effect=AssertionError):
            p=self.base/"public.json"
            self.assertEqual(m.main(["--plan-public",str(p)]),0)
            self.assertTrue(p.is_file())
    def test_28_dossier_prive_nouveau(self):
        f=m.private_new_folder(self.folder())
        self.assertTrue(f.is_dir())
        self.assertEqual(f.stat().st_mode&0o777,0o700)
    def test_29_dossier_existant_refuse(self):
        m.private_new_folder(self.folder())
        with self.assertRaises(ValueError):m.private_new_folder(self.folder())
    def test_30_lien_symbolique_parent_refuse(self):
        link=self.folder("symlink")
        link.symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(ValueError):
            m.private_new_folder(link/"subdir")
    def test_31_spec_inconnue_refusee(self):
        folder=m.private_new_folder(self.folder())
        with self.assertRaises(ValueError):
            m.retrieve_one({"code":"INCONNU"},folder,fetch=self.fetch)
    def test_32_https_reponse_ok(self):
        folder=m.private_new_folder(self.folder())
        with self.with_fake_rows():
            item=m.retrieve_one(m.official_sources()[0],folder,fetch=self.fetch)
        self.assertEqual(item["statut"],m.p55g.MATCH)
        self.assertEqual((folder/"VILLE_2024.pdf").stat().st_mode&0o777,0o600)
    def test_33_pdf_rejet_html(self):
        folder=m.private_new_folder(self.folder())
        def fetch(url):return FakeHTTP(url,b"<html>non PDF</html>",content_type="text/html")
        with self.assertRaises(ValueError):
            m.retrieve_one(m.official_sources()[0],folder,fetch=fetch)
        self.assertFalse((folder/"VILLE_2024.pdf").exists())
    def test_34_pdf_rejet_entete_html_mime_pdf(self):
        folder=m.private_new_folder(self.folder())
        def fetch(url):return FakeHTTP(url,b"<html>non PDF</html>")
        with self.assertRaises(ValueError):
            m.retrieve_one(m.official_sources()[0],folder,fetch=fetch)
    def test_35_http_403_refuse(self):
        folder=m.private_new_folder(self.folder())
        def fetch(url):return FakeHTTP(url,b"%PDF-123",status=403)
        with self.assertRaises(ValueError):
            m.retrieve_one(m.official_sources()[0],folder,fetch=fetch)
    def test_36_redirection_reponse_refusee(self):
        folder=m.private_new_folder(self.folder())
        def fetch(url):
            return FakeHTTP(url,b"%PDF-123",
                            final_url="https://other.example.org/abc")
        with self.assertRaises(ValueError):
            m.retrieve_one(m.official_sources()[0],folder,fetch=fetch)
    def test_37_content_length_sup_20m_refuse(self):
        folder=m.private_new_folder(self.folder())
        def fetch(url):
            return FakeHTTP(url,b"%PDF-123",declared_length="20000001")
        with self.assertRaises(ValueError):
            m.retrieve_one(m.official_sources()[0],folder,fetch=fetch)
    def test_38_content_length_non_numerique_refuse(self):
        folder=m.private_new_folder(self.folder())
        def fetch(url):
            return FakeHTTP(url,b"%PDF-123",declared_length="many")
        with self.assertRaises(ValueError):
            m.retrieve_one(m.official_sources()[0],folder,fetch=fetch)
    def test_39_contenu_binaire_max_verifie(self):
        folder=m.private_new_folder(self.folder())
        def fetch(url):return FakeHTTP(url,b"%PDF-123456789")
        with patch.object(m,"MAX_BYTES",8):
            with self.assertRaises(ValueError):
                m.retrieve_one(m.official_sources()[0],folder,fetch=fetch)
        self.assertFalse((folder/"VILLE_2024.pdf").exists())
    def test_40_mime_octet_stream_accepte(self):
        folder=m.private_new_folder(self.folder())
        def fetch(url):
            return FakeHTTP(url,b"%PDF-123",content_type="application/octet-stream")
        with self.assertRaises(AssertionError) if False else self.with_fake_rows():
            # Uses the unmodified historical expected digest, so status is divergent.
            item=m.retrieve_one(m.official_sources()[0],folder,fetch=fetch)
        self.assertEqual(item["statut"],m.p55g.DIVERGENT)
    def test_41_retour_deux_concordances_synthetiques(self):
        code,folder=self.do_acquire()
        self.assertEqual(code,0)
        self.assertTrue((folder/"RECU_P55H.json").exists())
        self.assertEqual(len(self.calls),2)
    def test_42_pdfs_0600(self):
        code,folder=self.do_acquire()
        self.assertEqual(code,0)
        for filename in m.FILENAME.values():
            self.assertEqual((folder/filename).stat().st_mode&0o777,0o600)
    def test_43_recu_0600(self):
        code,folder=self.do_acquire()
        self.assertEqual(code,0)
        self.assertEqual((folder/"RECU_P55H.json").stat().st_mode&0o777,0o600)
    def test_44_recu_empreintes_calculees(self):
        code,folder=self.do_acquire()
        data=json.loads((folder/"RECU_P55H.json").read_text())
        self.assertEqual(data["sources"][0]["sha256_octets_lus"],
                         hashlib.sha256(self.bodies[self.orig_source_data[0][2]]).hexdigest())
    def test_45_recu_pas_identites_ni_chemins(self):
        code,folder=self.do_acquire()
        raw=(folder/"RECU_P55H.json").read_text()
        self.assertNotIn(str(folder),raw)
        self.assertNotIn("prenom",raw)
        self.assertNotIn("signature_numérique",raw)
    def test_46_recu_pas_signatures_attestees(self):
        code,folder=self.do_acquire()
        data=json.loads((folder/"RECU_P55H.json").read_text())
        self.assertFalse(data["signature_professionnelle_authentifiee"])
        self.assertFalse(data["copie_actuelle_authentifiee_par_emetteur"])
    def test_47_recu_pas_reproduction(self):
        code,folder=self.do_acquire()
        data=json.loads((folder/"RECU_P55H.json").read_text())
        self.assertFalse(data["reproduction_nfkc_effectuee"])
    def test_48_recu_lecture_hors_reseau(self):
        code,folder=self.do_acquire()
        self.assertEqual(code,0)
        with patch.object(m,"open_public_https",side_effect=AssertionError):
            self.assertEqual(self.do_verify(folder),0)
    def test_49_recu_modifie_refuse(self):
        code,folder=self.do_acquire()
        receipt=folder/"RECU_P55H.json"
        data=json.loads(receipt.read_text())
        data["empreinte_metadonnees_sha256"]="0"*64
        receipt.write_text(json.dumps(data))
        receipt.chmod(0o600)
        self.assertEqual(self.do_verify(folder),2)
    def test_50_pdf_change_refuse(self):
        code,folder=self.do_acquire()
        target=folder/"VILLE_2024.pdf"
        target.write_bytes(b"%PDF-1.7 modified by outsider")
        target.chmod(0o600)
        self.assertEqual(self.do_verify(folder),2)
    def test_51_permission_pdf_change_refuse(self):
        code,folder=self.do_acquire()
        (folder/"VILLE_2024.pdf").chmod(0o644)
        self.assertEqual(self.do_verify(folder),2)
    def test_52_permission_folder_change_refuse(self):
        code,folder=self.do_acquire()
        folder.chmod(0o755)
        self.assertEqual(self.do_verify(folder),2)
    def test_53_fichier_ajoute_refuse(self):
        code,folder=self.do_acquire()
        (folder/"extra.txt").write_text("extra")
        self.assertEqual(self.do_verify(folder),2)
    def test_54_pdf_manquant_refuse(self):
        code,folder=self.do_acquire()
        (folder/"MAMH_23027_2024.pdf").unlink()
        self.assertEqual(self.do_verify(folder),2)
    def test_55_recu_absent_refuse(self):
        code,folder=self.do_acquire()
        (folder/"RECU_P55H.json").unlink()
        self.assertEqual(self.do_verify(folder),2)
    def test_56_recu_fausse_authentification_refuse(self):
        code,folder=self.do_acquire()
        receipt=folder/"RECU_P55H.json"
        data=json.loads(receipt.read_text())
        data["copie_actuelle_authentifiee_par_emetteur"]=True
        receipt.write_text(json.dumps(data))
        receipt.chmod(0o600)
        self.assertEqual(self.do_verify(folder),2)
    def test_57_date_recu_alteree_refusee(self):
        code,folder=self.do_acquire()
        receipt=folder/"RECU_P55H.json"
        data=json.loads(receipt.read_text())
        data["collecte_http_utc"]="2026-02-30T21:00:00+00:00"
        receipt.write_text(json.dumps(data))
        receipt.chmod(0o600)
        self.assertEqual(self.do_verify(folder),2)
    def test_58_recu_et_sources_inverses_refuses(self):
        code,folder=self.do_acquire()
        receipt=folder/"RECU_P55H.json"
        data=json.loads(receipt.read_text())
        data["sources"]=list(reversed(data["sources"]))
        receipt.write_text(json.dumps(data))
        receipt.chmod(0o600)
        self.assertEqual(self.do_verify(folder),2)
    def test_59_recu_nom_externe_refuse(self):
        code,folder=self.do_acquire()
        receipt=folder/"RECU_P55H.json"
        data=json.loads(receipt.read_text())
        data["nom_personne"]="FAUX"
        receipt.write_text(json.dumps(data))
        receipt.chmod(0o600)
        self.assertEqual(self.do_verify(folder),2)
    def test_60_refus_de_dupliquer_destination(self):
        code,folder=self.do_acquire()
        self.assertEqual(code,0)
        self.assertEqual(self.do_acquire(folder)[0],2)
    def test_61_editions_divergentes_conservees_en_reserve(self):
        code,folder=self.do_acquire(fake_rows=False)
        self.assertEqual(code,4)
        self.assertEqual(len(list(folder.glob("*.pdf"))),2)
        data=json.loads((folder/"RECU_P55H.json").read_text())
        self.assertEqual([x["statut"] for x in data["sources"]],
                         [m.p55g.DIVERGENT,m.p55g.DIVERGENT])
    def test_62_editions_divergentes_relecture_code4(self):
        code,folder=self.do_acquire(fake_rows=False)
        self.assertEqual(code,4)
        self.assertEqual(self.do_verify(folder,fake_rows=False),4)
    def test_63_net_second_failure_cleanup(self):
        counter=0
        def fail_second(url):
            nonlocal counter
            counter+=1
            if counter==2:raise URLError("simulation DNS")
            return self.fetch(url)
        code,folder=self.do_acquire(fetch=fail_second)
        self.assertEqual(code,2)
        self.assertFalse(folder.exists())
    def test_64_http_second_failure_cleanup(self):
        counter=0
        def fail_second(url):
            nonlocal counter
            counter+=1
            if counter==2:return FakeHTTP(url,b"%PDF-200",status=503)
            return self.fetch(url)
        code,folder=self.do_acquire(fetch=fail_second)
        self.assertEqual(code,2)
        self.assertFalse(folder.exists())
    def test_65_recontrole_sans_reseau_echec_si_fichiers_absents(self):
        folder=self.folder()
        with patch.object(m,"open_public_https",side_effect=AssertionError):
            self.assertEqual(m.main(
                ["--verifier-repertoire-prive",str(folder)]),2)
    def test_66_acquisition_et_recontrole_simultanes_refuses(self):
        self.assertEqual(m.main([
            "--autoriser-lecture-https-public",
            "--destination-privee",str(self.folder()),
            "--verifier-repertoire-prive",str(self.folder("other"))]),2)
    def test_67_bilan_public_sans_empreintes_actuelles(self):
        dest=self.folder()
        report=self.base/"summary.json"
        code=self.simulate([
            "--autoriser-lecture-https-public",
            "--destination-privee",str(dest),
            "--bilan-public",str(report)])
        self.assertEqual(code,0)
        raw=report.read_text()
        self.assertNotIn("sha256",raw)
        self.assertNotIn(str(dest),raw)
        self.assertEqual(json.loads(raw)[
            "copies_correspondant_au_sha_historique_non_authentifiees"],2)
    def test_68_pas_ecrasement_du_rapport(self):
        target=self.base/"public.json"
        target.write_text("{}")
        self.assertEqual(m.main(["--bilan-public",str(target)]),2)
    def test_69_sorties_publiques_conflictuelles_refusees(self):
        target=str(self.base/"public.json")
        self.assertEqual(m.main(["--bilan-public",target,
                                 "--plan-public",target]),2)
    def test_71_content_length_inexact_rejete_et_nettoye(self):
        folder=m.private_new_folder(self.folder())
        def fetch(url):
            return FakeHTTP(url,b"%PDF-123",declared_length="999")
        with self.assertRaises(ValueError):
            m.retrieve_one(m.official_sources()[0],folder,fetch=fetch)
        self.assertFalse((folder/"VILLE_2024.pdf").exists())

    def test_70_economies_et_mandats_toujours_non_certifies(self):
        r=m.public_report()
        self.assertEqual(r["avis_professionnels_authentifies"],0)
        self.assertEqual(r["mandats_signes"],0)
        self.assertIsNone(r["economies_certifiees_cad"])
        self.assertEqual(r["dossiers_p54e_ouverts"],4)
        self.assertEqual(r["blocages_p54o_non_leves"],10)
        self.assertFalse(r["eliminations_existantes_comme_nouveau_gain"])


if __name__ == "__main__":
    unittest.main()
