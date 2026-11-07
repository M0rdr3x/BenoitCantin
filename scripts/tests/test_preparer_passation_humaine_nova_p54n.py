#!/usr/bin/env python3
"""P54N: tests de passation sans aucune pièce ni demande réelle."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preparer_passation_humaine_nova_p54n as m

class TestP54N(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()
        cls.packet=m.workpack(cls.cfg)
        cls.report=m.report(cls.cfg)
    def test_01_version(self):self.assertEqual(self.cfg["schema_version"],"P54N-1")
    def test_02_year(self):self.assertEqual(self.cfg["source_exercice"],2024)
    def test_03_source(self):self.assertEqual(self.cfg["source_p54d_run"],40120462237)
    def test_04_upstream_chain(self):self.assertEqual(self.cfg["source_jalons"],["P54D","P54E","P54M"])
    def test_05_count_cases(self):self.assertEqual(len(self.cfg["dossiers"]),4)
    def test_06_count_tasks(self):self.assertEqual(len(self.cfg["taches"]),10)
    def test_07_count_positions(self):self.assertEqual(sum(len(c["instructions"]) for c in self.packet["dossiers"]),40)
    def test_08_all_unknown(self):self.assertTrue(all(c["classification"]=="INDETERMINE" for c in self.cfg["dossiers"]))
    def test_09_city_index(self):self.assertEqual(self.packet["dossiers"][0]["index_page_pdf_zero_based"],102)
    def test_10_mamh_index(self):self.assertTrue(all(c["index_page_pdf_zero_based"]==162 for c in self.packet["dossiers"][1:]))
    def test_11_zone_city(self):self.assertEqual(self.packet["dossiers"][0]["zone_approximative"],"FIN")
    def test_12_zone_first_mamh(self):self.assertEqual(self.packet["dossiers"][1]["zone_approximative"],"DEBUT")
    def test_13_other_mamh_zone(self):self.assertEqual([c["zone_approximative"] for c in self.packet["dossiers"][2:]],["FIN","FIN"])
    def test_14_ids_exact(self):
        self.assertEqual([c["dossier_id"] for c in self.packet["dossiers"]],["P54E-V-001","P54E-M-001","P54E-M-002","P54E-M-003"])
    def test_15_sources_exact(self):self.assertEqual([c["publication"] for c in self.packet["dossiers"]],["ville","mamh","mamh","mamh"])
    def test_16_observation_indices(self):self.assertEqual([c["index_observation_p54d"] for c in self.packet["dossiers"]],[0,1,3,4])
    def test_17_date_not_final(self):self.assertFalse(self.packet["observation_distincte_date_probable"]["qualif_definitive"])
    def test_18_date_still_open(self):self.assertEqual(self.report["observation_date_probable_non_resolue"],1)
    def test_19_no_resolved_discrepancy(self):
        self.assertIn("OCCURRENCES_LEXICALES",self.packet["objet"])
    def test_20_all_not_received(self):
        self.assertTrue(all(not task["piece_originale_recue"]
           for row in self.packet["dossiers"] for task in row["instructions"]))
    def test_21_no_expertise_falsely_received(self):
        self.assertTrue(all(not task["verification_professionnelle_obtenue"]
           for row in self.packet["dossiers"] for task in row["instructions"]))
    def test_22_no_request_executed(self):
        self.assertTrue(all(task["etat"]=="A_INSTRUIRE"
           for row in self.packet["dossiers"] for task in row["instructions"]))
    def test_23_role_source_documentary(self):
        self.assertEqual(self.cfg["taches"][0]["responsable"],"EXAMINATEUR_DOCUMENTAIRE")
    def test_24_accountant_role(self):
        self.assertTrue(any(x["responsable"]=="EXPERT_COMPTABLE_A_MANDATER" for x in self.cfg["taches"]))
    def test_25_law_role(self):
        self.assertTrue(any(x["responsable"]=="EXPERT_JURIDIQUE_A_MANDATER" for x in self.cfg["taches"]))
    def test_26_independent_countercheck(self):
        self.assertTrue(any(x["responsable"]=="CONTRE_REVISEUR_INDEPENDANT_A_MANDATER" for x in self.cfg["taches"]))
    def test_27_ravq_context(self):
        self.assertTrue(any("RAVQ_1435" in x["livrable"] for x in self.cfg["taches"]))
    def test_28_consolidation_care(self):
        self.assertTrue(any("VILLE_RTC_SOMHAC" in x["condition"] for x in self.cfg["taches"]))
    def test_29_no_closure(self):
        self.assertTrue(all(not x["cloture_autorisee"] for x in self.packet["dossiers"]))
    def test_30_no_signatures(self):self.assertEqual(self.report["avis_authentifies"],0)
    def test_31_no_real_mandates(self):self.assertEqual(self.report["mandats_effectifs_attribues"],0)
    def test_32_no_money(self):self.assertIsNone(self.report["economies_certifiees_cad"])
    def test_33_no_go(self):self.assertEqual(self.report["decision"],m.NO_GO)
    def test_34_p54b_remains(self):self.assertEqual(self.report["controles_p54b_non_attestes"],96)
    def test_35_p54c_remains(self):self.assertEqual(self.report["controles_p54c_non_attestes"],8)
    def test_36_no_merge(self):self.assertFalse(self.report["fusion_main_autorisee"])
    def test_37_markdown_includes_all(self):
        md=m.markdown(self.packet,self.report)
        for row in self.packet["dossiers"]:self.assertIn("## "+row["dossier_id"],md)
    def test_38_markdown_safe(self):
        md=m.markdown(self.packet,self.report)
        self.assertIn("NO_GO_AUTOMATIQUE",md)
        self.assertNotIn("1000000 $",md)
    def test_39_cli_json_output(self):
        with tempfile.TemporaryDirectory() as d:
            dossier=Path(d)/"dossier.json";bilan=Path(d)/"bilan.json"
            self.assertEqual(m.main(["--dossier",str(dossier),"--bilan",str(bilan)]),0)
            contents=json.loads(dossier.read_text(encoding="utf-8"))
            self.assertEqual(len(contents["dossiers"]),4)
            self.assertEqual(json.loads(bilan.read_text("utf-8"))["taches_documentaires_a_instruire"],40)
    def test_40_cli_markdown_output(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"instructions.md"
            self.assertEqual(m.main(["--instructions",str(path)]),0)
            self.assertIn("P54E-V-001",path.read_text(encoding="utf-8"))
    def test_41_cli_blocked_transmission(self):
        self.assertEqual(m.main(["--exiger-transmission"]),3)
    def test_42_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"dossier.json";path.write_text("PRESERVE",encoding="utf-8")
            self.assertEqual(m.main(["--dossier",str(path)]),2)
            self.assertEqual(path.read_text(encoding="utf-8"),"PRESERVE")
    def test_43_cli_no_destination_collision(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"same.json"
            self.assertEqual(m.main(["--dossier",str(path),"--bilan",str(path)]),2)
    def test_44_cli_no_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            real=Path(d)/"actual.json";real.write_text("KEEP",encoding="utf-8")
            alias=Path(d)/"alias.json";alias.symlink_to(real)
            self.assertEqual(m.main(["--dossier",str(alias)]),2)
            self.assertEqual(real.read_text(encoding="utf-8"),"KEEP")
    def test_45_real_urls_public_only(self):
        self.assertTrue(all(p["url_source_publique"].startswith("https://")
             for p in self.packet["dossiers"]))
    def test_46_full_10_distinct_codes(self):
        self.assertEqual(len({x["code"] for x in self.cfg["taches"]}),10)
    def test_47_package_has_no_private_sha(self):
        self.assertNotIn("sha256",json.dumps(self.packet).casefold())
    def test_48_not_police_audit(self):
        self.assertTrue(self.cfg["protections"]["aucune_anomalie_financiere_demontree"])
    def test_49_no_live_contact(self):
        self.assertTrue(self.cfg["protections"]["aucun_contact_avec_un_tiers_par_le_logiciel"])
    def test_50_report_no_attachments(self):
        self.assertEqual(self.report["sources_privees_reçues"],0)

def guard_test(key):
    def exercise(self):
        self.assertTrue(self.cfg["protections"][key])
    return exercise
for i,name in enumerate(sorted(m.GUARDS),51):
    setattr(TestP54N,"test_%02d_protection"%i,guard_test(name))

if __name__=="__main__":
    unittest.main()
