import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preparer_dossier_experts_nova_p55d as m


def positions():
    return [
        {
            "index_observation_p54d":idx,
            "source":src,
            "dossier":None if ref=="P54O-DATE-001" else ref,
            "pdf_index_zero":page,
            "offset_texte_extrait":100+idx,
            "longueur_texte_normalise_nfkc":10000,
            "zone_confirmee_par_parseur":zone,
            "classification_indicative":category,
            "aucune_conclusion_financiere":True,
        }
        for ref,src,idx,page,zone,category in m.p55c.ROWS
    ]


def reproduced():
    return {
        "statut":"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION",
        "sources":{k:"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION"
                   for k in m.p55c.p54q.NAMES},
        "copies_verifiees_par_hachage":2,
        "cinq_positions_reproduites":True,
        "positions":positions(),
    }


def source_states():
    return {k:m.p55b.CONCORDANCE for k in m.p55b.PDF_CODES}


class TestP55D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=m.configuration()

    def setUp(self):
        self.template=m.private_model(b'{"synthetic":"private sheet"}')

    def test_01_config_schema(self):
        self.assertEqual(self.config["schema_version"],"P55D-1")
    def test_02_exercice_2024(self):
        self.assertEqual(self.config["exercice"],2024)
    def test_03_cinq_observations(self):
        self.assertEqual(len(m.REFS),5)
    def test_04_huit_controles(self):
        self.assertEqual(len(m.GATES),8)
    def test_05_40_positions(self):
        self.assertEqual(sum(len(d["exigences"])
                             for d in self.template["observations"]),40)
    def test_06_deux_mandats_non_signes(self):
        self.assertEqual(len(m.MANDATES),2)
    def test_07_protections(self):
        self.assertTrue(all(self.config["protections"].values()))
    def test_08_statuts_fermes(self):
        self.assertEqual(len(m.STATES),5)
    def test_09_tous_a_collecter(self):
        self.assertEqual(m.empty_counts()["A_COLLECTER"],40)
    def test_10_aucun_avis(self):
        self.assertEqual(m.public_report()["avis_independants_authentifies"],0)
    def test_11_no_go(self):
        self.assertEqual(m.public_report()["decision"],m.NO_GO)
    def test_12_economies_null(self):
        self.assertIsNone(m.public_report()["economies_certifiees_cad"])
    def test_13_pas_fusion_main(self):
        self.assertFalse(m.public_report()["fusion_main_autorisee"])
    def test_14_pas_transmission(self):
        self.assertFalse(m.public_report()["envoi_dossier_a_expert_autorise"])
    def test_15_pas_depense(self):
        self.assertFalse(m.public_report()["engagement_de_depense_autorise"])
    def test_16_pas_cloture(self):
        self.assertFalse(m.public_report()["cloture_dossier_autorisee"])
    def test_17_pas_pieces_attestees(self):
        self.assertEqual(m.public_report()["pieces_professionnelles_authentifiees"],0)
    def test_18_sources_non_fournies(self):
        self.assertEqual(m.public_report()["sources_non_fournies"],2)
    def test_19_pas_repro(self):
        self.assertEqual(m.public_report()["positions_nfkc_reproduites"],0)
    def test_20_plan_40_positions(self):
        self.assertEqual(m.public_plan()["total_exigences"],40)
    def test_21_plan_mandats(self):
        self.assertEqual(len(m.public_plan()["mandats_projets_non_transmis"]),2)
    def test_22_plan_sources(self):
        self.assertEqual(len(m.public_plan()["sources_officielles_a_obtenir"]),2)
    def test_23_plan_non_certification(self):
        self.assertFalse(m.public_plan()["envoi_autorise"])
    def test_24_prive_pas_identite(self):
        self.assertNotIn("identite",json.dumps(self.template).lower())
    def test_25_prive_pas_signature(self):
        self.assertNotIn("signature",json.dumps(self.template).lower())
    def test_26_bilan_pas_sha_p55c(self):
        self.assertNotIn(self.template["sha256_fiche_p55c"],
                         json.dumps(m.public_report()))
    def test_27_bilan_pas_offsets(self):
        self.assertNotIn("offset_texte",json.dumps(m.public_report()))
    def test_28_validation_40_bases(self):
        counts=m.validate_followup(self.template,
                                   b'{"synthetic":"private sheet"}',
                                   None,None,None)
        self.assertEqual(counts["A_COLLECTER"],40)
    def test_29_sha_change_refuse(self):
        self.template["sha256_fiche_p55c"]="c"*64
        with self.assertRaises(ValueError):
            m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                None,None,None)
    def test_30_champ_identite_refuse(self):
        self.template["observations"][0]["identite"]="N"
        with self.assertRaises(ValueError):
            m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                None,None,None)
    def test_31_signature_cellule_refusee(self):
        self.template["observations"][0]["exigences"][0]["signature"]="X"
        with self.assertRaises(ValueError):
            m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                None,None,None)
    def test_32_dossier_duplique_refuse(self):
        self.template["observations"][1]["reference"]=m.REFS[0]
        with self.assertRaises(ValueError):
            m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                None,None,None)
    def test_33_missing_case_refuse(self):
        self.template["observations"].pop()
        with self.assertRaises(ValueError):
            m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                None,None,None)
    def test_34_missing_gate_refuse(self):
        self.template["observations"][0]["exigences"].pop()
        with self.assertRaises(ValueError):
            m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                None,None,None)
    def test_35_gate_name_change_refuse(self):
        self.template["observations"][0]["exigences"][0]["code"]="FAUX"
        with self.assertRaises(ValueError):
            m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                None,None,None)
    def test_36_fausse_certification_refusee(self):
        self.template["observations"][0]["exigences"][0]["etat"]="CERTIFIE"
        with self.assertRaises(ValueError):
            m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                None,None,None)
    def test_37_prep_sans_p55c_refusee(self):
        self.template["observations"][0]["exigences"][0]["etat"]="PREPARATION_DECLAREE_NON_ATTESTEE"
        with self.assertRaises(ValueError):
            m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                None,None,None)
    def test_38_reserve_permise_non_certifiante(self):
        self.template["observations"][0]["exigences"][0]["etat"]="RESERVE"
        counts=m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                   None,None,None)
        self.assertEqual(counts["RESERVE"],1)
    def test_39_inaccessible_permise(self):
        self.template["observations"][0]["exigences"][0]["etat"]="INACCESSIBLE"
        counts=m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                   None,None,None)
        self.assertEqual(counts["INACCESSIBLE"],1)
    def test_40_suspension_permise(self):
        self.template["observations"][0]["exigences"][0]["etat"]="SUSPENDU"
        counts=m.validate_followup(self.template,b'{"synthetic":"private sheet"}',
                                   None,None,None)
        self.assertEqual(counts["SUSPENDU"],1)
    def test_41_inherited_reserves(self):
        counts={s:(48 if s=="NON_INSTRUIT" else 1
                   if s in ("RESERVE","SUSPENDU") else 0)
                for s in m.p55a.STATES}
        r=m.public_report(upstream_a=counts,inherited_z=2,upstream_c=(3,1,1))
        self.assertEqual(r["suspensions_p54z_heritees"],2)
        self.assertEqual(r["reserves_p55a_heritees"],1)
        self.assertEqual(r["suspensions_p55c_heritees"],1)
    def test_42_suivi_sans_reproduction_refuse(self):
        data=m.empty_counts()
        data["A_COLLECTER"]-=1
        data["RESERVE"]=1
        with self.assertRaises(ValueError):
            m.public_report(followup=data)
    def test_43_fausses_sources_refusees(self):
        with self.assertRaises(ValueError):
            m.public_report(states={"VILLE_2024":"AUTHENTIFIE"})
    def test_44_sources_reprod_double_vraies(self):
        r=m.public_report(states=source_states(),reproduced=True)
        self.assertEqual(r["positions_nfkc_reproduites"],5)
        self.assertEqual(r["avis_independants_authentifies"],0)
    def test_45_reproduction_sans_sources_refusee(self):
        with self.assertRaises(ValueError):
            m.public_report(reproduced=True)
    def test_46_upstream_partiel_refuse(self):
        with self.assertRaises(ValueError):
            m.upstream("z.json",None,None,positions())
    def test_47_upstream_neutre_50(self):
        z,a,c,raw,counts,inherited,review=m.upstream()
        self.assertIsNone(raw)
        self.assertEqual(counts["NON_INSTRUIT"],50)
        self.assertEqual(review,(5,0,0))
    def test_48_prep_exige_contre_lecture(self):
        z=m.p54z.blank_model()
        a=m.p55a.model("a"*64)
        c=m.p55c.private_model(positions())
        self.assertFalse(m.is_prepared(0,z,a,c))
    def test_49_lien_vers_une_fiche_privee(self):
        self.assertEqual(len(self.template["sha256_fiche_p55c"]),64)
    def test_50_no_go_chaine(self):
        self.assertEqual(self.config["etat_initial"]["decision"],m.NO_GO)
        self.assertEqual(self.config["etat_initial"]["mandats_professionnels_signes"],0)
    def test_51_cli_neutre(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"out.json"
            self.assertEqual(m.main(["--bilan-public",str(p)]),0)
            self.assertEqual(json.loads(p.read_text())["decision"],m.NO_GO)
    def test_52_cli_plan_neutre(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"plan.json"
            self.assertEqual(m.main(["--plan-public",str(p)]),0)
            self.assertEqual(json.loads(p.read_text())["total_exigences"],40)
    def test_53_cli_exiger_transmission(self):
        self.assertEqual(m.main(["--exiger-transmission"]),3)
    def test_54_cli_pdf_unique_refuse(self):
        self.assertEqual(m.main(["--ville-pdf","/inexistant.pdf"]),2)
    def test_55_cli_suivi_sans_pdf_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(m.main(["--creer-suivi-prive",str(Path(t)/"followup.json")]),2)
    def test_56_cli_sorties_dupliquees(self):
        with tempfile.TemporaryDirectory() as t:
            p=str(Path(t)/"public.json")
            self.assertEqual(m.main(["--bilan-public",p,"--plan-public",p]),2)
    def test_57_cli_sortie_existante(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"public.json";p.write_text("{}")
            self.assertEqual(m.main(["--bilan-public",str(p)]),2)
    def test_58_cli_public_non_nominatif(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"public.json"
            self.assertEqual(m.main(["--bilan-public",str(p)]),0)
            self.assertNotIn("sha256",p.read_text())
            self.assertNotIn("offset_",p.read_text())
    def test_59_suivi_prive_0600(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"private.json"
            m.p54z.write_new(p,self.template,private=True)
            self.assertEqual(p.stat().st_mode&0o777,0o600)
    def test_60_symlink_private_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"private.json"
            m.p54z.write_new(p,self.template,private=True)
            s=Path(t)/"link.json";s.symlink_to(p)
            with self.assertRaises(ValueError):
                m.p55a.private_source(s)
    def test_61_perms_private_refusees(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"private.json";p.write_text(json.dumps(self.template))
            p.chmod(0o644)
            with self.assertRaises(ValueError):
                m.p55a.private_source(p)
    def test_62_no_false_court_decision(self):
        self.assertFalse(m.public_plan()["expert_mandate"])
        self.assertEqual(m.public_plan()["decision"],m.NO_GO)
    def test_63_no_human_decision_from_count_40(self):
        counts={name:(40 if name=="PREPARATION_DECLAREE_NON_ATTESTEE" else 0)
                for name in m.STATES}
        result=m.public_report(source_states() if False else None)
        self.assertEqual(result["pieces_professionnelles_authentifiees"],0)
        # Deliberately cannot claim all prepared without reproduction.
        with self.assertRaises(ValueError):
            m.public_report(followup=counts)
    def test_64_report_suspensions_without_closure(self):
        states=source_states()
        followup=m.empty_counts()
        followup["A_COLLECTER"]=39
        followup["SUSPENDU"]=1
        result=m.public_report(states,reproduced=True,followup=followup)
        self.assertEqual(result["exigences_p55d_suspendues"],1)
        self.assertFalse(result["cloture_dossier_autorisee"])


if __name__=="__main__":
    unittest.main()
