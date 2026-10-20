"""P52N: controles adversariaux des mandats et consultations fictives."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"auditer_mandats_consultation_nova_p52n.py"
spec=importlib.util.spec_from_file_location("p52n",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def context():
 d={k:m.read(path) for k,path in m.FILES.items()}
 return d,m.reference(d)

def person(code,grades=(3,3,3,3,3),conflict=False,recuse=False,ind=True):
 return {"ref":code,"scores":list(grades) if grades is not None else None,
         "conflit_signale":conflict,"recuse":recuse,
         "independance_declaree":ind}

def candidate():
 return {"preuve_id":"F09","candidat_ref":"SIM-ABC001",
         "document_sha256":"a"*64,
         "evaluateurs":[person("EV-001"),person("EV-002")],
         "orientation_proposee":"A_ETUDIER"}

def observation():
 return {"id":"OBS-0001","preuve_id":"F11","regime":"TOUS",
         "type_observation":"OBJECTION","canal":"ACCESSIBLE",
         "empreinte_note":"b"*64,"contenant_donnees_personnelles":False,
         "statut_reponse":"SANS_REPONSE","empreinte_reponse":None}

class ExpertsConsultationP52N(unittest.TestCase):
 def reject_candidate(self,change):
  d,x=context();c=candidate();change(c);d["simulation"]["simulations_candidatures"]=[c]
  with self.assertRaises(ValueError):m.examen(x,d["simulation"])
 def reject_observation(self,change):
  d,x=context();o=observation();change(o);d["simulation"]["simulations_observations"]=[o]
  with self.assertRaises(ValueError):m.examen(x,d["simulation"])
 def reject_policy(self,change):
  d,x=context();change(d)
  with self.assertRaises(ValueError):m.reference(d)
 def test_01_twenty_mandates(self):
  d,x=context();self.assertEqual(len(x),20)
 def test_02_unassigned_committees(self):
  d,x=context();self.assertEqual(set(x),{f"F{n:02}" for n in range(1,21)})
 def test_03_reference_no_go(self):
  d,x=context();self.assertEqual(m.examen(x,d["simulation"])["decision"],"NO_GO_AUTOMATIQUE")
 def test_04_no_real_experts(self):
  d,x=context();self.assertEqual(m.examen(x,d["simulation"])["experts_mandates"],0)
 def test_05_no_real_contributions(self):
  d,x=context();self.assertEqual(m.examen(x,d["simulation"])["contributions_reelles"],0)
 def test_06_missing_costs_remain_null(self):
  d,x=context();self.assertTrue(all(v["cout_reel"] is None for v in x.values()))
 def test_07_differing_jurisdictions(self):
  d,x=context();self.assertEqual(x["F15"]["regime"],"QUEBEC_SOUVERAIN")
 def test_08_f20_complementary_advisors(self):
  d,x=context();self.assertEqual(x["F20"]["comites_consultes"],["CJF","CDE"])
 def test_09_zero_session_no_go(self):
  d,x=context();self.assertEqual(m.examen(x,d["simulation"])["candidatures_simulees"],0)
 def test_10_valid_fictional_examination(self):
  d,x=context();d["simulation"]["simulations_candidatures"]=[candidate()]
  res=m.examen(x,d["simulation"])
  self.assertEqual(res["candidatures_avec_appreciation_favorable_simulee"],1)
  self.assertEqual(res["contrats_signes"],0)
 def test_11_two_independent_evaluators_needed(self):
  self.reject_candidate(lambda c:c["evaluateurs"].pop())
 def test_12_three_reviewer_declared_not_go(self):
  d,x=context();c=candidate();c["evaluateurs"].append(person("EV-003"))
  d["simulation"]["simulations_candidatures"]=[c]
  self.assertFalse(m.examen(x,d["simulation"])["autorisation_sollicitation"])
 def test_13_duplicate_evaluator(self):
  self.reject_candidate(lambda c:c["evaluateurs"][1].update(ref="EV-001"))
 def test_14_candidate_cannot_evaluate_itself(self):
  self.reject_candidate(lambda c:c.update(candidat_ref="SIM-ABC001") or c["evaluateurs"][0].update(ref="SIM-ABC001"))
 def test_15_declared_conflict_requires_recusal(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(conflit_signale=True))
 def test_16_recused_cannot_score(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(recuse=True))
 def test_17_nonindependent_requires_recusal(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(independance_declaree=False))
 def test_18_recused_count_eligible_two_needed(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(conflit_signale=True,recuse=True,scores=None))
 def test_19_recused_with_two_other_valid(self):
  d,x=context();c=candidate();c["evaluateurs"].append(person("EV-003"))
  c["evaluateurs"][0].update(conflit_signale=True,recuse=True,scores=None)
  d["simulation"]["simulations_candidatures"]=[c]
  self.assertEqual(m.examen(x,d["simulation"])["recusations_declarees_simulees"],1)
 def test_20_negative_grade(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(scores=[-1,4,4,4,4]))
 def test_21_decimal_grade_rejected(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(scores=[3,3,3,3,3.5]))
 def test_22_missing_criteria_rejected(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(scores=[4,4,4,4]))
 def test_23_low_total_with_favorable_rejected(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(scores=[2,2,2,2,2]))
 def test_24_low_dimension_with_favorable_rejected(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(scores=[1,4,4,4,4]))
 def test_25_nonfavorable_on_good_grades_rejected(self):
  self.reject_candidate(lambda c:c.update(orientation_proposee="COMPETENCES_A_REVOIR"))
 def test_26_valid_unfavorable_simulation(self):
  d,x=context();c=candidate()
  c["evaluateurs"][0]["scores"]=[2,2,2,2,2]
  c["orientation_proposee"]="COMPETENCES_A_REVOIR"
  d["simulation"]["simulations_candidatures"]=[c]
  self.assertEqual(m.examen(x,d["simulation"])["candidatures_avec_appreciation_favorable_simulee"],0)
 def test_27_source_proof_unknown(self):
  self.reject_candidate(lambda c:c.update(preuve_id="F99"))
 def test_28_invalid_hash(self):
  self.reject_candidate(lambda c:c.update(document_sha256="nohash"))
 def test_29_candidate_personal_data_refused(self):
  self.reject_candidate(lambda c:c.update(email="person@invalid.example"))
 def test_30_evaluator_personal_data_refused(self):
  self.reject_candidate(lambda c:c["evaluateurs"][0].update(adresse="quelque part"))
 def test_31_duplicate_candidate_ref(self):
  d,x=context();c=candidate();d["simulation"]["simulations_candidatures"]=[c,c]
  with self.assertRaises(ValueError):m.examen(x,d["simulation"])
 def test_32_valid_objection_simulated(self):
  d,x=context();d["simulation"]["simulations_observations"]=[observation()]
  self.assertEqual(m.examen(x,d["simulation"])["observations_simulees"],1)
 def test_33_observation_without_pii(self):
  d,x=context();d["simulation"]["simulations_observations"]=[observation()]
  self.assertEqual(m.examen(x,d["simulation"])["contributions_reelles"],0)
 def test_34_observation_pii_rejected(self):
  self.reject_observation(lambda c:c.update(contenant_donnees_personnelles=True))
 def test_35_observation_extra_free_text_rejected(self):
  self.reject_observation(lambda c:c.update(texte_libre="je suis une personne"))
 def test_36_observation_wrong_regime(self):
  self.reject_observation(lambda c:c.update(regime="QUEBEC_SOUVERAIN"))
 def test_37_observation_wrong_proof(self):
  self.reject_observation(lambda c:c.update(preuve_id="FXX"))
 def test_38_observation_wrong_channel(self):
  self.reject_observation(lambda c:c.update(canal="PRIVE_EMAIL"))
 def test_39_observation_wrong_type(self):
  self.reject_observation(lambda c:c.update(type_observation="PROPAGANDE"))
 def test_40_observation_without_reply_hash_cannot_reply(self):
  self.reject_observation(lambda c:c.update(statut_reponse="REPONSE_DECLAREE"))
 def test_41_observation_no_reply_cannot_have_hash(self):
  self.reject_observation(lambda c:c.update(empreinte_reponse="a"*64))
 def test_42_valid_declared_reply_does_not_authorize(self):
  d,x=context();o=observation();o.update(statut_reponse="REPONSE_DECLAREE",empreinte_reponse="c"*64)
  d["simulation"]["simulations_observations"]=[o]
  self.assertFalse(m.examen(x,d["simulation"])["autorisation_consultation"])
 def test_43_duplicate_observation_rejected(self):
  d,x=context();o=observation();d["simulation"]["simulations_observations"]=[o,o]
  with self.assertRaises(ValueError):m.examen(x,d["simulation"])
 def test_44_fake_contract_rejected(self):
  self.reject_policy(lambda d:d["mandats"]["processus_mandat"].update(contrats_signes=1))
 def test_45_fake_budget_rejected(self):
  self.reject_policy(lambda d:d["mandats"]["processus_mandat"].update(budget_autorise=True))
 def test_46_fake_cost_rejected(self):
  self.reject_policy(lambda d:d["mandats"]["mandats"][8].update(cout_reel="1000"))
 def test_47_fake_publication_rejected(self):
  self.reject_policy(lambda d:d["mandats"]["controles_transversaux"].update(publication_programmatique_autorisee=True))
 def test_48_fake_consultation_open_rejected(self):
  self.reject_policy(lambda d:d["mandats"]["consultation_citoyenne"].update(ouverture_autorisee=True))
 def test_49_fake_p52a_proof_rejected(self):
  self.reject_policy(lambda d:d["p52a"]["required_evidence"][8].update(statut="VALIDE"))
 def test_50_fake_p52m_appointment_rejected(self):
  self.reject_policy(lambda d:d["p52m"]["etat_reel"].update(membres_nommes=1))
 def test_51_fake_p52l_attestation_rejected(self):
  self.reject_policy(lambda d:d["p52l"]["politique_decision"].update(attestations_P52A_obtenues=1))
 def test_52_output_no_identifiers(self):
  d,x=context();d["simulation"]["simulations_candidatures"]=[candidate()]
  d["simulation"]["simulations_observations"]=[observation()]
  report=json.dumps(m.examen(x,d["simulation"]))
  for secret in ("SIM-ABC001","EV-001","OBS-0001","a"*64,"b"*64,"https://"):
   self.assertNotIn(secret,report)
 def test_53_cli_pass_but_no_go(self):
  with tempfile.TemporaryDirectory() as temp:
   f=Path(temp)/"rapport.json"
   self.assertEqual(m.main(["--rapport",str(f)]),0)
   self.assertEqual(json.loads(f.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_54_cli_strict_exit_three(self):
  with tempfile.TemporaryDirectory() as temp:
   self.assertEqual(m.main(["--exiger-autorisations","--rapport",str(Path(temp)/"refus.json")]),3)
 def test_55_cli_missing_data_exit_two(self):
  with tempfile.TemporaryDirectory() as temp:
   self.assertEqual(m.main(["--mandats",str(Path(temp)/"missing.json")]),2)
 def test_56_cli_never_overwrites(self):
  with tempfile.TemporaryDirectory() as temp:
   target=Path(temp)/"rapport.json"
   self.assertEqual(m.main(["--rapport",str(target)]),0)
   self.assertEqual(m.main(["--rapport",str(target)]),2)

 def test_57_selection_methode_reste_non_contractuelle(self):
  d,x=context()
  self.assertTrue(d["mandats"]["principes_selection"]["methode_proposee_pas_regle_contractuelle"])
if __name__=="__main__":
 unittest.main()
