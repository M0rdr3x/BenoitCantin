#!/usr/bin/env python3
"""Nova: le public ne voit jamais de votes individuels ou petites cellules."""
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
REL="projets/projet-nova/data/resultats-sondages-publics-v1.json"
CLIENT_REL="projets/projet-nova/assets/resultats-sondages.js"
CLOSED_CLIENT_GATE="const PUBLIC_AGGREGATES_ENABLED = false;"
# Empreinte du snapshot fermé public, approuvée avant ouverture de #675.
# Toute modification, même limitée aux espaces, requiert une revue explicite.
CLOSED_PUBLIC_SHA256="d439e45481f0319d522b7fd0d70c592b40dd6b2368b31b3c5214dbf958e3cf2e"
MAX_PUBLIC_BYTES=65536
CLOSED_SOURCE="aucune enquête enregistrée ou publiée"
CLOSED_NOTES="Aucun résultat de participation réelle n'est disponible. Les choix de démonstration ne sont ni envoyés ni comptabilisés."
SURVEYS={"nova-orientations-40-v1":(40,("pour","contre","sans_opinion")),
         "nova-consultation-64-v1":(64,("-3","-2","-1","0","1","2","3","skip"))}
FORBIDDEN=("person","user","email","ip_address","ipaddress","address","hash",
           "account","identity","identit","token","session","device","individual",
           "respondent_id","participant_id","ballot","raw_vote","demograph")

def validate(obj, review=False):
    """Fail closed: only the reviewed public aggregate schema is permitted.

    review=True is for local synthetic contract tests or a future independent
    human review. Production CI deliberately calls this with review=False.
    """
    bad=[]
    if not isinstance(obj,dict):
        return ["Snapshot non objet"]

    public_keys={"schema","publicationStatus","publicationApproved",
                 "privacyReviewApproved","surveys","rules","publishedOn",
                 "source","notes"}
    survey_keys={"status","questionCount","respondents","questions"}
    if set(obj)!=public_keys:
        bad.append("Champs publics manquants ou non approuvés")
    if obj.get("schema")!="nova-public-results-v1":
        bad.append("Version de snapshot inconnue")
    if (obj.get("rules")!=
            {"minimumParticipants":30,"minimumNonzeroCell":10,
             "suppression":"entire-question"}):
        bad.append("Seuils de confidentialité erronés")
    if (type(obj.get("publicationApproved"))!=bool or
            type(obj.get("privacyReviewApproved"))!=bool):
        bad.append("Drapeaux de publication invalides")
    for key in ("source","notes"):
        value=obj.get(key)
        if not isinstance(value,str) or not value.strip() or len(value)>400:
            bad.append("Métadonnée publique absente/invalide: "+key)

    status=obj.get("publicationStatus")
    if status not in ("not_open","approved_aggregate"):
        bad.append("Statut de publication incorrect")
    elif status=="not_open":
        if (obj.get("publicationApproved") is not False or
                obj.get("privacyReviewApproved") is not False or
                obj.get("publishedOn") is not None):
            bad.append("Un snapshot fermé ne peut afficher une approbation ou une date")
        if obj.get("source") != CLOSED_SOURCE or obj.get("notes") != CLOSED_NOTES:
            bad.append("Mentions publiques du statut fermé modifiées sans revue")
    else:
        if not review:
            bad.append("Les données réelles ne sont pas autorisées (#675)")
        if (obj.get("publicationApproved") is not True or
                obj.get("privacyReviewApproved") is not True):
            bad.append("Publication sans double approbation")
        published=obj.get("publishedOn")
        try:
            from datetime import date
            if type(published)!=str or date.fromisoformat(published).isoformat()!=published:
                raise ValueError("Format non canonique")
        except (ValueError, TypeError):
            bad.append("Date de publication invalide")

    surveys=obj.get("surveys")
    if not isinstance(surveys,dict) or set(surveys)!=set(SURVEYS):
        return bad+["Inventaire des deux sondages divergent"]
    approved_count=0
    for sid,(length,choices) in SURVEYS.items():
        entry=surveys[sid]
        if not isinstance(entry,dict) or set(entry)!=survey_keys:
            bad.append("Champs du questionnaire non approuvés: "+sid)
            continue
        if type(entry.get("questionCount"))!=int or entry["questionCount"]!=length:
            bad.append("Questionnaire divergent : "+sid)
            continue
        entry_status=entry.get("status")
        rows=entry.get("questions")
        if entry_status=="not_open":
            if entry.get("respondents") is not None or rows!=[]:
                bad.append("Chiffres présents sur consultation fermée")
        elif entry_status=="approved_aggregate":
            approved_count+=1
            if status!="approved_aggregate":
                bad.append("Agrégats publiés sous statut global fermé")
            if (obj.get("publicationApproved") is not True or
                    obj.get("privacyReviewApproved") is not True):
                bad.append("Publication non approuvée")
                continue
            n=entry.get("respondents")
            if type(n)!=int or n<30 or not isinstance(rows,list) or len(rows)!=length:
                bad.append("Échantillon public insuffisant")
                continue
            for index,row in enumerate(rows):
                if not isinstance(row,dict) or row.get("id")!="q"+str(index+1).zfill(2):
                    bad.append("Identifiant de question incorrect")
                    continue
                if row.get("status")=="suppressed":
                    if set(row)!={"id","status"}:
                        bad.append("Question masquée révélant des champs additionnels")
                    continue
                if (row.get("status")!="published" or
                    set(row)!={"id","status","total","counts"} or
                    type(row.get("total"))!=int or row["total"]!=n or
                    not isinstance(row.get("counts"),dict) or
                    set(row["counts"])!=set(choices)):
                    bad.append("Comptes erronés q"+str(index+1))
                    continue
                values=list(row["counts"].values())
                if (not all(type(v)==int and (v==0 or v>=10) for v in values)
                    or sum(values)!=n):
                    bad.append("Petite cellule ou total incohérent")
        else:
            bad.append("Statut inconnu pour "+sid)
    if status=="approved_aggregate" and not approved_count:
        bad.append("Publication annoncée sans questionnaire publié")
    return bad

