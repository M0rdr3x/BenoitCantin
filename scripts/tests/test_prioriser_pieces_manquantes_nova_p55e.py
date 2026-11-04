import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prioriser_pieces_manquantes_nova_p55e as m


def states(ville=None,mamh=None):
    return {
        "VILLE_2024":ville if ville is not None else m.MISSING,
        "MAMH_23027_2024":mamh if mamh is not None else m.MISSING,
    }


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


def reproduction():
    return {
        "statut":"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION",
        "sources":{x:"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION"
                   for x in m.p55c.p54q.NAMES},
        "copies_verifiees_par_hachage":2,
        "cinq_positions_reproduites":True,
        "positions":positions(),
    }


def fixture(root,prepared=False):
    root=Path(root)
    v=root/"ville.pdf";h=root/"mamh.pdf"
    v.write_bytes(b"%PDF-fausse-ville")
    h.write_bytes(b"%PDF-fausse-mamh")
    v.chmod(0o600);h.chmod(0o600)
    z=root/"p54z.json";a=root/"p55a.json"
    c=root/"p55c.json";d=root/"p55d.json"
    zd=m.p54z.blank_model()
    if prepared:
        for row in zd["dossiers"]:
            for item in row["controles"]:
                item["etat"]="PREPARATION_DECLAREE_NON_VERIFIEE"
    m.p54z.write_new(z,zd,private=True)
    _,sha=m.p55a.upstream(z)
    ad=m.p55a.model(sha)
    if prepared:
        for row in ad["dossiers"]:
            for item in row["verifications"]:
                item["etat"]="PREPARE_NON_ATTESTE"
    m.p54z.write_new(a,ad,private=True)
    cd=m.p55c.private_model(positions())
    if prepared:
        for obs in cd["observations"]:
            obs["etat_revue"]="REPERE_DECLARE_NON_AUTHENTIFIE"
            obs["contre_revue_declaree"]="DECLAREE_DISTINCTE_NON_AUTHENTIFIEE"
    m.p54z.write_new(c,cd,private=True)
    dd=m.p55d.private_model(c.read_bytes())
    m.p54z.write_new(d,dd,private=True)
    return v,h,z,a,c,d


