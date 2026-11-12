"""P50H: tests de contrôle documentaire, jamais d'autorisation réelle."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"audit_nova_habilitations_p50h.py"
spec=importlib.util.spec_from_file_location("p50h", SCRIPT)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
BASE=json.loads((ROOT/"projets"/"projet-nova"/"controles"/
    "P50H_REGISTRE_PUBLIC_MODELE.json").read_text(encoding="utf-8"))

class TestP50H(unittest.TestCase):
    def fresh(self):
        return copy.deepcopy(BASE)
    def check(self, changed=None):
        return m.inspect(self.fresh() if changed is None else changed)
    def test_registre_modele_valide(self):
        d=self.check()
        self.assertEqual(d["status"],"MODELE_VALIDEMENT_STRUCTURE")
        self.assertEqual(d["portes_total"],14)
        self.assertEqual(d["portes_pre"],12)
        self.assertEqual(d["portes_post"],2)
        self.assertEqual(d["etats"]["NON_DOCUMENTE"],14)
    def test_jamais_go_pour_un_modele_vide(self):
        self.assertEqual(self.check()["decision_publication"],"NO_GO_AUTOMATIQUE")
    def test_une_preuve_declaree_valide_ne_cree_jamais_un_go(self):
        d=self.fresh()
        d["portes"][0].update(statut="VERIFIE_HORS_DEPOT",
            reference_preuve="EV-ABCDEFG123",date_verification="2026-10-14")
        r=self.check(d)
        self.assertEqual(r["status"],"MODELE_VALIDEMENT_STRUCTURE")
        self.assertEqual(r["decision_publication"],"NO_GO_AUTOMATIQUE")
        self.assertEqual(r["preuves_authentifiees_par_ce_script"],0)
    def test_tentative_de_go_direct_invalide(self):
        d=self.fresh();d["decision"]["statut"]="GO"
        self.assertIn("DECISION_PUBLIQUE_INTERDITE",self.check(d)["problems"])
    def test_faux_deploiement_invalide(self):
        d=self.fresh();d["decision"]["publication_realisee"]=True
        self.assertEqual(self.check(d)["status"],"MODELE_INVALIDE")
    def test_pr_640_verrou_non_effacable(self):
        d=self.fresh();d["garde_fous"].remove("Ne pas fusionner PR 640")
        self.assertIn("VERROU_MANQUANT",self.check(d)["problems"])
    def test_retirer_une_porte_refuse(self):
        d=self.fresh();d["portes"].pop()
        self.assertIn("PORTES_MANQUANTES",self.check(d)["problems"])
    def test_porte_dupliquee_refusee(self):
        d=self.fresh();d["portes"][1]["id"]="B01"
        self.assertIn("PORTE_INCONNUE_OU_DUPLIQUEE",self.check(d)["problems"])
    def test_phase_post_ne_peut_devenir_pre(self):
        d=self.fresh();d["portes"][11]["phase"]="PRE"
        self.assertIn("MAUVAISE_PHASE_B12",self.check(d)["problems"])
    def test_etat_impossible_refuse(self):
        d=self.fresh();d["portes"][2]["statut"]="APPROUVE_AUTOMATIQUE"
        self.assertIn("ETAT_INVALIDE_B03",self.check(d)["problems"])
    def test_reference_pretendument_verifiee_sans_preuve(self):
        d=self.fresh();d["portes"][0]["statut"]="VERIFIE_HORS_DEPOT"
        errors=self.check(d)["problems"]
        self.assertIn("REFERENCE_NON_VERIFIABLE_B01",errors)
        self.assertIn("DATE_NON_VALIDE_B01",errors)
    def test_faux_sha_refuse(self):
        d=self.fresh();d["snapshot_source"]["main"]="abc"
        self.assertIn("SNAPSHOT_INCOMPLET_OU_INVALIDE",self.check(d)["problems"])
    def test_horizon_inverse_refuse(self):
        d=self.fresh();d["horizon"]["pre_deploiement"].append("B12")
        self.assertIn("HORIZON_INVALIDE",self.check(d)["problems"])
    def test_aucune_information_personnelle_obligatoire(self):
        d=self.fresh()
        self.assertEqual(set(d["habilitations"]["conseil_juridique"]),{"atteste","reference_preuve"})
    def test_mauvais_json_echec_ferme(self):
        with tempfile.TemporaryDirectory() as td:
            x=Path(td)/"registre.json";x.write_text("{invalid",encoding="utf-8")
            self.assertEqual(m.main(["--registre",str(x),"--rapport",str(Path(td)/"r.json")]),2)

if __name__=="__main__":unittest.main()
