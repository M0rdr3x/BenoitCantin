"""P52P: cinquante tests de couverture, de finance et de provenance."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"auditer_lacunes_preuves_nova_p52p.py"
spec=importlib.util.spec_from_file_location("nova_p52p",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def docs():
 return {k:m.read(p) for k,p in m.FILES.items()}

class P52PAudit(unittest.TestCase):
 def bad(self,mutate):
  d=docs()
  mutate(d)
  with self.assertRaises(ValueError):m.audit(d)
 def test_01_20_proofs(self):
  self.assertEqual(m.audit(docs())["preuves_total"],20)
 def test_02_zero_certified_proofs(self):
  self.assertEqual(m.audit(docs())["preuves_attestees"],0)
 def test_03_twenty_references(self):
  self.assertEqual(m.audit(docs())["pistes_referencees_total"],20)
 def test_04_at_least_one_unmapped_proof(self):
  self.assertGreater(m.audit(docs())["preuves_sans_piste_de_source"],0)
 def test_05_proof_count_conservation(self):
  r=m.audit(docs())
  self.assertEqual(r["preuves_avec_pistes_de_sources"]+r["preuves_sans_piste_de_source"],20)
 def test_06_primary_docs_do_not_certify(self):
  r=m.audit(docs())
  self.assertEqual(r["pdf_primaires_relecture_assistee"],2)
  self.assertEqual(r["pdf_budget_originaux_archives_attestes"],0)
 def test_07_b_count_dynamic(self):
  self.assertEqual(m.count_financial_unknowns(docs()["p52b"],docs()["p52d"])["p52b"],600)
 def test_08_d_count_dynamic(self):
  self.assertEqual(m.count_financial_unknowns(docs()["p52b"],docs()["p52d"])["p52d"],720)
 def test_09_adds_to_1320(self):
  self.assertEqual(m.audit(docs())["valeurs_monetaires_totales_inconnues"],1320)
 def test_10_context_not_counted_as_money(self):
  self.assertEqual(m.audit(docs())["autres_indicateurs_p52b_inconnus"],120)
 def test_11_sixty_exercises(self):
  self.assertEqual(m.audit(docs())["exercices_scenarios_p52b"],60)
 def test_12_thirty_households(self):
  self.assertEqual(m.audit(docs())["cas_menages_p52d"],30)
 def test_13_twelve_businesses(self):
  self.assertEqual(m.audit(docs())["cas_entreprises_p52d"],12)
 def test_14_separate_regimes(self):
  self.assertEqual(len(m.audit(docs())["par_regime"]),2)
 def test_15_each_regime_b_300(self):
  self.assertTrue(all(x["monetaires_p52b_manquantes"]==300 for x in m.audit(docs())["par_regime"].values()))
 def test_16_each_regime_d_360(self):
  self.assertTrue(all(x["monetaires_p52d_manquantes"]==360 for x in m.audit(docs())["par_regime"].values()))
 def test_17_f09_relecture_not_attestation(self):
  a=docs()
  self.assertTrue(a["registre"]["exigences"][8]["relecture_budgetaire_P52J_disponible"])
  self.assertFalse(a["registre"]["exigences"][8]["preuve_independante_authentifiee"])
 def test_18_20_empty_proof_checklists(self):
  a=docs()
  self.assertEqual(sum(len(x["pieces_obligatoires"]) for x in a["registre"]["exigences"]),160)
 def test_19_no_tax_rate_adopted(self):
  self.assertFalse(docs()["p52a"]["rates_selected"])
 def test_20_no_purchasing_power_guarantee(self):
  self.assertFalse(m.audit(docs())["assurance_non_appauvrissement"])
 def test_21_anti_evasion_stays_uncertified(self):
  self.assertFalse(m.audit(docs())["recettes_nouvelles_certifiees"])
 def test_22_f09_fake_attestation_rejected(self):
  self.bad(lambda d:d["registre"]["exigences"][8].update(preuve_independante_authentifiee=True))
 def test_23_f20_fake_validation_rejected(self):
  self.bad(lambda d:d["registre"]["exigences"][19].update(statut_juridique="VALIDE"))
 def test_24_f01_source_as_proof_rejected(self):
  self.bad(lambda d:d["registre"]["exigences"][0].update(source_identifiee_est_une_preuve=True))
 def test_25_f09_false_budget_certification_rejected(self):
  self.bad(lambda d:d["registre"]["exigences"][8].update(certification_budgetaire=True))
 def test_26_source_id_tamper_rejected(self):
  self.bad(lambda d:d["registre"]["index_pistes"][0].update(id="SXX"))
 def test_27_url_tamper_rejected(self):
  self.bad(lambda d:d["registre"]["index_pistes"][0].update(url="https://fake.invalid"))
 def test_28_url_version_false_certification_rejected(self):
  self.bad(lambda d:d["registre"]["index_pistes"][0].update(version_publique_confirmee=True))
 def test_29_false_pdf_archiving_rejected(self):
  self.bad(lambda d:d["registre"]["index_pistes"][18].update(empreinte_pdf_recue=True))
 def test_30_f02_sources_disappear_rejected(self):
  self.bad(lambda d:d["registre"]["exigences"][1].update(pistes_sources_reperées=[]))
 def test_31_f09_piece_inserted_without_receipt_rejected(self):
  self.bad(lambda d:d["registre"]["exigences"][8]["pieces_obligatoires"].update(document_source_complet_et_version="fictif"))
 def test_32_external_signature_claim_rejected(self):
  self.bad(lambda d:d["gabarit"].update(signature_et_identite_authentifiees=True))
 def test_33_fake_template_proof_id_rejected(self):
  self.bad(lambda d:d["gabarit"].update(preuve_id="F09"))
 def test_34_p52a_status_fake_rejected(self):
  self.bad(lambda d:d["p52a"]["required_evidence"][0].update(statut="VALIDE"))
 def test_35_p52i_source_certification_fake_rejected(self):
  self.bad(lambda d:d["p52i"].update(donnees_extraites_certifiees=True))
 def test_36_p52j_budget_certification_fake_rejected(self):
  self.bad(lambda d:d["p52j"]["validation_de_nature"].update(preuve_F09_independamment_attestee=True))
 def test_37_p52k_hash_fake_rejected(self):
  self.bad(lambda d:d["p52k"]["fichiers_source"][0].update(empreinte_sha256_pdf_original="a"*64))
 def test_38_p52o_evidence_fake_rejected(self):
  self.bad(lambda d:d["p52o"]["preuves"][0].update(preuve_independante_obtenue=True))
 def test_39_p52n_expert_fake_rejected(self):
  self.bad(lambda d:d["p52n"]["mandats"][0].update(expert_mandate=True))
 def test_40_b_missing_money_changed_rejected(self):
  self.bad(lambda d:d["p52b"]["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0]["recettes"].update(impot_revenu_net="500"))
 def test_41_b_anti_evasion_unsupported_rejected(self):
  self.bad(lambda d:d["p52b"]["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0]["recettes"].update(anti_evasion_additionnelle_nette="100"))
 def test_42_b_context_invalid_claim_rejected(self):
  self.bad(lambda d:d["p52b"]["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0].update(perimetre_reconcilie=True))
 def test_43_b_year_missing_rejected(self):
  self.bad(lambda d:d["p52b"]["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"].pop())
 def test_44_d_population_unsupported_rejected(self):
  self.bad(lambda d:d["p52d"].update(aucune_ponderation_population=False))
 def test_45_d_fabricated_income_rejected(self):
  self.bad(lambda d:d["p52d"]["regimes"]["QUEBEC_DANS_CANADA"]["scenarios"]["central"]["menages"][0]["actuel"].update(revenu_brut="45000"))
 def test_46_d_fabricated_company_rejected(self):
  self.bad(lambda d:d["p52d"]["regimes"]["QUEBEC_SOUVERAIN"]["scenarios"]["stress"]["entreprises"][0]["propose"].update(chiffre_affaires="123"))
 def test_47_aggregates_no_url_no_identifying_cases(self):
  r=json.dumps(m.audit(docs()),ensure_ascii=False)
  for v in ("https://","S01","REF01","F09","personne_seule_revenu_modeste"):
   self.assertNotIn(v,r)
 def test_48_cli_normal_no_go(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/"report.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(json.loads(p.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_49_cli_strict_exit3(self):
  with tempfile.TemporaryDirectory() as temp:
   self.assertEqual(m.main(["--exiger-preuves","--rapport",str(Path(temp)/"r.json")]),3)
 def test_50_cli_missing_file_exit2(self):
  with tempfile.TemporaryDirectory() as temp:
   self.assertEqual(m.main(["--p52b",str(Path(temp)/"missing.json")]),2)
 def test_51_cli_non_overwrite(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/"r.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(m.main(["--rapport",str(p)]),2)
if __name__=="__main__":
 unittest.main()
