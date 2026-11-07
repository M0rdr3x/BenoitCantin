import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controler_integrite_pieces_nova_p55g as m


def pdf(p,data=b"%PDF-synthetic-copy-2024\\n%%EOF"):
    p=Path(p)
    p.write_bytes(data)
    p.chmod(0o600)
    return p


def synthetic_data(v,h):
    values=[]
    for p,row in zip((v,h),m.p55b.SOURCE_DATA):
        seq=list(row)
        seq[5]=p.stat().st_size
        seq[6]=hashlib.sha256(p.read_bytes()).hexdigest()
        values.append(tuple(seq))
    return tuple(values)


def input_pair(prefix):
    v=pdf(Path(prefix)/"ville2024.pdf",b"%PDF-synthetic-ville-2024\\n%%EOF")
    h=pdf(Path(prefix)/"mamh2024.pdf",b"%PDF-synthetic-mamh-2024\\n%%EOF")
    return v,h


def original_states():
    return {code:m.p55b.CONCORDANCE for code in m.CODES}


def dummy_reproduction():
    return {
        "cinq_positions_reproduites":True,
        "positions":[{"offset_texte_extrait":i} for i in range(5)],
    }


def neutral_reproduction():
    return original_states(),dummy_reproduction()


class TestP55G(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()

    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.v,self.h=input_pair(self.root)

    def matched(self):
        return patch.object(m.p55b,"SOURCE_DATA",synthetic_data(self.v,self.h))

    def run_cli(self,*arguments,pdf_reproduce=True,matched=True):
        old_config=self.cfg
        context=self.matched() if matched else patch.object(
            m.p55b,"SOURCE_DATA",m.p55b.SOURCE_DATA)
        fake=neutral_reproduction() if pdf_reproduce else (original_states(),None)
        with patch.object(m,"configuration",return_value=old_config),context,patch.object(
                m.p55c,"local_sources",return_value=fake):
            return m.main(["--ville-pdf",str(self.v),
                           "--mamh-pdf",str(self.h),*arguments])

    def test_01_config_version(self):
        self.assertEqual(self.cfg["schema_version"],"P55G-1")
    def test_02_document_codes(self):
        self.assertEqual(self.cfg["codes_documents"],["VILLE_2024","MAMH_23027_2024"])
    def test_03_etats_trois(self):
        self.assertEqual(len(m.STATES),3)
    def test_04_gardes_36(self):
        self.assertEqual(len(m.GUARDS),36)
    def test_05_protections_toutes_true(self):
        self.assertTrue(all(self.cfg["protections"].values()))
    def test_06_no_go(self):
        self.assertEqual(self.cfg["etat_initial"]["decision"],m.NO_GO)
    def test_07_aucune_economie_certifiee(self):
        self.assertIsNone(self.cfg["etat_initial"]["economies_certifiees_cad"])
    def test_08_deux_sources_vraies_non_acquises(self):
        self.assertEqual(self.cfg["etat_initial"]["documents_fournis"],0)
    def test_09_jalons_de_reference(self):
        self.assertEqual(self.cfg["sources"][-2:],["P55E","P55F"])
    def test_10_checksum_fichier_reel_synthetique(self):
        size,sha=m.checksum_pdf(self.v)
        self.assertEqual(size,self.v.stat().st_size)
        self.assertEqual(sha,hashlib.sha256(self.v.read_bytes()).hexdigest())
    def test_11_hash_concordance_test_synthetique(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            self.assertEqual([r["statut"] for r in rows],[m.MATCH,m.MATCH])
    def test_12_edition_divergente_reference_vraie(self):
        rows=m.capture_pair(self.v,self.h)
        self.assertEqual([r["statut"] for r in rows],[m.DIVERGENT,m.DIVERGENT])
    def test_13_recu_hash_ensemble(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            r=m.make_receipt(rows)
        self.assertEqual(r["sha256_ensemble_metadonnees"],m.joint_hash(rows))
    def test_14_recu_date_utc(self):
        with self.matched():
            r=m.make_receipt(m.capture_pair(self.v,self.h))
        self.assertTrue(r["controle_informatique_utc"].endswith("+00:00"))
    def test_15_recu_date_naive_refusee(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            with self.assertRaises(ValueError):
                m.make_receipt(rows,checked_at="2026-11-03T23:15:00")
    def test_16_recu_date_locale_refusee(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            with self.assertRaises(ValueError):
                m.make_receipt(rows,checked_at="2026-11-03T18:15:00-05:00")
    def test_17_recu_sans_signature(self):
        with self.matched():
            r=m.make_receipt(m.capture_pair(self.v,self.h))
        self.assertNotIn("signature",json.dumps(r).replace(
            '"absence_signature_professionnelle": true',""))
        self.assertTrue(r["absence_signature_professionnelle"])
    def test_18_recu_ne_contient_ni_chemin_ni_texte_pdf(self):
        with self.matched():
            txt=json.dumps(m.make_receipt(m.capture_pair(self.v,self.h)))
        self.assertNotIn(str(self.root),txt)
        self.assertNotIn("synthetic-ville",txt)
    def test_19_recu_relecture_identique_ok(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            receipt=m.make_receipt(rows,reproduced=True)
            self.assertTrue(m.verify_receipt(receipt,rows,True))
    def test_20_recu_taille_alteree_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            receipt=m.make_receipt(rows)
            receipt["sources"][0]["taille_octets_lus"]+=1
            with self.assertRaises(ValueError):m.verify_receipt(receipt,rows,False)
    def test_21_recu_sha_altere_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            receipt=m.make_receipt(rows)
            receipt["sources"][0]["sha256_octets_lus"]="f"*64
            with self.assertRaises(ValueError):m.verify_receipt(receipt,rows,False)
    def test_22_recu_champ_nominatif_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            receipt=m.make_receipt(rows)
            receipt["identite"]="personne"
            with self.assertRaises(ValueError):m.verify_receipt(receipt,rows,False)
    def test_23_recu_fausse_certification_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            receipt=m.make_receipt(rows)
            receipt["absence_authentification_emetteur"]=False
            with self.assertRaises(ValueError):m.verify_receipt(receipt,rows,False)
    def test_24_recu_authenticite_fausse_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            receipt=m.make_receipt(rows)
            receipt["decision"]="GO"
            with self.assertRaises(ValueError):m.verify_receipt(receipt,rows,False)
    def test_25_recu_reproduction_alteree_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            receipt=m.make_receipt(rows,False)
            receipt["positions_nfkc_reproduites_techniquement"]=5
            with self.assertRaises(ValueError):m.verify_receipt(receipt,rows,False)
    def test_26_deux_sources_inversees_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            with self.assertRaises(ValueError):m.valid_rows(rows[::-1])
    def test_27_edition_divergente_ne_peut_declarer_match(self):
        rows=m.capture_pair(self.v,self.h)
        rows[0]["statut"]=m.MATCH
        with self.assertRaises(ValueError):m.valid_rows(rows)
    def test_28_recu_duplique_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            with self.assertRaises(ValueError):m.valid_rows([rows[0],rows[0]])
    def test_29_recu_sha_invalide_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            rows[1]["sha256_octets_lus"]="xxx"
            with self.assertRaises(ValueError):m.valid_rows(rows)
    def test_30_recu_zero_octet_refuse(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            rows[0]["taille_octets_lus"]=0
            with self.assertRaises(ValueError):m.valid_rows(rows)
    def test_31_recu_ajout_champ_interdit(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            rows[0]["noms"]=["X"]
            with self.assertRaises(ValueError):m.valid_rows(rows)
    def test_32_recu_fausse_date_calendrier_refusee(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            with self.assertRaises(ValueError):
                m.make_receipt(rows,checked_at="2026-02-30T00:00:00+00:00")
    def test_33_pas_reproduction_sur_edition(self):
        rows=m.capture_pair(self.v,self.h)
        with self.assertRaises(ValueError):m.public_report(rows,True)
    def test_34_rapport_neutre(self):
        r=m.public_report()
        self.assertEqual(r["copies_locales_fournies"],0)
        self.assertEqual(r["etape_prioritaire_p55e"],"COPIES_MANQUANTES")
    def test_35_rapport_neutre_no_go(self):
        self.assertEqual(m.public_report()["decision"],m.NO_GO)
    def test_36_rapport_neutre_aucun_sha(self):
        s=json.dumps(m.public_report())
        self.assertNotIn("sha256",s)
        self.assertNotIn(str(self.v),s)
    def test_37_rapport_deux_concordances_non_certifiantes(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            r=m.public_report(rows,True)
        self.assertEqual(r["copies_concordantes_historique_non_authentifiees"],2)
        self.assertFalse(r["source_actuelle_authentifiee_par_emetteur"])
        self.assertFalse(r["recu_prive_est_attestation_de_provenance"])
    def test_38_rapport_deux_editions_divergentes(self):
        r=m.public_report(m.capture_pair(self.v,self.h))
        self.assertEqual(r["editions_divergentes_a_instruire"],2)
        self.assertIsNone(r["economies_certifiees_cad"])
    def test_39_rapport_sans_fichiers_ne_peut_recu_verifie(self):
        with self.assertRaises(ValueError):m.public_report(None,False,True)
    def test_40_recu_pas_economie_certifiee(self):
        with self.matched():
            r=m.make_receipt(m.capture_pair(self.v,self.h))
        self.assertNotIn("economies_certifiees_cad",r)
        self.assertEqual(r["decision"],m.NO_GO)
    def test_41_plan_sans_info_privee(self):
        s=json.dumps(m.public_plan())
        self.assertNotIn("sha256",s)
        self.assertNotIn(str(self.root),s)
    def test_42_plan_2_urls_sources(self):
        self.assertEqual(len(m.public_plan()["sources_officielles_a_obtenir"]),2)
    def test_43_plan_recu_non_signature(self):
        self.assertTrue(m.public_plan()["recu_n_est_pas_signature"])
    def test_44_permission_pdf_refuse(self):
        self.v.chmod(0o644)
        with self.assertRaises(ValueError):m.checksum_pdf(self.v)
    def test_45_fichier_absent_refuse(self):
        with self.assertRaises(ValueError):m.checksum_pdf(self.root/"non.pdf")
    def test_46_lien_symbolique_refuse(self):
        link=self.root/"link.pdf"
        link.symlink_to(self.v)
        with self.assertRaises(ValueError):m.checksum_pdf(link)
    def test_47_entete_non_pdf_refuse(self):
        pdf(self.v,b"NONPDF")
        with self.assertRaises(ValueError):m.checksum_pdf(self.v)
    def test_48_trop_gros_refuse(self):
        with self.assertRaises(ValueError):m.checksum_pdf(self.v,max_size=5)
    def test_49_lecture_meme_fichier_deux_fois_refuse(self):
        with self.assertRaises(ValueError):m.capture_pair(self.v,self.v)
    def test_50_cli_neutre_bilan_et_plan(self):
        p=self.root/"bilan.json";q=self.root/"plan.json"
        self.assertEqual(m.main(["--bilan-public",str(p),"--plan-public",str(q)]),0)
        self.assertEqual(json.loads(p.read_text())["copies_locales_fournies"],0)
    def test_51_cli_exiger_authenticite_refuse(self):
        self.assertEqual(m.main(["--exiger-authenticite"]),3)
    def test_52_cli_pdf_unique_refuse(self):
        self.assertEqual(m.main(["--ville-pdf",str(self.v)]),2)
    def test_53_cli_recu_sans_pdfs_refuse(self):
        self.assertEqual(m.main(["--creer-recu-prive",str(self.root/"rec.json")]),2)
    def test_54_cli_recu_lecture_et_creation_exclues(self):
        self.assertEqual(m.main([
            "--creer-recu-prive",str(self.root/"rec.json"),
            "--verifier-recu-prive",str(self.root/"other.json")]),2)
    def test_55_cli_sorties_dupliquees_refusees(self):
        p=str(self.root/"out.json")
        self.assertEqual(m.main(["--bilan-public",p,"--plan-public",p]),2)
    def test_56_cli_sortie_existante_refuse(self):
        p=self.root/"out.json";p.write_text("{}")
        self.assertEqual(m.main(["--plan-public",str(p)]),2)
    def test_57_cli_editions_divergentes_recu_non_certifie(self):
        p=self.root/"recu.json";b=self.root/"bilan.json"
        code=self.run_cli("--creer-recu-prive",str(p),"--bilan-public",str(b),
                          matched=False)
        self.assertEqual(code,4)
        data=json.loads(p.read_text())
        self.assertEqual([r["statut"] for r in data["sources"]],
                         [m.DIVERGENT,m.DIVERGENT])
        self.assertEqual(p.stat().st_mode&0o777,0o600)
        self.assertEqual(json.loads(b.read_text())["editions_divergentes_a_instruire"],2)
    def test_58_cli_creation_recu_synthetique_concordant(self):
        rec=self.root/"recu.json";b=self.root/"bilan.json"
        code=self.run_cli("--creer-recu-prive",str(rec),
                          "--bilan-public",str(b))
        self.assertEqual(code,0)
        self.assertEqual(rec.stat().st_mode&0o777,0o600)
        d=json.loads(rec.read_text())
        self.assertEqual(d["positions_nfkc_reproduites_techniquement"],5)
        self.assertTrue(d["absence_authentification_emetteur"])
        self.assertEqual(json.loads(b.read_text())["decision"],m.NO_GO)
    def test_59_cli_relecture_recu_synthetique_ok(self):
        rec=self.root/"recu.json";b=self.root/"bilan.json"
        self.assertEqual(self.run_cli("--creer-recu-prive",str(rec)),0)
        self.assertEqual(self.run_cli("--verifier-recu-prive",str(rec),
                                      "--bilan-public",str(b)),0)
        self.assertTrue(json.loads(b.read_text())["recu_prive_recontrole_octets"])
    def test_60_cli_relecture_recu_altere_refus(self):
        rec=self.root/"recu.json"
        self.assertEqual(self.run_cli("--creer-recu-prive",str(rec)),0)
        obj=json.loads(rec.read_text())
        obj["sha256_ensemble_metadonnees"]="0"*64
        rec.write_text(json.dumps(obj))
        rec.chmod(0o600)
        self.assertEqual(self.run_cli("--verifier-recu-prive",str(rec)),2)
    def test_61_cli_pdf_change_apres_recu_refuse(self):
        rec=self.root/"recu.json"
        self.assertEqual(self.run_cli("--creer-recu-prive",str(rec)),0)
        pdf(self.v,b"%PDF-nouvelle-copie-ville\\n%%EOF")
        self.assertEqual(self.run_cli("--verifier-recu-prive",str(rec)),2)
    def test_62_cli_recu_ne_peut_ecraser(self):
        rec=self.root/"recu.json"
        self.assertEqual(self.run_cli("--creer-recu-prive",str(rec)),0)
        self.assertEqual(self.run_cli("--creer-recu-prive",str(rec)),2)
    def test_63_cli_second_hash_stabilite_test(self):
        original=m.capture_pair
        with self.matched():
            pristine=m.capture_pair(self.v,self.h)
        altered=copy.deepcopy(pristine)
        altered[1]["sha256_octets_lus"]="a"*64
        with patch.object(m,"configuration",return_value=self.cfg),self.matched(),patch.object(
                m,"capture_pair",side_effect=[pristine,altered]),patch.object(
                m.p55c,"local_sources",return_value=neutral_reproduction()):
            status=m.main(["--ville-pdf",str(self.v),"--mamh-pdf",str(self.h)])
        self.assertEqual(status,2)
    def test_64_cli_reproduction_echouee_retour_4(self):
        self.assertEqual(self.run_cli(pdf_reproduce=False),4)
    def test_65_cli_reproduction_echouee_pouvant_creer_recu_non_certifiant(self):
        rec=self.root/"recu.json"
        self.assertEqual(self.run_cli("--creer-recu-prive",str(rec),
                                      pdf_reproduce=False),4)
        self.assertEqual(json.loads(rec.read_text())[
            "positions_nfkc_reproduites_techniquement"],0)
    def test_66_date_de_recu_non_signature_numerique(self):
        with self.matched():
            r=m.make_receipt(m.capture_pair(self.v,self.h))
        self.assertNotIn("signature_numérique",r)
        self.assertTrue(r["absence_attestation_de_provenance"])
    def test_67_source_sha256_empreinte_ensemble_sans_signature(self):
        with self.matched():
            rows=m.capture_pair(self.v,self.h)
            r=m.make_receipt(rows)
            self.assertTrue(m.verify_receipt(r,rows,False))
        self.assertFalse(m.public_report()["recu_prive_est_attestation_de_provenance"])
    def test_68_rapport_maintient_dossiers_et_controles_ouverts(self):
        r=m.public_report()
        self.assertEqual(r["dossiers_p54e_ouverts"],4)
        self.assertEqual(r["blocages_p54o_non_leves"],10)
        self.assertEqual(r["controles_p54b_non_attestes"],96)
        self.assertEqual(r["controles_p54c_non_attestes"],8)
    def test_69_public_pas_double_compte(self):
        r=m.public_report()
        self.assertFalse(r["eliminations_ville_rtc_somhac_sont_gains_nouveaux"])
        self.assertFalse(r["redressement_comparatif_2023_est_economie_2024"])
    def test_70_tous_etats_sans_go(self):
        for state in (m.MATCH,m.DIVERGENT):
            with self.matched():
                rows=m.capture_pair(self.v,self.h)
                if state==m.DIVERGENT:continue
                result=m.public_report(rows,True)
                self.assertEqual(result["decision"],m.NO_GO)


if __name__=="__main__":
    unittest.main()
