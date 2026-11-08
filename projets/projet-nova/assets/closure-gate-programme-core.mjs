// Projet NOVA — barrière de clôture vérifiable (G0.17).
// Un score de suivi, une source candidate ou une CI verte n'est PAS une preuve d'adoption.
import {inspectProgramCompleteness,REQUIRED_DOMAINS,REQUIRED_SECTORS}
  from "./audit-completude-programme-core.mjs";

export const FISCAL_PROOF_IDS=Object.freeze(
  Array.from({length:15},(_,i)=>"V"+String(i+1).padStart(2,"0"))
);
export const SCENARIOS=Object.freeze(["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
export const TEN_YEARS=Object.freeze(
  Array.from({length:10},(_,i)=>(2026+i)+"-"+(2027+i))
);
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const safeArray=x=>Array.isArray(x)?x:[];
const isText=x=>typeof x==="string"&&x.trim().length>0;
const isAmount=x=>typeof x==="number"&&Number.isFinite(x);
const keys=x=>Object.keys(x||{});
const uniqueExactly=(a,expected)=>a.length===expected.length&&
 new Set(a).size===a.length&&expected.every(id=>a.includes(id));

// Fields are NOT comparable across the two institutional scenarios.
const ANNUAL_FIELDS={
  QUEBEC_CANADA:[
    "nova_income_tax_revenue","nova_anti_tax_haven_measure_net_revenue",
    "remaining_revenues_after_tax_reform","verified_federal_transfers",
    "portfolio_expenditure_after_measures","debt_service_after_measures",
    "contingency_reserve","generations_fund_deposits",
    "capital_and_transition_costs","employment_impact","net_budgetary_balance"
  ],
  QUEBEC_SOUVERAIN:[
    "nova_income_tax_revenue","nova_anti_tax_haven_measure_net_revenue",
    "other_sovereign_revenues_after_transition","federal_revenue_replacement_verified",
    "transferred_federal_program_expenditures","debt_and_asset_allocation",
    "currency_and_central_bank_transition_costs",
    "pensions_and_social_benefits_continuity_costs",
    "defence_diplomacy_customs_costs",
    "indigenous_nations_rights_and_agreements_costs",
    "service_continuity_reserve","total_public_spending_after_transition",
    "net_budgetary_balance"
  ]
};
const BRIDGE_FIELDS=[
  "nova_income_tax_revenue_mcad","net_haven_yield_mcad",
  "other_retained_revenues_mcad","provincial_services_cost_mcad",
  "federal_functions_cost_mcad","debt_service_mcad",
  "social_continuity_cost_mcad","net_balance_mcad"
];
const isAuditedYear=(row,kind,bridgeRow,scenario,bridgeScenario,year)=>
  object(row)&&object(bridgeRow)&&row.year===year&&
  row.government_comparator_year===year&&bridgeRow.year===year&&
  row.legal_review_completed===true&&
  row.independent_financial_audit_completed===true&&
  ANNUAL_FIELDS[kind].every(k=>isAmount(row[k]))&&
  scenario&&bridgeScenario&&
  bridgeScenario.legal_authority_verified===true&&
  bridgeScenario.independent_fiscal_review===true&&
  bridgeScenario.revenue_base_calibrated===true&&
  bridgeRow.external_audit_completed===true&&
  BRIDGE_FIELDS.every(k=>isAmount(bridgeRow[k]));

export function inspectNOVACompletionGate(audit,g015,g013,g016e){
  const errors=[];
  const a=inspectProgramCompleteness(audit);
  if(!a.ok)errors.push("AUDIT_INTERNE_INVALIDE");
  if(!object(g015)||g015.schema!=="nova-g015-preuves-fiscalite/v1"||
     !Array.isArray(g015.proofs)||!uniqueExactly(g015.proofs.map(p=>p?.id),
        FISCAL_PROOF_IDS))errors.push("PREUVES_FISCALES_NON_CONFORMES");
  if(!object(g013)||g013.schema!=="nova-g013-fiscal-readiness/v1"||
     !Array.isArray(g013.scenarios)||!uniqueExactly(
        g013.scenarios.map(s=>s?.id),SCENARIOS))errors.push("SCENARIOS_G013_NON_CONFORMES");
  if(!object(g016e)||g016e.schema!=="nova-g016e-pont-financier/v1"||
     !Array.isArray(g016e.scenarios)||!uniqueExactly(
        g016e.scenarios.map(s=>s?.id),SCENARIOS))errors.push("SCENARIOS_G016E_NON_CONFORMES");

  const dimensions=safeArray(audit?.dimensions);
  const sectors=safeArray(audit?.sector_register);
  const completeDomains=dimensions.filter(d=>object(d)&&
    Number.isInteger(d.weight)&&Number.isInteger(d.points)&&
    d.weight>0&&d.points===d.weight).length;
  const reviewedSectors=sectors.filter(s=>object(s)&&
    Number.isInteger(s.completed_measure_sheets_confirmed)&&
    s.completed_measure_sheets_confirmed>0&&
    ["source_baseline_confirmed","full_costed_budget_confirmed",
      "legal_review_confirmed","territorial_impact_confirmed",
      "consultation_confirmed","independent_validation_confirmed"]
       .every(k=>s[k]===true)).length;
  const reviewedFiscal=safeArray(g015?.proofs).filter(p=>object(p)&&
    p.status==="VALIDE_INDEPENDAMMENT"&&p.reviewed_independently===true&&
    isText(p.primary_source)&&p.primary_source.startsWith("https://")&&
    isText(p.document_ref)&&
    (Number.isInteger(p.year)&&p.year>=2000)).length;

  let completeBudgetRows=0,completeBudgetScenarios=0;
  for(const kind of SCENARIOS){
    const g13=safeArray(g013?.scenarios).find(s=>s?.id===kind);
    const bridge=safeArray(g016e?.scenarios).find(s=>s?.id===kind);
    if(!object(g13)||!object(bridge)||!Array.isArray(g13.annual)||
       !Array.isArray(bridge.annual)||g13.annual.length!==10||
       bridge.annual.length!==10){
       errors.push("EXERCICES_DIX_ANS_INCOMPLETS:"+kind);continue;
    }
    let scenarioComplete=0;
    for(let i=0;i<TEN_YEARS.length;i++){
      const valid=isAuditedYear(g13.annual[i],kind,bridge.annual[i],
        g13,bridge,TEN_YEARS[i]);
      if(valid){completeBudgetRows++;scenarioComplete++;}
      else if(g13.annual[i]?.year!==TEN_YEARS[i]||
              bridge.annual[i]?.year!==TEN_YEARS[i])
        errors.push("EXERCICE_INCOHERENT:"+kind+":"+i);
    }
    if(scenarioComplete===10)completeBudgetScenarios++;
  }

  const independentReview=audit?.decisions?.independent_review_completed===true&&
    audit?.decisions?.sector_budgets_certified===true;
  const officialAdoption=audit?.decisions?.not_officially_adopted===false&&
    audit?.decisions?.ready_to_govern===true;
  const gates={
    audit_score_100:a.ok&&a.percent===100,
    ten_domains_complete:a.ok&&completeDomains===REQUIRED_DOMAINS.length,
    fourteen_sectors_evidenced:a.ok&&reviewedSectors===REQUIRED_SECTORS.length,
    fifteen_fiscal_proofs_validated:reviewedFiscal===FISCAL_PROOF_IDS.length,
    twenty_financed_scenario_years:completeBudgetRows===20&&
      completeBudgetScenarios===2,
    independent_review:independentReview,
    formal_adoption:officialAdoption
  };
  const sourceValid=errors.length===0;
  return {
    ok:sourceValid,
    errors:[...new Set(errors)],
    schema:"nova-programme-closure-gate/v1",
    audit_date:audit?.date??null,
    checked_score:sourceValid?a.percent:null,
    points_remaining:sourceValid?100-a.score:null,
    documentation_maturity_is_completion:false,
    domains_completed:completeDomains,domains_required:10,
    sector_measure_sheets_confirmed:sectors.reduce((n,s)=>n+
      (Number.isInteger(s?.completed_measure_sheets_confirmed)?
       s.completed_measure_sheets_confirmed:0),0),
    sectors_validated:reviewedSectors,sectors_required:14,
    fiscal_proofs_validated:reviewedFiscal,fiscal_proofs_required:15,
    audited_scenario_years:completeBudgetRows,scenario_years_required:20,
    scenarios_financed:completeBudgetScenarios,scenarios_required:2,
    gates,
    gates_passed:Object.values(gates).filter(Boolean).length,
    gates_total:7,
    completion_certified:sourceValid&&Object.values(gates).every(Boolean),
    notification_authorized:sourceValid&&Object.values(gates).every(Boolean),
    note:"Même une grille à 100/100 ne prouve pas, à elle seule, la disponibilité juridique, financière et démocratique."
  };
}
