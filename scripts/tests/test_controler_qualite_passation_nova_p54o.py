#!/usr/bin/env python3
"""P54O: 69 validations de passation, sans preuves privées ou contact externe."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controler_qualite_passation_nova_p54o as m

def sources():
    cfg=m.configuration()
    package,notes=m.canonical_sources(cfg)
    return cfg,package,notes,m.matrix(cfg,package)

class TestP54O(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.package,cls.notes,cls.matrix=sources()
        cls.bilan=m.summary(cls.cfg,cls.matrix)
    def test_01_version(self):self.assertEqual(self.cfg["schema_version"],"P54O-1")
    def test_02_upstream(self):self.assertEqual(self.cfg["source_jalon"],"P54N")
    def test_03_2024(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_04_provenance_run(self):self.assertEqual(self.cfg["source_p54d_run"],40120462237)
    def test_05_total_five(self):self.assertEqual(len(self.matrix["observations"]),5)
    def test_06_index_set(self):self.assertEqual({c["observation_index"] for c in self.matrix["observations"]},set(range(5)))
    def test_07_four_unknown(self):self.assertEqual(sum(c["classification"]=="INDETERMINE" for c in self.matrix["observations"]),4)
    def test_08_date_probable_once(self):self.assertEqual(sum(c["classification"]=="ANNEE_DATE_PROBABLE" for c in self.matrix["observations"]),1)
    def test_09_date_index(self):self.assertEqual(self.matrix["observations"][4]["observation_index"],2)
    def test_10_date_mamh(self):self.assertEqual(self.matrix["observations"][4]["source"],"mamh")
    def test_11_date_zone(self):self.assertEqual(self.matrix["observations"][4]["zone"],"FIN")
    def test_12_date_pdf(self):self.assertEqual(self.matrix["observations"][4]["index_pdf_base_zero"],162)
    def test_13_date_not_p54e(self):self.assertFalse(self.matrix["observations"][4]["est_dossier_p54e"])
    def test_14_four_in_p54e(self):self.assertEqual(sum(c["est_dossier_p54e"] for c in self.matrix["observations"]),4)
    def test_15_city_first(self):self.assertEqual(self.matrix["observations"][0]["identifiant"],"P54E-V-001")
    def test_16_city_pdf(self):self.assertEqual(self.matrix["observations"][0]["index_pdf_base_zero"],102)
    def test_17_mamh_three(self):self.assertEqual(len([x for x in self.matrix["observations"] if x["source"]=="mamh" and x["est_dossier_p54e"]]),3)
    def test_18_hash_ville(self):self.assertEqual(len(self.matrix["copies_pdf_sha256_reference"]["ville"]),64)
    def test_19_hash_mamh(self):self.assertEqual(len(self.matrix["copies_pdf_sha256_reference"]["mamh"]),64)
    def test_20_initial_ready_false(self):self.assertFalse(self.bilan["pret_a_transmettre"])
    def test_21_initial_no_go(self):self.assertEqual(self.bilan["decision"],m.NO_GO)
    def test_22_no_money(self):self.assertIsNone(self.bilan["economies_certifiees_cad"])
    def test_23_four_open(self):self.assertEqual(self.bilan["dossiers_p54e_ouverts"],4)
    def test_24_40_unverified(self):self.assertEqual(self.bilan["taches_p54n_a_instruire"],40)
    def test_25_96_open(self):self.assertEqual(self.bilan["controles_p54b_non_attestes"],96)
    def test_26_8_open(self):self.assertEqual(self.bilan["controles_p54c_non_attestes"],8)
    def test_27_10_blockers(self):self.assertEqual(len(self.matrix["points_bloquants"]),10)
    def test_28_all_blocked(self):self.assertTrue(all(x["etat"]=="NON_LEVE" for x in self.matrix["points_bloquants"]))
    def test_29_no_false_authentication(self):self.assertTrue(all(not x["preuve_reçue_et_authentifiee"] for x in self.matrix["points_bloquants"]))
    def test_30_no_false_approval(self):self.assertEqual(self.bilan["autorisations_de_transmission_obtenues"],0)
    def test_31_no_real_contract(self):self.assertEqual(self.bilan["mandats_professionnels_reellement_signes"],0)
    def test_32_no_signed_opinion(self):self.assertEqual(self.bilan["avis_originaux_independants_authentifies"],0)
    def test_33_no_merge(self):self.assertFalse(self.bilan["fusion_main_autorisee"])
    def test_34_all_positions_non_financial(self):self.assertTrue(all(not x["pret_a_declarer_financier"] for x in self.matrix["observations"]))
    def test_35_all_positions_need_localisation(self):self.assertTrue(all(x["localisation_exacte_et_nature_a_revoir"] for x in self.matrix["observations"]))
    def test_36_canonical_public_packet(self):self.assertEqual(m.validate_public_inputs(self.cfg,self.package)[0],self.package)
    def test_37_canonical_public_instructions(self):self.assertEqual(m.validate_public_inputs(self.cfg,instructions=self.notes)[1],self.notes)
    def test_38_packet_altered_task_refused(self):
        t=copy.deepcopy(self.package)
        t["dossiers"][0]["instructions"][0]["etat"]="VERIFIE"
        with self.assertRaises(ValueError):m.validate_public_inputs(self.cfg,t)
    def test_39_packet_altered_approval_refused(self):
        t=copy.deepcopy(self.package);t["dossiers"][0]["cloture_autorisee"]=True
        with self.assertRaises(ValueError):m.validate_public_inputs(self.cfg,t)
    def test_40_packet_altered_source_refused(self):
        t=copy.deepcopy(self.package);t["dossiers"][0]["index_page_pdf_zero_based"]=103
        with self.assertRaises(ValueError):m.validate_public_inputs(self.cfg,t)
    def test_41_packet_extra_private_field_refused(self):
        t=copy.deepcopy(self.package);t["expert_nominatif"]="PERSONNE"
        with self.assertRaises(ValueError):m.validate_public_inputs(self.cfg,t)
    def test_42_bad_instructions_refused(self):
        with self.assertRaises(ValueError):m.validate_public_inputs(self.cfg,instructions=self.notes+"\nGO")
    def test_43_report_all_five(self):
        text=m.markdown_report(self.matrix,self.bilan)
        for x in self.matrix["observations"]:self.assertIn(x["identifiant"],text)
    def test_44_report_all_blocks(self):
        text=m.markdown_report(self.matrix,self.bilan)
        for x in self.matrix["points_bloquants"]:self.assertIn(x["reference"],text)
    def test_45_report_no_personal_names(self):
        self.assertNotIn("Jean Dupont",m.markdown_report(self.matrix,self.bilan))
    def test_46_no_effective_solicitations(self):
        self.assertTrue(self.cfg["protections"]["aucune_solicitation_automatique"])
    def test_47_cli_baseline_three_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);a=p/"plan.json";b=p/"bilan.json";c=p/"plan.md"
            self.assertEqual(m.main(["--plan",str(a),"--bilan",str(b),"--rapport",str(c)]),0)
            self.assertEqual(len(json.loads(a.read_text("utf-8"))["observations"]),5)
            self.assertEqual(json.loads(b.read_text("utf-8"))["conditions_humaines_non_levees"],10)
            self.assertIn("NO_GO_AUTOMATIQUE",c.read_text("utf-8"))
    def test_48_cli_canonical_generated_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"p54n.json";b=Path(d)/"p54n.md";out=Path(d)/"p54o.json"
            self.assertEqual(m.p54n.main(["--dossier",str(a),"--instructions",str(b)]),0)
            self.assertEqual(m.main(["--paquet-p54n",str(a),
                 "--instructions-p54n",str(b),"--bilan",str(out)]),0)
    def test_49_cli_tampered_p54n_json_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"source.json";bad=copy.deepcopy(self.package)
            bad["dossiers"][0]["instructions"][0]["verification_professionnelle_obtenue"]=True
            f.write_text(json.dumps(bad),encoding="utf-8")
            self.assertEqual(m.main(["--paquet-p54n",str(f)]),2)
    def test_50_cli_tampered_p54n_md_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"instructions.md";f.write_text(self.notes+"\nMODIFIE",encoding="utf-8")
            self.assertEqual(m.main(["--instructions-p54n",str(f)]),2)
    def test_51_cli_explicit_transmission_refusal(self):
        self.assertEqual(m.main(["--exiger-transmission"]),3)
    def test_52_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"bilan.json";f.write_text("PRESERVE",encoding="utf-8")
            self.assertEqual(m.main(["--bilan",str(f)]),2)
            self.assertEqual(f.read_text(encoding="utf-8"),"PRESERVE")
    def test_53_cli_duplicate_out_paths_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"same.json"
            self.assertEqual(m.main(["--plan",str(f),"--bilan",str(f)]),2)
    def test_54_cli_source_output_collision_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"same.json"
            self.assertEqual(m.main(["--paquet-p54n",str(f),"--plan",str(f)]),2)
    def test_55_cli_symlink_input_refused(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"original.json";target.write_text(json.dumps(self.package),encoding="utf-8")
            alias=Path(d)/"alias.json";alias.symlink_to(target)
            self.assertEqual(m.main(["--paquet-p54n",str(alias)]),2)
    def test_56_cli_invalid_json_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"bad.json";f.write_text("{!",encoding="utf-8")
            self.assertEqual(m.main(["--paquet-p54n",str(f)]),2)
    def test_57_cli_oversized_packet_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"bad.json";f.write_text("X"*131073,encoding="utf-8")
            self.assertEqual(m.main(["--paquet-p54n",str(f)]),2)
    def test_58_no_go_all_layers(self):
        self.assertEqual(self.matrix["decision"],self.bilan["decision"])
    def test_59_original_config_stays_neutral(self):
        self.assertEqual(self.cfg["etat_initial"]["mandats_reels_signes"],0)
    def test_60_public_sources_only(self):
        self.assertTrue(all(x["publication"] in ("ville","mamh") for x in self.package["dossiers"]))

def guard_test(name):
    def test(self):self.assertTrue(self.cfg["protections"][name])
    return test
for i,key in enumerate(sorted(m.GUARDS),61):
    setattr(TestP54O,"test_%02d_guard"%i,guard_test(key))

if __name__=="__main__":
    unittest.main()