def parse_public_snapshot(text):
    """Refuser les clés dupliquées et valeurs hors JSON, même ignorées par JSON.parse.

    Le fichier brut est public : une valeur écrasée à la lecture reste lisible
    par un visiteur. Les validateurs d'objets ne doivent pas la masquer.
    """
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Clé JSON dupliquée")
            result[key] = value
        return result

    def reject_nonfinite(_value):
        raise ValueError("Valeur numérique JSON non standard")

    return json.loads(text, object_pairs_hook=unique_keys,
                      parse_constant=reject_nonfinite)


def check(root,built=None):
    target=root/REL
    browser=root/CLIENT_REL
    if not target.is_file() or target.is_symlink():return ["Snapshot absent ou symbolique"]
    if not browser.is_file() or browser.is_symlink():
        return ["Client résultats absent ou symbolique"]
    try:
        browser_bytes=browser.read_bytes()
        browser_code=browser_bytes.decode("utf-8")
    except (OSError,UnicodeError):
        return ["Client résultats illisible"]
    bad=[]
    if browser_code.count(CLOSED_CLIENT_GATE)!=1:
        bad.append("Verrou navigateur de publication désactivé (#675)")
    try:
        if target.stat().st_size > MAX_PUBLIC_BYTES:
            return ["Snapshot public trop volumineux"]
        source_bytes=target.read_bytes()
        if len(source_bytes)>MAX_PUBLIC_BYTES:
            return ["Snapshot public trop volumineux"]
        data=parse_public_snapshot(source_bytes.decode("utf-8"))
    except (OSError,ValueError,UnicodeError):
        return ["Snapshot illisible"]
    bad+=validate(data)
    # Un schéma formellement valide ne suffit pas à approuver les octets
    # destinés au site public : bloquer même une version reformattée.
    if hashlib.sha256(source_bytes).hexdigest()!=CLOSED_PUBLIC_SHA256:
        bad.append("Snapshot fermé différent de la version approuvée (#675)")
    if built is not None:
        dest=built/REL
        if not dest.is_file() or dest.is_symlink():
            bad.append("Snapshot absent du build")
        elif dest.read_bytes()!=source_bytes:
            bad.append("Snapshot altéré dans Jekyll")
        client_dest=built/CLIENT_REL
        if not client_dest.is_file() or client_dest.is_symlink():
            bad.append("Client résultats absent du build Jekyll")
        elif client_dest.read_bytes()!=browser_bytes:
            bad.append("Client résultats altéré dans Jekyll")
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
      {"id":"q"+str(i+1).zfill(2),"status":"published","total":30,
       "counts":{"pour":20,"contre":10,"sans_opinion":0}} for i in range(40)])
    assert validate(sample), "Ne jamais approuver une publication réelle en CI"
    # Les vérifications négatives s'appliquent même au mode revue.
    mutation=json.loads(json.dumps(source))
    mutation["publicationStatus"]="approved_aggregate"
    assert validate(mutation,review=True), "Statut global incohérent accepté"
    mutation=json.loads(json.dumps(source))
    mutation["surveys"]["nova-orientations-40-v1"]["individualResponses"]=[]
    assert validate(mutation,review=True), "Champ individuel imprévu accepté"
    mutation=json.loads(json.dumps(source))
    mutation["source"]={"extra":"identité"}
    assert validate(mutation,review=True), "Métadonnée imbriquée acceptée"
    mutation=json.loads(json.dumps(source))
    mutation["privacyReviewApproved"]=0
    assert validate(mutation,review=True), "Faux booléen accepté"
    for field in ("source", "notes"):
        mutation=json.loads(json.dumps(source))
        mutation[field]="contact de participant fictif: test@example.invalid"
        assert validate(mutation), "Texte non approuvé accepté sur état fermé"
        assert validate(mutation,review=True), "Revue synthétique a contourné le verrou des mentions"
    mutation=json.loads(json.dumps(source))
    mutation["publishedOn"]="2026-10-22"
    assert validate(mutation,review=True), "Date non approuvée acceptée"
    assert not validate(sample,review=True), "Agrégation synthétique valide refusée"
    a["questions"][0]["counts"]={"pour":24,"contre":6,"sans_opinion":0}
    assert validate(sample,review=True), "Petite cellule publiée"
    a["questions"][0]={"id":"q01","status":"suppressed"}
    assert not validate(sample,review=True), "Suppression sûre d'une question refusée"
    a["questions"][0]["counts"]={"pour":24,"contre":6,"sans_opinion":0}
    assert validate(sample,review=True), "Comptes divulgués dans une question masquée"
    a["questions"][0]={"id":"q01","status":"published","total":30,
                        "counts":{"pour":20,"contre":10,"sans_opinion":0}}
    with TemporaryDirectory() as name:
        out=Path(name)/REL;out.parent.mkdir(parents=True)
        out.write_bytes((ROOT/REL).read_bytes())
        browser=Path(name)/CLIENT_REL
        browser.parent.mkdir(parents=True,exist_ok=True)
        browser.write_bytes((ROOT/CLIENT_REL).read_bytes())
        assert not check(ROOT,Path(name))
        assert not check(Path(name))
        original_client=browser.read_text("utf-8")
        browser.write_text(original_client.replace(CLOSED_CLIENT_GATE,
                           "const PUBLIC_AGGREGATES_ENABLED = true;"), "utf-8")
        assert any("Verrou navigateur" in e for e in check(Path(name))), (
            "Le client a affiché un agrégat avant la revue #675"
        )
        browser.write_text(original_client, "utf-8")
        assert not check(Path(name))
        # Le parseur JSON standard perd la première valeur d'une clé dupliquée.
        # Or les octets de cette première valeur resteraient publiquement lisibles.
        original = (ROOT/REL).read_text("utf-8")
        mutations = (
            original.replace('"publicationApproved": false,',
                '"publicationApproved": true, "publicationApproved": false,', 1),
            original.replace('"status": "not_open",',
                '"status": "approved_aggregate", "status": "not_open",', 1),
            original.replace('"respondents": null,',
                '"respondents": NaN, "respondents": null,', 1),
        )
        for altered in mutations:
            assert altered != original, "Mutation de test inactive"
            out.write_text(altered, "utf-8")
            assert any("Snapshot illisible" in error for error in check(Path(name))), (
                "JSON ambigu ou non standard accepté par la validation publique"
            )
        out.write_bytes((ROOT/REL).read_bytes())
        assert not check(Path(name))
        # Régression : un JSON structurellement identique, mais différent
        # octet par octet, ne peut être publié sans révision du snapshot.
        out.write_text(original + " ", "utf-8")
        assert not validate(parse_public_snapshot(out.read_text("utf-8")))
        assert any("version approuvée" in e for e in check(Path(name))), (
            "Modification silencieuse des octets publics acceptée"
        )
        out.write_text(original + " " * MAX_PUBLIC_BYTES, "utf-8")
        assert any("trop volumineux" in e for e in check(Path(name))), (
            "Snapshot public non borné accepté"
        )
        out.write_bytes((ROOT/REL).read_bytes())
        assert not check(Path(name))
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
