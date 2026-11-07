import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_interpretation_sources_nova_p55f as m


def statuses(ville=None,mamh=None):
    return {
        "VILLE_2024":m.p55b.NON_FOURNIE if ville is None else ville,
        "MAMH_23027_2024":m.p55b.NON_FOURNIE if mamh is None else mamh,
    }


class TestP55F(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()

    def test_01_schema(self):
        self.assertEqual(self.cfg["schema_version"],"P55F-1")
    def test_02_exercice(self):
        self.assertEqual(self.cfg["exercice"],2024)
    def test_03_date_de_reference(self):
        self.assertEqual(self.cfg["date_reference"],"2026-11-03")
    def test_04_cinq_chainages(self):
        self.assertEqual(self.cfg["ancrages"],["P54Q","P55B","P55C","P55D","P55E"])
    def test_05_deux_documents_2024(self):
        self.assertEqual(len(m.SOURCES[:2]),2)
    def test_06_notice_versions(self):
        self.assertEqual(m.SOURCES[2][0],"DONNEES_QUEBEC_MAMH")
    def test_07_quatre_constats(self):
        self.assertEqual(len(m.NOTES),4)
    def test_08_constats_tous_non_authentifiants(self):
        self.assertTrue(all(x["niveau_preuve"]=="TEXTE_PUBLIC_NON_AUTHENTIFIANT"
                            for x in m.notes_expected()))
    def test_09_redressement_comparatif_2023(self):
        self.assertEqual(m.INTERPRETATION["redressement_comparatif_2023_cad"],1825176)
    def test_10_redressement_non_gain(self):
        self.assertFalse(m.INTERPRETATION["correction_comparative_comme_gain_autorisee"])
    def test_11_elimination_non_gain(self):
        self.assertFalse(m.INTERPRETATION["eliminations_comme_gain_autorisees"])
    def test_12_edition_exacte_obligatoire(self):
        self.assertFalse(m.INTERPRETATION["comparaison_sans_edition_exacte_autorisee"])
    def test_13_economies_certifiees_null(self):
        self.assertIsNone(m.INTERPRETATION["economies_certifiees_cad"])
    def test_14_originalite_non_confirmee(self):
        self.assertEqual(m.SOURCES[0][3],"NON_VERIFIES_DANS_CE_JALON")
    def test_15_no_gO_configuration(self):
        self.assertEqual(self.cfg["etat_initial"]["decision"],m.NO_GO)
    def test_16_toutes_protections_activees(self):
        self.assertTrue(all(self.cfg["protections"].values()))
    def test_17_ravq_contextuel(self):
        self.assertEqual(m.NOTES[0][3],"VENTILATION_SELON_RAVQ_1435")
    def test_18_edition_mamh_publique(self):
        self.assertIn("mamh.gouv.qc.ca",m.SOURCES[1][1])
    def test_19_rapport_ville_public(self):
        self.assertIn("ville.quebec.qc.ca",m.SOURCES[0][1])
    def test_20_rapport_initial_phase_manquants(self):
        self.assertEqual(m.public_report()["phase_prioritaire_p55e"],"COPIES_MANQUANTES")
    def test_21_rapport_initial_priorites(self):
        self.assertEqual(m.public_report()["prochaines_actions_p55e"],["A01","A02"])
    def test_22_rapport_initial_manquants_deux(self):
        self.assertEqual(m.public_report()["copies_pdf_manquantes"],2)
    def test_23_rapport_aucune_position(self):
        self.assertEqual(m.public_report()["positions_nfkc_reproduites_techniquement"],0)
    def test_24_rapport_contexte_quatre(self):
        self.assertEqual(m.public_report()["contextes_textuels_publics_references"],4)
    def test_25_rapport_montant_comparatif(self):
        self.assertEqual(m.public_report()["redressement_comparatif_2023_cad"],1825176)
    def test_26_rapport_redressement_pas_economie(self):
        self.assertFalse(m.public_report()["redressement_2023_est_economie_2024"])
    def test_27_rapport_elimination_pas_economie(self):
        self.assertFalse(m.public_report()["colonne_eliminations_est_gain_nouveau"])
    def test_28_rapport_aucune_authentification_emetteur(self):
        self.assertFalse(m.public_report()["version_pdf_officielle_actuelle_authentifiee"])
    def test_29_rapport_aucun_avis_independant(self):
        self.assertEqual(m.public_report()["avis_independants_authentifies"],0)
    def test_30_rapport_aucune_economie_certifiee(self):
        self.assertIsNone(m.public_report()["economies_certifiees_cad"])
    def test_31_rapport_no_go(self):
        self.assertEqual(m.public_report()["decision"],m.NO_GO)
    def test_32_rapport_pas_transmission(self):
        self.assertFalse(m.public_report()["transmission_externe_autorisee"])
    def test_33_rapport_pas_cloture(self):
        self.assertFalse(m.public_report()["cloture_automatique_autorisee"])
    def test_34_rapport_pas_fusion(self):
        self.assertFalse(m.public_report()["fusion_main_autorisee"])
    def test_35_etat_une_source_edition_differente(self):
        r=m.public_report(statuses(m.p55b.EDITION,m.p55b.CONCORDANCE))
        self.assertEqual(r["editions_divergentes_a_instruire"],1)
        self.assertEqual(r["phase_prioritaire_p55e"],"EDITIONS_A_INSTRUIRE")
    def test_36_etat_une_copie_manquante(self):
        r=m.public_report(statuses(m.p55b.CONCORDANCE))
        self.assertEqual(r["copies_pdf_manquantes"],1)
        self.assertEqual(r["prochaines_actions_p55e"],["A02"])
    def test_37_deux_concordances_pas_reproduction(self):
        r=m.public_report(statuses(m.p55b.CONCORDANCE,m.p55b.CONCORDANCE))
        self.assertEqual(r["phase_prioritaire_p55e"],"REPRODUCTION_NON_OBTENUE")
        self.assertEqual(r["positions_nfkc_reproduites_techniquement"],0)
    def test_38_deux_concordances_reproduction_technique(self):
        r=m.public_report(statuses(m.p55b.CONCORDANCE,m.p55b.CONCORDANCE),True)
        self.assertEqual(r["positions_nfkc_reproduites_techniquement"],5)
        self.assertFalse(r["version_pdf_officielle_actuelle_authentifiee"])
        self.assertIsNone(r["economies_certifiees_cad"])
    def test_39_reproduction_sans_deux_pdf_refuse(self):
        with self.assertRaises(ValueError):
            m.public_report(reproduced=True)
    def test_40_sources_inconnues_refusees(self):
        with self.assertRaises(ValueError):
            m.public_report({"FAUX":"CERTIFIE"},False)
    def test_41_plan_public_sans_offsets_ni_sha(self):
        plan=m.public_plan(m.public_report())
        txt=json.dumps(plan,ensure_ascii=False)
        self.assertNotIn("sha256",txt)
        self.assertNotIn("offset_texte",txt)
    def test_42_plan_sources_et_notice(self):
        self.assertEqual(len(m.public_plan(m.public_report())["sources_et_notice"]),3)
    def test_43_plan_constats_prudence(self):
        self.assertEqual(len(m.public_plan(m.public_report())["constats_prudence"]),4)
    def test_44_plan_priorites_amont(self):
        self.assertEqual(m.public_plan(m.public_report())["prochaines_actions_techniques"],["A01","A02"])
    def test_45_plan_refuse_gO(self):
        r=m.public_report();r["decision"]="GO"
        with self.assertRaises(ValueError):m.public_plan(r)
    def test_46_plan_refuse_redressement_converti_economie(self):
        r=m.public_report();r["redressement_2023_est_economie_2024"]=True
        with self.assertRaises(ValueError):m.public_plan(r)
    def test_47_plan_refuse_elimination_convertie_economie(self):
        r=m.public_report();r["colonne_eliminations_est_gain_nouveau"]=True
        with self.assertRaises(ValueError):m.public_plan(r)
    def test_48_plan_refuse_economie_factice(self):
        r=m.public_report();r["economies_certifiees_cad"]=1825176
        with self.assertRaises(ValueError):m.public_plan(r)
    def test_49_bilan_neutre_pas_donnees_privees(self):
        s=json.dumps(m.public_report(),ensure_ascii=False)
        for token in ("offset_texte","sha256","/mnt/","professionnel_identite"):
            self.assertNotIn(token,s)
    def test_50_plan_pas_demarche_externe(self):
        self.assertFalse(m.public_plan(m.public_report())["avis_comptable_ou_juridique_recu"])
    def test_51_cli_baseline(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"rapport.json"
            self.assertEqual(m.main(["--bilan-public",str(p)]),0)
            d=json.loads(p.read_text("utf8"))
            self.assertEqual(d["decision"],m.NO_GO)
    def test_52_cli_plan(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"plan.json"
            self.assertEqual(m.main(["--plan-public",str(p)]),0)
            d=json.loads(p.read_text("utf8"))
            self.assertEqual(len(d["constats_prudence"]),4)
    def test_53_cli_certification_interdite(self):
        self.assertEqual(m.main(["--exiger-certification"]),3)
    def test_54_cli_un_pdf_refuse(self):
        self.assertEqual(m.main(["--ville-pdf","/absent.pdf"]),2)
    def test_55_cli_une_sortie_dupliquee_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            p=str(Path(t)/"rapport.json")
            self.assertEqual(m.main(["--bilan-public",p,"--plan-public",p]),2)
    def test_56_cli_sortie_existante_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"rapport.json";p.write_text("{}")
            self.assertEqual(m.main(["--bilan-public",str(p)]),2)
    def test_57_cli_editions_divergentes_retour_4(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-fictive-ville");h.write_bytes(b"%PDF-fictive-mamh")
            v.chmod(0o600);h.chmod(0o600)
            b=Path(t)/"bilan.json"
            self.assertEqual(m.main(["--ville-pdf",str(v),
                                     "--mamh-pdf",str(h),
                                     "--bilan-public",str(b)]),4)
            data=json.loads(b.read_text())
            self.assertEqual(data["editions_divergentes_a_instruire"],2)
            self.assertEqual(data["redressement_2023_est_economie_2024"],False)
    def test_58_cli_entree_sous_permissions_non_securisees(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-fictive-ville");h.write_bytes(b"%PDF-fictive-mamh")
            v.chmod(0o644);h.chmod(0o600)
            self.assertEqual(m.main(["--ville-pdf",str(v),
                                     "--mamh-pdf",str(h)]),2)
    def test_59_cli_lien_symbolique_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf";alias=Path(t)/"alias.pdf"
            v.write_bytes(b"%PDF-fictive-ville");h.write_bytes(b"%PDF-fictive-mamh")
            v.chmod(0o600);h.chmod(0o600)
            alias.symlink_to(v)
            self.assertEqual(m.main(["--ville-pdf",str(alias),
                                     "--mamh-pdf",str(h)]),2)
    def test_60_p55e_priorites_et_version_semblable_pas_certifiant(self):
        r=m.public_report(statuses(m.p55b.CONCORDANCE,m.p55b.CONCORDANCE),True)
        p=m.public_plan(r)
        self.assertEqual(p["prochaines_actions_techniques"],["A05","A06"])
        self.assertFalse(p["avis_comptable_ou_juridique_recu"])
        self.assertFalse(r["qualification_professionnelle_independante"])


if __name__=="__main__":
    unittest.main()
