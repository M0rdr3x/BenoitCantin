"""P52O: tests de dependances, sources, devis synthetiques et NO_GO."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"auditer_acquisition_preuves_nova_p52o.py"
spec=importlib.util.spec_from_file_location("p52o",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixtures():
 d={k:m.read(path) for k,path in m.FILES.items()}
 return d,m.reference(d)

def quote(i=1,lot="B-BUD",scope="a"*64,days=10,rate="100.00"):
 return {"id":f"Q-AB{i:04d}","lot_id":lot,
         "portee_sha256":scope,"preuve_devis_sha256":"b"*64,
         "valide_jusquau":"2026-11-19","devise":"CAD","jours":days,
         "tarif_journalier_cad":rate,"frais_fixes_cad":"50.00",
         "provision_cad":"100.00","taxes_cad":"0.00",
         "total_cad":f"{days*float(rate)+150:.2f}",
         "simulation_synthetique":True}

class EtudesP52O(unittest.TestCase):
 def reject_reference(self,change):
  d,o=fixtures();change(d)
  with self.assertRaises(ValueError):m.reference(d)
 def reject_quotes(self,change):
  d,o=fixtures()
  d["devis"]["simulations"]=[quote(1),quote(2)]
  change(d["devis"]["simulations"])
  with self.assertRaises(ValueError):m.evaluer_devis(o,d["devis"])
 def test_01_twenty_proofs(self):
  d,o=fixtures();self.assertEqual(len(o),20)
 def test_02_six_waves(self):
  d,o=fixtures();self.assertEqual(set(o.values()),set(range(1,7)))
 def test_03_no_duplicate_proof(self):
  d,o=fixtures();self.assertEqual(len(set(o)),20)
 def test_04_early_f01(self):
  d,o=fixtures();self.assertEqual(o["F01"],1)
 def test_05_early_f09(self):
  d,o=fixtures();self.assertEqual(o["F09"],1)
 def test_06_late_f12(self):
  d,o=fixtures();self.assertEqual(o["F12"],6)
 def test_07_f10_comes_after_evasion(self):
  d,o=fixtures();self.assertGreater(o["F10"],o["F08"])
 def test_08_all_prerequisites_earlier(self):
  d,o=fixtures()
  self.assertTrue(all(o[pr]<o[k] for k,ds in m.DEPS.items() for pr in ds))
 def test_09_ten_sources(self):
  d,o=fixtures();self.assertEqual(len(d["sources"]["references"]),10)
 def test_10_sources_not_independently_certified(self):
  d,o=fixtures();self.assertTrue(all(not x["attestation_expert_independant"] for x in d["sources"]["references"]))
 def test_11_still_1320_unknown(self):
  d,o=fixtures();self.assertEqual(d["plan"]["gouvernance"]["variables_financieres_inconnues"],1320)
 def test_12_zero_real_quotes(self):
  d,o=fixtures();self.assertEqual(m.evaluer_devis(o,d["devis"])["offres_reelles_reçues"],0)
 def test_13_no_go_default(self):
  d,o=fixtures();self.assertEqual(m.evaluer_devis(o,d["devis"])["decision"],"NO_GO_AUTOMATIQUE")
 def test_14_empty_packs_have_null_costs(self):
  d,o=fixtures();self.assertTrue(all(all(p[k] is None for k in m.NULL_COSTS) for p in d["plan"]["lot_expertises"]))
 def test_15_valid_fake_comparison(self):
  d,o=fixtures();d["devis"]["simulations"]=[quote(1),quote(2)]
  r=m.evaluer_devis(o,d["devis"])
  self.assertEqual(r["devis_synthetiques_evalues"],2)
  self.assertEqual(r["lots_avec_comparaison_fictive"],1)
  self.assertEqual(r["experts_independants_recrutes"],0)
 def test_16_one_quote_cannot_be_called_comparison(self):
  self.reject_quotes(lambda q:q.pop())
 def test_17_mismatched_scope_rejected(self):
  self.reject_quotes(lambda q:q[1].update(portee_sha256="c"*64))
 def test_18_mismatched_currency_rejected(self):
  self.reject_quotes(lambda q:q[0].update(devise="USD"))
 def test_19_unknown_lot_rejected(self):
  self.reject_quotes(lambda q:q[0].update(lot_id="B-FAKE"))
 def test_20_real_quote_claim_rejected(self):
  self.reject_quotes(lambda q:q[0].update(simulation_synthetique=False))
 def test_21_missing_sha_rejected(self):
  self.reject_quotes(lambda q:q[0].update(preuve_devis_sha256="not-hash"))
 def test_22_nonmatching_total_rejected(self):
  self.reject_quotes(lambda q:q[0].update(total_cad="9999.00"))
 def test_23_negative_fees_rejected(self):
  self.reject_quotes(lambda q:q[0].update(frais_fixes_cad="-50.00"))
 def test_24_float_amount_rejected(self):
  self.reject_quotes(lambda q:q[0].update(tarif_journalier_cad=100.0))
 def test_25_decimals_too_many_rejected(self):
  self.reject_quotes(lambda q:q[0].update(tarif_journalier_cad="100.005"))
 def test_26_zero_rate_rejected(self):
  self.reject_quotes(lambda q:q[0].update(tarif_journalier_cad="0.00"))
 def test_27_zero_days_rejected(self):
  self.reject_quotes(lambda q:q[0].update(jours=0))
 def test_28_float_days_rejected(self):
  self.reject_quotes(lambda q:q[0].update(jours=2.5))
 def test_29_excessive_days_rejected(self):
  self.reject_quotes(lambda q:q[0].update(jours=400))
 def test_30_expired_quote_rejected(self):
  self.reject_quotes(lambda q:q[0].update(valide_jusquau="2026-01-01"))
 def test_31_nonexistent_date_rejected(self):
  self.reject_quotes(lambda q:q[0].update(valide_jusquau="2026-02-30"))
 def test_32_extra_private_data_rejected(self):
  self.reject_quotes(lambda q:q[0].update(nom_expert="Confidentiel"))
 def test_33_duplicate_quote_id_rejected(self):
  self.reject_quotes(lambda q:q[1].update(id=q[0]["id"]))
 def test_34_wrong_hash_scope_rejected(self):
  self.reject_quotes(lambda q:q[0].update(portee_sha256="short"))
 def test_35_plan_missing_wave_rejected(self):
  self.reject_reference(lambda d:d["plan"]["vagues"].pop())
 def test_36_plan_future_dependency_rejected(self):
  self.reject_reference(lambda d:d["plan"]["preuves"][9].update(dependances_techniques=["F12"]))
 def test_37_plan_wrong_committee_rejected(self):
  self.reject_reference(lambda d:d["plan"]["preuves"][8].update(comite_pilote="CJF"))
 def test_38_plan_tax_rate_not_adopted(self):
  d,o=fixtures();self.assertFalse(d["p52a"]["rates_selected"])
 def test_39_p52a_false_proof_rejected(self):
  self.reject_reference(lambda d:d["p52a"]["required_evidence"][8].update(preuve_independante_obtenue=True))
 def test_40_p52m_fake_expert_rejected(self):
  self.reject_reference(lambda d:d["p52m"]["etat_reel"].update(membres_nommes=1))
 def test_41_p52n_fake_mandate_rejected(self):
  self.reject_reference(lambda d:d["p52n"]["mandats"][8].update(expert_mandate=True))
 def test_42_source_fake_certification_rejected(self):
  self.reject_reference(lambda d:d["sources"]["references"][0].update(attestation_expert_independant=True))
 def test_43_source_official_url_mutated_rejected(self):
  self.reject_reference(lambda d:d["sources"]["references"][0].update(url="https://fake.example.com"))
 def test_44_false_cost_estimate_rejected(self):
  self.reject_reference(lambda d:d["plan"]["lot_expertises"][0].update(coute_estime_total_cad="1000.00"))
 def test_45_false_budget_approval_rejected(self):
  self.reject_reference(lambda d:d["plan"]["lot_expertises"][0].update(financement_approuve=True))
 def test_46_false_seao_requirement_claim_rejected(self):
  self.reject_reference(lambda d:d["plan"]["regles_acquisition"].update(obligations_SEAO_uniquement_si_organisme_assujetti=False))
 def test_47_fake_licence_rejected(self):
  self.reject_reference(lambda d:d["plan"]["gouvernance"].update(licences_de_microsimulation_obtenues=True))
 def test_48_registre_fake_real_offer_rejected(self):
  self.reject_reference(lambda d:d["devis"].update(aucun_devis_reel_obtenu=False))
 def test_49_no_url_or_identity_in_public_report(self):
  d,o=fixtures();d["devis"]["simulations"]=[quote(1),quote(2)]
  text=json.dumps(m.evaluer_devis(o,d["devis"]))
  for needle in ("Q-AB0001","https://","a"*64,"1000.00"):
   self.assertNotIn(needle,text)
 def test_50_cli_coherent_no_go(self):
  with tempfile.TemporaryDirectory() as temp:
   target=Path(temp)/"r.json"
   self.assertEqual(m.main(["--rapport",str(target)]),0)
   self.assertEqual(json.loads(target.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_51_cli_strict_code_3(self):
  with tempfile.TemporaryDirectory() as temp:
   self.assertEqual(m.main(["--exiger-preuves","--rapport",str(Path(temp)/"r.json")]),3)
 def test_52_cli_missing_file_code_2(self):
  with tempfile.TemporaryDirectory() as temp:
   self.assertEqual(m.main(["--plan",str(Path(temp)/"none.json")]),2)
 def test_53_report_never_overwritten(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/"r.json"
   self.assertEqual(m.main(["--rapport",str(path)]),0)
   self.assertEqual(m.main(["--rapport",str(path)]),2)
if __name__=="__main__":
 unittest.main()
