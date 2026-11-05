/**
 * Projet Nova G0.13 : contrôle des prévisions publiques et des inconnues Nova.
 * Aucun budget Nova n'est autorisé par une opération arithmétique.
 */
export const YEARS=Object.freeze(Array.from({length:10},(_,i)=>(2026+i)+"-"+(2027+i)));
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const num=x=>Number.isFinite(x);
const nonneg=x=>Number.isSafeInteger(x)&&x>=0;
const keys=["own_revenue","federal_transfers","total_revenue","portfolio_expenditures","debt_service","total_expenditures","contingency_reserve","accounting_balance_before_gap","gap_to_be_bridged","generations_fund_deposits","budgetary_balance_after_assumed_gap"];
const requiredUnknowns=["economic_incidences_modelled","all_ten_years_source_backed","both_scenarios_quantified","tax_bases_reconciled","sovereign_costs_valued","distributional_impact_verified","region_and_workers_protection_verified","independent_fiscal_review","legal_powers_review","public_consultation_and_adoption","fiscal_plan_certified","budget_balance_claim_authorized","g0_passed"];

export function verifyFiscalReadiness(doc){
 const errors=[],add=e=>errors.push(e);
 if(!obj(doc)||doc.schema!=="nova-g013-fiscal-readiness/v1"||
    !Array.isArray(doc.budget_reference)||!Array.isArray(doc.scenarios)||!obj(doc.blocking_gates))
   return {ok:false,errors:["INVALID_DATASET"],progress_percent:null};
 if(doc.units!=="millions CAD courants, flux par exercice; dépenses positives, soldes signés")add("UNITS_MISSING");
 if(doc.budget_reference.length!==10)add("TEN_YEARS_REQUIRED");
 let official=0,unknown=0;
 for(let i=0;i<doc.budget_reference.length;i++){
  const r=doc.budget_reference[i];
  if(!obj(r)||r.year!==YEARS[i]){add("YEAR_ORDER:"+i);continue}
  if(i<5){
   official++;
   if(r.source_year_state!=="OFFICIAL_AUGUST_2026_PROJECTION"||!keys.every(k=>num(r[k]))){
    add("INCOMPLETE_OFFICIAL_YEAR:"+i);continue;
   }
   if(!nonneg(r.own_revenue)||!nonneg(r.federal_transfers)||
      r.own_revenue+r.federal_transfers!==r.total_revenue||
      r.portfolio_expenditures+r.debt_service!==r.total_expenditures||
      r.total_revenue-r.total_expenditures-r.contingency_reserve!==r.accounting_balance_before_gap||
      r.accounting_balance_before_gap+r.gap_to_be_bridged-r.generations_fund_deposits!==r.budgetary_balance_after_assumed_gap)
      add("OFFICIAL_ARITHMETIC:"+i);
   if(r.budget_balance_conditional_on_future_gap!==(i>=2))add("GAP_CONDITIONALITY:"+i);
  }else{
   unknown++;
   if(r.source_year_state!=="NO_OFFICIAL_SOURCE_IN_SELECTED_FRAME"||
      !keys.every(k=>r[k]===null)||r.budget_balance_conditional_on_future_gap!==null)
      add("UNSOURCED_YEARS_NOT_NULL:"+i);
  }
 }
 const components=doc.five_year_income_components_2026_2027;
 const incomeKeys=["personal_income_tax","health_services_contributions","corporate_taxes","school_property_tax","consumption_taxes","duties_licenses_royalties","miscellaneous_revenue","government_enterprises"];
 if(!obj(components)||!incomeKeys.every(k=>nonneg(components[k]))||
   incomeKeys.reduce((sum,k)=>sum+(components?.[k]||0),0)!==components?.own_revenue_total||
   components?.own_revenue_total+components?.federal_transfers!==doc.budget_reference[0]?.total_revenue)
   add("INCOME_COMPONENTS_DONT_RECONCILE");
 const ids=new Set();
 for(const scenario of doc.scenarios){
  if(!obj(scenario)||!["QUEBEC_CANADA","QUEBEC_SOUVERAIN"].includes(scenario.id)||
     ids.has(scenario.id)||!Array.isArray(scenario.annual)||scenario.annual.length!==10){
   add("INVALID_SCENARIO");continue
  }
  ids.add(scenario.id);
  scenario.annual.forEach((year,i)=>{
   if(!obj(year)||year.year!==YEARS[i]||year.net_budgetary_balance!==null||
      year.nova_income_tax_revenue!==null||
      year.nova_anti_tax_haven_measure_net_revenue!==null||
      year.legal_review_completed!==false||
      year.independent_financial_audit_completed!==false)
      add("UNPROVEN_NOVA_BUDGET:"+scenario.id+":"+i);
   if(scenario.id==="QUEBEC_SOUVERAIN"&&(
      year.transferred_federal_program_expenditures!==null||
      year.debt_and_asset_allocation!==null||
      year.other_sovereign_revenues_after_transition!==null||
      year.federal_revenue_replacement_verified!==null))
      add("UNPROVEN_SOVEREIGN_ASSUMPTIONS:"+i);
  });
 }
 if(ids.size!==2)add("BOTH_SCENARIOS_REQUIRED");
 if(!requiredUnknowns.every(k=>doc.blocking_gates[k]===false)||
    doc.blocking_gates.programme_progress_percent_previous!==47||
    doc.blocking_gates.programme_progress_percent_after!==47)
    add("FALSE_COMPLETION_OR_AUTHORIZATION");
 if(!obj(doc.tax_policy)||doc.tax_policy.tax_incomes_all_groups_rate_percent!==null||
    doc.tax_policy.anti_tax_haven_rate_percent!==null||
    doc.tax_policy.anti_tax_haven_collectible_yield!==null||
    doc.tax_policy.no_unfunded_tax_removal!==true)
    add("UNFUNDED_TAX_PROMISE");
 if(doc.source?.is_nova_fiscal_plan!==false||
    doc.source?.source_is_a_forecast!==true||
    doc.source?.budget_March_2026_historical_only!==true)
    add("FORECAST_PROVENANCE_INCORRECT");
 return {ok:errors.length===0,errors:[...new Set(errors)],
  official_years:official,unavailable_years:unknown,
  constitutional_scenarios:[...ids],
  nova_scenarios_budgeted_years:0,
  baseline_2026_revenues:doc.budget_reference[0]?.total_revenue??null,
  baseline_2026_budgetary_balance:doc.budget_reference[0]?.budgetary_balance_after_assumed_gap??null,
  progress_percent:47,fiscal_plan_certified:false,
  independent_audit_completed:false,g0_passed:false};
}
export function summarizeFiscalStatus(doc){
 const v=verifyFiscalReadiness(doc);
 if(!v.ok)throw new Error("G013_INVALID:"+v.errors.join("|"));
 return {label:"COMPARATEUR OFFICIEL, NON BUDGET NOVA",progress_percent:47,
  official_projection_years:5,unsupported_last_years:5,
  nova_proposed_revenue:null,nova_proposed_expenses:null,
  nova_proposed_balance:null,fiscal_savings_proven:null,
  ready_for_government_adoption:false};
}
