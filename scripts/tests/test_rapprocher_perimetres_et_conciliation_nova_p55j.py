"""P55J — soixante tests de résidus et de pont fiscal sur chiffres publics."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import rapprocher_perimetres_et_conciliation_nova_p55j as m


class TestP55J(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()

    def test_01_configuration(self):
        self.assertEqual(self.cfg["schema_version"],"P55J-1")
    def test_02_date(self):
        self.assertEqual(self.cfg["date_reference"],"2026-11-04")
    def test_03_exercice(self):
        self.assertEqual(self.cfg["exercice"],2024)
    def test_04_deux_pages_visuelles(self):
        self.assertEqual(m.SOURCE["pages_pdf_index_zero"],[6,12])
    def test_05_pages_imprimees(self):
        self.assertEqual(m.SOURCE["pages_imprimees"],[7,13])
    def test_06_statut_pas_sha_actuel(self):
        self.assertIn("SANS_SHA_ACTUEL",m.SOURCE["attestation"])
    def test_07_source_officielle(self):
        self.assertIn("ville.quebec.qc.ca",m.SOURCE["url_officielle"])
    def test_08_dependances(self):
        self.assertEqual(self.cfg["dependances"],["P54Q","P55H","P55I"])
    def test_09_huit_lignes(self):
        self.assertEqual(len(m.ROWS),8)
    def test_10_codes_uniques(self):
        self.assertEqual(len({x[0] for x in m.ROWS}),8)
    def test_11_34_garde_fous(self):
        self.assertEqual(len(m.GUARDS),34)
    def test_12_tous_garde_fous_actifs(self):
        self.assertTrue(all(self.cfg["protections"].values()))
    def test_13_interpretations_interdites(self):
        self.assertEqual(len(m.BLOCKED),4)
    def test_14_revenu_total_consolide(self):
        self.assertEqual(m.reference_rows()[2]["total_consolide_cad"],2449480745)
    def test_15_charge_totale_consolidee(self):
        self.assertEqual(m.reference_rows()[3]["total_consolide_cad"],2107478001)
    def test_16_excedent_comptable_consolide(self):
        self.assertEqual(m.reference_rows()[4]["total_consolide_cad"],342002744)
    def test_17_residu_recettes(self):
        self.assertEqual(m.reference_rows()[2]["residu_consolidation_cad"],-176548476)
    def test_18_residu_charges(self):
        self.assertEqual(m.reference_rows()[3]["residu_consolidation_cad"],-178606212)
    def test_19_residu_excedent(self):
        self.assertEqual(m.reference_rows()[4]["residu_consolidation_cad"],2057736)
    def test_20_identite_solde_residus(self):
        self.assertEqual(-176548476-(-178606212),2057736)
    def test_21_pont_budget_solde_comptable(self):
        self.assertEqual(400167919-403091050,-2923131)
    def test_22_pont_budget_fiscal(self):
        self.assertEqual(-2923131+2923131,0)
    def test_23_pont_reel_fonctionnement(self):
        self.assertEqual(342002744-262872891,79129853)
    def test_24_pont_reel_fiscal(self):
        self.assertEqual(79129853+50206104,129335957)
    def test_25_pont_variations(self):
        self.assertEqual(82052984+47282973,129335957)
    def test_26_residus_non_certifies(self):
        r=m.public_report()
        self.assertEqual(r["residus_expliques_et_attestes_par_expert"],0)
        self.assertFalse(r["ecarts_consolidation_equivalent_eliminations_certifiees"])
    def test_27_fiscal_non_tresorerie_libre(self):
        self.assertFalse(m.public_report()["excedent_fiscal_equivaut_tresorerie_libre"])
    def test_28_fiscal_non_economie(self):
        self.assertFalse(m.public_report()["excedent_fiscal_equivaut_economie_certifiee"])
    def test_29_avis_non_recus(self):
        self.assertEqual(m.public_report()["engagement_professionnel_authentifie"],0)
    def test_30_economies_null(self):
        self.assertIsNone(m.public_report()["economies_certifiees_cad"])
    def test_31_no_go(self):
        self.assertEqual(m.public_report()["decision"],m.NO_GO)
    def test_32_pas_fusion(self):
        self.assertFalse(m.public_report()["fusion_main_autorisee"])
    def test_33_pas_transmission(self):
        self.assertFalse(m.public_report()["transmission_externe_autorisee"])
    def test_34_validation_table_originale(self):
        self.assertTrue(m.validate_table(m.reference_rows(),m.BRIDGE))
    def test_35_mutation_dollar_refusee(self):
        records=copy.deepcopy(m.reference_rows())
        records[2]["total_consolide_cad"]+=1
        with self.assertRaises(ValueError):
            m.validate_table(records,m.BRIDGE)
    def test_36_mutation_pont_fiscal_refusee(self):
        data=dict(m.BRIDGE)
        data["elements_conciliation_realises_cad"]+=1
        with self.assertRaises(ValueError):
            m.validate_table(m.reference_rows(),data)
    def test_37_residu_revenus_fonctionnement(self):
        row=m.reference_rows()[0]
        self.assertEqual(row["code"],"REVENUS_FONCTIONNEMENT")
        self.assertEqual(row["total_consolide_cad"]-row["administration_municipale_cad"]-row["organismes_controles_partenariats_cad"],row["residu_consolidation_cad"])

    def test_38_residu_revenus_investissement(self):
        row=m.reference_rows()[1]
        self.assertEqual(row["code"],"REVENUS_INVESTISSEMENT")
        self.assertEqual(row["total_consolide_cad"]-row["administration_municipale_cad"]-row["organismes_controles_partenariats_cad"],row["residu_consolidation_cad"])

    def test_39_residu_revenus_totaux(self):
        row=m.reference_rows()[2]
        self.assertEqual(row["code"],"REVENUS_TOTAUX")
        self.assertEqual(row["total_consolide_cad"]-row["administration_municipale_cad"]-row["organismes_controles_partenariats_cad"],row["residu_consolidation_cad"])

    def test_40_residu_charges(self):
        row=m.reference_rows()[3]
        self.assertEqual(row["code"],"CHARGES")
        self.assertEqual(row["total_consolide_cad"]-row["administration_municipale_cad"]-row["organismes_controles_partenariats_cad"],row["residu_consolidation_cad"])

    def test_41_residu_excedent_activites(self):
        row=m.reference_rows()[4]
        self.assertEqual(row["code"],"EXCEDENT_ACTIVITES")
        self.assertEqual(row["total_consolide_cad"]-row["administration_municipale_cad"]-row["organismes_controles_partenariats_cad"],row["residu_consolidation_cad"])

    def test_42_residu_fonctionnement_avant_conciliation(self):
        row=m.reference_rows()[5]
        self.assertEqual(row["code"],"FONCTIONNEMENT_AVANT_CONCILIATION")
        self.assertEqual(row["total_consolide_cad"]-row["administration_municipale_cad"]-row["organismes_controles_partenariats_cad"],row["residu_consolidation_cad"])

    def test_43_residu_elements_conciliation_fiscale(self):
        row=m.reference_rows()[6]
        self.assertEqual(row["code"],"ELEMENTS_CONCILIATION_FISCALE")
        self.assertEqual(row["total_consolide_cad"]-row["administration_municipale_cad"]-row["organismes_controles_partenariats_cad"],row["residu_consolidation_cad"])

    def test_44_residu_excedent_fonctionnement_fiscal(self):
        row=m.reference_rows()[7]
        self.assertEqual(row["code"],"EXCEDENT_FONCTIONNEMENT_FISCAL")
        self.assertEqual(row["total_consolide_cad"]-row["administration_municipale_cad"]-row["organismes_controles_partenariats_cad"],row["residu_consolidation_cad"])

    def test_45_revenus_0(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["REVENUS_FONCTIONNEMENT"]["administration_municipale_cad"]+r["REVENUS_INVESTISSEMENT"]["administration_municipale_cad"],r["REVENUS_TOTAUX"]["administration_municipale_cad"])

    def test_46_activites_0(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["REVENUS_TOTAUX"]["administration_municipale_cad"]-r["CHARGES"]["administration_municipale_cad"],r["EXCEDENT_ACTIVITES"]["administration_municipale_cad"])

    def test_47_fonctionnement_0(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["EXCEDENT_ACTIVITES"]["administration_municipale_cad"]-r["REVENUS_INVESTISSEMENT"]["administration_municipale_cad"],r["FONCTIONNEMENT_AVANT_CONCILIATION"]["administration_municipale_cad"])

    def test_48_fiscal_0(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["FONCTIONNEMENT_AVANT_CONCILIATION"]["administration_municipale_cad"]+r["ELEMENTS_CONCILIATION_FISCALE"]["administration_municipale_cad"],r["EXCEDENT_FONCTIONNEMENT_FISCAL"]["administration_municipale_cad"])

    def test_49_revenus_1(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["REVENUS_FONCTIONNEMENT"]["organismes_controles_partenariats_cad"]+r["REVENUS_INVESTISSEMENT"]["organismes_controles_partenariats_cad"],r["REVENUS_TOTAUX"]["organismes_controles_partenariats_cad"])

    def test_50_activites_1(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["REVENUS_TOTAUX"]["organismes_controles_partenariats_cad"]-r["CHARGES"]["organismes_controles_partenariats_cad"],r["EXCEDENT_ACTIVITES"]["organismes_controles_partenariats_cad"])

    def test_51_fonctionnement_1(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["EXCEDENT_ACTIVITES"]["organismes_controles_partenariats_cad"]-r["REVENUS_INVESTISSEMENT"]["organismes_controles_partenariats_cad"],r["FONCTIONNEMENT_AVANT_CONCILIATION"]["organismes_controles_partenariats_cad"])

    def test_52_fiscal_1(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["FONCTIONNEMENT_AVANT_CONCILIATION"]["organismes_controles_partenariats_cad"]+r["ELEMENTS_CONCILIATION_FISCALE"]["organismes_controles_partenariats_cad"],r["EXCEDENT_FONCTIONNEMENT_FISCAL"]["organismes_controles_partenariats_cad"])

    def test_53_revenus_2(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["REVENUS_FONCTIONNEMENT"]["total_consolide_cad"]+r["REVENUS_INVESTISSEMENT"]["total_consolide_cad"],r["REVENUS_TOTAUX"]["total_consolide_cad"])

    def test_54_activites_2(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["REVENUS_TOTAUX"]["total_consolide_cad"]-r["CHARGES"]["total_consolide_cad"],r["EXCEDENT_ACTIVITES"]["total_consolide_cad"])

    def test_55_fonctionnement_2(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["EXCEDENT_ACTIVITES"]["total_consolide_cad"]-r["REVENUS_INVESTISSEMENT"]["total_consolide_cad"],r["FONCTIONNEMENT_AVANT_CONCILIATION"]["total_consolide_cad"])

    def test_56_fiscal_2(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["FONCTIONNEMENT_AVANT_CONCILIATION"]["total_consolide_cad"]+r["ELEMENTS_CONCILIATION_FISCALE"]["total_consolide_cad"],r["EXCEDENT_FONCTIONNEMENT_FISCAL"]["total_consolide_cad"])

    def test_57_revenus_3(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["REVENUS_FONCTIONNEMENT"]["residu_consolidation_cad"]+r["REVENUS_INVESTISSEMENT"]["residu_consolidation_cad"],r["REVENUS_TOTAUX"]["residu_consolidation_cad"])

    def test_58_activites_3(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["REVENUS_TOTAUX"]["residu_consolidation_cad"]-r["CHARGES"]["residu_consolidation_cad"],r["EXCEDENT_ACTIVITES"]["residu_consolidation_cad"])

    def test_59_fonctionnement_3(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["EXCEDENT_ACTIVITES"]["residu_consolidation_cad"]-r["REVENUS_INVESTISSEMENT"]["residu_consolidation_cad"],r["FONCTIONNEMENT_AVANT_CONCILIATION"]["residu_consolidation_cad"])

    def test_60_fiscal_3(self):
        r={row["code"]:row for row in m.reference_rows()}
        self.assertEqual(r["FONCTIONNEMENT_AVANT_CONCILIATION"]["residu_consolidation_cad"]+r["ELEMENTS_CONCILIATION_FISCALE"]["residu_consolidation_cad"],r["EXCEDENT_FONCTIONNEMENT_FISCAL"]["residu_consolidation_cad"])

    def test_61_type_entier_bool_refuse(self):
        rows=m.reference_rows()
        rows[0]["total_consolide_cad"]=True
        with self.assertRaises(ValueError):
            m.validate_table(rows,m.BRIDGE)
    def test_62_doublon_ligne_refuse(self):
        rows=m.reference_rows()
        rows[1]=copy.deepcopy(rows[0])
        with self.assertRaises(ValueError):
            m.validate_table(rows,m.BRIDGE)
    def test_63_ligne_supprimee_refuse(self):
        with self.assertRaises(ValueError):
            m.validate_table(m.reference_rows()[:-1],m.BRIDGE)
    def test_64_table_nonneutre_rejetee(self):
        edited=copy.deepcopy(self.cfg)
        edited["protections"]["aucun_residu_qualifie_automatiquement_elimination"]=False
        with patch.object(m.p54z,"read_json",return_value=edited):
            with self.assertRaises(ValueError):m.configuration()
    def test_65_config_montant_change_refuse(self):
        edited=copy.deepcopy(self.cfg)
        edited["lignes"][0]["total_consolide_cad"]+=100
        with patch.object(m.p54z,"read_json",return_value=edited):
            with self.assertRaises(ValueError):m.configuration()
    def test_66_explications_non_automatiques(self):
        self.assertEqual(len(m.explanations()),4)
        self.assertTrue(all(x["statut"]=="A_INSTRUIRE_HUMAINEMENT"
                            for x in m.explanations()))
    def test_67_table_sans_hash_prive(self):
        raw=json.dumps(m.public_table())
        self.assertNotIn("sha256",raw)
        self.assertNotIn("offset_texte",raw)
    def test_68_bilan_ouvert_et_non_certifie(self):
        r=m.public_report()
        self.assertEqual(r["dossiers_p54e_ouverts"],4)
        self.assertEqual(r["date_probable_non_certifiee"],1)
        self.assertEqual(r["taches_p54n_non_attestees"],40)
        self.assertEqual(r["blocages_p54o_non_leves"],10)
        self.assertEqual(r["controles_p54b_non_attestes"],96)
        self.assertEqual(r["controles_p54c_non_attestes"],8)
    def test_69_cli_bilan_et_tableau(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d)/"bilan.json";t=Path(d)/"table.json"
            self.assertEqual(m.main(["--bilan-public",str(b),
                                     "--table-public",str(t)]),0)
            out=json.loads(b.read_text())
            rows=json.loads(t.read_text())
            self.assertEqual(out["ecart_charges_consolidation_derive_cad"],-178606212)
            self.assertEqual(len(rows["lignes"]),8)
    def test_70_cli_refus_cloture(self):
        self.assertEqual(m.main(["--exiger-cloture"]),3)
    def test_71_cli_sortie_existante_refusee(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"out.json";p.write_text("{}")
            self.assertEqual(m.main(["--bilan-public",str(p)]),2)
    def test_72_cli_sorties_dupliquees_refusees(self):
        with tempfile.TemporaryDirectory() as d:
            p=str(Path(d)/"out.json")
            self.assertEqual(m.main(["--bilan-public",p,"--table-public",p]),2)
    def test_73_identites_budget_et_fiscal_non_additionnees(self):
        self.assertEqual(m.BRIDGE["excedent_fonctionnement_fiscal_budget_cad"],0)
        self.assertEqual(m.public_report()["variation_budget_resultat_fiscal_cad"],129335957)
    def test_74_two_pdf_local_not_claimed(self):
        self.assertEqual(self.cfg["etat_initial"]["copies_pdf_verifiees_par_sha_actuel"],0)
    def test_75_succes_public_sans_go(self):
        self.assertEqual(m.main([]),0)
        self.assertEqual(m.public_table()["decision"],m.NO_GO)


if __name__=="__main__":
    unittest.main()
