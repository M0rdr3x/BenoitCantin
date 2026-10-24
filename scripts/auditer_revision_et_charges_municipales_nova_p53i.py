#!/usr/bin/env python3
"""P53I: verify two MAMH 2024 versions, one additional municipality, and payer charges."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "p53i":D/"P53I_SOURCES_REVISION_ET_CHARGES_2024.json",
 "p53e":D/"P53E_PREUVES_HISTORIQUES_MUNICIPALES.json",
 "p53g":D/"P53G_COUVERTURE_1343_ORGANISMES_2024.json",
 "p53h":D/"P53H_PRIORITES_VERIFICATION_2024.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
OLD_LOCAL=D/"sources"/"P53E_MAMH_2024_MUNICIPALITES_LOCALES_SELECTION.csv"
OLD_OTHER=D/"sources"/"P53G_MAMH_2024_249_ORGANISMES_COMPLEMENTAIRES.csv"
NEW=D/"sources"/"P53I_MAMH_2024_1344_RECETTES_CHARGES_SELECTION.csv"
DESC=D/"sources"/"P53I_MAMH_2024_DICTIONNAIRE_CHARGES.json"
SOURCE_SHA="fa310f380e295ae359a2aafe83beb1dd45cd4888571e133398ad51f4b7db8c43"
OLD_SOURCE_SHA="151c0a2b1fc0dfac8c8cc3dba04b74f5c49fbb98fdfd78251925959d1ad35fff"
OLD_LOCAL_SHA="11f940092a6a7eb54bf7dc39c6e5b4b44e73c82e9bb34ce7aae2e7278269aa5e"
OLD_OTHER_SHA="65e3bb97fd9a8bb3bfb16eef77f35036e60cb53a0796cdd491894ad7267db9b0"
NEW_SHA="cef644e3f16ebea6bc727b009037638fa70443fe66fbeb55e4ac1e3cb1071213"
DESC_SHA="5ed56370bc00cd4752d3982958236093d1803e60331251afb76a24f87856ab10"
FULL_DICT_SHA="23cd037a93d0ea7a8acd21a768838df8b6cd6a88d827778be68ee82f5186f542"
CODES=["CRIIX00681","CRIIX00682","CRIIX00683","CRIIX00685","CRIIX00686"]
OLD_COLUMNS=["cod_geo","nom_organisme","type_org","CRIIX00016","CRIIX00018"]+[
 f"CRIIX{k:05d}" for k in range(405,418)]
NEW_COLUMNS=OLD_COLUMNS+CODES
EXPENSE={
 "CRIIX00681":("2526339827",1098,246,0,4,1094),
 "CRIIX00682":("53587714",77,1267,0,2,75),
 "CRIIX00683":("254824938",334,1010,1,4,329),
 "CRIIX00685":("386907793",213,1131,1,3,209),
 "CRIIX00686":("816798326",626,718,1,3,622),
}
GUARDS=[
 "versions_anciennes_maintenues_sans_recriture",
 "nouvelle_archive_derivee_non_equivalente_original_integral",
 "annee_financiere_2024_pas_budget_2026_2027",
 "nouvel_organisme_ne_prouve_pas_hausse_economique_2024",
 "identite_codes_ne_prouve_pas_identite_transactionnelle",
 "montants_recus_ne_sont_pas_eliminations",
 "montants_depenses_ne_sont_pas_eliminations",
 "difference_621869270_n_est_pas_economie",
 "champs_vides_distincts_de_zero",
 "charges_negatives_preservees",
 "pas_de_double_cumul_niveaux_de_gouvernement",
 "pas_de_taux_fiscal_Nova_inferé",
 "pas_de_preuve_F01_F20_auto_validée",
]
NO_GO="NO_GO_AUTOMATIQUE"

def must(check,reason):
 if not check:raise ValueError(reason)

def load_json(path):
 p=Path(path)
 must(p.is_file() and not p.is_symlink() and
      0<p.stat().st_size<700000,"JSON_NON_LISIBLE")
 value=json.loads(p.read_text(encoding="utf-8"))
 must(type(value) is dict,"JSON_NON_OBJET")
 return value

def read_csv(path,sha,count,columns):
 p=Path(path)
 must(p.is_file() and not p.is_symlink() and
      100<p.stat().st_size<500000,"CSV_NON_LISIBLE")
 data=p.read_bytes()
 must(hashlib.sha256(data).hexdigest()==sha,"CSV_EMPREINTE_DIFFERENTE")
 rows=list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
 must(len(rows)==count and list(rows[0])==columns and
      all(list(r)==columns and r.get(None) is None for r in rows),
      "CSV_NOMBRE_LIGNES_OU_COLONNES_ERRONE")
 must(len({r["cod_geo"] for r in rows})==count,"CODES_ORGANISMES_DUPLIQUES")
 return rows

def get_sources(local_path=OLD_LOCAL,other_path=OLD_OTHER,new_path=NEW,desc_path=DESC):
 local=read_csv(local_path,OLD_LOCAL_SHA,1094,OLD_COLUMNS)
 other=read_csv(other_path,OLD_OTHER_SHA,249,OLD_COLUMNS)
 newest=read_csv(new_path,NEW_SHA,1344,NEW_COLUMNS)
 old=local+other
 must(len({r["cod_geo"] for r in old})==1343,
      "ANCIENS_COMPTES_SE_CHEVAUCHENT")
 p=Path(desc_path)
 must(p.is_file() and not p.is_symlink() and
      p.stat().st_size==1634,"DICTIONNAIRE_NON_LISIBLE")
 raw=p.read_bytes()
 must(hashlib.sha256(raw).hexdigest()==DESC_SHA,"DICTIONNAIRE_EMPREINTE_DIFFERENTE")
 desc=json.loads(raw.decode("utf-8"))
 must(type(desc) is list and len(desc)==5 and
      [r.get("Code de postes") for r in desc]==CODES,"CINQ_POSTES_DEPENSES_NON_VERIFIES")
 for i,r in enumerate(desc):
  must(r.get("Sous-section")=="S19" and
       r.get("Sujet","").startswith("Charges par objets - Contributions à des organismes - ") and
       "Exercice en cours - Réalisations - Intégral - Intégral"==
       r.get("Facettes (exercice - type de données - consolidation - compétences - spécifique)"),
       "DICTIONNAIRE_EXERCICE_OU_NATURE_INCORRECTS")
 return old,newest,desc

def integers(rows,key):
 result=[]
 for r in rows:
  v=r[key]
  must(v=="" or (v.lstrip("-").isdigit() and
       not v.startswith("+")),"MONTANT_NON_ENTIER")
  result.append(None if v=="" else int(v))
 return result

def compare(old,newest):
 old_codes={r["cod_geo"]:r for r in old}
 new_codes={r["cod_geo"]:r for r in newest}
 must(len(old_codes)==1343 and len(new_codes)==1344,
      "VERSION_COMPTE_INCORRECT")
 added=sorted(new_codes.keys()-old_codes.keys())
 removed=sorted(old_codes.keys()-new_codes.keys())
 must(added==["39135"] and not removed,"AJOUT_OU_SUPPRESSION_INEXPLIQUES")
 changes=[]
 for code,r in old_codes.items():
  if any(r[k]!=new_codes[code][k] for k in OLD_COLUMNS):
   changes.append(code)
 must(not changes,"REVISION_LIGNE_PREEXISTANTE_NON_ANALYSEE")
 n=new_codes["39135"]
 must(n["nom_organisme"]=="Saint-Valère" and
      n["type_org"]=="Municipalité locale" and
      n["CRIIX00405"]=="2951221" and
      n["CRIIX00406"]=="2276820" and
      n["CRIIX00016"]=="2069797" and
      n["CRIIX00409"]=="503955" and
      n["CRIIX00408"]=="0" and
      n["CRIIX00681"]=="165346" and
      n["CRIIX00686"]=="13976",
      "NOUVEL_ORGANISME_NON_RECONCILIE")
 must(sum(r["type_org"]=="Municipalité locale" for r in newest)==1095,
      "LOCALITES_NOUVELLE_VERSION_INATTENDUES")
 must(sum(r["type_org"]!="Municipalité locale" for r in newest)==249,
      "AUTRES_ORGANISMES_MODIFIES")
 for r in newest:
  parent=int(r["CRIIX00405"])
  components=sum(int(r[k] or "0") for k in OLD_COLUMNS[6:18])
  must(parent==components,"12_CATEGORIES_RECETTES_NON_RECONCILIEES")
 return n

def calculate(newest):
 stats={}
 for key,expected in EXPENSE.items():
  values=integers(newest,key)
  actual=(str(sum(v for v in values if v is not None)),
          sum(v is not None for v in values),
          sum(v is None for v in values),
          sum(v is not None and v<0 for v in values),
          sum(v==0 for v in values),
          sum(v is not None and v>0 for v in values))
  must(actual==expected,"DEPENSES_VALEURS_OU_BLANC_MODIFIES")
  stats[key]=dict(zip(
   ("montant_signe_cad","observations","blancs","negatifs","zeros","positifs"),actual))
 totals={
 "total_revenus_tous_organismes_cad":sum(v for v in integers(newest,"CRIIX00405") if v is not None),
 "taxes_tous_organismes_cad":sum(v for v in integers(newest,"CRIIX00406") if v is not None),
 "quotes_parts_recues_tous_organismes_cad":sum(v for v in integers(newest,"CRIIX00408") if v is not None),
 "transferts_recus_tous_organismes_cad":sum(v for v in integers(newest,"CRIIX00409") if v is not None),
 "foncier_local_2024_cad":sum(
  int(r["CRIIX00016"] or "0") for r in newest
  if r["type_org"]=="Municipalité locale")
 }
 totals["quotes_plus_transferts_recus_somme_signee_cad"]=(
   totals["quotes_parts_recues_tous_organismes_cad"]+
   totals["transferts_recus_tous_organismes_cad"])
 must(totals=={
  "total_revenus_tous_organismes_cad":41666627807,
  "taxes_tous_organismes_cad":17339561033,
  "quotes_parts_recues_tous_organismes_cad":3148209097,
  "transferts_recus_tous_organismes_cad":7716577059,
  "foncier_local_2024_cad":15087601369,
  "quotes_plus_transferts_recus_somme_signee_cad":10864786156
 },"RECETTES_REVISION_NON_RECONCILIEES")
 return stats,totals

def audit(docs,old,newest,desc):
 must(type(docs) is dict and set(docs)==set(FILES),"REGISTRES_REFERENCE_MANQUANTS")
 m,e,g,h,a=(docs[k] for k in FILES)
 must(m.get("schema_version")=="P53I-1" and m.get("jalon")=="P53I" and
      m.get("date_reference")=="2026-10-22" and
      m.get("statut")=="REVISION_SOURCE_OFFICIELLE_2024_ET_CHARGES_RECIPROQUES_NON_APPARIEES",
      "P53I_STATUS_INVALIDE")
 must(m.get("references")=={
  k:str(FILES[k].relative_to(ROOT)) for k in FILES if k!="p53i"},
  "LIENS_SOURCES_MODIFIES")
 provenance=m.get("historique_provenance",{})
 must(provenance.get("ancienne_source_2026_10_21_sha256")==OLD_SOURCE_SHA and
      provenance.get("nouvelle_source_2026_10_22_sha256")==SOURCE_SHA and
      provenance.get("nouvelle_source_2026_10_22_octets")==20268526 and
      provenance.get("ancienne_source_2026_10_21_octets")==20254172 and
      provenance.get("dictionnaire_officiel_sha256")==FULL_DICT_SHA and
      provenance.get("dictionnaire_officiel_octets")==1749357 and
      provenance.get("originaux_complets_archives_dans_git") is False and
      provenance.get("avis_comptable_independant_signé_obtenu") is False,
      "PROVENANCE_ORIGINALS_FAUSSE")
 archives=m.get("archives_derivées",{})
 must(archives=={
  "ancienne_selection_locale":str(OLD_LOCAL.relative_to(ROOT)),
  "ancienne_selection_complementaire":str(OLD_OTHER.relative_to(ROOT)),
  "nouvelle_selection":str(NEW.relative_to(ROOT)),
  "nouvelle_selection_sha256":NEW_SHA,
  "nouvelle_selection_octets":188879,
  "nouvelle_selection_git_blob":"bb09a7d5f27e8915fd2d12edba89c2a0ac83cabd",
  "dictionnaire_5_charges":str(DESC.relative_to(ROOT)),
  "dictionnaire_5_charges_sha256":DESC_SHA,
  "dictionnaire_5_charges_octets":1634,
  "dictionnaire_5_charges_git_blob":"d07c6866861a7c95d65d1ad59820b17589d8a990",
 },"SHA_DES_EXTRAITS_INCOHERENTS")
 must(e.get("schema_version")=="P53E-1" and
      e.get("sources",{}).get("donnees",{}).get("sha256_derive")==OLD_LOCAL_SHA and
      e.get("bilan",{}).get("decision")==NO_GO,
      "HISTORIQUE_P53E_MODIFIE")
 must(g.get("schema_version")=="P53G-1" and
      g.get("provenance",{}).get("selection_complementaire_sha256")==OLD_OTHER_SHA and
      g.get("totaux_bruts_cad",{}).get("revenus")=="41663676586" and
      g.get("bilan",{}).get("decision")==NO_GO,
      "P53G_ANCIENNE_VERSION_MODIFIEE")
 must(h.get("schema_version")=="P53H-1" and
      h.get("bilan",{}).get("lignes_analysees")==1343 and
      h.get("bilan",{}).get("decision")==NO_GO,
      "P53H_PRIORITES_NON_VERSIONNEES")
 must(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
      a.get("automatic_go") is False and
      a.get("financial_model_certified") is False and
      len(a.get("required_evidence",[]))==20 and
      all(r.get("statut")=="NON_VALIDE" for r in a["required_evidence"]),
      "F01_F20_PSEUDO_VALIDES")
 newrec=compare(old,newest)
 drift=m.get("variation_et_population",{})
 must(drift.get("ancien_nombre_organismes")==1343 and
      drift.get("nouveau_nombre_organismes")==1344 and
      drift.get("anciens_codes_absents_de_nouvelle_source")==0 and
      drift.get("anciens_codes_avec_revision_sur_18_colonnes")==0 and
      drift.get("nouveaux_codes")==["39135"] and
      drift.get("nouvelle_municipalite")=="Saint-Valère" and
      drift.get("nombre_local_ancien")==1094 and
      drift.get("nombre_local_nouveau")==1095 and
      drift.get("nombre_complementaire_inchange")==249 and
      drift.get("différences_de_recettes_attribuables_a_nouvelle_ligne_seulement") is True and
      drift.get("exhaustivite_revision_autres_colonnes_non_extraite") is True,
      "DRIFT_SOURCE_PSEUDO_VALIDÉ")
 n=m.get("nouvelle_ligne_municipale",{})
 must(n=={
  "code":"39135","nom":"Saint-Valère","type":"Municipalité locale",
  "revenus_totaux_cad":"2951221","taxes_cad":"2276820",
  "foncier_inclus_cad":"2069797","transferts_cad":"503955",
  "quotes_parts_cad":"0","charges_quotes_parts_payees_cad":"165346",
  "autres_contributions_aux_autres_organismes_cad":"13976"},
  "SAINT_VALERE_CHIFFRES_INEXACTS")
 stats,totals=calculate(newest)
 recorded=m.get("charges_reelles_comptables")
 must(type(recorded) is list and
      [r.get("code") for r in recorded]==CODES,
      "POSTES_CHARGES_5_REQUIS")
 for r in recorded:
  key=r["code"]
  must(all(r.get(k)==v for k,v in stats[key].items()) and
       r.get("contrepartie_payee_identifiee") is False and
       r.get("montant_apparie_cad") is None,
       "CHARGES_DECLAREES_APPARIEES_SANS_PREUVE")
 tracked=m.get("totaux_recettes_2024_mis_a_jour",{})
 must(all(tracked.get(k)==str(v) for k,v in totals.items()) and
      tracked.get("montant_apparemment_double_compte_certifie_cad") is None and
      tracked.get("montant_net_apres_elimination_cad") is None and
      tracked.get("projection_budget_2026_2027_mcad") is None,
      "RECETTE_RECENTE_OU_CONSOLIDATION_FICTIVE")
 comparedata=m.get("confrontation_non_transactionnelle",{})
 must(comparedata=={
  "charges_quotes_parts_vers_organismes_municipaux_cad":"2526339827",
  "quotes_parts_recues_tous_organismes_cad":"3148209097",
  "ecart_receipts_moins_charges_cad":"621869270",
  "valeur_cote_payeur_et_cote_beneficiaire_potentiellement_superposes":False,
  "exactitude_appariement_transactionnel_etablie":False,
  "montant_eliminable_deduit_de_l_ecart_cad":None,
  "absence_de_doublon_demontree":False,
  "périmètres_de_consolidation_etats_internes_a_verifier":True,
 },"APPARIEMENT_OU_GAINS_INVENTES")
 guards=m.get("garde_fous")
 must(type(guards) is dict and set(guards)==set(GUARDS) and
      all(guards[k] is True for k in GUARDS),"GARDE_FOUS_VERSIONS_PERDUS")
 must(m.get("etat")=={
  "sources_officielles_retelechargees":2,
  "extracts_signes_et_SHA256_reproductibles":2,
  "revisions_anciens_organismes_sur_18_colonnes":0,
  "nouveaux_organismes":1,
  "organismes_comptables_couverts":1344,
  "postes_charges_officiels_recoupes":5,
  "appariements_transactionnels_confirmes":0,
  "eliminations_certifiees":0,
  "preuves_F01_F20_validees":0,
  "montants_Nova_inconnus":1320,
  "taux_Nova_adoptes":0,
  "publication_autorisee":False,
  "fusion_autorisee":False,
  "adoption_autorisee":False,
  "decision":NO_GO
 },"FAUSSE_COUVERTURE_CERTIFIEE")
 return {
  "jalon":"P53I","annee_comptable":2024,
  "ancienne_version_organismes":1343,
  "nouvelle_version_organismes":1344,
  "organisme_ajoute":"39135",
  "anciens_organismes_modifies_sur_18_champs":0,
  "revenus_bruts_nouvelle_version_cad":totals["total_revenus_tous_organismes_cad"],
  "taxes_municipales_brutes_cad":totals["taxes_tous_organismes_cad"],
  "quotes_parts_recues_cad":totals["quotes_parts_recues_tous_organismes_cad"],
  "charges_quotes_parts_organismes_municipaux_cad":int(stats["CRIIX00681"]["montant_signe_cad"]),
  "ecart_quotes_recues_moins_charges_cad":621869270,
  "appariements_transactionnels_confirmes":0,
  "eliminations_certifiees_cad":None,
  "preuves_F01_F20_non_validees":20,
  "parametres_Nova_inconnus":1320,
  "publication_autorisee":False,
  "fusion_autorisee":False,
  "adoption_autorisee":False,
  "decision":NO_GO
 }

def write_new(path,text):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(text)

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 for k,path in FILES.items():ap.add_argument("--"+k,type=Path,default=path)
 ap.add_argument("--ancien-local",type=Path,default=OLD_LOCAL)
 ap.add_argument("--ancien-complementaire",type=Path,default=OLD_OTHER)
 ap.add_argument("--nouveau",type=Path,default=NEW)
 ap.add_argument("--dictionnaire",type=Path,default=DESC)
 ap.add_argument("--rapport",type=Path)
 ap.add_argument("--exiger-appariements",action="store_true")
 args=ap.parse_args(argv)
 try:
  d={k:load_json(getattr(args,k)) for k in FILES}
  old,current,desc=get_sources(args.ancien_local,args.ancien_complementaire,
                               args.nouveau,args.dictionnaire)
  result=audit(d,old,current,desc)
  if args.rapport:write_new(args.rapport,json.dumps(result,ensure_ascii=False,indent=2)+"\n")
  else:print(json.dumps(result,ensure_ascii=False,indent=2))
  return 3 if args.exiger_appariements else 0
 except (OSError,ValueError,UnicodeError,KeyError,TypeError) as e:
  print(json.dumps({"jalon":"P53I","statut":"CONTROLE_REJETE",
    "type_erreur":type(e).__name__,
    "publication_autorisee":False,"fusion_autorisee":False,
    "adoption_autorisee":False,"decision":NO_GO},ensure_ascii=False))
  return 2

if __name__=="__main__":
 sys.exit(main())
