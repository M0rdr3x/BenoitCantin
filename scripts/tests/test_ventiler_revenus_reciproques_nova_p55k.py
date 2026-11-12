"""P55K — 70 tests synthétiques, sans PDF original ni réseau."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ventiler_revenus_reciproques_nova_p55k as m

class TestP55K(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()

    def test_01_schema(self):
        self.assertEqual(self.cfg["schema_version"],"P55K-1")

    def test_02_date(self):
        self.assertEqual(self.cfg["date_reference"],"2026-11-04")

    def test_03_exercice(self):
        self.assertEqual(self.cfg["exercice"],2024)

    def test_04_sources(self):
        self.assertEqual(self.cfg["references"],["P54Q","P55H","P55I","P55J"])

    def test_05_guards_count(self):
        self.assertEqual(len(m.GUARDS),39)

    def test_06_guards_all(self):
        self.assertTrue(all(self.cfg['protections'].values()))

    def test_07_rows_count(self):
        self.assertEqual(len(m.ROWS),10)

    def test_08_codes_unique(self):
        self.assertEqual(len({r[0] for r in m.ROWS}),10)

    def test_09_human_tasks(self):
        self.assertEqual(len(m.review_tasks()),5)

    def test_10_method_page(self):
        self.assertEqual(m.SOURCE['page_pdf_index_zero_methodes'],34)

    def test_11_budget_page(self):
        self.assertEqual(m.SOURCE['page_pdf_index_zero_budget'],196)

    def test_12_s12_page(self):
        self.assertEqual(m.SOURCE['page_pdf_index_zero_ventilation'],62)

    def test_13_source_text_only(self):
        self.assertTrue('NON_CONTROLEE_VISUELLEMENT' in m.SOURCE['niveau_preuve_ventilation'])

    def test_14_source_no_original(self):
        self.assertEqual(m.SOURCE['etat_original_local'],"NON_ACQUIS_NON_AUTHENTIFIE")

    def test_15_admin_total(self):
        self.assertEqual(m.TOTALS['administration_revenus_fonctionnement_cad'],2008356306)

    def test_16_org_total(self):
        self.assertEqual(m.TOTALS['organismes_revenus_fonctionnement_cad'],354693719)

    def test_17_consol_total(self):
        self.assertEqual(m.TOTALS['total_revenus_fonctionnement_consolides_cad'],2186607854)

    def test_18_residu_total(self):
        self.assertEqual(m.TOTALS['residu_revenus_fonctionnement_cad'],-176442171)

    def test_19_quotes_residu(self):
        self.assertEqual(m.TOTALS['residu_quotes_parts_cad'],-154047800)

    def test_20_residu_rest(self):
        self.assertEqual(m.TOTALS['autres_residus_cad'],-22394371)

    def test_21_share(self):
        self.assertEqual(m.percent_rounded(154047800,176442171),"87.3")

    def test_22_share_half_up(self):
        self.assertEqual(m.percent_rounded(1,8),"12.5")

    def test_23_share_no_zero(self):
        with self.assertRaises(ValueError):m.percent_rounded(1,0)

    def test_24_share_no_bool(self):
        with self.assertRaises(ValueError):m.percent_rounded(True,10)

    def test_25_valid_totals(self):
        self.assertEqual(m.validate_lines(m.reference_lines(),m.TOTALS)['residu_total_moins_somme_cad'],-176442171)

    def test_26_no_rtc_split(self):
        self.assertFalse(m.TOTALS['organismes_individuels_rtc_somhac_ventiles'])

    def test_27_no_cpa(self):
        self.assertFalse(m.public_report()['quotes_parts_qualifiees_par_ecritures'])

    def test_28_no_pdf(self):
        self.assertFalse(m.public_report()['page_ventilation_s12_verifiee_visuellement'])

    def test_29_no_sha(self):
        self.assertEqual(m.public_report()['copies_pdf_authentifiees_sha_actuel'],0)

    def test_30_no_attestation(self):
        self.assertEqual(m.public_report()['attestations_professionnelles'],0)

    def test_31_no_mandates(self):
        self.assertEqual(m.public_report()['mandats_signes'],0)

    def test_32_no_savings(self):
        self.assertFalse(m.public_report()['ecarts_sont_economies_certifiees'])

    def test_33_savings_none(self):
        self.assertEqual(m.public_report()['economies_certifiees_cad'],None)

    def test_34_no_go(self):
        self.assertEqual(m.public_report()['decision'],m.NO_GO)

    def test_35_no_merge(self):
        self.assertFalse(m.public_report()['fusion_main_autorisee'])

    def test_36_no_send(self):
        self.assertFalse(m.public_report()['transmission_externe_autorisee'])

    def test_37_qualify_7(self):
        self.assertEqual(m.public_report()['nombre_categories_a_qualifier_humainement'],7)

    def test_38_zero_residue_3(self):
        self.assertEqual(sum(r['residu_total_moins_somme_cad']==0 for r in m.reference_lines()),3)

    def test_39_public_table_10(self):
        self.assertEqual(len(m.public_table()['lignes']),10)

    def test_40_public_table_5_actions(self):
        self.assertEqual(len(m.public_table()['travaux_humains_requis']),5)

    def test_41_public_table_no_hash(self):
        self.assertNotIn('sha256',json.dumps(m.public_table()))

    def test_42_mutation_amount(self):
        r=copy.deepcopy(m.reference_lines())
        r[0]['total_consolide_cad']+=1
        with self.assertRaises(ValueError):m.validate_lines(r,m.TOTALS)

    def test_43_mutation_total(self):
        tot=dict(m.TOTALS)
        tot['autres_residus_cad']+=1
        with self.assertRaises(ValueError):m.validate_lines(m.reference_lines(),tot)

    def test_44_mutation_guard(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['protections']['aucune_economie_certifiee_sur_residus']=False
        with patch.object(m.p54z,'read_json',return_value=cfg):
            with self.assertRaises(ValueError):m.configuration()

    def test_45_mutation_source(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['source']['page_pdf_index_zero_ventilation']=60
        with patch.object(m.p54z,'read_json',return_value=cfg):
            with self.assertRaises(ValueError):m.configuration()

    def test_46_cli_neutral(self):
        self.assertEqual(m.main([]),0)

    def test_47_cli_refuses_cert(self):
        self.assertEqual(m.main(['--exiger-certification']),3)

    def test_48_cli_writes_two(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d)/'bilan.json';t=Path(d)/'table.json'
            self.assertEqual(m.main(['--bilan-public',str(b),'--table-public',str(t)]),0)
            self.assertEqual(json.loads(b.read_text())['residu_quotes_parts_cad'],-154047800)
            self.assertEqual(len(json.loads(t.read_text())['lignes']),10)

    def test_49_cli_refuses_existing(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d)/'bilan.json';b.write_text('{}')
            self.assertEqual(m.main(['--bilan-public',str(b)]),2)

    def test_50_cli_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            p=str(Path(d)/'bilan.json')
            self.assertEqual(m.main(['--bilan-public',p,'--table-public',p]),2)

    def test_51_code_taxes(self):
        self.assertEqual(m.reference_lines()[0]['code'],"TAXES")

    def test_52_arithmetic_taxes(self):
        r=m.reference_lines()[0]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

    def test_53_code_compensations_tenant_lieu_taxes(self):
        self.assertEqual(m.reference_lines()[1]['code'],"COMPENSATIONS_TENANT_LIEU_TAXES")

    def test_54_arithmetic_compensations_tenant_lieu_taxes(self):
        r=m.reference_lines()[1]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

    def test_55_code_quotes_parts(self):
        self.assertEqual(m.reference_lines()[2]['code'],"QUOTES_PARTS")

    def test_56_arithmetic_quotes_parts(self):
        r=m.reference_lines()[2]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

    def test_57_code_transferts(self):
        self.assertEqual(m.reference_lines()[3]['code'],"TRANSFERTS")

    def test_58_arithmetic_transferts(self):
        r=m.reference_lines()[3]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

    def test_59_code_services_rendus(self):
        self.assertEqual(m.reference_lines()[4]['code'],"SERVICES_RENDUS")

    def test_60_arithmetic_services_rendus(self):
        r=m.reference_lines()[4]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

    def test_61_code_imposition_de_droits(self):
        self.assertEqual(m.reference_lines()[5]['code'],"IMPOSITION_DE_DROITS")

    def test_62_arithmetic_imposition_de_droits(self):
        r=m.reference_lines()[5]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

    def test_63_code_amendes_et_penalites(self):
        self.assertEqual(m.reference_lines()[6]['code'],"AMENDES_ET_PENALITES")

    def test_64_arithmetic_amendes_et_penalites(self):
        r=m.reference_lines()[6]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

    def test_65_code_revenus_placements(self):
        self.assertEqual(m.reference_lines()[7]['code'],"REVENUS_PLACEMENTS")

    def test_66_arithmetic_revenus_placements(self):
        r=m.reference_lines()[7]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

    def test_67_code_autres_revenus_interets(self):
        self.assertEqual(m.reference_lines()[8]['code'],"AUTRES_REVENUS_INTERETS")

    def test_68_arithmetic_autres_revenus_interets(self):
        r=m.reference_lines()[8]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

    def test_69_code_autres_revenus(self):
        self.assertEqual(m.reference_lines()[9]['code'],"AUTRES_REVENUS")

    def test_70_arithmetic_autres_revenus(self):
        r=m.reference_lines()[9]
        self.assertEqual(r['total_consolide_cad']-r['administration_municipale_cad']-r['organismes_controles_partenariats_cad'],r['residu_total_moins_somme_cad'])

if __name__=="__main__":
    unittest.main()
