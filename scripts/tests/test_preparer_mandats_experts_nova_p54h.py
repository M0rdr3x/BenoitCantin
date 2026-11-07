#!/usr/bin/env python3
"""P54H: tests sans données personnelles, contacts ou avis imaginaires."""
import copy
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preparer_mandats_experts_nova_p54h as m

def clean_doc():
    return m.template(m.configuration())

def declaration(mandate="MANDAT-COMPTABLE-2024",who="CAND-TEST0001"):
    return {
      "mandat":mandate,"code_opaque":who,
      "verification_appartenance_declaree":"NON_VERIFIEE",
      "conflit":"NON_EXAMINE","honoraires":"NON_EXAMINE",
      "controles_declares":[],
      "dossier_de_pieces_privées_declare":"AUCUNE_PIECE",
      "contact_reel_effectue":False,"mandat_accepte_verifie":False,
      "avis_signe_authentifie":False,
      "qualification_verifiee_par_systeme":False,
      "autorisation_financiere":False,
    }

class TestP54H(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()

    def invalid(self,mod):
        d=clean_doc()
        d["declarations"]=[declaration()]
        mod(d)
        with self.assertRaises((ValueError,TypeError,KeyError)):
            m.analyze_declarations(d,self.cfg)
    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54H-1")
    def test_02_source_year(self):self.assertEqual(self.cfg["exercice_source"],2024)
    def test_03_p54g_anchor(self):self.assertEqual(self.cfg["source"],"P54G_REGISTRE_DECISIONS_PROCEDURALES_2024.json")
    def test_04_mandates_count(self):self.assertEqual(len(self.cfg["mandats"]),2)
    def test_05_accountant(self):self.assertEqual(self.cfg["mandats"][0]["specialite"],"COMPTABILITE_MUNICIPALE_2024")
    def test_06_legal(self):self.assertEqual(self.cfg["mandats"][1]["specialite"],"DROIT_MUNICIPAL_ET_MANDAT_D_AUDIT")
    def test_07_twelve_gates(self):self.assertEqual(len(m.REQUIREMENTS),12)
    def test_08_24_points(self):self.assertEqual(len(m.build_mandates(self.cfg)["mandats"])*len(m.REQUIREMENTS),24)
    def test_09_4_cases_both(self):self.assertTrue(all(len(z["dossiers"])==4 for z in self.cfg["mandats"]))
    def test_10_no_officials_named(self):self.assertTrue(all("contact" not in z for z in self.cfg["mandats"]))
    def test_11_register_professional(self):self.assertIn("ORDRE_PROFESSIONNEL_ET_PERMIS_EXAMINES",m.REQUIREMENTS)
    def test_12_conflicts(self):self.assertIn("INDEPENDANCE_ET_CONFLITS_DECLARÉS",m.REQUIREMENTS)
    def test_13_privacy(self):self.assertIn("CONFIDENTIALITE_ET_SECRET_PROFESSIONNEL",m.REQUIREMENTS)
    def test_14_savings_guard(self):self.assertIsNone(self.cfg["etat_initial"]["economies_certifiees_cad"])
    def test_15_zero_signed(self):self.assertEqual(self.cfg["etat_initial"]["avis_originaux_signes_recus"],0)
    def test_16_zero_employed(self):self.assertEqual(self.cfg["etat_initial"]["experts_engages"],0)
    def test_17_all_not_sent(self):self.assertTrue(all(x["statut"]=="PROJET_NON_TRANSMIS" for x in m.build_mandates(self.cfg)["mandats"]))
    def test_18_initial_economy(self):self.assertIsNone(m.report(self.cfg)["economies_certifiees_cad"])
    def test_19_initial_p54b_remains(self):self.assertEqual(m.report(self.cfg)["controles_p54b_en_attente"],96)
    def test_20_initial_p54c_remains(self):self.assertEqual(m.report(self.cfg)["controles_p54c_en_attente"],8)
    def test_21_initial_undecided(self):self.assertEqual(m.report(self.cfg)["decision"],m.NO_GO)
    def test_22_initial_unverified_all(self):self.assertTrue(all(not y["deja_atteste"] for x in m.build_mandates(self.cfg)["mandats"] for y in x["controles"]))
    def test_23_empty_valid(self):self.assertEqual(m.analyze_declarations(clean_doc(),self.cfg)["declarations_non_authentifiees"],0)
    def test_24_one_valid(self):
        d=clean_doc();d["declarations"]=[declaration()]
        self.assertEqual(m.analyze_declarations(d,self.cfg)["declarations_non_authentifiees"],1)
    def test_25_both_valid(self):
        d=clean_doc();d["declarations"]=[declaration(),declaration("MANDAT-JURIDIQUE-2024","CAND-JUR0001")]
        self.assertEqual(m.analyze_declarations(d,self.cfg)["declarations_non_authentifiees"],2)
    def test_26_duplicates_denied(self):
        self.invalid(lambda d:d["declarations"].append(declaration()))
    def test_27_unknown_mandate(self):
        self.invalid(lambda d:d["declarations"][0].update(mandat="INCONNU"))
    def test_28_reject_name_in_id(self):
        self.invalid(lambda d:d["declarations"][0].update(code_opaque="Monsieur Dupont"))
    def test_29_reject_freestyle(self):
        self.invalid(lambda d:d["declarations"][0].update(contact_email="example@example.com"))
    def test_30_reject_verified_license_claim(self):
        self.invalid(lambda d:d["declarations"][0].update(qualification_verifiee_par_systeme=True))
    def test_31_reject_signed_opinion(self):
        self.invalid(lambda d:d["declarations"][0].update(avis_signe_authentifie=True))
    def test_32_reject_contact_claim(self):
        self.invalid(lambda d:d["declarations"][0].update(contact_reel_effectue=True))
    def test_33_reject_contract_claim(self):
        self.invalid(lambda d:d["declarations"][0].update(mandat_accepte_verifie=True))
    def test_34_reject_money(self):
        self.invalid(lambda d:d["declarations"][0].update(autorisation_financiere=True))
    def test_35_licenses_declared_not_verified(self):
        d=clean_doc();x=declaration();x["verification_appartenance_declaree"]="CONTROLE_HUMAIN_DECLARE_NON_AUTHENTIFIE"
        d["declarations"]=[x]
        result=m.report(self.cfg,m.analyze_declarations(d,self.cfg))
        self.assertEqual(result["appartenances_ordre_verifiees_par_procedure_independante"],0)
    def test_36_reject_false_license_value(self):
        self.invalid(lambda d:d["declarations"][0].update(verification_appartenance_declaree="VERIFIE_CPA"))
    def test_37_legal_real_conflict(self):
        d=clean_doc();x=declaration("MANDAT-JURIDIQUE-2024");x["conflit"]="REEL";d["declarations"]=[x]
        self.assertEqual(m.analyze_declarations(d,self.cfg)["dossiers_risque_ou_incitation_a_expertiser"],1)
    def test_38_potential_conflict(self):
        d=clean_doc();x=declaration();x["conflit"]="POTENTIEL";d["declarations"]=[x]
        self.assertEqual(m.analyze_declarations(d,self.cfg)["dossiers_risque_ou_incitation_a_expertiser"],1)
    def test_39_apparent_conflict(self):
        d=clean_doc();x=declaration();x["conflit"]="APPARENT";d["declarations"]=[x]
        self.assertEqual(m.analyze_declarations(d,self.cfg)["dossiers_risque_ou_incitation_a_expertiser"],1)
    def test_40_contingent_fees_flagged(self):
        d=clean_doc();x=declaration();x["honoraires"]="INCITATION_AU_RESULTAT_A_EVALUER";d["declarations"]=[x]
        self.assertEqual(m.analyze_declarations(d,self.cfg)["dossiers_risque_ou_incitation_a_expertiser"],1)
    def test_41_no_false_absence_of_conflict(self):
        d=clean_doc();x=declaration();x["conflit"]="ABSENCE_DECLAREE_NON_VERIFIEE";d["declarations"]=[x]
        self.assertEqual(m.report(self.cfg,m.analyze_declarations(d,self.cfg))["absences_conflit_certifiees"],0)
    def test_42_invalid_conflict(self):
        self.invalid(lambda d:d["declarations"][0].update(conflit="INEXISTANT_CERTIFIE"))
    def test_43_invalid_fee(self):
        self.invalid(lambda d:d["declarations"][0].update(honoraires="HONORAIRES_100000"))
    def test_44_check_count_not_certification(self):
        d=clean_doc();x=declaration();x["controles_declares"]=list(m.REQUIREMENTS);d["declarations"]=[x]
        report=m.report(self.cfg,m.analyze_declarations(d,self.cfg))
        self.assertEqual(report["declarations_locales"]["controles_declares_examines_non_attestes"],12)
        self.assertEqual(report["avis_independants_originaux_signes_reçus"],0)
    def test_45_duplicate_checks(self):
        self.invalid(lambda d:d["declarations"][0].update(controles_declares=[m.REQUIREMENTS[0]]*2))
    def test_46_unknown_check(self):
        self.invalid(lambda d:d["declarations"][0].update(controles_declares=["CERTIFICATION_AUTO"]))
    def test_47_bad_pieces_mentioned(self):
        self.invalid(lambda d:d["declarations"][0].update(dossier_de_pieces_privées_declare="SECRET_LOCAL"))
    def test_48_template_privacy(self):
        self.assertNotIn("nom",json.dumps(clean_doc()).casefold())
    def test_49_cli_neutral_outputs(self):
        with tempfile.TemporaryDirectory() as root:
            mandats=Path(root)/"mandats.json";result=Path(root)/"result.json"
            self.assertEqual(m.main(["--mandats",str(mandats),"--bilan",str(result)]),0)
            self.assertEqual(json.loads(result.read_text("utf-8"))["mandats_prepares"],2)
    def test_50_cli_explicit_refusal(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(m.main(["--bilan",str(Path(root)/"b.json"),"--exiger-avis-certifie"]),3)
    def test_51_private_template_mode(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"priv.json"
            self.assertEqual(m.main(["--modele-prive",str(f)]),0)
            self.assertEqual(stat.S_IMODE(f.stat().st_mode),0o600)
    def test_52_cli_private_read(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"priv.json";out=Path(root)/"public.json"
            d=clean_doc();d["declarations"]=[declaration()]
            f.write_text(json.dumps(d),encoding="utf-8");os.chmod(f,0o600)
            self.assertEqual(m.main(["--declarations-locales",str(f),"--bilan",str(out)]),0)
            self.assertEqual(json.loads(out.read_text("utf-8"))["declarations_locales"]["declarations_non_authentifiees"],1)
    def test_53_cli_reject_world_readable(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"priv.json"
            f.write_text(json.dumps(clean_doc()),encoding="utf-8");os.chmod(f,0o644)
            self.assertEqual(m.main(["--declarations-locales",str(f)]),2)
    def test_54_cli_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"public.json";f.write_text("keep",encoding="utf-8")
            self.assertEqual(m.main(["--bilan",str(f)]),2)
            self.assertEqual(f.read_text("utf-8"),"keep")
    def test_55_cli_refuse_same_output(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"public.json"
            self.assertEqual(m.main(["--bilan",str(f),"--mandats",str(f)]),2)

def make_guard_test(flag):
    def test(self):
        self.assertTrue(self.cfg["garde_fous"][flag])
    return test

for i,flag in enumerate(sorted(m.GUARDS),56):
    setattr(TestP54H,"test_%02d_safety_gate"%i,make_guard_test(flag))

if __name__=="__main__":
    unittest.main()
