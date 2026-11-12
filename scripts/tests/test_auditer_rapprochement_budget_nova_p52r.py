"""P52R: test autonome des chiffres de mars 2026 et du hachage local non attesté."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
PY=ROOT/"scripts"/"auditer_rapprochement_budget_nova_p52r.py"
spec=importlib.util.spec_from_file_location("nova_p52r",PY)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def get():
    return {k:m.read(p) for k,p in m.FILES.items()}
class BudgetP52R(unittest.TestCase):
    def reject(self,change):
        d=get()
        change(d)
        with self.assertRaises(ValueError):m.check(d)
    def sample_pdf(self,dir,name="one.pdf",end=True):
        path=Path(dir)/name
        content=b"%PDF-1.4\nsynthetic-test-only\n"+(b"%%EOF\n" if end else b"unfinished\n")
        path.write_bytes(content)
        return path,content
    def test_01_21_rows(self):
        self.assertEqual(m.check(get())["lignes_budget_discours_controlees"],21)
    def test_02_eight_subtotals(self):
        self.assertEqual(m.check(get())["sous_totaux_budget_discours_controles"],8)
    def test_03_ten_signed(self):
        self.assertEqual(m.check(get())["agregats_signes_plan_controles"],10)
    def test_04_ten_reconciliation_equations(self):
        self.assertEqual(m.check(get())["identites_arithmetiques_confirmees"],10)
    def test_05_expected_revenues(self):
        self.assertEqual(m.PASSAGES["revenus_totaux"],166492)
    def test_06_expected_expenses(self):
        self.assertEqual(m.PASSAGES["depenses_totales"],-170757)
    def test_07_expected_deficit(self):
        self.assertEqual(m.PASSAGES["solde_budgetaire_loi_equilibre"],-8612)
    def test_08_expected_before_provision(self):
        self.assertEqual(m.PASSAGES["solde_avant_provision"],-4265)
    def test_09_discours_sums(self):
        self.assertEqual(sum(m.OFFICIAL_LINES["group_income"]),76050)
        self.assertEqual(sum(m.OFFICIAL_LINES["group_consumption"]),30008)
        self.assertEqual(sum(m.OFFICIAL_LINES["group_business"]),5853)
    def test_10_federal_transfers(self):
        self.assertEqual(sum(m.OFFICIAL_LINES["group_federal"]),32131)
    def test_11_no_certificate(self):
        self.assertEqual(m.check(get())["pdf_originaux_autentifies"],0)
    def test_12_no_go(self):
        self.assertEqual(m.check(get())["decision"],"NO_GO_AUTOMATIQUE")
    def test_13_fake_budget_row(self):
        self.reject(lambda d:d["p52r"]["figures_lues_depuis_images_publiees_mcad"]["group_income"].update(impot_particuliers=9999))
    def test_14_fake_budget_subtotal(self):
        self.reject(lambda d:d["p52r"]["agrege_officiel_2026_2027_mcad"].update(revenus_autonomes=1))
    def test_15_fake_budget_signed(self):
        self.reject(lambda d:d["p52r"]["agrege_officiel_2026_2027_mcad"].update(depenses_totales=170757))
    def test_16_fake_reconciliation(self):
        self.reject(lambda d:d["p52r"]["rapprochements_attendus_mcad"].update(solde_avant_provision=999))
    def test_17_fake_p52j_row(self):
        self.reject(lambda d:d["p52j"]["transcription_discours_tableau3"]["lignes_revenus"][0].update(valeur_mcad="0"))
    def test_18_fake_p52c_row(self):
        self.reject(lambda d:d["p52c"]["lignes_revenus"][0].update(valeur_mcad="0"))
    def test_19_fake_p52j_subtotal(self):
        self.reject(lambda d:d["p52j"]["transcription_discours_tableau3"]["sous_totaux_officiels_mcad"].update(revenus_totaux="100"))
    def test_20_fake_p52c_expense(self):
        self.reject(lambda d:d["p52c"]["depenses_et_ajustements_officiels_mcad"].update(service_dette="10267"))
    def test_21_fake_p52j_signed(self):
        self.reject(lambda d:d["p52j"]["transcription_plan_budgetaire_f2"]["montants_signes_comme_affiches_mcad"].update(deficit_comptable="-7000"))
    def test_22_wrong_page_number(self):
        self.reject(lambda d:d["p52r"]["origine_constats"][0].update(page_pdf_index_zero=30))
    def test_23_wrong_url(self):
        self.reject(lambda d:d["p52r"]["origine_constats"][1].update(url="https://fake.example"))
    def test_24_false_original_hash(self):
        self.reject(lambda d:d["p52r"]["origine_constats"][0].update(sha256_original="a"*64))
    def test_25_false_k_source_download(self):
        self.reject(lambda d:d["p52k"]["fichiers_source"][0].update(acquisition_document_origine="EFFECTUEE"))
    def test_26_false_j_F09_attestation(self):
        self.reject(lambda d:d["p52j"]["validation_de_nature"].update(preuve_F09_independamment_attestee=True))
    def test_27_false_p52a_adoption(self):
        self.reject(lambda d:d["p52a"].update(automatic_go=True))
    def test_28_false_F09_liberated(self):
        self.reject(lambda d:d["p52r"]["etat_dossiers"].update(F09="VALIDE"))
    def test_29_removed_caution(self):
        self.reject(lambda d:d["p52r"]["limitations"].update(transferts_federaux_non_presumes_en_cas_de_souverainete=False))
    def test_30_valid_local_receipt_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p,content=self.sample_pdf(d)
            receipt=m.read_pdf_receipt(p)
            self.assertEqual(receipt["sha256_octets_lus"],hashlib.sha256(content).hexdigest())
            self.assertEqual(receipt["taille_octets"],len(content))
            self.assertFalse(receipt["authenticite_ministerielle_attestee"])
    def test_31_missing_eof_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p,_=self.sample_pdf(d,end=False)
            with self.assertRaises(ValueError):m.read_pdf_receipt(p)
    def test_32_non_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.pdf";p.write_bytes(b"not a pdf %%EOF")
            with self.assertRaises(ValueError):m.read_pdf_receipt(p)
    def test_33_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.read_pdf_receipt(Path(d)/"no.pdf")
    def test_34_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p,_=self.sample_pdf(d)
            link=Path(d)/"link.pdf";link.symlink_to(p)
            with self.assertRaises(ValueError):m.read_pdf_receipt(link)
    def test_35_cli_no_pdf_no_go(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"report.json"
            self.assertEqual(m.main(["--rapport",str(path)]),0)
            r=json.loads(path.read_text())
            self.assertIsNone(r["reception_octets_locale_non_attestee"])
            self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_36_cli_exige_originaux_code3(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.main(["--exiger-originaux","--rapport",str(Path(d)/"x.json")]),3)
    def test_37_cli_exige_expertise_code3(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.main(["--exiger-expertise","--rapport",str(Path(d)/"x.json")]),3)
    def test_38_cli_requires_both_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            pdf,_=self.sample_pdf(d)
            self.assertEqual(m.main(["--discours-fichier",str(pdf),"--rapport",str(Path(d)/"x.json")]),2)
    def test_39_cli_distinct_pdf_files(self):
        with tempfile.TemporaryDirectory() as d:
            pdf,_=self.sample_pdf(d)
            self.assertEqual(m.main(["--discours-fichier",str(pdf),"--plan-fichier",str(pdf),"--rapport",str(Path(d)/"x.json")]),2)
    def test_40_cli_two_synthetic_receipts_only(self):
        with tempfile.TemporaryDirectory() as d:
            p1,_=self.sample_pdf(d,"d.pdf")
            p2,_=self.sample_pdf(d,"p.pdf")
            path=Path(d)/"report.json"
            self.assertEqual(m.main(["--discours-fichier",str(p1),"--plan-fichier",str(p2),"--rapport",str(path)]),0)
            result=json.loads(path.read_text())
            self.assertEqual(len(result["reception_octets_locale_non_attestee"]),2)
            self.assertEqual(result["pdf_originaux_autentifies"],0)
            self.assertFalse(result["adoption_autorisee"])
    def test_41_cli_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"report.json"
            self.assertEqual(m.main(["--rapport",str(path)]),0)
            self.assertEqual(m.main(["--rapport",str(path)]),2)
    def test_42_cli_missing_ref_code2(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.main(["--p52r",str(Path(d)/"missing.json")]),2)
    def test_43_report_no_values_or_url(self):
        text=json.dumps(m.check(get()),ensure_ascii=False)
        for secret in ("https://","134361","166492","-8612","Budget2627","F09"):
            self.assertNotIn(secret,text)
    def test_44_rejected_fake_legal_authorization(self):
        self.reject(lambda d:d["p52r"]["etat_dossiers"].update(adoption_autorisee=True))
if __name__=="__main__":
    unittest.main()
