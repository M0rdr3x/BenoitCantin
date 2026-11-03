import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import rapprocher_pieces_documentaires_nova_p55c as m


def synthetic_positions():
    """P54P-style synthetic offsets, never actual PDF data."""
    results=[]
    for ref,src,idx,page,zone,category in m.ROWS:
        results.append({
            "index_observation_p54d":idx,
            "source":src,
            "dossier":None if ref=="P54O-DATE-001" else ref,
            "pdf_index_zero":page,
            "offset_texte_extrait":100+idx,
            "longueur_texte_normalise_nfkc":10000,
            "zone_confirmee_par_parseur":zone,
            "classification_indicative":category,
            "aucune_conclusion_financiere":True,
        })
    return results


def synthetic_attempt():
    return {
        "statut":"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION",
        "sources":{x:"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION"
                   for x in m.p54q.NAMES},
        "copies_verifiees_par_hachage":2,
        "cinq_positions_reproduites":True,
        "positions":synthetic_positions(),
    }


def prepared_upstream():
    z=m.p54z.blank_model()
    for row in z["dossiers"]:
        for part in row["controles"]:
            part["etat"]="PREPARATION_DECLAREE_NON_VERIFIEE"
    a=m.p55a.model("a"*64)
    for row in a["dossiers"]:
        for part in row["verifications"]:
            part["etat"]="PREPARE_NON_ATTESTE"
    return z,a


