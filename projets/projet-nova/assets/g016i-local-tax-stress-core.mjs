// Projet Nova G0.16i — calcul historique, jamais une proposition budgétaire.
export const MODES=Object.freeze([
 ["NO_TAX_REMOVAL","none"],
 ["GENERAL_PROPERTY_TAX_ONLY","property_general_tax_cad"],
 ["ALL_PROPERTY_BASED_TAXES","property_base_taxes_cad"],
 ["ALL_MUNICIPAL_TAXES","taxes_cad"]
]);
export const SERVICE_CODES=Object.freeze([
 "EAU_ET_EGOUTS","VOIRIE_ET_DENEIGEMENT","INCENDIE_ET_SECURITE_CIVILE",
 "TRANSPORTS_ET_EQUIPEMENTS","AMENAGEMENT_ET_LOGEMENT",
 "MAIN_OEUVRE_ET_REGIMES_RETRAITE","DETTE_ET_FINANCEMENT"
]);
export const YEARS=Object.freeze(Array.from({length:10},(_,i)=>
   (2026+i)+"-"+(2027+i)));
const isObj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const baseFields=["taxes_cad","property_base_taxes_cad","property_general_tax_cad",
 "total_revenues_cad","total_expenses_cad","operating_surplus_cad",
 "government_transfers_cad","financing_charges_cad"];
const strictFalse=(o,keys)=>keys.every(k=>o?.[k]===false);
const strictTrue=(o,keys)=>keys.every(k=>o?.[k]===true);
const yearFields=["municipal_revenue_current_cad","municipal_tax_retirement_cad",
 "legal_replacement_tax_yield_cad","municipal_essential_service_cost_cad",
 "provincial_transfer_changes_cad","new_national_function_cost_cad",
 "pension_worker_protection_cost_cad","municipal_net_balance_cad"];
