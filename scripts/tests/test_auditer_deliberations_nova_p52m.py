"""Projet Nova P52M : contre-tests des simulations de deliberation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
S=ROOT/"scripts"/"auditer_deliberations_nova_p52m.py"
spec=importlib.util.spec_from_file_location("p52m",S)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixtures():
 d={k:m.load(v) for k,v in m.FILES.items()}
 return d,m.auditer_regles(d)

def person(seat,n,vote="POUR",conflit=False,recuse=False,ind=True):
 return {"siege":seat,"acteur_ref":"A-VOT"+str(n).zfill(3),
         "independance_declaree":ind,"conflit_signale":conflit,
         "recuse":recuse,"vote":vote}

def mock(pid="F09"):
 pilot=next(k for k,vs in m.COMITES.items() if pid in vs)
 return {"id":"SIM-0001","preuve_id":pid,"comite_id":pilot,"regime":"TOUS" if pid=="F09" else "QUEBEC_DANS_CANADA",
         "date_utc":"2026-10-19T19:00:00Z","document_sha256":"a"*64,
         "deposant_ref":"A-DEP000",
         "participants":[person(role,i) for i,role in enumerate(m.SIEGES,1)],
         "reserves":[],
         "avis_croises":[{"comite_id":c,"orientation":"FAVORABLE","empreinte_avis":"b"*64}
                       for c in m.CROISES[pid]],
         "orientation_declaree":"FAVORABLE"}

class EtudesP52M(unittest.TestCase):
 def fail_sim(self,edit):
  d,x=fixtures();s=mock();edit(s);d["seances"]["simulations"]=[s]
  with self.assertRaises(ValueError):m.verifier_seances(x,d["seances"])
 def fail_reg(self,edit):
  d,x=fixtures();edit(d)
  with self.assertRaises(ValueError):m.auditer_regles(d)
 def test_01_cinq_comites(self):
  d,x=fixtures();self.assertEqual(len(d["politique"]["comites"]),5)
 def test_02_vingt_preuves(self):
  d,x=fixtures();self.assertEqual(len(x),20)
 def test_03_absence_experts_reels(self):
  d,x=fixtures();self.assertEqual(d["politique"]["etat_reel"]["membres_nommes"],0)
 def test_04_critere_f09_critique(self):
  d,x=fixtures();self.assertEqual(x["F09"]["score_indicatif"],11)
 def test_05_f20_avis_croises(self):
  d,x=fixtures();self.assertEqual(x["F20"]["comites_consultes"],["CJF","CDE"])
 def test_06_toutes_bloquantes(self):
  d,x=fixtures();self.assertTrue(all(z["priorite_p52a"]=="BLOQUANT" for z in x.values()))
 def test_07_vide_no_go(self):
  d,x=fixtures();r=m.verifier_seances(x,d["seances"])
  self.assertEqual(r["simulations_examinees"],0)
  self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
 def test_08_favorable_simule_pas_go(self):
  d,x=fixtures();d["seances"]["simulations"]=[mock()]
  r=m.verifier_seances(x,d["seances"])
  self.assertEqual(r["orientations_non_authentifiees"]["FAVORABLE"],1)
  self.assertFalse(r["adoption_autorisee"])
 def test_09_favorable_eleve_3_oui(self):
  d,x=fixtures();s=mock("F03");s["participants"][3]["vote"]="CONTRE";s["participants"][4]["vote"]="ABSTENTION"
  d["seances"]["simulations"]=[s]
  self.assertEqual(m.verifier_seances(x,d["seances"])["orientations_non_authentifiees"]["FAVORABLE"],1)
 def test_10_critique_3_oui_insuffisant(self):
  self.fail_sim(lambda s: [s["participants"][k].update(vote="CONTRE") for k in (3,4)])
 def test_11_double_votant(self):
  self.fail_sim(lambda s:s["participants"][1].update(acteur_ref="A-VOT001"))
 def test_12_double_siege(self):
  self.fail_sim(lambda s:s["participants"][1].update(siege="PRESIDENCE"))
 def test_13_deposant_votant(self):
  self.fail_sim(lambda s:s["participants"][2].update(acteur_ref="A-DEP000"))
 def test_14_conflit_exige_recusation(self):
  self.fail_sim(lambda s:s["participants"][2].update(conflit_signale=True))
 def test_15_recuse_pas_de_vote(self):
  self.fail_sim(lambda s:s["participants"][2].update(recuse=True))
 def test_16_non_independant_recuse(self):
  self.fail_sim(lambda s:s["participants"][2].update(independance_declaree=False))
 def test_17_quorum_apres_recusations(self):
  self.fail_sim(lambda s:[s["participants"][k].update(conflit_signale=True,recuse=True,vote="NON_PARTICIPANT") for k in (2,3,4)])
 def test_18_presidence_recusee(self):
  self.fail_sim(lambda s:s["participants"][0].update(conflit_signale=True,recuse=True,vote="NON_PARTICIPANT"))
 def test_19_rapporteur_recuse(self):
  self.fail_sim(lambda s:s["participants"][1].update(conflit_signale=True,recuse=True,vote="NON_PARTICIPANT"))
 def test_20_reserve_bloquante_ouverte(self):
  self.fail_sim(lambda s:s["reserves"].append({"id":"R-0001","gravite":"BLOQUANTE",
      "etat":"OUVERTE","empreinte_piece":"c"*64,"empreinte_resolution":None}))
 def test_21_reserve_majeure_ouverte(self):
  self.fail_sim(lambda s:s["reserves"].append({"id":"R-0001","gravite":"MAJEURE",
      "etat":"OUVERTE","empreinte_piece":"c"*64,"empreinte_resolution":None}))
 def test_22_reserve_mineure_ouverte_comptee(self):
  d,x=fixtures();s=mock()
  s["reserves"]=[{"id":"R-0001","gravite":"MINEURE","etat":"OUVERTE",
                  "empreinte_piece":"c"*64,"empreinte_resolution":None}]
  d["seances"]["simulations"]=[s]
  self.assertEqual(m.verifier_seances(x,d["seances"])["reserves_ouvertes_fictives"],1)
 def test_23_reserve_resolution_sans_piece(self):
  self.fail_sim(lambda s:s["reserves"].append({"id":"R-0001","gravite":"MAJEURE",
      "etat":"RESOLUTION_DECLAREE","empreinte_piece":"c"*64,"empreinte_resolution":None}))
 def test_24_double_reserve(self):
  self.fail_sim(lambda s:s["reserves"].extend([{"id":"R-0001","gravite":"MINEURE",
      "etat":"OUVERTE","empreinte_piece":"c"*64,"empreinte_resolution":None}]*2))
 def test_25_avis_croise_manquant(self):
  self.fail_sim(lambda s:s["avis_croises"].clear())
 def test_26_avis_croise_defavorable(self):
  self.fail_sim(lambda s:s["avis_croises"][0].update(orientation="DEFAVORABLE"))
 def test_27_avis_croise_inconnu(self):
  self.fail_sim(lambda s:s["avis_croises"][0].update(comite_id="CTE"))
 def test_28_double_avis_croise(self):
  self.fail_sim(lambda s:s["avis_croises"].append(s["avis_croises"][0]))
 def test_29_faux_sha_document(self):
  self.fail_sim(lambda s:s.update(document_sha256="abc"))
 def test_30_faux_sha_reserve(self):
  self.fail_sim(lambda s:s["reserves"].append({"id":"R-0001","gravite":"MINEURE",
      "etat":"OUVERTE","empreinte_piece":"x","empreinte_resolution":None}))
 def test_31_faux_regime(self):
  self.fail_sim(lambda s:s.update(regime="QUEBEC_SOUVERAIN"))
 def test_32_faux_comite(self):
  self.fail_sim(lambda s:s.update(comite_id="CJF"))
 def test_33_faux_heure(self):
  self.fail_sim(lambda s:s.update(date_utc="2026-10-19T25:00:00Z"))
 def test_34_faux_votant(self):
  self.fail_sim(lambda s:s["participants"][0].update(vote="POUR_ET_CONTRE"))
 def test_35_champs_personnels_refuses(self):
  self.fail_sim(lambda s:s["participants"][0].update(email="prive@example.test"))
 def test_36_id_inconnu(self):
  self.fail_sim(lambda s:s.update(preuve_id="F99"))
 def test_37_id_seance_double(self):
  d,x=fixtures();s=mock();d["seances"]["simulations"]=[s,s]
  with self.assertRaises(ValueError):m.verifier_seances(x,d["seances"])
 def test_38_chronologie_erronee(self):
  d,x=fixtures();s=mock();n=mock();n["id"]="SIM-0002";n["date_utc"]="2026-10-19T18:00:00Z"
  d["seances"]["simulations"]=[s,n]
  with self.assertRaises(ValueError):m.verifier_seances(x,d["seances"])
 def test_39_defavorable_simule_pas_go(self):
  d,x=fixtures();s=mock()
  for p in s["participants"]:p["vote"]="CONTRE"
  s["orientation_declaree"]="DEFAVORABLE"
  d["seances"]["simulations"]=[s]
  self.assertFalse(m.verifier_seances(x,d["seances"])["publication_autorisee"])
 def test_40_ajournement_possible(self):
  d,x=fixtures();s=mock();s["orientation_declaree"]="AJOURNER"
  d["seances"]["simulations"]=[s]
  self.assertEqual(m.verifier_seances(x,d["seances"])["orientations_non_authentifiees"]["AJOURNER"],1)
 def test_41_comite_faussement_constitue(self):
  self.fail_reg(lambda d:d["politique"]["etat_reel"].update(comites_constitues=1))
 def test_42_faux_mandat(self):
  self.fail_reg(lambda d:d["politique"]["etat_reel"].update(mandats_signes=True))
 def test_43_risque_falsifie(self):
  self.fail_reg(lambda d:d["politique"]["cartographie"][8].update(score_indicatif=5))
 def test_44_avis_obligatoire_efface(self):
  self.fail_reg(lambda d:d["politique"]["cartographie"][19].update(comites_consultes=[]))
 def test_45_P52A_go_interdit(self):
  self.fail_reg(lambda d:d["p52a"].update(automatic_go=True))
 def test_46_P52L_avis_fictif(self):
  self.fail_reg(lambda d:d["p52l"]["exigences"][8].update(etape_canonique="AVIS_INDEPENDANT_DECLARE"))
 def test_47_P52K_hash_fictif(self):
  self.fail_reg(lambda d:d["p52k"]["fichiers_source"][0].update(empreinte_sha256_pdf_original="e"*64))
 def test_48_avis_reels_fictifs(self):
  self.fail_reg(lambda d:d["politique"]["etat_reel"].update(avis_authentifies=1))
 def test_49_journal_authentifie_fictivement(self):
  self.fail_reg(lambda d:d["seances"].update(avis_externes_authentifies=True))
 def test_50_aucun_identifiant_dans_rapport(self):
  d,x=fixtures();d["seances"]["simulations"]=[mock()]
  report=json.dumps(m.verifier_seances(x,d["seances"]))
  for secret in ("A-VOT001","A-DEP000","a"*64,"https://"):
   self.assertNotIn(secret,report)
 def test_51_cli_normale_pas_go(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"report.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(json.loads(p.read_text())["decision"],"NO_GO_AUTOMATIQUE")
 def test_52_cli_approbation_refusee(self):
  with tempfile.TemporaryDirectory() as tmp:
   self.assertEqual(m.main(["--exiger-adoption","--rapport",str(Path(tmp)/"r.json")]),3)
 def test_53_cli_entree_absente(self):
  with tempfile.TemporaryDirectory() as tmp:
   self.assertEqual(m.main(["--politique",str(Path(tmp)/"absent")]),2)
 def test_54_rapport_non_ecrase(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"r.json"
   self.assertEqual(m.main(["--rapport",str(p)]),0)
   self.assertEqual(m.main(["--rapport",str(p)]),2)
if __name__=="__main__":
 unittest.main()
