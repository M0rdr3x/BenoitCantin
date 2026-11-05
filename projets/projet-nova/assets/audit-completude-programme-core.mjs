/**
 * Projet Nova — grille de complétude du programme, G0.12.
 * Score de pilotage rédactionnel et de préparation, sans valeur réglementaire.
 * Ne doit pas être utilisé pour certifier l'adoption ou la faisabilité politique.
 */
export const EXPECTED_SCORE_DATE="2026-11-05";
export const REQUIRED_DOMAINS=Object.freeze([
 "VISION","INSTITUTIONS","DROITS","SERVICES","ECONOMIE",
 "FINANCES","SOUVERAINETE","EXECUTION","PREUVES","ADOPTION"
]);
export const REQUIRED_SECTORS=Object.freeze([
 "POUVOIR","FISCALITE","SANTE","LOGEMENT","EDUCATION","ADMIN","TRAVAIL",
 "PME","FAMILLES","JUSTICE","REGIONS","DEMOCRATIE","ENVIRONNEMENT","SOUVERAINETE"
]);
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const text=x=>typeof x==="string"&&x.trim().length>0;
const nat=x=>Number.isInteger(x)&&x>=0;
export function inspectProgramCompleteness(doc){
 const errors=[];
 if(!object(doc)||doc.schema!=="nova-programme-completude-v1"||
    !Array.isArray(doc.dimensions)||!Array.isArray(doc.sector_register)||
    !object(doc.scoring)||!object(doc.decisions))return {ok:false,errors:["INVALID_SCHEMA"],percent:null};
 if(doc.date!==EXPECTED_SCORE_DATE)errors.push("UNEXPECTED_ASSESSMENT_DATE");
 const dimensions=doc.dimensions, sectors=doc.sector_register;
 const ids=new Set(),weights=[],earned=[];
 for(const [i,d] of dimensions.entries()){
   if(!object(d)||!text(d.id)||!text(d.name)||!nat(d.weight)||d.weight===0||
      !nat(d.points)||d.points>d.weight||!text(d.evidence)||!text(d.gap)||
      !text(d.next)||!Array.isArray(d.source)||d.source.length===0||
      !d.source.every(text))errors.push("INVALID_DIMENSION:"+i);
   else {ids.add(d.id);weights.push(d.weight);earned.push(d.points);}
 }
 if(ids.size!==REQUIRED_DOMAINS.length||!REQUIRED_DOMAINS.every(k=>ids.has(k))||
    dimensions.length!==REQUIRED_DOMAINS.length)errors.push("DOMAINS_MISSING_OR_DUPLICATED");
 const max=weights.reduce((n,v)=>n+v,0),score=earned.reduce((n,v)=>n+v,0);
 if(max!==100||doc.scoring.maximum!==100)errors.push("TOTAL_WEIGHT_NOT_100");
 if(doc.scoring.earned!==score||doc.scoring.percentage!==score||
    score<0||score>100)errors.push("SCORE_ARITHMETIC_INCORRECT");
 const sectorIds=new Set();
 for(const [i,s] of sectors.entries()){
   if(!object(s)||!text(s.id)||!text(s.name)||!text(s.next_evidence)||
      s.stage!=="CADRAGE_DOCUMENTAIRE"||
      !Array.isArray(s.linked_dimensions)||s.linked_dimensions.length===0||
      !s.linked_dimensions.every(k=>ids.has(k))||
      !nat(s.completed_measure_sheets_confirmed)||s.completed_measure_sheets_confirmed!==0||
      !["source_baseline_confirmed","full_costed_budget_confirmed","legal_review_confirmed",
        "territorial_impact_confirmed","consultation_confirmed","independent_validation_confirmed"]
        .every(k=>s[k]===null))errors.push("SECTOR_HAS_UNSUPPORTED_CLAIMS:"+i);
   sectorIds.add(s?.id);
 }
 if(sectorIds.size!==REQUIRED_SECTORS.length||sectors.length!==REQUIRED_SECTORS.length||
    !REQUIRED_SECTORS.every(k=>sectorIds.has(k)))
   errors.push("SECTORS_MISSING_OR_DUPLICATED");
 if(!Array.isArray(doc.critical_blockers)||doc.critical_blockers.length<4||
    !doc.critical_blockers.every(b=>object(b)&&text(b.id)&&text(b.next)&&
      ["P0","P1","P2"].includes(b.priority)))
   errors.push("BLOCKER_REGISTER_INVALID");
 if(doc.scoring.documentation_maturity_is_independently_measured!==false||
    doc.scoring.legal_government_approval!==false||
    doc.status!=="AUDIT_INTERNE_PROVISOIRE_NON_CERTIFIE"||
    doc.decisions.independent_review_completed!==false||
    doc.decisions.ready_to_govern!==false||
    doc.decisions.not_officially_adopted!==true||
    doc.decisions.pilot_authorized!==false||
    doc.decisions.sector_budgets_certified!==false)
   errors.push("FALSE_READINESS_OR_ADOPTION_CLAIM");
 const pct=max?Math.round(100*score/max):null;
 return {
   ok:errors.length===0,errors:[...new Set(errors)],
   score:errors.length?null:score,
   maximum:max,
   percent:errors.length?null:pct,
   sectors_in_scope:sectors.length,
   dimensions_in_scope:dimensions.length,
   maturity_is_assessment:true,
   fiscal_model_independently_certified:false,
   constitutional_transition_approved:false,
   ready_to_govern:false,political_party_authorization_confirmed:false,
   note:"Une estimation documentaire n'atteste ni budgets équilibrés, ni conformité juridique, ni adoption politique."
 };
}
export function listPriorities(doc){
 const result=inspectProgramCompleteness(doc);
 if(!result.ok)throw new Error("AUDIT_COMPLETUDE_INVALIDE:"+result.errors.join(","));
 return [...doc.critical_blockers].sort((a,b)=>{
  const rank={P0:0,P1:1,P2:2};
  return rank[a.priority]-rank[b.priority];
 }).map(b=>({id:b.id,priority:b.priority,work:b.next,source:b.source}));
}
