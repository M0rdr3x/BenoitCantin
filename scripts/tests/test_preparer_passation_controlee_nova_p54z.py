import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import preparer_passation_controlee_nova_p54z as m


class TestP54Z(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = m.configuration()

    def setUp(self):
        self.template = m.blank_model()

    def test_01_schema(self): self.assertEqual(self.config["schema_version"],"P54Z-1")
    def test_02_historique(self): self.assertEqual(self.config["exercice"],2024)
    def test_03_cinq_references(self): self.assertEqual(len(m.REFS),5)
    def test_04_huit_controles(self): self.assertEqual(len(m.CONTROLS),8)
    def test_05_quarante_cases(self): self.assertEqual(len(self.template["dossiers"])*8,40)
    def test_06_roles_non_attribues(self): self.assertEqual(len(self.config["roles_non_designes"]),5)
    def test_07_toutes_protections(self): self.assertTrue(all(self.config["protections"].values()))
    def test_08_modele_initial(self): self.assertEqual(m.validate_declarations(self.template)["NON_INSTRUIT"],40)
    def test_09_bilan_aucune_economie(self): self.assertIsNone(m.public_report()["economies_certifiees_cad"])
    def test_10_bilan_no_go(self): self.assertEqual(m.public_report()["decision"],m.NO_GO)
    def test_11_certification_bloquee(self): self.assertFalse(m.public_report()["certification_autorisee"])
    def test_12_transmission_bloquee(self): self.assertFalse(m.public_report()["transmission_autorisee"])
    def test_13_fusion_bloquee(self): self.assertFalse(m.public_report()["fusion_main_autorisee"])
    def test_14_aucune_signature(self): self.assertEqual(m.public_report()["signatures_professionnelles_verifiees"],0)
    def test_15_absence_identites(self): self.assertNotIn("identite",json.dumps(self.template).lower())
    def test_16_preparation_non_preuve(self):
        self.template["dossiers"][0]["controles"][0]["etat"]="PREPARATION_DECLAREE_NON_VERIFIEE"
        self.assertEqual(m.validate_declarations(self.template)["PREPARATION_DECLAREE_NON_VERIFIEE"],1)
        self.assertEqual(m.public_report(m.validate_declarations(self.template))["revues_humaines_authentifiees"],0)
    def test_17_suspension_bloquante(self):
        self.template["dossiers"][0]["controles"][0]["etat"]="SUSPENDU"
        self.assertEqual(m.public_report(m.validate_declarations(self.template))["suspensions_prioritaires"],1)
        self.assertFalse(m.public_report(m.validate_declarations(self.template))["certification_autorisee"])
    def test_18_ref_manquante(self):
        self.template["dossiers"].pop()
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_19_ref_incorrecte(self):
        self.template["dossiers"][0]["reference"]="INVENTEE"
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_20_doublon_ref(self):
        self.template["dossiers"][1]["reference"]=m.REFS[0]
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_21_code_invalide(self):
        self.template["dossiers"][0]["controles"][0]["code"]="CERTIFIER"
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_22_code_manquant(self):
        self.template["dossiers"][0]["controles"].pop()
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_23_statut_faux_go(self):
        self.template["dossiers"][0]["controles"][0]["etat"]="CERTIFIE"
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_24_signature_injectee(self):
        self.template["dossiers"][0]["signature"]="ABC"
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_25_commentaire_libre_interdit(self):
        self.template["dossiers"][0]["controles"][0]["note"]="secret"
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_26_annee_incorrecte(self):
        self.template["exercice"]=2026
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_27_type_booleen(self):
        self.template["exercice"]=True
        with self.assertRaises(ValueError):m.validate_declarations(self.template)
    def test_28_doublon_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"double.json";f.write_text('{"a":1,"a":2}',encoding="utf-8")
            with self.assertRaises(ValueError):m.read_json(f)
    def test_29_creation_privee(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"passation.json"
            m.write_new(p,self.template,private=True)
            self.assertEqual(p.stat().st_mode & 0o777,0o600)
            self.assertEqual(m.read_private_declarations(p)["NON_INSTRUIT"],40)
    def test_30_refus_reecriture(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"passation.json"
            m.write_new(p,self.template,private=True)
            with self.assertRaises(ValueError):m.write_new(p,self.template,private=True)
    def test_31_permissions_refusees(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"passation.json";p.write_text(json.dumps(self.template))
            p.chmod(0o644)
            with self.assertRaises(ValueError):m.read_private_declarations(p)
    def test_32_lien_symbolique_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"original.json";p.write_text(json.dumps(self.template))
            p.chmod(0o600)
            link=Path(tmp)/"lien.json";link.symlink_to(p)
            with self.assertRaises(ValueError):m.read_private_declarations(link)
    def test_33_somme_invalides(self):
        with self.assertRaises(ValueError):m.public_report({x:1 for x in m.STATES})
    def test_34_bilan_agrege_sans_jeton(self):
        r=m.public_report()
        self.assertNotIn("positions_caracteres",json.dumps(r))
        self.assertNotIn("jeton",json.dumps(r))
    def test_35_cli_go_refuse(self): self.assertEqual(m.main(["--exiger-go"]),3)
    def test_36_cli_bilan(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"public.json"
            self.assertEqual(m.main(["--bilan-public",str(out)]),0)
            self.assertEqual(json.loads(out.read_text())["decision"],m.NO_GO)
    def test_37_cli_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"private.json"
            self.assertEqual(m.main(["--creer-modele",str(out)]),0)
            self.assertTrue(out.exists())
    def test_38_cli_creation_plus_lecture_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=str(Path(tmp)/"x.json")
            self.assertEqual(m.main(["--creer-modele",p,"--declarations",p]),2)
    def test_39_refus_dans_depot(self):
        with self.assertRaises(ValueError):
            m.outside_repo(m.ROOT/"interdit.json")
        with tempfile.TemporaryDirectory() as tmp:
            alias=Path(tmp)/"alias"
            alias.symlink_to(m.ROOT,target_is_directory=True)
            with self.assertRaises(ValueError):
                m.outside_repo(alias/"interdit.json")
    def test_40_preserve_audit_dependances(self):
        self.assertEqual(self.config["etat_initial"]["decision"],m.NO_GO)


if __name__=="__main__":
    unittest.main()