class TestP55C(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=m.configuration()

    def setUp(self):
        self.positions=synthetic_positions()
        self.sheet=m.private_model(self.positions)

    def t(self,i):
        return self.sheet["observations"][i]

    def test_01_schema(self):
        self.assertEqual(self.config["schema_version"],"P55C-1")
    def test_02_exercice(self):
        self.assertEqual(self.config["exercice"],2024)
    def test_03_cinq_observations(self):
        self.assertEqual(len(m.ROWS),5)
    def test_04_sources(self):
        self.assertEqual({r[1] for r in m.ROWS},{"ville","mamh"})
    def test_05_page_ville(self):
        self.assertEqual(m.ROWS[0][3],102)
    def test_06_page_mamh(self):
        self.assertTrue(all(r[3]==162 for r in m.ROWS[1:]))
    def test_07_date_probable(self):
        self.assertEqual(m.ROWS[2][0],"P54O-DATE-001")
    def test_08_cinq_positions_validees(self):
        self.assertEqual(len(m.validate_positions(self.positions)),5)
    def test_09_schema_prive(self):
        self.assertEqual(self.sheet["schema_version"],"P55C-FICHE-PRIVEE-1")
    def test_10_tous_non_examnes(self):
        self.assertTrue(all(r["etat_revue"]=="NON_EXAMINE"
                            for r in self.sheet["observations"]))
    def test_11_qualification_non_certifiee(self):
        self.assertIn("VALEUR_A_EXAMINER_NON_CERTIFIEE",m.QUALIFICATIONS)
    def test_12_protections(self):
        self.assertTrue(all(self.config["protections"].values()))
    def test_13_pas_economies(self):
        self.assertIsNone(m.public_report()["economies_certifiees_cad"])
    def test_14_no_go(self):
        self.assertEqual(m.public_report()["decision"],m.NO_GO)
    def test_15_pas_original(self):
        self.assertEqual(m.public_report()["sources_pdf_locales_soumises"],0)
    def test_16_pas_reproduction(self):
        self.assertEqual(m.public_report()["positions_nfkc_reproduites_techniquement"],0)
    def test_17_aucune_signature(self):
        self.assertEqual(m.public_report()["avis_independants_authentifies"],0)
    def test_18_pas_transmission(self):
        self.assertFalse(m.public_report()["transmission_externe_autorisee"])
    def test_19_pas_fermeture(self):
        self.assertFalse(m.public_report()["cloture_des_dossiers_autorisee"])
    def test_20_pas_fusion(self):
        self.assertFalse(m.public_report()["fusion_main_autorisee"])
    def test_21_no_sensitive_baseline(self):
        s=json.dumps(m.public_report())
        self.assertNotIn("offset_texte",s)
        self.assertNotIn("P54E-V-001",s)
        self.assertNotIn("sha256",s)
    def test_22_private_sheet_initial(self):
        counts,second,kinds=m.validate_private(self.sheet,self.positions)
        self.assertEqual(counts["NON_EXAMINE"],5)
        self.assertEqual(second["NON_EFFECTUEE"],5)
        self.assertEqual(kinds["NON_QUALIFIE"],5)
    def test_23_reject_six_positions(self):
        p=self.positions + [copy.deepcopy(self.positions[-1])]
        with self.assertRaises(ValueError):m.private_model(p)
    def test_24_reject_offset_negative(self):
        p=copy.deepcopy(self.positions)
        p[0]["offset_texte_extrait"]=-1
        with self.assertRaises(ValueError):m.private_model(p)
    def test_25_reject_offset_duplicate(self):
        p=copy.deepcopy(self.positions)
        p[3]["offset_texte_extrait"]=p[1]["offset_texte_extrait"]
        with self.assertRaises(ValueError):m.private_model(p)
    def test_26_reject_source_wrong(self):
        p=copy.deepcopy(self.positions)
        p[0]["source"]="mamh"
        with self.assertRaises(ValueError):m.private_model(p)
    def test_27_reject_raw_token(self):
        p=copy.deepcopy(self.positions)
        p[0]["jeton"]="1234"
        with self.assertRaises(ValueError):m.private_model(p)
    def test_28_reject_changed_offset_sheet(self):
        self.t(0)["offset_texte_nfkc"]+=1
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_29_reject_changed_page(self):
        self.t(0)["pdf_index_zero"]=103
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_30_reject_boolean_offset(self):
        self.t(0)["offset_texte_nfkc"]=True
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_31_reject_duplicate_reference(self):
        self.t(1)["reference"]=self.t(0)["reference"]
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_32_reject_personal_field(self):
        self.t(0)["identite"]="secret"
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_33_reject_signature(self):
        self.t(0)["signature"]="FAUSSE"
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_34_reject_unrecognized_status(self):
        self.t(0)["etat_revue"]="CERTIFIE"
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_35_reject_qualif_sans_examen(self):
        self.t(0)["qualification_declaree"]="DATE_POSSIBLE_NON_CERTIFIEE"
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_36_reject_contre_revue_sans_examen(self):
        self.t(0)["contre_revue_declaree"]="DECLAREE_DISTINCTE_NON_AUTHENTIFIEE"
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_37_reject_revue_sans_amont(self):
        self.t(0)["etat_revue"]="REPERE_DECLARE_NON_AUTHENTIFIE"
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_38_revue_non_authentifiee_avec_amont(self):
        z,a=prepared_upstream()
        self.t(0)["etat_revue"]="REPERE_DECLARE_NON_AUTHENTIFIE"
        result=m.validate_private(self.sheet,self.positions,z,a)
        self.assertEqual(result[0]["REPERE_DECLARE_NON_AUTHENTIFIE"],1)
    def test_39_contre_revue_non_authentifiee_avec_amont(self):
        z,a=prepared_upstream()
        self.t(0)["etat_revue"]="REPERE_DECLARE_NON_AUTHENTIFIE"
        self.t(0)["contre_revue_declaree"]="DECLAREE_DISTINCTE_NON_AUTHENTIFIEE"
        result=m.validate_private(self.sheet,self.positions,z,a)
        self.assertEqual(result[1]["DECLAREE_DISTINCTE_NON_AUTHENTIFIEE"],1)
    def test_40_amont_p54z_suspendu_bloque_avis(self):
        z,a=prepared_upstream()
        z["dossiers"][0]["controles"][0]["etat"]="SUSPENDU"
        self.t(0)["etat_revue"]="REPERE_DECLARE_NON_AUTHENTIFIE"
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions,z,a)
    def test_41_amont_p55a_reserve_bloque_avis(self):
        z,a=prepared_upstream()
        a["dossiers"][0]["verifications"][0]["etat"]="RESERVE"
        self.t(0)["etat_revue"]="REPERE_DECLARE_NON_AUTHENTIFIE"
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions,z,a)
    def test_42_reserve_permise_sans_pretendre_certification(self):
        self.t(0)["etat_revue"]="RESERVE_OUVERTE"
        result=m.validate_private(self.sheet,self.positions)
        self.assertEqual(result[0]["RESERVE_OUVERTE"],1)
    def test_43_suspension_permise(self):
        self.t(0)["etat_revue"]="SUSPENDU"
        result=m.validate_private(self.sheet,self.positions)
        self.assertEqual(result[0]["SUSPENDU"],1)
    def test_44_desaccord_requiert_reserve(self):
        self.t(0)["contre_revue_declaree"]="DESACCORD_OUVERT"
        with self.assertRaises(ValueError):
            m.validate_private(self.sheet,self.positions)
    def test_45_desaccord_reserve_autorise(self):
        self.t(0)["etat_revue"]="RESERVE_OUVERTE"
        self.t(0)["contre_revue_declaree"]="DESACCORD_OUVERT"
        result=m.validate_private(self.sheet,self.positions)
        self.assertEqual(result[1]["DESACCORD_OUVERT"],1)
    def test_46_pas_qualif_monetaire_certifiee(self):
        self.t(0)["etat_revue"]="RESERVE_OUVERTE"
        self.t(0)["qualification_declaree"]="VALEUR_A_EXAMINER_NON_CERTIFIEE"
        result=m.validate_private(self.sheet,self.positions)
        report=m.public_report(claimed=result)
        self.assertIsNone(report["economies_certifiees_cad"])
        self.assertEqual(report["avis_independants_authentifies"],0)
    def test_47_refus_comptage_ouvert_sans_reproduction(self):
        counts={name:(1 if name=="RESERVE_OUVERTE"
                      else 4 if name=="NON_EXAMINE" else 0)
                for name in m.STATES}
        second={name:(5 if name=="NON_EFFECTUEE" else 0)
                for name in m.COUNTER_REVIEWS}
        qual={name:(5 if name=="NON_QUALIFIE" else 0)
              for name in m.QUALIFICATIONS}
        with self.assertRaises(ValueError):
            m.public_report(claimed=(counts,second,qual))
    def test_48_reproduction_simulee_non_certifiante(self):
        states={k:m.p55b.CONCORDANCE for k in m.p55b.PDF_CODES}
        r=m.public_report(states,synthetic_attempt())
        self.assertEqual(r["positions_nfkc_reproduites_techniquement"],5)
        self.assertEqual(r["avis_independants_authentifies"],0)
    def test_49_reproduction_sans_copies_rejetee(self):
        with self.assertRaises(ValueError):
            m.public_report(attempt=synthetic_attempt())
    def test_50_blocages_amont_conserves(self):
        counts={name:(1 if name=="SUSPENDU" else
                      1 if name=="RESERVE" else
                      48 if name=="NON_INSTRUIT" else 0)
                for name in m.p55a.STATES}
        r=m.public_report(upstream_counts=counts,inherited=2)
        self.assertEqual(r["suspensions_p54z_heritees"],2)
        self.assertEqual(r["suspensions_p55a_non_levees"],1)
        self.assertEqual(r["reserves_p55a_non_levees"],1)
    def test_51_refus_booleen_suspension(self):
        with self.assertRaises(ValueError):
            m.public_report(inherited=True)
    def test_52_sources_edition_differente(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-FAUX-VILLE");h.write_bytes(b"%PDF-FAUX-MAMH")
            v.chmod(0o600);h.chmod(0o600)
            states,attempt=m.local_sources(str(v),str(h))
            self.assertIsNone(attempt)
            self.assertEqual(sum(s==m.p55b.EDITION for s in states.values()),2)
    def test_53_pdf_unique_refuse(self):
        with self.assertRaises(ValueError):
            m.local_sources("ville.pdf",None)
    def test_54_pdf_lien_symbolique_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-FAUX-VILLE");h.write_bytes(b"%PDF-FAUX-MAMH")
            v.chmod(0o600);h.chmod(0o600)
            alias=Path(t)/"alias.pdf";alias.symlink_to(v)
            with self.assertRaises(ValueError):
                m.local_sources(str(alias),str(h))
    def test_55_amont_deux_ou_aucun(self):
        with self.assertRaises(ValueError):
            m.upstream_claims(path_z="z.json")
    def test_56_amont_par_defaut(self):
        z,a,counts,inherit=m.upstream_claims()
        self.assertIsNone(z)
        self.assertIsNone(a)
        self.assertEqual(inherit,0)
    def test_57_cli_neutre(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"bilan.json"
            self.assertEqual(m.main(["--bilan-public",str(out)]),0)
            d=json.loads(out.read_text())
            self.assertEqual(d["positions_nfkc_reproduites_techniquement"],0)
            self.assertEqual(d["decision"],m.NO_GO)
    def test_58_cli_exiger_go(self):
        self.assertEqual(m.main(["--exiger-go"]),3)
    def test_59_cli_fiche_sans_pdf_refusee(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"fiche.json"
            self.assertEqual(m.main(["--creer-fiche-privee",str(out)]),2)
    def test_60_cli_sources_differentes_statut_4(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-FAUX-VILLE");h.write_bytes(b"%PDF-FAUX-MAMH")
            v.chmod(0o600);h.chmod(0o600)
            out=Path(t)/"bilan.json"
            self.assertEqual(m.main(["--ville-pdf",str(v),
                                     "--mamh-pdf",str(h),
                                     "--bilan-public",str(out)]),4)
            self.assertEqual(json.loads(out.read_text())["editions_divergentes_a_instruire"],2)
    def test_61_cli_fiche_neutre_interdite_si_pas_positions(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-FAUX-VILLE");h.write_bytes(b"%PDF-FAUX-MAMH")
            v.chmod(0o600);h.chmod(0o600)
            out=Path(t)/"fiche.json"
            self.assertEqual(m.main(["--ville-pdf",str(v),
                                     "--mamh-pdf",str(h),
                                     "--creer-fiche-privee",str(out)]),4)
            self.assertFalse(out.exists())
    def test_62_cli_fiche_synthetique_creation(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-FAUX-VILLE");h.write_bytes(b"%PDF-FAUX-MAMH")
            v.chmod(0o600);h.chmod(0o600)
            out=Path(t)/"fiche.json"
            states={k:m.p55b.CONCORDANCE for k in m.p55b.PDF_CODES}
            with patch.object(m,"local_sources",return_value=(states,synthetic_attempt())):
                self.assertEqual(m.main(["--ville-pdf",str(v),
                                         "--mamh-pdf",str(h),
                                         "--creer-fiche-privee",str(out)]),0)
            self.assertEqual(out.stat().st_mode&0o777,0o600)
            self.assertEqual(len(json.loads(out.read_text())["observations"]),5)
    def test_63_cli_fiche_synthetique_relecture_et_ancrage(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-FAUX-VILLE");h.write_bytes(b"%PDF-FAUX-MAMH")
            v.chmod(0o600);h.chmod(0o600)
            z=Path(t)/"z.json";a=Path(t)/"a.json"
            f=Path(t)/"fiche.json";out=Path(t)/"bilan.json"
            uz=m.p54z.blank_model()
            uz["dossiers"][0]["controles"][0]["etat"]="SUSPENDU"
            m.p54z.write_new(z,uz,private=True)
            _,sha=m.p55a.upstream(z)
            m.p54z.write_new(a,m.p55a.model(sha),private=True)
            m.p54z.write_new(f,self.sheet,private=True)
            states={k:m.p55b.CONCORDANCE for k in m.p55b.PDF_CODES}
            with patch.object(m,"local_sources",return_value=(states,synthetic_attempt())):
                self.assertEqual(m.main(["--ville-pdf",str(v),
                                         "--mamh-pdf",str(h),
                                         "--declarations-p54z",str(z),
                                         "--relecture-p55a",str(a),
                                         "--fiche-privee-p55c",str(f),
                                         "--bilan-public",str(out)]),0)
            d=json.loads(out.read_text())
            self.assertEqual(d["suspensions_p54z_heritees"],1)
            self.assertEqual(d["positions_nfkc_reproduites_techniquement"],5)
            self.assertEqual(d["avis_independants_authentifies"],0)
    def test_64_cli_fiche_altérée_refusee(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-FAUX-VILLE");h.write_bytes(b"%PDF-FAUX-MAMH")
            v.chmod(0o600);h.chmod(0o600)
            z=Path(t)/"z.json";a=Path(t)/"a.json"
            f=Path(t)/"fiche.json"
            m.p54z.write_new(z,m.p54z.blank_model(),private=True)
            _,sha=m.p55a.upstream(z)
            m.p54z.write_new(a,m.p55a.model(sha),private=True)
            doc=copy.deepcopy(self.sheet)
            doc["observations"][0]["offset_texte_nfkc"]=999
            m.p54z.write_new(f,doc,private=True)
            states={k:m.p55b.CONCORDANCE for k in m.p55b.PDF_CODES}
            with patch.object(m,"local_sources",return_value=(states,synthetic_attempt())):
                self.assertEqual(m.main(["--ville-pdf",str(v),
                                         "--mamh-pdf",str(h),
                                         "--declarations-p54z",str(z),
                                         "--relecture-p55a",str(a),
                                         "--fiche-privee-p55c",str(f)]),2)
    def test_65_cli_faux_go_meme_si_reproduction(self):
        with tempfile.TemporaryDirectory() as t:
            v=Path(t)/"ville.pdf";h=Path(t)/"mamh.pdf"
            v.write_bytes(b"%PDF-FAUX-VILLE");h.write_bytes(b"%PDF-FAUX-MAMH")
            v.chmod(0o600);h.chmod(0o600)
            states={k:m.p55b.CONCORDANCE for k in m.p55b.PDF_CODES}
            with patch.object(m,"local_sources",return_value=(states,synthetic_attempt())):
                self.assertEqual(m.main(["--ville-pdf",str(v),
                                         "--mamh-pdf",str(h),"--exiger-go"]),3)
    def test_66_code_no_go_dependances(self):
        self.assertEqual(self.config["etat_initial"]["decision"],m.NO_GO)
        self.assertEqual(self.config["etat_initial"]["mandats_p54h_signes"],0)


if __name__=="__main__":
    unittest.main()
