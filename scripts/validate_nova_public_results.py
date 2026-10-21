#!/usr/bin/env python3
"""Nova: le public ne voit jamais de votes individuels ou petites cellules."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
REL="projets/projet-nova/data/resultats-sondages-publics-v1.json"
SURVEYS={"nova-orientations-40-v1":(40,("pour","contre","sans_opinion")),
         "nova-consultation-64-v1":(64,("-3","-2","-1","0","1","2","3","skip"))}
FORBIDDEN=("person","user","email","ip_address","ipaddress","address","hash",
           "account","identity","identit","token","session","device","individual",
           "respondent_id","participant_id","ballot","raw_vote","demograph")

def validate(obj, review=False):
    bad=[]
    if not isinstance(obj,dict):return ["Snapshot non objet"]
    def sensitive(value):
        if isinstance(value,dict):
            return any(any(w in k.lower() for w in FORBIDDEN) or sensitive(v)
                       for k,v in value.items())
        if isinstance(value,list):return any(sensitive(v) for v in value)
        return False
    if sensitive(obj):bad.append("Renseignements individuels interdits")
    if obj.get("schema")!="nova-public-results-v1":bad.append("Version de snapshot inconnue")
    if obj.get("rules")!={"minimumParticipants":30,"minimumNonzeroCell":10,"suppression":"entire-question"}:
        bad.append("Seuils de confidentialité erronés")
    if obj.get("publicationStatus") not in ("not_open","approved_aggregate"):
        bad.append("Statut de publication incorrect")
    if not review and (obj.get("publicationStatus")!="not_open" or
                       obj.get("publicationApproved") is not False or
                       obj.get("privacyReviewApproved") is not False or
                       obj.get("publishedOn") is not None):
        bad.append("Les données réelles ne sont pas autorisées (#675)")
    surveys=obj.get("surveys")
    if not isinstance(surveys,dict) or set(surveys)!=set(SURVEYS):
        return bad+["Inventaire des deux sondages divergent"]
    for sid,(length,choices) in SURVEYS.items():
        entry=surveys[sid]
        if not isinstance(entry,dict) or entry.get("questionCount")!=length:
            bad.append("Questionnaire divergent : "+sid);continue
        status=entry.get("status")
        rows=entry.get("questions")
        if status=="not_open":
            if entry.get("respondents") is not None or rows!=[]:
                bad.append("Chiffres présents sur consultation fermée")
        elif status=="approved_aggregate":
            if (obj.get("publicationStatus")!="approved_aggregate" or
                obj.get("publicationApproved") is not True or
                obj.get("privacyReviewApproved") is not True):
                bad.append("Publication non approuvée");continue
            n=entry.get("respondents")
            if type(n)!=int or n<30 or not isinstance(rows,list) or len(rows)!=length:
                bad.append("Échantillon public insuffisant");continue
            for index,row in enumerate(rows):
                if (not isinstance(row,dict) or set(row)!={"id","total","counts"} or
                    row.get("id")!="q"+str(index+1).zfill(2) or row.get("total")!=n or
                    not isinstance(row.get("counts"),dict) or set(row["counts"])!=set(choices)):
                    bad.append("Comptes erronés q"+str(index+1));continue
                values=list(row["counts"].values())
                if (not all(type(v)==int and (v==0 or v>=10) for v in values)
                    or sum(values)!=n):
                    bad.append("Petite cellule ou total incohérent")
        else:bad.append("Statut inconnu pour "+sid)
    return bad

def check(root,built=None):
    target=root/REL
    if not target.is_file() or target.is_symlink():return ["Snapshot absent ou symbolique"]
    try:data=json.loads(target.read_text("utf-8"))
    except (OSError,ValueError,UnicodeError):return ["Snapshot illisible"]
    bad=validate(data)
    if built is not None:
        dest=built/REL
        if not dest.is_file() or dest.is_symlink():bad.append("Snapshot absent du build")
        elif dest.read_bytes()!=target.read_bytes():bad.append("Snapshot altéré dans Jekyll")
    return bad

def self_test():
    source=json.loads((ROOT/REL).read_text("utf-8"))
    assert not validate(source)
    sample=json.loads(json.dumps(source))
    sample["person_id"]="fictif"
    assert validate(sample)
    sample=json.loads(json.dumps(source))
    sample["surveys"]["nova-orientations-40-v1"]["respondents"]=1
    assert validate(sample)
    sample=json.loads(json.dumps(source))
    sample.update(publicationStatus="approved_aggregate",publicationApproved=True,
                  privacyReviewApproved=True,publishedOn="2026-10-21")
    a=sample["surveys"]["nova-orientations-40-v1"]
    a.update(status="approved_aggregate",respondents=30,questions=[
      {"id":"q"+str(i+1).zfill(2),"total":30,
       "counts":{"pour":20,"contre":10,"sans_opinion":0}} for i in range(40)])
    assert validate(sample), "Ne jamais approuver une publication réelle en CI"
    assert not validate(sample,review=True), "Agrégation synthétique valide refusée"
    a["questions"][0]["counts"]={"pour":24,"contre":6,"sans_opinion":0}
    assert validate(sample,review=True), "Petite cellule publiée"
    with TemporaryDirectory() as name:
        out=Path(name)/REL;out.parent.mkdir(parents=True)
        out.write_bytes((ROOT/REL).read_bytes())
        assert not check(ROOT,Path(name))
        out.write_text("{}","utf-8")
        assert check(ROOT,Path(name))
    print("OK : aucune donnée individuelle, aucun petit groupe, aucune diffusion non approuvée")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=ROOT)
    p.add_argument("--built",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:self_test()
    errors=check(a.source,a.built)
    for e in errors:print("ECHEC : "+e)
    if not errors:print("OK : snapshot sans résultat réel et sans identité")
    return bool(errors)
if __name__=="__main__":raise SystemExit(main())
