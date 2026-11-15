// G0.16 — précontrôle documentaire avant tout scénario fiscal.
// Pur, sans réseau, sans opinion politique ni acte administratif.
const GROUPS={
 V01:"VENTILATION",V02:"VENTILATION",V03:"VENTILATION",V04:"VENTILATION",
 V05:"ASSIETTE",V06:"ASSIETTE",
 V07:"CONTINUITE",V08:"CONTINUITE",V09:"CONTINUITE",V10:"CONTINUITE",
 V11:"CONFORMITE",V12:"INCIDENCE",V13:"INCIDENCE",
 V14:"CONSTITUTION",V15:"BUDGET"
};
const IDS=Object.keys(GROUPS);
const statuses=new Set(["A_DOCUMENTER","SOURCE_EN_REVUE","REVUE_INDEPENDANTE"]);
const string=x=>typeof x==="string"&&x.trim().length>0;
const record=x=>!!x&&typeof x==="object"&&!Array.isArray(x);
const verifiedUrl=x=>{
 if(!string(x)||!/^https:\/\//.test(x)||/[\x00-\x1f\x7f]/.test(x))return false;
 try{
  const u=new URL(x);
  return u.protocol==="https:"&&u.hostname.includes(".")&&!u.username&&!u.password;
 }catch{return false;}
};
export function assessG016Preflight(manifest,audit){
 const errors=[];
 if(!record(manifest)||manifest.schema!=="nova-g015-preuves-fiscalite/v1"||
    !Array.isArray(manifest.proofs)||!record(manifest.decision)||
    !record(manifest.source_baseline_2026_2027)||
    !record(audit)||!record(audit.scoring)||!Array.isArray(audit.dimensions)){
  return {valid:false,errors:["SCHEMA"],required:15,documented:0,
   missing:IDS,programme_percent:null,simulation_authorized:false};
 }
 const weight=audit.dimensions.reduce((n,d)=>n+Number(d.weight||0),0);
 const scored=audit.dimensions.reduce((n,d)=>n+Number(d.points||0),0);
 if(weight!==100||scored!==47||audit.scoring.earned!==47||
    audit.scoring.percentage!==47||manifest.programme_score!==47||
    audit.status!=="AUDIT_INTERNE_PROVISOIRE_NON_CERTIFIE")
  errors.push("PROGRAMME_SCORE_UNVERIFIED");
 if(manifest.status!=="NON_FRANCHIE"||manifest.phase!=="G0.15"||
    manifest.decision.rates_authorized!==false||
    manifest.decision.abolitions_authorized!==false||
    manifest.decision.programme_certified!==false||
    manifest.decision.transition_authorized!==false||
    manifest.nova_tax_rate_percent!==null||
    manifest.net_additional_haven_yield_mcad!==null||
    manifest.financed_scenario_canada!==null||
    manifest.financed_scenario_sovereign!==null)
  errors.push("PREMATURE_FISCAL_OR_LEGAL_APPROVAL");
 const base=manifest.source_baseline_2026_2027;
 if(base.autonomous_revenue_mcad!==135343||
    base.federal_transfers_mcad!==33046||
    base.total_revenue_mcad!==168389||
    base.is_nova_budget!==false)
  errors.push("OFFICIAL_BASELINE_CHANGED");
 const proofs=manifest.proofs;
 if(proofs.length!==15||new Set(proofs.map(x=>x?.id)).size!==15||
    proofs.some(x=>!record(x)||!Object.hasOwn(GROUPS,x.id)||x.group!==GROUPS[x.id]))
  errors.push("PROOF_INVENTORY_CHANGED");
 const documented=[];
 for(const proof of proofs){
  if(!record(proof)||!Object.hasOwn(GROUPS,proof.id))continue;
  if(!string(proof.required_evidence)||!statuses.has(proof.status)||
    (proof.amount_mcad!==null&&(!Number.isFinite(proof.amount_mcad)||proof.amount_mcad<0))||
    ![true,false].includes(proof.reviewed_independently)){
   errors.push("INVALID_PROOF:"+proof.id);
   continue;
  }
  const sourceReady=verifiedUrl(proof.primary_source)&&
    Number.isInteger(proof.year)&&proof.year>=2000&&proof.year<=2100&&
    string(proof.document_ref)&&proof.document_ref.trim().length>=8&&
    !/[\x00-\x1f\x7f]/.test(proof.document_ref);
  if(proof.status==="REVUE_INDEPENDANTE"&&
     proof.reviewed_independently===true&&sourceReady) documented.push(proof.id);
  else if(proof.status==="REVUE_INDEPENDANTE"||proof.reviewed_independently===true)
   errors.push("UNSUPPORTED_INDEPENDENT_REVIEW:"+proof.id);
 }
 const missing=IDS.filter(id=>!documented.includes(id));
 return {
  valid:errors.length===0,errors:[...new Set(errors)],
  required:15,documented:documented.length,missing,
  programme_percent:47,sector_budget_certified:false,
  source_is_self_declared:true,
  stage:errors.length?"INVALID_DOCUMENTATION":
        missing.length?"EVIDENCE_MISSING":"EXTERNAL_APPROVAL_REQUIRED",
  simulation_authorized:false,
  new_tax_rate_authorized:false,government_budget_approved:false,
  next:"Obtenir et faire réviser les 15 preuves V01–V15; séparer les deux statuts constitutionnels et soumettre ensuite tout modèle à une validation indépendante."
 };
}
