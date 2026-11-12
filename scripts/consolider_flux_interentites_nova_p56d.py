#!/usr/bin/env python3
"""P56D : consolider les flux fictifs sans transformer transferts en économies."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

SCHEMA = "P56D-1"
MONEY = re.compile(r"(?:0|[1-9][0-9]{0,8})\.[0-9]{2}\Z")
ENTS = {
    "CANADA":("FEDERAL",False,False,False),
    "QUEBEC":("ETAT_QUEBEC",True,True,False),
    "ORGANISME_QC":("ORGANISME_ETAT",True,True,False),
    "FONDS_ETAT_AFFECTE":("FONDS_AFFECTE",True,True,True),
    "VILLE_A":("MUNICIPALITE",False,True,False),
    "VILLE_B":("MUNICIPALITE",False,True,False),
    "FOURNISSEUR":("TIERS",False,False,False),
    "MENAGES":("TIERS",False,False,False),
    "CREANCIER":("TIERS",False,False,False),
}
FLOW_DEFS = {
    "F01":("CANADA","QUEBEC","TRANSFERT"),
    "F02":("QUEBEC","VILLE_A","TRANSFERT"),
    "F03":("QUEBEC","ORGANISME_QC","TRANSFERT"),
    "F04":("VILLE_A","FOURNISSEUR","SERVICE_EXTERNE"),
    "F05":("VILLE_A","MENAGES","REMUNERATION"),
    "F06":("MENAGES","VILLE_A","IMPOT_MUNICIPAL_EXISTANT"),
    "F07":("CANADA","VILLE_A","TRANSFERT"),
    "F08":("QUEBEC","FOURNISSEUR","SERVICE_EXTERNE"),
    "F09":("CREANCIER","QUEBEC","EMPRUNT"),
    "F10":("QUEBEC","FONDS_ETAT_AFFECTE","TRANSFERT_AFFECTE"),
    "F11":("VILLE_A","VILLE_B","TRANSFERT"),
    "F12":("VILLE_B","FOURNISSEUR","SERVICE_EXTERNE"),
}
DOC_URLS = {
    "https://www.quebec.ca/gouvernement/finances-publiques/budget-comptes-publics/comptes-publics/volumes-comptes-publics",
    "https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/normes-comptables",
    "https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/fiscalite/encadrement",
    "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf"
}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def amt(v):
    if v is None:
        return None
    require(type(v) is str and bool(MONEY.fullmatch(v)), "MONTANT_DECIMAL_OU_NULL")
    return Decimal(v)

def verifie(data):
    require(isinstance(data,dict) and data.get("schema_version")==SCHEMA, "SCHEMA_INVALIDE")
    require(data.get("territoire")=="QUEBEC_DANS_CANADA" and data.get("annee")=="2026-2027", "EXERCICE_OU_REGIME_INVALIDE")
    require(data.get("nature")=="FICTIF_NON_OBSERVE" and data.get("unite")=="M_CAD", "DONNEES_REELLES_NON_AUTHENTIFIEES")
    require(data.get("decision")=="NO_GO_AUTOMATIQUE" and data.get("autorisation_de_reforme") is False, "FAUX_GO")
    require(data.get("verification_juridique") is False and data.get("certification_independante") is False, "CERTIFICATION_INVENTEE")
    require(data.get("projections_p52b_modifiees") is False and data.get("economies_nova_certifiees_mcad") is None, "ECONOMIES_INVENTEES")
    require(data.get("p52b_inconnues")==600 and data.get("p52d_incidences_inconnues")==720 and data.get("p55n_score_estimatif")==53, "PREUVES_INVENTEES")
    sources=data.get("sources_cadre_non_monetaires")
    require(isinstance(sources,list) and len(sources)==4 and
            {x.get("url") for x in sources if isinstance(x,dict)}==DOC_URLS, "REFERENCE_CADRE_INCOMPLETE")
    ents=data.get("entites")
    require(isinstance(ents,list) and len(ents)==len(ENTS), "ENTITES_INCOMPLETES")
    seen=set()
    for x in ents:
        require(isinstance(x,dict), "ENTITE_INVALIDE")
        eid=x.get("id")
        require(isinstance(eid,str) and eid in ENTS and eid not in seen, "ENTITE_DUPLIQUEE")
        seen.add(eid)
        expected=ENTS[eid]
        require((x.get("categorie"),x.get("dans_etat_quebec"),x.get("dans_secteur_public_qc_elargi_fictif"),x.get("affectation_protegee"))==expected, "PERIMETRE_MODIFIE")
    flows=data.get("flux")
    require(isinstance(flows,list) and len(flows)==len(FLOW_DEFS), "FLUX_MANQUANT")
    seen=set()
    for f in flows:
        require(isinstance(f,dict), "FLUX_INVALIDE")
        fid=f.get("id")
        require(isinstance(fid,str) and fid in FLOW_DEFS and fid not in seen, "FLUX_DUPLIQUE")
        seen.add(fid)
        require((f.get("source"),f.get("destination"),f.get("nature"))==FLOW_DEFS[fid], "CONTREPARTIE_OU_NATURE_INVALIDE")
        require(f.get("provenance")=="HYPOTHESE_FICTIVE_NON_SOURCE", "PREUVE_FICTIVE_INVALIDE")
        require(f.get("droit_financement_a_preserver") is (fid in ("F06","F10")), "DROIT_NON_PRESERVE")
        amt(f.get("montant_mcad"))
    return flows

def vue(flows, key):
    recep=Decimal(0)
    dep=Decimal(0)
    elim=Decimal(0)
    dette=Decimal(0)
    inconnus=0
    lines=[]
    for f in flows:
        val=amt(f.get("montant_mcad"))
        a=ENTS[f["source"]][key]
        b=ENTS[f["destination"]][key]
        if f["nature"]=="EMPRUNT":
            classification="FINANCEMENT_NON_RECETTE" if (a!=b and b) else "HORS_VUE_OU_INTERNE"
            if val is not None and a!=b and b:
                dette+=val
        elif a and b:
            classification="ELIMINE_INTERNE_POUR_CETTE_VUE"
            if val is not None:
                elim+=val
        elif not a and b:
            classification="REVENU_EXTERNE_DE_LA_VUE"
            if val is not None:
                recep+=val
        elif a and not b:
            classification="DEPENSE_EXTERNE_DE_LA_VUE"
            if val is not None:
                dep+=val
        else:
            classification="HORS_PERIMETRE"
        if val is None:
            inconnus+=1
        lines.append({"id":f["id"],"classification":classification,"montant_fictif_mcad":f.get("montant_mcad")})
    ready=inconnus==0
    def output(v):
        return str(v.quantize(Decimal(".01"))) if ready else None
    return {
        "revenus_externes_fictifs_mcad":output(recep),
        "depenses_externes_fictives_mcad":output(dep),
        "solde_arithmetique_fictif_mcad":output(recep-dep),
        "transferts_internes_elimines_fictifs_mcad":output(elim),
        "financement_par_emprunt_hors_revenus_mcad":output(dette),
        "flux_montant_inconnu":inconnus,
        "lignes":lines,
        "economies_reelles_certifiees_mcad":None
    }

def analyser(d):
    flows=verifie(d)
    provincial=vue(flows,1)
    elargi=vue(flows,2)
    require(provincial["revenus_externes_fictifs_mcad"] is None or
            provincial["transferts_internes_elimines_fictifs_mcad"] is not None, "CONSOLIDATION_INVALIDE")
    return {
        "jalon":"P56D","schema_version":SCHEMA,
        "statut":"DEMONSTRATION_FICTIVE_SANS_PREUVE_FINANCIERE",
        "exercice":"2026-2027","territoire":"QUEBEC_DANS_CANADA",
        "vues":{
            "ETAT_QUEBEC_FICTIF_NON_OFFICIEL":provincial,
            "SECTEUR_PUBLIC_QC_ELARGI_FICTIF_NON_OFFICIEL":elargi
        },
        "elimination_transferts_egale_economie":False,
        "municipalites_dans_perimetre_etat_quebec_fictif":False,
        "fonds_affecte_automatiquement_disponible":False,
        "financement_dette_traite_comme_recette":False,
        "budget_nova_certifie":False,
        "transposition_aux_exercices_p52b":False,
        "p52b_inconnues":600,"p52d_incidences_inconnues":720,
        "p55n_maturite_estimee_pourcent":53,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entree",required=True,type=Path)
    p.add_argument("--rapport",type=Path)
    p.add_argument("--exiger-faisabilite",action="store_true")
    a=p.parse_args(argv)
    if a.exiger_faisabilite:
        print("NO_GO_AUTOMATIQUE: preuve financiere et revue independante absentes",file=sys.stderr)
        return 3
    try:
        d=json.loads(a.entree.read_text(encoding="utf-8"))
        out=json.dumps(analyser(d),ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as f:
                f.write(out)
        else:
            print(out,end="")
        return 0
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
