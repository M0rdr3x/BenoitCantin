// Projet Nova G0.16 : vérification du plan, sans promesse fiscale.
// Les données synthétiques ne constituent jamais une preuve ni un budget.
export const SCENARIOS=Object.freeze(["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
export const OUTCOMES=Object.freeze([
 "baseline_net_income_cad","baseline_essential_expenses_cad","baseline_remainder_cad",
 "scenario_net_income_cad","scenario_essential_expenses_cad","scenario_remainder_cad",
 "net_change_cad","sample_size","uncertainty_low_cad","uncertainty_high_cad"
]);
export const PROOFS=Object.freeze(Array.from({length:15},(_,i)=>"V"+String(i+1).padStart(2,"0")));
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const integer=x=>Number.isSafeInteger(x)&&x>=0;
const finite=x=>typeof x==="number"&&Number.isFinite(x);

export function inspectG16Plan(d,g015){
 const errors=[];
 if(!object(d)||d.schema!=="nova-g016-incidence-distributive/v1"||
    !Array.isArray(d.scenarios)||!Array.isArray(d.mandatory_proofs)||
    !object(d.source_reference)||!object(d.safety_gates)||
    !object(d.study_design)||!object(d.unknowns)||!object(d.decision))
  return {ok:false,errors:["SCHEMA"],calibrated_scenarios:0};
 if(d.status!=="CADRAGE_NON_CALIBRE"||d.adopted!==false||
    d.programme_score!==47||d.decision.g016_passed!==false||
    d.decision.ready_to_reform!==false||d.decision.valid_for_policy_takeup!==false||
    d.decision.synthetic_cases_are_only_demo!==true)errors.push("FALSE_AUTHORIZATION");
 if(d.source_reference.budget_year!=="2026-2027"||
    d.source_reference.own_revenues_mcad!==135343||
    d.source_reference.federal_transfers_mcad!==33046||
    d.source_reference.total_revenues_mcad!==168389||
    d.source_reference.own_revenues_mcad+d.source_reference.federal_transfers_mcad!==d.source_reference.total_revenues_mcad||
    d.source_reference.meaning!=="PREVISIONS_GOUVERNEMENTALES_NON_BUDGET_NOVA")
  errors.push("REFERENCE_NOT_RECONCILED");
 if(!same(d.mandatory_proofs,PROOFS))errors.push("PROOFS_NOT_COMPLETE");
 if(!object(g015)||g015.schema!=="nova-g015-preuves-fiscalite/v1"||
    !Array.isArray(g015.proofs)||!same(g015.proofs.map(x=>x.id),PROOFS)||
    g015.proofs.some(x=>x.status!=="A_DOCUMENTER"||
         x.reviewed_independently!==false||x.amount_mcad!==null)||
    g015.programme_score!==47||g015.status!=="NON_FRANCHIE"||
    g015.nova_tax_rate_percent!==null||
    g015.net_additional_haven_yield_mcad!==null)errors.push("PREDECESSOR_NOT_VALIDATED");
 if(d.study_design.unit!=="MENAGE"||
    d.study_design.income_decile_basis!=="REVENU_DISPONIBLE_EQUIVALISE_DEFINITION_A_VALIDER"||
    d.study_design.period!=="ANNEE_FISCALE_HOMOGENE_A_DEFINIR"||
    d.study_design.privacy!=="DONNEES_AGREGEES_SEULEMENT_SANS_REIDENTIFICATION"||
    d.study_design.coverage_evidence!==null||
    d.study_design.company_panel_separate!==true||
    !Array.isArray(d.study_design.household_compositions)||
    !Array.isArray(d.study_design.cross_cutting_dimensions)||
    d.study_design.cross_cutting_dimensions.length<5)
   errors.push("MEASUREMENT_OR_PRIVACY_NOT_DEFINED");
 if(d.scenarios.length!==2||new Set(d.scenarios.map(x=>x?.id)).size!==2||
    !SCENARIOS.every(id=>d.scenarios.some(x=>x?.id===id)))
   errors.push("SCENARIOS_NOT_SEPARATE");
 for(const s of d.scenarios){
  if(!object(s)||!SCENARIOS.includes(s.id)||!Array.isArray(s.distribution)||
     s.distribution.length!==10){errors.push("SCENARIO_SHAPE");continue}
  if(s.legal_reviewed!==false||s.source_data_verified!==false||
     s.fiscal_model_calibrated!==false||s.financed_ten_year_plan!==false||
     s.federal_transfers_after_sovereignty_mcad!==null)
    errors.push("UNPROVEN_SCENARIO:"+s.id);
  const deciles=new Set();
  for(const r of s.distribution){
   if(!object(r)||!integer(r.decile)||r.decile<1||r.decile>10||
      deciles.has(r.decile)||!OUTCOMES.every(k=>Object.hasOwn(r,k)&&r[k]===null)){
    errors.push("UNVERIFIED_DECILE:"+s.id);break;
   }
   deciles.add(r.decile);
  }
  if(deciles.size!==10)errors.push("INCOMPLETE_DECILES:"+s.id);
 }
 const expectedGates=["g015_proofs_independently_reviewed","privacy_impact_assessed",
 "household_bases_verified","business_bases_verified","social_funds_continuity_financed",
 "regional_coverage_verified","distributional_impact_audited",
 "legal_compatibility_audited","public_consultation_done","claims_authorized"];
 if(!expectedGates.every(k=>d.safety_gates[k]===false))errors.push("UNPROVEN_GATE");
 if(Object.values(d.unknowns).some(x=>x!==null)||
    Object.keys(d.unknowns).length!==6)errors.push("INVENTED_RESULTS");
 return {ok:errors.length===0,errors:[...new Set(errors)],
   scenarios_count:2,deciles_planned:10,calibrated_scenarios:0,
   published_household_results:0,programme_percent:47,g016_passed:false};
}

// Calcul pédagogique uniquement. Aucune donnée réelle ou fiscale n'est fournie par défaut.
export function compareSyntheticCases(input){
 if(!object(input)||input.mode!=="SYNTHETIC_EXERCISE"||
    !object(input.current)||!object(input.proposed))
  return {ok:false,code:"DEMO_ONLY"};
 const fields=["gross_income_cad","taxes_cad","contributions_cad",
   "benefits_cad","essential_expenses_cad"];
 for(const stage of ["current","proposed"]){
   const x=input[stage];
   if(!fields.every(k=>finite(x[k])&&x[k]>=0))
     return {ok:false,code:"INCOMPLETE_OR_INVALID_INPUT"};
 }
 const calc=x=>{
   const net=x.gross_income_cad-x.taxes_cad-x.contributions_cad+x.benefits_cad;
   return {net_income_cad:net,after_essentials_cad:net-x.essential_expenses_cad};
 };
 const before=calc(input.current),after=calc(input.proposed);
 return {ok:true,kind:"SYNTHETIC_EXERCISE_NOT_POLICY_EVIDENCE",before,after,
   change_after_essentials_cad:after.after_essentials_cad-before.after_essentials_cad,
   count_as_validated_nova_result:false};
}
