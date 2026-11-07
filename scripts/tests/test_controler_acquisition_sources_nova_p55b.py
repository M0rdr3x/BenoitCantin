import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controler_acquisition_sources_nova_p55b as m


class TestP55B(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = m.configuration()

    def fake(self,root,content=b"%PDF-1.7\nTEST_P55B_SYNTHESE\n%%EOF"):
        f=Path(root)/"copie_publique.pdf"
        f.write_bytes(content)
        f.chmod(0o600)
        return f,hashlib.sha256(content).hexdigest(),len(content)

    def test_01_schema(self):
        self.assertEqual(self.cfg["schema_version"],"P55B-1")
    def test_02_exercice_2024(self):
        self.assertEqual(self.cfg["exercice"],2024)
    def test_03_sources_deux(self):
        self.assertEqual(len(m.SOURCE_DATA),2)
    def test_04_urls_https(self):
        self.assertTrue(all(s[2].startswith("https://") for s in m.SOURCE_DATA))
    def test_05_domains_institutionnels(self):
        self.assertIn("ville.quebec.qc.ca",m.SOURCE_DATA[0][2])
        self.assertIn("mamh.gouv.qc.ca",m.SOURCE_DATA[1][2])
    def test_06_p54q_empreintes(self):
        self.assertEqual(len(m.SOURCE_DATA[0][6]),64)
        self.assertEqual(len(m.SOURCE_DATA[1][6]),64)
    def test_07_ville_page(self):
        self.assertEqual(m.SOURCE_DATA[0][4],102)
    def test_08_mamh_page(self):
        self.assertEqual(m.SOURCE_DATA[1][4],162)
    def test_09_cinq_refs(self):
        self.assertEqual(sum(len(s[-1]) for s in m.SOURCE_DATA),5)
    def test_10_quatre_plus_date(self):
        self.assertIn("P54O-DATE-001",m.SOURCE_DATA[1][-1])
    def test_11_mandats(self):
        self.assertEqual(len(m.MANDATES),2)
    def test_12_etapes(self):
        self.assertEqual(len(m.PHASES),8)
    def test_13_ordre_priorites(self):
        self.assertEqual(m.PHASES[0][0],"A01_ACQUISITION_OFFICIELLE")
        self.assertEqual(m.PHASES[-1][0],"A08_DECISION_INSTITUTIONNELLE")
    def test_14_protections(self):
        self.assertTrue(all(self.cfg["protections"].values()))
    def test_15_no_go(self):
        self.assertEqual(m.public_report()["decision"],m.NO_GO)
    def test_16_aucune_economie(self):
        self.assertIsNone(m.public_report()["economies_certifiees_cad"])
    def test_17_aucun_expert(self):
        self.assertEqual(m.public_report()["avis_independants_authentifies"],0)
    def test_18_no_go_transmission(self):
        self.assertFalse(m.public_report()["envoi_externe_autorise"])
    def test_19_no_go_engagement(self):
        self.assertFalse(m.public_report()["engagement_depense_autorise"])
    def test_20_no_go_main(self):
        self.assertFalse(m.public_report()["fusion_main_autorisee"])
    def test_21_pas_authentification_emetteur(self):
        self.assertEqual(m.public_report()["sources_authentifiees_par_emetteur"],0)
    def test_22_sources_absentes(self):
        self.assertEqual(m.public_report()["sources_non_fournies"],2)
    def test_23_bilan_no_pdf(self):
        self.assertEqual(m.public_report()["copies_locales_concordantes_p54q_non_authentifiees"],0)
    def test_24_plan_humain(self):
        self.assertTrue(all(x["etat_reel"]=="NON_REALISE_PAR_CE_PROGRAMME"
                            for x in m.operation_plan()["operations_humaines"]))
    def test_25_plan_transmission_bloquee(self):
        self.assertTrue(m.operation_plan()["aucune_transmission_externe"])
    def test_26_plan_aucun_avis(self):
        self.assertEqual(m.operation_plan()["decision"],m.NO_GO)
    def test_27_pdf_synthetique_sha(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            self.assertEqual(m.local_pdf_status(p,size,sha),m.CONCORDANCE)
    def test_28_pdf_synthetique_edition_differente(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            self.assertEqual(m.local_pdf_status(p,size,"f"*64),m.EDITION)
    def test_29_pdf_taille_differente(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            self.assertEqual(m.local_pdf_status(p,size+1,sha),m.EDITION)
    def test_30_pdf_header_faux(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t,b"PAS_PDF" + b"X"*60)
            self.assertEqual(m.local_pdf_status(p,size,sha),m.EDITION)
    def test_31_sha_invalide(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            with self.assertRaises(ValueError):
                m.local_pdf_status(p,size,"no")
    def test_32_une_taille_non_autorisee(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            with self.assertRaises(ValueError):
                m.local_pdf_status(p,0,sha)
    def test_33_grande_taille_non_autorisee(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            with self.assertRaises(ValueError):
                m.local_pdf_status(p,20_000_001,sha)
    def test_34_permissions_refusees(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            p.chmod(0o644)
            with self.assertRaises(ValueError):
                m.local_pdf_status(p,size,sha)
    def test_35_lien_pdf_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            link=Path(t)/"alias.pdf";link.symlink_to(p)
            with self.assertRaises(ValueError):
                m.local_pdf_status(link,size,sha)
    def test_36_lien_repertoire_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            alias=Path(t)/"aliasdir";alias.symlink_to(t,target_is_directory=True)
            with self.assertRaises(ValueError):
                m.local_pdf_status(alias/p.name,size,sha)
    def test_37_source_identique_refusee(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            out=p
            self.assertEqual(m.main(["--ville-pdf",str(p),
                                     "--bilan-public",str(out)]),2)
    def test_38_chemins_sorties_identiques(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"public.json"
            self.assertEqual(m.main(["--bilan-public",str(p),
                                     "--plan-public",str(p)]),2)
    def test_39_chemin_public_existants(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"public.json";p.write_text("{}")
            self.assertEqual(m.main(["--bilan-public",str(p)]),2)
    def test_40_schema_statuts_inconnu(self):
        with self.assertRaises(ValueError):
            m.public_report({"VILLE_2024":"CERTIFIE",
                             "MAMH_23027_2024":m.NON_FOURNIE})
    def test_41_source_manquante_cle(self):
        with self.assertRaises(ValueError):
            m.public_report({"VILLE_2024":m.NON_FOURNIE})
    def test_42_statut_different_permet_compte(self):
        statuts={"VILLE_2024":m.CONCORDANCE,
                 "MAMH_23027_2024":m.EDITION}
        r=m.public_report(statuts)
        self.assertEqual(r["copies_locales_concordantes_p54q_non_authentifiees"],1)
        self.assertEqual(r["editions_divergentes_a_instruire"],1)
    def test_43_doubles_concordances_ne_certifient_rien(self):
        r=m.public_report({x:m.CONCORDANCE for x in m.PDF_CODES})
        self.assertEqual(r["sources_authentifiees_par_emetteur"],0)
        self.assertIsNone(r["economies_certifiees_cad"])
    def test_44_rapport_censure_empreintes(self):
        s=json.dumps(m.public_report(),ensure_ascii=False)
        self.assertNotIn(m.SOURCE_DATA[0][6],s)
        self.assertNotIn(m.SOURCE_DATA[1][6],s)
    def test_45_rapport_censure_chemins(self):
        self.assertNotIn("/stockage",json.dumps(m.public_report()))
    def test_46_declara_p55a_absente_refuse(self):
        with self.assertRaises(ValueError):
            m.declared_checks("fiche.json")
    def test_47_declara_p54z_absente_refuse(self):
        with self.assertRaises(ValueError):
            m.declared_checks(p55a_path="fiche.json")
    def test_48_declarations_absentes_statuts_par_defaut(self):
        self.assertEqual(m.declared_checks(),(None,0))
    def test_49_declarations_incorrectes(self):
        with self.assertRaises(ValueError):
            m.public_report(declarations={"NON_INSTRUIT":50})
    def test_50_declarations_somme_incorrecte(self):
        with self.assertRaises(ValueError):
            m.public_report(declarations={k:1 for k in m.p55a.STATES})
    def test_51_suspensions_heritees_conservees(self):
        r=m.public_report(inherited=3)
        self.assertEqual(r["suspensions_p54z_heritees"],3)
    def test_52_suspensions_excessives_refusees(self):
        with self.assertRaises(ValueError):
            m.public_report(inherited=41)
    def test_53_cli_bilan_neutre(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"bilan.json"
            self.assertEqual(m.main(["--bilan-public",str(out)]),0)
            self.assertEqual(json.loads(out.read_text())["sources_non_fournies"],2)
    def test_54_cli_plan_public(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"plan.json"
            self.assertEqual(m.main(["--plan-public",str(out)]),0)
            self.assertEqual(len(json.loads(out.read_text())["operations_humaines"]),8)
    def test_55_cli_faux_go(self):
        self.assertEqual(m.main(["--exiger-go"]),3)
    def test_56_cli_faux_pdf_retour_edition(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t)
            self.assertEqual(m.main(["--ville-pdf",str(p)]),4)
    def test_57_cli_faux_pdf_rapport_divergence(self):
        with tempfile.TemporaryDirectory() as t:
            p,sha,size=self.fake(t); out=Path(t)/"bilan.json"
            self.assertEqual(m.main(["--ville-pdf",str(p),
                                     "--bilan-public",str(out)]),4)
            report=json.loads(out.read_text())
            self.assertEqual(report["editions_divergentes_a_instruire"],1)
            self.assertEqual(report["sources_authentifiees_par_emetteur"],0)
    def test_58_sha_ou_source_publiee_non_identite(self):
        self.assertTrue(all(not s["url_officielle"].startswith("http://")
                            for s in m.expected_sources()))
        self.assertNotIn("signature",json.dumps(m.operation_plan()).lower())
    def test_59_references_les_memes_p55a(self):
        self.assertEqual(set(m.operation_plan()["references_non_certifiees"]),
                         set(m.p55a.REFS))
    def test_60_codes_actions_sans_doublon(self):
        codes=[x["code"] for x in m.expected_phases()]
        self.assertEqual(len(codes),len(set(codes)))
    def test_61_prerequis_actions_anterieurs(self):
        codes=[x["code"] for x in m.expected_phases()]
        for i,item in enumerate(m.expected_phases()):
            self.assertTrue(all(dep in codes[:i] for dep in item["prerequis"]))
    def test_62_no_automatic_savings(self):
        self.assertEqual(self.cfg["etat_initial"]["decision"],m.NO_GO)
        self.assertEqual(self.cfg["etat_initial"]["mandats_reels_signes"],0)
    def test_63_chaine_p54z_p55a_maintient_suspension(self):
        with tempfile.TemporaryDirectory() as t:
            p54z=Path(t)/"p54z.json"
            p55a=Path(t)/"p55a.json"
            out=Path(t)/"public.json"
            upstream=m.p54z.blank_model()
            upstream["dossiers"][0]["controles"][0]["etat"]="SUSPENDU"
            m.p54z.write_new(p54z,upstream,private=True)
            _doc,sha=m.p55a.upstream(p54z)
            m.p54z.write_new(p55a,m.p55a.model(sha),private=True)
            self.assertEqual(m.main(["--declarations-p54z",str(p54z),
                                     "--relecture-p55a",str(p55a),
                                     "--bilan-public",str(out)]),0)
            r=json.loads(out.read_text())
            self.assertEqual(r["suspensions_p54z_heritees"],1)
            self.assertEqual(r["avis_independants_authentifies"],0)
    def test_64_chaine_sha_p55a_invalide_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            p54z=Path(t)/"p54z.json"
            p55a=Path(t)/"p55a.json"
            m.p54z.write_new(p54z,m.p54z.blank_model(),private=True)
            m.p54z.write_new(p55a,m.p55a.model("e"*64),private=True)
            self.assertEqual(m.main(["--declarations-p54z",str(p54z),
                                     "--relecture-p55a",str(p55a)]),2)
    def test_65_statuts_vides_refuses(self):
        with self.assertRaises(ValueError):
            m.public_report(source_states={})
    def test_66_booleen_non_admis_pour_suspensions(self):
        with self.assertRaises(ValueError):
            m.public_report(inherited=True)


if __name__ == "__main__":
    unittest.main()
