"""P52Q : tests adversariaux des sources et des huit dossiers sans expertise."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
p=ROOT/"scripts"/"controler_dossiers_primaires_nova_p52q.py"
spec=importlib.util.spec_from_file_location("p52q",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def files():
    return {k:m.load(p) for k,p in m.FILES.items()}

class SourcesP52Q(unittest.TestCase):
    def rejects(self,change):
        d=files();change(d)
        with self.assertRaises(ValueError):m.verifier(d)

    def test_01_eight_first_proofs(self):
        self.assertEqual(m.verifier(files())["dossiers_prioritaires"],8)
    def test_02_13_official_sources(self):
        self.assertEqual(m.verifier(files())["liens_officiels_a_analyser"],13)
    def test_03_f19_new_legal_reference(self):
        self.assertEqual(m.verifier(files())["nouveaux_reperes_pour_F19"],1)
    def test_04_budget_preexisting_two(self):
        self.assertEqual(m.verifier(files())["sources_budget_P52J_sans_nouvel_archivage"],2)
    def test_05_four_tasks_each(self):
        self.assertEqual(m.verifier(files())["taches_instruction_explicitement_documentees"],32)
    def test_06_no_expert_ever_claimed(self):
        self.assertEqual(m.verifier(files())["dossiers_avec_avis_independant_recu"],0)
    def test_07_zero_pdf_hashes(self):
        self.assertEqual(m.verifier(files())["hashes_originaux_certifies"],0)
    def test_08_no_go(self):
        self.assertEqual(m.verifier(files())["decision"],"NO_GO_AUTOMATIQUE")
    def test_09_exact_f19_scope(self):
        self.assertEqual([x for x in files()["dossiers"]["dossiers"] if x["id"]=="F19"][0]["regime"],"TOUS")
    def test_10_confidentiality_sectors_separate(self):
        refs=files()["references"]["sources"]
        self.assertEqual([x["id"] for x in refs if "F20" in x["preuves_associees"]],["Q08","Q10","Q11"])
    def test_11_f01_federal_limits(self):
        ref=files()["references"]["sources"]
        self.assertEqual([x["id"] for x in ref if "F01" in x["preuves_associees"]],["Q01","Q02","Q03"])
    def test_12_f09_two_primary_docs(self):
        refs=files()["references"]["sources"]
        self.assertEqual([x["id"] for x in refs if "F09" in x["preuves_associees"]],["Q12","Q13"])
    def test_13_20_upstream_still_unattested(self):
        self.assertTrue(all(x["statut"]=="NON_VALIDE" for x in files()["p52a"]["required_evidence"]))
    def test_14_no_PDF_in_repo(self):
        self.assertTrue(all(x["sha256_octets_origine"] is None for x in files()["references"]["sources"]))
    def test_15_no_new_representativeness_claim(self):
        self.assertFalse(files()["dossiers"]["gouvernance"]["approbation_juridique_recue"])
    def test_16_wrong_source_url(self):
        self.rejects(lambda d:d["references"]["sources"][0].update(url="https://other.invalid"))
    def test_17_fake_source_authentication(self):
        self.rejects(lambda d:d["references"]["sources"][0].update(certification_origine_documentaire=True))
    def test_18_fake_download(self):
        self.rejects(lambda d:d["references"]["sources"][4].update(copie_originale_hors_git_obtenue=True))
    def test_19_fake_sha(self):
        self.rejects(lambda d:d["references"]["sources"][11].update(sha256_octets_origine="b"*64))
    def test_20_false_expert_interpretation(self):
        self.rejects(lambda d:d["references"]["sources"][1].update(interpretation_par_expert_independant=True))
    def test_21_wrong_tax_version(self):
        self.rejects(lambda d:d["references"]["sources"][2].update(version_visible_au_moment_de_consultation="2024"))
    def test_22_wrong_official_source_id(self):
        self.rejects(lambda d:d["references"]["sources"][8].update(id="Q99"))
    def test_23_wrong_budget_status(self):
        self.rejects(lambda d:d["references"]["sources"][11].update(statut_reperage="CONSULTE_SOURCE_OFFICIELLE_EN_LIGNE"))
    def test_24_wrong_budget_url(self):
        self.rejects(lambda d:d["references"]["sources"][12].update(url="https://fake.invalid/pdf"))
    def test_25_f19_removed(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"].pop(6))
    def test_26_f19_false_adoption(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][6].update(decision_adoption_autorisee=True))
    def test_27_f20_false_legal_opinion(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][7].update(avis_favorable_recu=True))
    def test_28_f01_false_expert(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][0].update(expert_reel_mandate=True))
    def test_29_F09_phantom_certificate(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][5].update(justificatif_signature_authentifie="signé"))
    def test_30_fake_reception_count(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][3].update(pieces_recues_verifiees=1))
    def test_31_change_jurisdiction(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][1].update(regime="QUEBEC_SOUVERAIN"))
    def test_32_change_committee(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][5].update(comite_pilote="CJF"))
    def test_33_erase_old_references(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][0].update(sources_precedemment_reperees=[]))
    def test_34_erase_new_f19_reference(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][6].update(nouveaux_reperes_officiels=[]))
    def test_35_delete_required_work(self):
        self.rejects(lambda d:d["dossiers"]["dossiers"][3]["travaux_requis"].pop())
    def test_36_false_p52a_attestation(self):
        self.rejects(lambda d:d["p52a"]["required_evidence"][18].update(statut="VALIDE"))
    def test_37_false_p52p_validation(self):
        self.rejects(lambda d:d["p52p"]["exigences"][18].update(statut_juridique="VALIDE"))
    def test_38_p52o_changed_first_wave(self):
        self.rejects(lambda d:d["p52o"]["vagues"][0]["preuves"].remove("F19"))
    def test_39_false_p52n_mandate(self):
        self.rejects(lambda d:d["p52n"]["mandats"][18].update(expert_mandate=True))
    def test_40_false_p52j_budget_signature(self):
        self.rejects(lambda d:d["p52j"]["validation_de_nature"].update(preuve_F09_independamment_attestee=True))
    def test_41_false_p52k_hashed_document(self):
        self.rejects(lambda d:d["p52k"]["fichiers_source"][0].update(empreinte_sha256_pdf_original="a"*64))
    def test_42_go_false_publication(self):
        self.rejects(lambda d:d["dossiers"]["gouvernance"].update(publication_autorisee=True))
    def test_43_go_false_fusion(self):
        self.rejects(lambda d:d["dossiers"]["gouvernance"].update(fusion_autorisee=True))
    def test_44_report_only_aggregates(self):
        d=files()
        text=json.dumps(m.verifier(d),ensure_ascii=False)
        for secret in ("Q09","\"id\": \"F19\"","https://","2026-02-23","loi", "\"id\": \"F01\""):
            self.assertNotIn(secret,text)
    def test_45_cli_normal_keeps_NO_GO(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"report.json"
            self.assertEqual(m.main(["--rapport",str(p)]),0)
            self.assertEqual(json.loads(p.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_46_cli_strict_returns_three(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(m.main(["--exiger-expertises","--rapport",
                                      str(Path(temp)/"r.json")]),3)
    def test_47_cli_missing_document_returns_two(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(m.main(["--dossiers",str(Path(temp)/"no.json")]),2)
    def test_48_report_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"r.json"
            self.assertEqual(m.main(["--rapport",str(p)]),0)
            self.assertEqual(m.main(["--rapport",str(p)]),2)
if __name__=="__main__":
    unittest.main()