class TestP55E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()

    def test_01_config_schema(self):
        self.assertEqual(self.cfg["schema_version"],"P55E-1")
    def test_02_exercice(self):
        self.assertEqual(self.cfg["exercice"],2024)
    def test_03_cinq_references(self):
        self.assertEqual(len(m.REFS),5)
    def test_04_deux_mandats_amont(self):
        self.assertEqual(len(m.p55d.MANDATES),2)
    def test_05_actions_douze(self):
        self.assertEqual(len(m.ACTIONS),12)
    def test_06_actions_sans_doublon(self):
        self.assertEqual(len(set(x[0] for x in m.ACTIONS)),12)
    def test_07_categories_fermees(self):
        self.assertEqual(len(m.ACCESS),4)
    def test_08_protections(self):
        self.assertTrue(all(self.cfg["protections"].values()))
    def test_09_compatibilite_p55d(self):
        self.assertEqual(m.p55d.configuration()["etat_initial"]["positions_a_instruire"],40)
    def test_10_rapport_initial(self):
        self.assertEqual(m.report()["phase_prioritaire"],"COPIES_MANQUANTES")
    def test_11_rapport_priorites(self):
        self.assertEqual(m.report()["prochaines_actions_codes"],["A01","A02"])
    def test_12_deux_absentes(self):
        self.assertEqual(m.report()["copies_publiques_absentes"],2)
    def test_13_rapport_40_non_traitements(self):
        self.assertEqual(m.report()["suivi_p55d_declaratif_non_atteste"]["A_COLLECTER"],40)
    def test_14_rapport_aucun_avis(self):
        self.assertEqual(m.report()["avis_independants_authentifies"],0)
    def test_15_economies_null(self):
        self.assertIsNone(m.report()["economies_certifiees_cad"])
    def test_16_refus_go(self):
        self.assertEqual(m.report()["decision"],m.NO_GO)
    def test_17_refus_transmission(self):
        self.assertFalse(m.report()["transmission_externe_autorisee"])
    def test_18_refus_depense(self):
        self.assertFalse(m.report()["engagement_depense_autorise"])
    def test_19_refus_cloture(self):
        self.assertFalse(m.report()["cloture_dossier_autorisee"])
    def test_20_refus_fusion(self):
        self.assertFalse(m.report()["fusion_main_autorisee"])
    def test_21_priorite_si_ville_manquante(self):
        phase,code=m.priority(states(mamh=m.MATCH),False)
        self.assertEqual((phase,code),("COPIES_MANQUANTES",["A01"]))
    def test_22_priorite_si_mamh_manquant(self):
        phase,code=m.priority(states(ville=m.MATCH),False)
        self.assertEqual((phase,code),("COPIES_MANQUANTES",["A02"]))
    def test_23_edition_modifiee(self):
        phase,code=m.priority(states(ville=m.EDITION,mamh=m.MATCH),False)
        self.assertEqual((phase,code),("EDITIONS_A_INSTRUIRE",["A03"]))
    def test_24_edition_et_absence(self):
        phase,code=m.priority(states(ville=m.EDITION),False)
        self.assertEqual((phase,code),("EDITIONS_A_INSTRUIRE",["A02","A03"]))
    def test_25_deux_sha_reproduction_manquante(self):
        phase,code=m.priority(states(m.MATCH,m.MATCH),False)
        self.assertEqual((phase,code),("REPRODUCTION_NON_OBTENUE",["A04"]))
    def test_26_reproduites_non_certifiees(self):
        phase,code=m.priority(states(m.MATCH,m.MATCH),True)
        self.assertEqual((phase,code),("REVUE_HUMAINE_A_ORGANISER",["A05","A06"]))
    def test_27_reserves_prioritaires(self):
        phase,code=m.priority(states(m.MATCH,m.MATCH),True,1)
        self.assertEqual(code,["A05","A07"])
    def test_28_reproduction_si_pdf_manquant_refuse(self):
        with self.assertRaises(ValueError):
            m.priority(states(),True)
    def test_29_reproduction_si_edition_refuse(self):
        with self.assertRaises(ValueError):
            m.priority(states(m.EDITION,m.MATCH),True)
    def test_30_action_inconnue_refusee(self):
        with self.assertRaises(ValueError):
            m.priority({"VILLE_2024":"CERTIFIE","MAMH_23027_2024":m.MATCH},False)
    def test_31_keys_source_strictes(self):
        with self.assertRaises(ValueError):
            m.priority({"VILLE_2024":m.MISSING},False)
    def test_32_booleen_nombre_reserves_refuse(self):
        with self.assertRaises(ValueError):
            m.priority(states(m.MATCH,m.MATCH),True,True)
    def test_33_reserves_excessives_refusees(self):
        with self.assertRaises(ValueError):
            m.priority(states(m.MATCH,m.MATCH),True,201)
    def test_34_bilan_edition_pas_economie(self):
        r=m.report(states(m.EDITION,m.MATCH))
        self.assertEqual(r["editions_divergentes_a_instruire"],1)
        self.assertIsNone(r["economies_certifiees_cad"])
    def test_35_bilan_reproduction_non_certifiant(self):
        r=m.report(states(m.MATCH,m.MATCH),True)
        self.assertEqual(r["positions_nfkc_reproduites_techniquement"],5)
        self.assertEqual(r["experts_engages_authentifies"],0)
    def test_36_blocages_herites_sans_cloture(self):
        parent={k:(1 if k=="RESERVE" else
                   49 if k=="NON_INSTRUIT" else 0)
                for k in m.p55a.STATES}
        r=m.report(states(m.MATCH,m.MATCH),True,
                   p55a_counts=parent,inherited_z=2,p55c_review=(4,1,1))
        self.assertEqual(r["suspensions_p54z_heritees"],2)
        self.assertEqual(r["reserves_p55a_heritees"],1)
        self.assertEqual(r["phase_prioritaire"],"RESERVES_ET_ACCES_A_EXAMINER")
        self.assertFalse(r["cloture_dossier_autorisee"])
    def test_37_mauvais_compteur_p55d(self):
        with self.assertRaises(ValueError):
            m.report(totals={"A_COLLECTER":40})
    def test_38_somme_p55d_wrong(self):
        with self.assertRaises(ValueError):
            m.report(totals={k:1 for k in m.p55d.STATES})
    def test_39_declarations_p55d_sans_pdf_refusees(self):
        count=m.p55d.empty_counts()
        count["A_COLLECTER"]=39;count["RESERVE"]=1
        with self.assertRaises(ValueError):
            m.report(totals=count)
    def test_40_p55a_reporte_50(self):
        r=m.report()
        self.assertEqual(r["suspensions_p55a_heritees"],0)
        self.assertEqual(r["reserves_p55a_heritees"],0)
    def test_41_p55a_nombre_invalide(self):
        with self.assertRaises(ValueError):
            m.report(p55a_counts={"NON_INSTRUIT":50})
    def test_42_p55c_suspensions_bool_refuse(self):
        with self.assertRaises(ValueError):
            m.report(p55c_review=(5,True,0))
    def test_43_plan_12_actions(self):
        self.assertEqual(len(m.public_plan(m.report())["actions"]),12)
    def test_44_plan_deux_actions_prioritaires(self):
        p=m.public_plan(m.report())
        self.assertEqual([x["code"] for x in p["actions"]
                          if x["statut"]=="ACTION_PRIORITAIRE_A_REALISER"],["A01","A02"])
    def test_45_plan_sans_experts_mandates(self):
        p=m.public_plan(m.report())
        self.assertEqual(p["decision"],m.NO_GO)
        self.assertTrue(p["aucune_requete_externe_effectuee"])
    def test_46_plan_deux_sources_publiques(self):
        self.assertEqual(len(m.public_plan(m.report())["sources_officielles_a_consulter"]),2)
    def test_47_plan_censure_sha_et_offsets(self):
        raw=json.dumps(m.public_plan(m.report()),ensure_ascii=False)
        self.assertNotIn("sha256",raw)
        self.assertNotIn("offset_",raw)
    def test_48_bilan_censure_sha_et_offsets(self):
        raw=json.dumps(m.report(),ensure_ascii=False)
        self.assertNotIn("sha256",raw)
        self.assertNotIn("offset_",raw)
    def test_49_plan_faux_go_refuse(self):
        with self.assertRaises(ValueError):
            m.public_plan({"schema_version":"P55E-BILAN-PUBLIC-1","decision":"GO",
                           "prochaines_actions_codes":[]})
    def test_50_plan_injection_action_refusee(self):
        r=m.report();r["prochaines_actions_codes"]=["INCONNU"]
        with self.assertRaises(ValueError):m.public_plan(r)
    def test_51_cli_plan_neutre(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"plan.json";b=Path(t)/"bilan.json"
            self.assertEqual(m.main(["--plan-public",str(p),
                                     "--bilan-public",str(b)]),0)
            self.assertEqual(json.loads(p.read_text())["actions"][0]["code"],"A01")
            self.assertEqual(json.loads(b.read_text())["copies_publiques_absentes"],2)
    def test_52_cli_faux_go(self):
        self.assertEqual(m.main(["--exiger-go"]),3)
    def test_53_cli_pdf_unique_refuse(self):
        self.assertEqual(m.main(["--ville-pdf","/absent.pdf"]),2)
    def test_54_cli_plan_prive_sans_chainage_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(m.main(["--plan-prive",str(Path(t)/"prive.json")]),2)
    def test_55_cli_sources_privées_partielles_refuse(self):
        self.assertEqual(m.main(["--declarations-p54z","/absent.json"]),2)
    def test_56_cli_sortie_existante_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"out.json";out.write_text("{}")
            self.assertEqual(m.main(["--plan-public",str(out)]),2)
    def test_57_cli_sorties_dupliquees_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            out=str(Path(t)/"out.json")
            self.assertEqual(m.main(["--plan-public",out,"--bilan-public",out]),2)
    def test_58_privé_0600_et_dossiers_en_cours(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t)
            p=Path(t)/"plan_prive.json"
            with patch.object(m.p55c,"local_sources",
                              return_value=(states(m.MATCH,m.MATCH),reproduction())):
                code=m.main(["--ville-pdf",str(v),"--mamh-pdf",str(h),
                             "--declarations-p54z",str(z),"--relecture-p55a",str(a),
                             "--fiche-p55c",str(c),"--suivi-p55d",str(d),
                             "--plan-prive",str(p)])
            self.assertEqual(code,0)
            self.assertEqual(p.stat().st_mode & 0o777,0o600)
            result=json.loads(p.read_text())
            self.assertEqual(len(result["dossiers"]),5)
            self.assertEqual(len(result["dossiers"][0]["exigences_a_traiter"]),8)
            self.assertFalse(result["transmission_autorisee"])
    def test_59_privé_reprise_reserve_et_suspension(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t)
            x=json.loads(d.read_text())
            x["observations"][0]["exigences"][0]["etat"]="RESERVE"
            x["observations"][1]["exigences"][1]["etat"]="INACCESSIBLE"
            d.unlink()
            m.p54z.write_new(d,x,private=True)
            p=Path(t)/"plan_prive.json";b=Path(t)/"bilan.json"
            with patch.object(m.p55c,"local_sources",
                              return_value=(states(m.MATCH,m.MATCH),reproduction())):
                code=m.main(["--ville-pdf",str(v),"--mamh-pdf",str(h),
                             "--declarations-p54z",str(z),"--relecture-p55a",str(a),
                             "--fiche-p55c",str(c),"--suivi-p55d",str(d),
                             "--plan-prive",str(p),"--bilan-public",str(b)])
            self.assertEqual(code,0)
            out=json.loads(b.read_text())
            self.assertEqual(out["phase_prioritaire"],"RESERVES_ET_ACCES_A_EXAMINER")
            self.assertEqual(out["obstacles_declaratifs_agreges_non_uniques"],2)
    def test_60_fiche_alteree_refusee(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t)
            c.write_text("{}")
            c.chmod(0o600)
            with patch.object(m.p55c,"local_sources",
                              return_value=(states(m.MATCH,m.MATCH),reproduction())):
                self.assertEqual(m.main([
                    "--ville-pdf",str(v),"--mamh-pdf",str(h),
                    "--declarations-p54z",str(z),"--relecture-p55a",str(a),
                    "--fiche-p55c",str(c),"--suivi-p55d",str(d)]),2)
    def test_61_pdf_versions_differentes_retour_4(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"v.pdf";h=Path(t)/"h.pdf"
            v.write_bytes(b"%PDF-FAUX-V");h.write_bytes(b"%PDF-FAUX-H")
            v.chmod(0o600);h.chmod(0o600)
            p=Path(t)/"bilan.json"
            self.assertEqual(m.main(["--ville-pdf",str(v),"--mamh-pdf",str(h),
                                     "--bilan-public",str(p)]),4)
            self.assertEqual(json.loads(p.read_text())["editions_divergentes_a_instruire"],2)
    def test_62_privé_source_non_reproduite_refus_4(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t)
            with patch.object(m.p55c,"local_sources",
                              return_value=(states(m.EDITION,m.MATCH),None)):
                self.assertEqual(m.main([
                    "--ville-pdf",str(v),"--mamh-pdf",str(h),
                    "--declarations-p54z",str(z),"--relecture-p55a",str(a),
                    "--fiche-p55c",str(c),"--suivi-p55d",str(d)]),4)
    def test_63_etats_p55d_non_certification(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t,prepared=True)
            doc=json.loads(d.read_text())
            doc["observations"][0]["exigences"][0]["etat"]="PREPARATION_DECLAREE_NON_ATTESTEE"
            d.unlink();m.p54z.write_new(d,doc,private=True)
            with patch.object(m.p55c,"local_sources",
                              return_value=(states(m.MATCH,m.MATCH),reproduction())):
                _,totals,_,_,_=m.private_followup(str(z),str(a),str(c),str(d),positions())
            self.assertEqual(totals["PREPARATION_DECLAREE_NON_ATTESTEE"],1)
            self.assertEqual(m.report(states(m.MATCH,m.MATCH),True,totals)["experts_engages_authentifies"],0)
    def test_64_plan_prive_sans_offsets(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t)
            data=json.loads(d.read_text())
            p=m.private_worklist(data)
            txt=json.dumps(p)
            self.assertNotIn("offset_texte",txt)
            self.assertNotIn("sha256",txt)
            self.assertNotIn("signature",txt)
    def test_65_references_privees_cinq(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t)
            p=m.private_worklist(json.loads(d.read_text()))
            self.assertEqual([x["reference"] for x in p["dossiers"]],list(m.REFS))
    def test_66_schema_privé_refuse_faux(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t)
            p=json.loads(d.read_text());p["schema_version"]="FAUX"
            with self.assertRaises(ValueError):m.private_worklist(p)
    def test_67_lien_prive_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t)
            link=Path(t)/"alias.json";link.symlink_to(d)
            with self.assertRaises(ValueError):m.p55a.private_source(link)
    def test_68_permissions_prive_refusees(self):
        with tempfile.TemporaryDirectory() as t:
            v,h,z,a,c,d=fixture(t)
            d.chmod(0o644)
            with self.assertRaises(ValueError):m.p55a.private_source(d)
    def test_69_gouv_ni_deploiement(self):
        self.assertEqual(self.cfg["etat_initial"]["decision"],m.NO_GO)
        self.assertEqual(self.cfg["etat_initial"]["mandats_professionnels_reels_signes"],0)
    def test_70_workflow_ne_publie_aucune_preuve(self):
        self.assertEqual(m.report()["avis_independants_authentifies"],0)
        self.assertEqual(m.report()["obstacles_declaratifs_agreges_non_uniques"],0)


if __name__=="__main__":
    unittest.main()
