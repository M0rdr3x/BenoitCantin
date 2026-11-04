"""P55I — tests sur les nombres publiés, sans PDF local et sans réseau."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import rapprocher_sommaire_budgetaire_nova_p55i as m


class TestP55I(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=m.configuration()

    def test_01_config_schema(self):
        self.assertEqual(self.config["schema_version"],"P55I-1")
    def test_02_config_exercice(self):
        self.assertEqual(self.config["exercice"],2024)
    def test_03_config_date(self):
        self.assertEqual(self.config["date_reference"],"2026-11-04")
    def test_04_config_jalons(self):
        self.assertEqual(self.config["source_amont"],["P54Q","P55F","P55G","P55H"])
    def test_05_annee_source(self):
        self.assertEqual(m.SOURCE["pdf_index_zero"],6)
    def test_06_page_imprimee(self):
        self.assertEqual(m.SOURCE["page_imprimee"],"7")
    def test_07_sommaire_non_audite(self):
        self.assertIn("NON_AUDITE",m.SOURCE["qualification"])
    def test_08_source_institution(self):
        self.assertEqual(m.SOURCE["institution"],"VILLE_DE_QUEBEC")
    def test_09_url_officielle(self):
        self.assertIn("ville.quebec.qc.ca",m.SOURCE["url"])
    def test_10_quatre_lignes(self):
        self.assertEqual(len(m.ROWS),4)
    def test_11_codes_uniques(self):
        self.assertEqual(len(set(row[0] for row in m.ROWS)),4)
    def test_12_protections(self):
        self.assertTrue(all(self.config["protections"].values()))
    def test_13_gardes_32(self):
        self.assertEqual(len(m.GUARDS),32)
    def test_14_zero_copies_authentifiees(self):
        self.assertEqual(self.config["etat_initial"]["copies_pdf_actuelles_authentifiees"],0)
    def test_15_aucune_economie_certifiee(self):
        self.assertIsNone(self.config["etat_initial"]["economies_certifiees_cad"])
    def test_16_aucun_go(self):
        self.assertEqual(self.config["etat_initial"]["decision"],m.NO_GO)
    def test_17_revenus_fonctionnement(self):
        a=m.reference_lines()[0]
        self.assertEqual((a["budget_cad"],a["realisation_cad"],a["ecart_realisation_moins_budget_cad"]),
                         (2089556928,2186607854,97050926))
    def test_18_revenus_investissement(self):
        a=m.reference_lines()[1]
        self.assertEqual((a["budget_cad"],a["realisation_cad"],a["ecart_realisation_moins_budget_cad"]),
                         (403091050,262872891,-140218159))
    def test_19_charges(self):
        a=m.reference_lines()[2]
        self.assertEqual((a["budget_cad"],a["realisation_cad"],a["ecart_realisation_moins_budget_cad"]),
                         (2092480059,2107478001,14997942))
    def test_20_resultat(self):
        a=m.reference_lines()[3]
        self.assertEqual((a["budget_cad"],a["realisation_cad"],a["ecart_realisation_moins_budget_cad"]),
                         (400167919,342002744,-58165175))
    def test_21_identites_reproduites(self):
        self.assertTrue(m.validate_rows(m.reference_lines()))
    def test_22_budget_identity(self):
        self.assertEqual(2089556928+403091050-2092480059,400167919)
    def test_23_real_identity(self):
        self.assertEqual(2186607854+262872891-2107478001,342002744)
    def test_24_delta_identity(self):
        self.assertEqual(97050926-140218159-14997942,-58165175)
    def test_25_result_difference(self):
        self.assertEqual(342002744-400167919,-58165175)
    def test_26_percent_revenus(self):
        self.assertEqual(m.percent(97050926,2089556928),"4.6")
    def test_27_percent_investissements(self):
        self.assertEqual(m.percent(-140218159,403091050),"-34.8")
    def test_28_percent_charges(self):
        self.assertEqual(m.percent(14997942,2092480059),"0.7")
    def test_29_percent_excedent(self):
        self.assertEqual(m.percent(-58165175,400167919),"-14.5")
    def test_30_pas_addition_pourcentages(self):
        self.assertEqual(m.percent(1,4),"25.0")
        self.assertNotEqual(m.percent(97050926-140218159,2089556928+403091050),"4.6")
    def test_31_zero_division_refusee(self):
        with self.assertRaises(ValueError):m.percent(2,0)
    def test_32_bool_valeur_refusee(self):
        with self.assertRaises(ValueError):m.percent(True,10)
    def test_33_mutation_dollar_refusee(self):
        r=copy.deepcopy(m.reference_lines())
        r[0]["realisation_cad"]+=1
        with self.assertRaises(ValueError):m.validate_rows(r)
    def test_34_mutation_solde_refusee(self):
        r=copy.deepcopy(m.reference_lines())
        r[3]["ecart_realisation_moins_budget_cad"]+=1
        with self.assertRaises(ValueError):m.validate_rows(r)
    def test_35_mutation_classe_refusee(self):
        r=copy.deepcopy(m.reference_lines())
        r[2]["nature"]="economie"
        with self.assertRaises(ValueError):m.validate_rows(r)
    def test_36_doublon_poste_refuse(self):
        r=copy.deepcopy(m.reference_lines())
        r[2]=copy.deepcopy(r[1])
        with self.assertRaises(ValueError):m.validate_rows(r)
    def test_37_ligne_supplementaire_refusee(self):
        r=copy.deepcopy(m.reference_lines())
        r.append(copy.deepcopy(r[0]))
        with self.assertRaises(ValueError):m.validate_rows(r)
    def test_38_bool_en_dollars_refuse(self):
        r=copy.deepcopy(m.reference_lines())
        r[2]["budget_cad"]=True
        with self.assertRaises(ValueError):m.validate_rows(r)
    def test_39_pas_economie_sur_lignes(self):
        self.assertTrue(all(row["economie_nouvelle_demontree"] is False for row in m.detail_rows()))
    def test_40_signe_charges_pour_resultat(self):
        self.assertEqual(m.detail_rows()[2]["contribution_variation_resultat_cad"],-14997942)
    def test_41_contribution_resultat_nulle(self):
        self.assertIsNone(m.detail_rows()[3]["contribution_variation_resultat_cad"])
    def test_42_rapport_no_go(self):
        r=m.public_report()
        self.assertEqual(r["decision"],m.NO_GO)
        self.assertFalse(r["ecarts_sont_economies_certifiees"])
        self.assertIsNone(r["economies_certifiees_cad"])
    def test_43_rapport_statuts_amont(self):
        r=m.public_report()
        self.assertTrue(r["sommaire_budget_realisation_non_audite"])
        self.assertEqual(r["copies_originales_authentifiees_p55h"],0)
        self.assertFalse(r["comparaison_mamh_expertisee"])
    def test_44_table_publique_quatre_lignes(self):
        t=m.public_table()
        self.assertEqual(len(t["lignes"]),4)
        self.assertEqual(t["identites_comptables"]["ecart_resultat_cad"],-58165175)
    def test_45_table_publique_aucune_certification(self):
        t=m.public_table()
        self.assertTrue(t["aucune_economie_affirmee"])
        self.assertEqual(t["decision"],m.NO_GO)
    def test_46_bilan_sans_donnees_privees(self):
        raw=json.dumps(m.public_report())
        self.assertNotIn("sha256",raw)
        self.assertNotIn("offset_texte",raw)
    def test_47_cli_sorties_neutres(self):
        with tempfile.TemporaryDirectory() as t:
            b=Path(t)/"bilan.json";f=Path(t)/"table.json"
            self.assertEqual(m.main(["--bilan-public",str(b),"--table-public",str(f)]),0)
            data=json.loads(b.read_text())
            table=json.loads(f.read_text())
            self.assertEqual(data["variation_excédent_exercice_cad"],-58165175)
            self.assertEqual(len(table["lignes"]),4)
    def test_48_cli_aucune_sortie_no_go(self):
        self.assertEqual(m.main([]),0)
    def test_49_cli_certification_refusee(self):
        self.assertEqual(m.main(["--exiger-certification"]),3)
    def test_50_cli_fichier_existant_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            b=Path(t)/"bilan.json";b.write_text("{}")
            self.assertEqual(m.main(["--bilan-public",str(b)]),2)
    def test_51_cli_sorties_conflictuelles_refusees(self):
        with tempfile.TemporaryDirectory() as t:
            b=str(Path(t)/"bilan.json")
            self.assertEqual(m.main(["--bilan-public",b,"--table-public",b]),2)
    def test_52_config_source_corrompue_refuse(self):
        with patch.object(m.p54z,"read_json",return_value={}):
            with self.assertRaises(ValueError):m.configuration()
    def test_53_config_ligne_modifiee_refuse(self):
        edited=copy.deepcopy(self.config)
        edited["lignes"][0]["budget_cad"]+=100
        with patch.object(m.p54z,"read_json",return_value=edited):
            with self.assertRaises(ValueError):m.configuration()
    def test_54_config_gain_2023_fictif_refuse(self):
        edited=copy.deepcopy(self.config)
        edited["faits_contextuels_exclus"]["redressement_n_est_pas_economie"]=False
        with patch.object(m.p54z,"read_json",return_value=edited):
            with self.assertRaises(ValueError):m.configuration()
    def test_55_maintien_dossiers_non_clos(self):
        r=m.public_report()
        self.assertEqual((r["dossiers_p54e_ouverts"],r["date_probable_non_certifiee"],
                          r["taches_p54n_non_attestees"],r["blocages_p54o_non_leves"]),
                         (4,1,40,10))
    def test_56_p55b_controles_non_attestes(self):
        r=m.public_report()
        self.assertEqual((r["controles_p54b_non_attestes"],
                          r["controles_p54c_non_attestes"]),(96,8))
    def test_57_interdiction_envoi_fusion(self):
        r=m.public_report()
        self.assertFalse(r["transmission_externe_autorisee"])
        self.assertFalse(r["fusion_main_autorisee"])
    def test_58_redressement_2023_non_gain(self):
        r=m.public_report()
        self.assertFalse(r["redressement_comparatif_2023_est_gain_2024"])
    def test_59_eliminations_existantes_non_gain(self):
        self.assertFalse(m.public_report()["eliminations_existantes_sont_economies_nouvelles"])
    def test_60_soldes_en_entiers(self):
        self.assertTrue(all(type(x["ecart_realisation_moins_budget_cad"]) is int
                            for x in m.public_table()["lignes"]))


if __name__=="__main__":
    unittest.main()