export function calculateFrozenStress(baseline,mode){
 if(!isObj(baseline)||!baseFields.every(k=>
   Number.isSafeInteger(baseline[k])&&baseline[k]>=0)||
   baseline.total_revenues_cad-baseline.total_expenses_cad!==baseline.operating_surplus_cad||
   baseline.property_general_tax_cad>baseline.property_base_taxes_cad||
   baseline.property_base_taxes_cad>baseline.taxes_cad||
   baseline.taxes_cad>baseline.total_revenues_cad||
   !MODES.some(([id])=>id===mode))
   throw new Error("INVALID_REFERENCE_OR_MODE");
 const field=MODES.find(([id])=>id===mode)[1];
 const removed=field==="none"?0:baseline[field];
 return {
  id:mode,baseline_year:2024,removed_revenue_cad:removed,
  remaining_revenue_cad:baseline.total_revenues_cad-removed,
  unchanged_expenses_cad:baseline.total_expenses_cad,
  arithmetic_operating_balance_cad:baseline.operating_surplus_cad-removed,
  replacement_to_hold_reference_balance_cad:removed,
  verified_replacement_cad:null,continuity_financed:false,
  legally_approved:false,actual_nova_prediction:false
 };
}
export function inspectG016iLocalTaxStress(d,g016h,g016g,g014,g015){
 const errors=[],bad=x=>errors.push(x);
 if(!isObj(d)||d.schema!=="nova-g016i-local-tax-continuity-static/v1"||
   !isObj(d.provenance)||!isObj(d.fixed_2024_baseline)||
   !Array.isArray(d.static_stress)||!isObj(d.methodology)||
   !Array.isArray(d.essential_services)||!isObj(d.geographic_coverage)||
   !Array.isArray(d.two_constitutional_budgets)||!Array.isArray(d.evidence_dependencies)||
   !Array.isArray(d.unresolved_actions)||!isObj(d.decisions))
   return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.date!=="2026-11-07"||d.phase!=="G0.16i"||
   d.status!=="STRESS_ARITHMETIQUE_2024_NON_FORECAST"||
   d.adopted!==false||d.programme_score_before!==47||
   d.programme_score_after!==47||
   d.primary_source!=="data/finances-municipales-g0-16h-2024.json")
    bad("FALSE_PROGRAMME_STATUS");
 const p=d.provenance;
 if(p.source_grain!=="AGGREGATED_INCLUDED_MUNICIPALITIES"||
    p.included_local_municipalities!==1056||p.report_year!==2024||
    p.catalogue_updated_on!=="2026-11-05"||
    p.catalogue_financial_dataset_year!==2024||
    p.latest_catalogue_url!=="https://www.donneesquebec.ca/recherche/dataset/profil-financier-des-municipalites-locales"||
    !strictTrue(p,["source_categories_not_mutually_independent",
      "detailed_tax_analysis_marked_unaudited","missing_municipalities",
      "catalogue_2025_values_are_property_assessment_not_2025_financial_revenues",
      "other_provincial_federal_municipal_flows_not_net_reconciled"])||
    p.external_audit_nova!==false)
    bad("PROVENANCE_AND_YEARS");
 const observed=g016h?.annual?.[0];
 if(g016h?.schema!=="nova-g016h-finances-municipales-observees/v1"||
    g016h.programme_score_after!==47||
    g016h?.source?.municipalities_included!==1056||
    g016h?.source?.report_year!==2024||!isObj(observed)||
    !baseFields.every(k=>observed[k]===d.fixed_2024_baseline[k])||
    d.fixed_2024_baseline.total_revenues_cad-
      d.fixed_2024_baseline.total_expenses_cad!==
      d.fixed_2024_baseline.operating_surplus_cad)
    bad("HISTORICAL_BASELINE_MISMATCH");
 if(d.static_stress.length!==4||
    !same(d.static_stress.map(x=>x?.id),MODES.map(x=>x[0]))||
    d.static_stress.some(x=>{
      if(!isObj(x))return true;
      try{return !same(x,calculateFrozenStress(d.fixed_2024_baseline,x.id));}
      catch{return true;}
    }))
    bad("STATIC_STRESS_INCORRECT");
 const m=d.methodology;
 const trueFlags=["expenditure_numbers_frozen_for_sensitivity_only",
  "category_stresses_overlap_never_add_together",
  "other_revenues_2024_unchanged_assumed",
  "2024_balance_is_accounting_not_free_cash",
  "2024_balances_not_future_government_nova_predictions",
  "tax_abolition_nova_neither_adopted_nor_possible_unilaterally_all_levels",
  "liquidity_and_reserves_not_modeled","price_inflation_interest_changes_not_modeled",
  "changes_in_federal_provincial_transfers_not_modeled",
  "municipal_service_staff_continuity_not_guaranteed",
  "household_distribution_by_income_missing","regional_and_community_impact_missing",
  "cannot_derive_2026_tax_rate"];
 if(!strictTrue(m,trueFlags)||
   !strictFalse(m,["fixed_budget_with_same_services",
    "actual_replacement_yield_verified","anti_haven_net_revenue_modeled"])||
   typeof m.tax_exemption_notes!=="string"||
   typeof d.static_observation_note!=="string"||
   !d.static_observation_note.includes("liquidités"))
    bad("MISLEADING_POLICY_PROJECTIONS");
 if(!same(d.essential_services.map(x=>x?.code),SERVICE_CODES)||
    d.essential_services.some(x=>x.protected_in_principle!==true||
    x.annual_continuity_cost_cad!==null||
    x.income_replacement_identified_cad!==null||
    x.local_legal_review!==false||x.worker_rights_audit!==false))
    bad("SERVICE_FINANCING_UNVERIFIED");
 const geoKeys=["municipal_row_level_data_imported",
  "missing_municipalities_quantified","mrc_and_special_entities_reconciled",
  "regional_service_costs_comparable",
  "intergovernmental_transfers_eliminated_for_consolidated_budget"];
 if(!strictFalse(d.geographic_coverage,geoKeys))
    bad("LOCAL_DATA_COVERAGE_UNVERIFIED");
 const scBoolKeys=["legal_competence_reviewed","public_finance_reconciliation_audited",
  "municipalities_tax_autonomy_decided","workers_continuity_cost_verified",
  "federal_transfers_assumed_retained"];
 if(!same(d.two_constitutional_budgets.map(x=>x?.id),
    ["QUEBEC_CANADA","QUEBEC_SOUVERAIN"])||
    d.two_constitutional_budgets.some(s=>
      !isObj(s)||!strictFalse(s,scBoolKeys)||
      !Array.isArray(s.annual)||s.annual.length!==10||
      s.annual.some((y,i)=>!isObj(y)||y.year!==YEARS[i]||
        y.frozen_2024_stress_not_automatically_projected!==true||
        y.independent_verification!==false||
        !yearFields.every(key=>y[key]===null)||
        !same(Object.keys(y).sort(),["year","frozen_2024_stress_not_automatically_projected",
           ...yearFields,"independent_verification"].sort()))))
    bad("FALSE_DECADAL_SCENARIO");
 const ids=Array.from({length:15},(_,i)=>"V"+String(i+1).padStart(2,"0"));
 if(!same(d.evidence_dependencies,ids)||
   g015?.status!=="NON_FRANCHIE"||g015?.programme_score!==47||
   g015.proofs?.length!==15||
   g015.proofs.some(x=>x.status!=="A_DOCUMENTER"))
    bad("G015_NOT_VALIDATED");
 if(d.unresolved_actions.length!==6||
   d.unresolved_actions.some(a=>a?.proof_status!=="NOT_COMPLETED"||
      !a.id||!a.deliverable))
    bad("ACTION_PREMATURELY_CLOSED");
 const falseDecision=["g016i_financial_proof_passed",
  "municipalities_fully_financed_under_nova","legal_tax_change_approved",
  "sovereign_scenario_certified","municipal_assistance_budget_authorized",
  "two_taxes_achievable_certified","programme_complete"];
 if(d.decisions.g016i_reference_stress_documented!==true||
   !strictFalse(d.decisions,falseDecision)||
   Object.keys(d.decisions).length!==8)
    bad("FALSE_APPROVAL");
 if(g016g?.schema!=="nova-g016g-education-municipalites-travail-dette/v1"||
   g016g.programme_score_after!==47||
   g014?.revenue_categories?.find(x=>x.id==="FONCIER_SCOLAIRE")?.amount_mcad!==1301)
    bad("PREDECESSOR_CHAIN_BROKEN");
 return {ok:errors.length===0,errors:[...new Set(errors)],
  programme_score:47,source_year:2024,stress_cases:4,
  legal_approvals:0,verified_replacements:0,
  local_municipalities_in_reference:1056,
  all_tax_removal_frozen_balance_cad:17188134046===d.fixed_2024_baseline.taxes_cad
    ?d.fixed_2024_baseline.operating_surplus_cad-17188134046:null,
  actual_nova_budget_available:false};
}
