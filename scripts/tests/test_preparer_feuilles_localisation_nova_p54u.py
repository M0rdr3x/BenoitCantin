#!/usr/bin/env python3
"""P54U: tests hors réseau des cinq fiches publiques de localisation."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preparer_feuilles_localisation_nova_p54u as m

class TestsP54U(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()
        cls.fixed=m.p54t.verify_frozen(m.p54t.configuration())
        cls.cards=m.build_cards(cls.cfg,cls.fixed)
        cls.report=m.report(cls.cfg,cls.fixed)

    def test_01_version(self):self.assertEqual(self.cfg["schema_version"],"P54U-1")
    def test_02_source(self):self.assertEqual(self.cfg["source_jalons"],["P54P","P54T","P54O","P54N"])
    def test_03_exercice(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_04_historical_run(self):self.assertEqual(self.cfg["reference_run_p54p"],40151185184)
    def test_05_historical_artifact(self):self.assertEqual(self.cfg["reference_artifact_p54p"],12583661231)
    def test_06_two_frozen_members(self):self.assertEqual(self.fixed["bilans_figes_verifies"],2)
    def test_07_byte_count(self):self.assertEqual(self.fixed["tailles_octets_verifiees"],3426)
    def test_08_five_offsets_sha_checked(self):self.assertEqual(self.fixed["positions_historiques_hachees"],5)
    def test_09_five_cards(self):self.assertEqual(len(self.cards["fiches"]),5)
    def test_10_four_p54e(self):self.assertEqual(sum(x["dossier_p54e"] for x in self.cards["fiches"]),4)
    def test_11_last_date_distinct(self):self.assertEqual(sum(not x["dossier_p54e"] for x in self.cards["fiches"]),1)
    def test_12_order_ids(self):
        self.assertEqual([x["identifiant"] for x in self.cards["fiches"]],
          ["P54E-V-001","P54E-M-001","P54O-DATE-001","P54E-M-002","P54E-M-003"])
    def test_13_offsets(self):
        self.assertEqual([x["offset_caractere_nfkc"] for x in self.cards["fiches"]],
          [2359,18,2420,2430,2436])
    def test_14_normalised_lengths(self):
        self.assertEqual([x["longueur_texte_nfkc"] for x in self.cards["fiches"]],
          [2364,2439,2439,2439,2439])
    def test_15_page_indexes(self):
        self.assertEqual([x["page_pdf_index_zero"] for x in self.cards["fiches"]],
          [102,162,162,162,162])
    def test_16_zone(self):
        self.assertEqual([x["zone_indicative"] for x in self.cards["fiches"]],
          ["FIN","DEBUT","FIN","FIN","FIN"])
    def test_17_date_indicative_not_certified(self):
        self.assertEqual(self.cards["fiches"][2]["qualification_indicative"],"ANNEE_DATE_PROBABLE")
        self.assertFalse(self.cards["fiches"][2]["qualification_humaine_confirmee"])
    def test_18_total_tasks(self):
        self.assertEqual(sum(len(x["travail_humain_a_effectuer"]) for x in self.cards["fiches"]),25)
    def test_19_five_control_types(self):
        self.assertEqual(len(self.cfg["controles_humains_par_observation"]),5)
    def test_20_tasks_all_pending(self):
        self.assertTrue(all(t["etat"]=="A_INSTRUIRE"
           for x in self.cards["fiches"] for t in x["travail_humain_a_effectuer"]))
    def test_21_no_attestations(self):
        self.assertTrue(all(t["attestation_reelle"] is False
           for x in self.cards["fiches"] for t in x["travail_humain_a_effectuer"]))
    def test_22_no_pdf_reopened(self):
        self.assertEqual(self.cards["pdf_relus_au_run_courant"],0)
        self.assertEqual(self.report["pdf_originaux_reacquis_ce_run"],0)
    def test_23_not_page_coordinates(self):
        self.assertTrue(all(x["type_position"]=="INDEX_CARACTERE_TEXTE_NFKC_NON_COORDONNEE_PDF"
            for x in self.cards["fiches"]))
    def test_24_no_expert_real(self):
        self.assertEqual(self.report["mandats_originaux_authentifies"],0)
        self.assertFalse(self.cards["signature_certifiee"])
    def test_25_no_money(self):
        self.assertIsNone(self.report["economies_certifiees_cad"])
        self.assertIsNone(self.cards["economies_certifiees_cad"])
    def test_26_no_go(self):
        self.assertEqual(self.report["decision"],m.NO_GO)
        self.assertEqual(self.cards["decision"],m.NO_GO)
    def test_27_no_delivery(self):
        self.assertFalse(self.report["pret_a_transmettre"])
        self.assertFalse(self.cards["autorisation_transmission_obtenue"])
    def test_28_upstream_open(self):
        self.assertEqual(self.report["blocages_p54o_non_leves"],10)
        self.assertEqual(self.report["taches_p54n_non_attestees"],40)
    def test_29_p54b_and_p54c(self):
        self.assertEqual((self.report["controles_p54b_non_attestes"],
                          self.report["controles_p54c_non_attestes"]),(96,8))
    def test_30_no_snapshot_false_positive(self):
        self.assertEqual(m.report(self.cfg)["deux_bilans_publics_p54t_reverifies_ce_run"],0)
        self.assertEqual(m.report(self.cfg)["positions_historiques_vers_fiches"],0)
    def test_31_refuse_zero_validation(self):
        with self.assertRaises(ValueError):m.build_cards(self.cfg,None)
    def test_32_refuse_missing_member(self):
        t=copy.deepcopy(self.fixed);t["bilans_figes_verifies"]=1
        with self.assertRaises(ValueError):m.build_cards(self.cfg,t)
    def test_33_refuse_wrong_byte_count(self):
        t=copy.deepcopy(self.fixed);t["tailles_octets_verifiees"]=1
        with self.assertRaises(ValueError):m.build_cards(self.cfg,t)
    def test_34_refuse_fake_offset(self):
        t=copy.deepcopy(self.fixed)
        t["positions_de_reference"][0]["offset_texte_extrait"]=23
        with self.assertRaises(ValueError):m.build_cards(self.cfg,t)
    def test_35_refuse_broken_order(self):
        t=copy.deepcopy(self.fixed)
        t["positions_de_reference"]=list(reversed(t["positions_de_reference"]))
        with self.assertRaises(ValueError):m.build_cards(self.cfg,t)
    def test_36_refuse_wrong_dossier(self):
        t=copy.deepcopy(self.fixed)
        t["positions_de_reference"][2]["dossier"]="P54E-M-999"
        with self.assertRaises(ValueError):m.build_cards(self.cfg,t)
    def test_37_refuse_unhashed_member(self):
        with tempfile.TemporaryDirectory() as folder:
            mapping={}
            for name in m.p54t.NAMES:
                original=m.p54t.FROZEN/name
                target=Path(folder)/name
                shutil.copyfile(original,target)
                mapping[name]=target
            first=m.p54t.NAMES[0]
            mapping[first].write_bytes(mapping[first].read_bytes()+b" ")
            with self.assertRaises(ValueError):
                m.p54t.verify_frozen(m.p54t.configuration(),mapping)
    def test_38_refuse_unhashed_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            mapping={name:m.p54t.FROZEN/name for name in m.p54t.NAMES}
            name=m.p54t.NAMES[0]
            link=Path(folder)/name
            link.symlink_to(mapping[name])
            mapping[name]=link
            with self.assertRaises(ValueError):
                m.p54t.verify_frozen(m.p54t.configuration(),mapping)
    def test_39_markdown_five(self):
        md=m.instructions(self.cards)
        for row in self.cards["fiches"]:
            self.assertIn("## "+row["identifiant"],md)
    def test_40_markdown_offsets_not_as_money(self):
        md=m.instructions(self.cards)
        self.assertIn("NFKC",md)
        self.assertIn("PAS des coordonnées",md)
        self.assertIn("NO_GO_AUTOMATIQUE",md)
    def test_41_cli_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"baseline.json"
            self.assertEqual(m.main(["--bilan",str(out)]),0)
            doc=json.loads(out.read_text("utf-8"))
            self.assertEqual(doc["deux_bilans_publics_p54t_reverifies_ce_run"],0)
    def test_42_cli_needs_validation_for_cards(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"cards.json"
            self.assertEqual(m.main(["--fiches",str(out)]),2)
            self.assertFalse(out.exists())
    def test_43_cli_produces_three_files(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"cards.json";b=Path(d)/"instructions.md";c=Path(d)/"bilan.json"
            self.assertEqual(m.main(["--verifier-bilans-figes","--fiches",str(a),
                          "--instructions",str(b),"--bilan",str(c)]),0)
            self.assertEqual(len(json.loads(a.read_text("utf-8"))["fiches"]),5)
            self.assertIn("P54E-V-001",b.read_text("utf-8"))
            self.assertEqual(json.loads(c.read_text("utf-8"))["positions_historiques_vers_fiches"],5)
    def test_44_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"exists.json";p.write_text("KEEP",encoding="utf-8")
            self.assertEqual(m.main(["--bilan",str(p)]),2)
            self.assertEqual(p.read_text("utf-8"),"KEEP")
    def test_45_cli_no_duplicate_dest(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"same.json"
            self.assertEqual(m.main(["--verifier-bilans-figes",
                "--fiches",str(p),"--bilan",str(p)]),2)
    def test_46_cli_no_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/"real.json"
            original.write_text("KEEP",encoding="utf-8")
            link=Path(d)/"alias.json";link.symlink_to(original)
            self.assertEqual(m.main(["--bilan",str(link)]),2)
            self.assertEqual(original.read_text("utf-8"),"KEEP")
    def test_47_cli_explicit_refusal(self):
        self.assertEqual(m.main(["--exiger-remise"]),3)
    def test_48_cli_refusal_even_verified(self):
        self.assertEqual(m.main(["--verifier-bilans-figes","--exiger-remise"]),3)
    def test_49_no_personal_or_raw_pdf(self):
        s=json.dumps(self.cards,ensure_ascii=False)
        self.assertNotIn("jeton_brut",s)
        self.assertNotIn("signature_image",s)
        self.assertNotIn("document_pdf_octets",s)
    def test_50_sha_real_member_not_pdf(self):
        self.assertTrue(self.cards["verification_octets_bilans_au_run_courant"])
        self.assertFalse(self.report["zip_original_reverifie_ce_run"])

def guard_check(name):
    def test(self):self.assertTrue(self.cfg["protections"][name])
    return test
for i,name in enumerate(sorted(m.GUARDS),51):
    setattr(TestsP54U,"test_%02d_protection"%i,guard_check(name))

if __name__=="__main__":
    unittest.main()
