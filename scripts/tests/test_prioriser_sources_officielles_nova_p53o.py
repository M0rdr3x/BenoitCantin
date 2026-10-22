#!/usr/bin/env python3
"""P53O : tests documentaires, sans automatisation de demandes externes."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prioriser_sources_officielles_nova_p53o as m

def demande(cfg):
    cat=cfg["categories"][0]
    return {
      "schema_version":"P53O-DECLARATION-1",
      "regime":m.REGIMES[0],"categorie":cat,
      "sources_consultees":{s:"NON_CONSULTE" for s in m.PER_CATEGORIE[cat]},
      "statut_competence":"INCONNU",
      "statut_donnees_services":"INCONNU",
      "statut_droits_acces":"INCONNU",
    }

class TestP53O(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p53m,cls.p53n,cls.cfg,cls.nb,cls.dos=m.sources()
        cls.rows=m.matrice(cls.cfg)
    def etat(self,x):return m.examiner(x,self.cfg)["statut"]
    def test_01_population(self):self.assertEqual(self.nb,1344)
    def test_02_dossiers_26(self):self.assertEqual(self.dos,26)
    def test_03_douze_lignes(self):self.assertEqual(len(self.rows),12)
    def test_04_deux_regimes(self):self.assertEqual({r["regime"] for r in self.rows},set(m.REGIMES))
    def test_05_six_familles(self):self.assertEqual(len(self.cfg["categories"]),6)
    def test_06_douze_unique(self):self.assertEqual(len({(r["regime"],r["categorie"]) for r in self.rows}),12)
    def test_07_sept_pages_officielles(self):self.assertEqual(len(m.SOURCES),7)
    def test_08_url_exacte(self):self.assertTrue(all(s["url"]==m.SOURCES[s["id"]][0] for s in self.cfg["sources"]))
    def test_09_aucune_source_equivalente_pieces(self):self.assertTrue(all(s["pieces_transactionnelles_authentifiees"]==0 for s in self.cfg["sources"]))
    def test_10_mamh_limited(self):self.assertTrue(all(
        x["reference_municipale_utilisable"]=="UNIQUEMENT_SI_ORGANISME_MUNICIPAL_IDENTIFIE"
        for x in self.rows if "MAMH_FINANCES" in x["sources_candidats"]))
    def test_11_souverain_hypothetique(self):self.assertTrue(all(
        x["sources_du_quebec_souverain"]=="COMPARATEUR_HISTORIQUE_SANS_AUTORITE_FUTURE"
        for x in self.rows if x["regime"]==m.REGIMES[1]))
    def test_12_p0_pour_tous(self):self.assertTrue(all(x["priorite_procedurale"]==m.PHASES[0] for x in self.rows))
    def test_13_six_etapes_par_fiche(self):self.assertTrue(all(len(x["phases"])==6 for x in self.rows))
    def test_14_etapes_non_faites(self):self.assertTrue(all(set(x["phases"].values())=={"A_REALISER"} for x in self.rows))
    def test_15_source_dossier_non_consultee(self):self.assertTrue(all(set(x["statut_sources"].values())=={"NON_CONSULTE_DANS_CE_DOSSIER"} for x in self.rows))
    def test_16_montants_inconnus(self):self.assertTrue(all(x["economies_certifiees_cad"] is None for x in self.rows))
    def test_17_aucune_competence_presumee(self):self.assertTrue(all(x["applicabilite_juridique"]=="A_ETABLIR" for x in self.rows))
    def test_18_p53n_preuves_demandees(self):self.assertTrue(all(x["preuves_p53n_attendues"]==12 for x in self.rows))
    def test_19_declaration_defaut(self):self.assertEqual(self.etat(demande(self.cfg)),"P0_ORGANISME_ET_COMPETENCE_INCONNUS")
    def test_20_access_refuse(self):
        d=demande(self.cfg);d["statut_droits_acces"]="ACCES_NON_AUTORISE"
        self.assertEqual(self.etat(d),"ARRET_ACCES_NON_AUTORISE")
    def test_21_services_proteges(self):
        d=demande(self.cfg);d["statut_donnees_services"]="GARANTIES_VIOLEES"
        self.assertEqual(self.etat(d),"ARRET_PROTECTION_SERVICES_EMPLOIS")
    def test_22_p1_reperage(self):
        d=demande(self.cfg);d["statut_competence"]="IDENTIFIE_DECLARE_NON_VERIFIE"
        self.assertEqual(self.etat(d),"P1_REPERAGE_PUBLIC_NON_EFFECTUE")
    def test_23_p3_droits(self):
        d=demande(self.cfg);d["statut_competence"]="IDENTIFIE_DECLARE_NON_VERIFIE"
        d["sources_consultees"][list(d["sources_consultees"])[0]]="PAGE_PUBLIQUE_REPEREE_NON_PIECE"
        self.assertEqual(self.etat(d),"P3_DROIT_ACCES_A_VERIFIER")
    def test_24_p4_effets(self):
        d=demande(self.cfg);d["statut_competence"]="IDENTIFIE_DECLARE_NON_VERIFIE"
        d["statut_droits_acces"]="ACCES_POTENTIEL_DECLARATIF"
        d["sources_consultees"][list(d["sources_consultees"])[0]]="PAGE_PUBLIQUE_REPEREE_NON_PIECE"
        self.assertEqual(self.etat(d),"P4_PROTECTIONS_A_VERIFIER")
    def test_25_candidats_non_certifies(self):
        d=demande(self.cfg);d["statut_competence"]="IDENTIFIE_DECLARE_NON_VERIFIE"
        d["statut_droits_acces"]="ACCES_POTENTIEL_DECLARATIF"
        d["statut_donnees_services"]="MESURES_DECLAREES_NON_VERIFIEES"
        d["sources_consultees"][list(d["sources_consultees"])[0]]="DOCUMENT_CANDIDAT_NON_AUTHENTIFIE"
        self.assertEqual(self.etat(d),"DOCUMENTS_CANDIDATS_NON_AUTHENTIFIES")
    def test_26_rejette_source_supplementaire(self):
        d=demande(self.cfg);d["sources_consultees"]["EXTERNE_NON_REPERTOIRIE"]="PAGE_PUBLIQUE_REPEREE_NON_PIECE"
        with self.assertRaises(ValueError):self.etat(d)
    def test_27_rejette_certification(self):
        d=demande(self.cfg);d["statut_competence"]="CERTIFIE"
        with self.assertRaises(ValueError):self.etat(d)
    def test_28_rejette_certification_service(self):
        d=demande(self.cfg);d["statut_donnees_services"]="SERVICES_CERTIFIES"
        with self.assertRaises(ValueError):self.etat(d)
    def test_29_rejette_acces_verifie(self):
        d=demande(self.cfg);d["statut_droits_acces"]="ACCES_AUTORISE_ET_VERIFIE"
        with self.assertRaises(ValueError):self.etat(d)
    def test_30_rejette_donnees_personnelles(self):
        d=demande(self.cfg);d["email_contact"]="invented@example.invalid"
        with self.assertRaises(ValueError):self.etat(d)
    def test_31_rejette_source_manquante(self):
        d=demande(self.cfg);d["sources_consultees"].pop(list(d["sources_consultees"])[0])
        with self.assertRaises(ValueError):self.etat(d)
    def test_32_rejette_regime_autre(self):
        d=demande(self.cfg);d["regime"]="REGIME_INCONNU"
        with self.assertRaises(ValueError):self.etat(d)
    def test_33_rejette_categorie_autre(self):
        d=demande(self.cfg);d["categorie"]="AUTRE_CATEGORIE"
        with self.assertRaises(ValueError):self.etat(d)
    def test_34_bilan_no_go(self):
        b=m.bilan(self.cfg,self.nb,self.dos,[])
        self.assertEqual(b["decision"],"NO_GO_AUTOMATIQUE")
        self.assertIsNone(b["economies_annuelles_certifiees_cad"])
    def test_35_bilan_demandes_zero(self):
        self.assertEqual(m.bilan(self.cfg,self.nb,self.dos,[])["demandes_acces_envoyees"],0)
    def test_36_bilan_originaux_zero(self):
        self.assertEqual(m.bilan(self.cfg,self.nb,self.dos,[])["publications_transactionnelles_originales_telechargees"],0)
    def test_37_bilan_144_pieces_attendues(self):
        self.assertEqual(m.bilan(self.cfg,self.nb,self.dos,[])["documents_p53n_toujours_a_documenter"],144)
    def test_38_cli_genere(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"bilan.json",Path(td)/"matrice.json"
            self.assertEqual(m.main(["--bilan",str(a),"--matrice",str(b)]),0)
            self.assertEqual(json.loads(a.read_text("utf-8"))["pages_officielles_repertoiriees"],7)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["fiches"]),12)
    def test_39_cli_refus_strict(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--exiger-economies-certifiees","--bilan",
                                     str(Path(td)/"strict.json")]),3)
    def test_40_cli_pas_ecrasement(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"existing.json";a.write_text("intact","utf-8")
            self.assertEqual(m.main(["--bilan",str(a)]),2)
            self.assertEqual(a.read_text("utf-8"),"intact")
    def test_41_cli_chemins_identiques(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"same.json"
            self.assertEqual(m.main(["--bilan",str(a),"--matrice",str(a)]),2)
            self.assertFalse(a.exists())
    def test_42_cli_audit_agrege(self):
        with tempfile.TemporaryDirectory() as td:
            data=demande(self.cfg)
            f=Path(td)/"f.json";f.write_text(json.dumps(data),"utf-8")
            dest=Path(td)/"b.json"
            self.assertEqual(m.main(["--declaration",str(f),"--bilan",str(dest)]),0)
            text=dest.read_text("utf-8")
            self.assertIn("P0_ORGANISME_ET_COMPETENCE_INCONNUS",text)
            self.assertNotIn(data["categorie"],text)
            self.assertNotIn(m.SOURCES["SEAO_DONNEES"][0],text)
    def test_43_cli_double_fiche(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"f.json";f.write_text(json.dumps(demande(self.cfg)),"utf-8")
            self.assertEqual(m.main(["--declaration",str(f),"--declaration",str(f)]),2)
    def test_44_deux_regimes_admis_mais_non_additifs(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            data=demande(self.cfg)
            a.write_text(json.dumps(data),"utf-8")
            data["regime"]=m.REGIMES[1]
            b.write_text(json.dumps(data),"utf-8")
            self.assertEqual(m.main(["--declaration",str(a),"--declaration",str(b)]),0)

if __name__=="__main__":
    unittest.main()
