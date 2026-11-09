/**
 * G0.19 — Réconciliation en lecture seule de sources provinciales et locales.
 * Aucune recette Nova, taux, économie, certification ni prévision nouvelle.
 */
export const EXERCICES_G019=Object.freeze(
  Array.from({length:10},(_,i)=>`${2026+i}-${2027+i}`)
);
const has=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const whole=x=>Number.isSafeInteger(x)&&x>=0;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const catIDs=["IMPOT_PARTICULIERS","IMPOTS_SOCIETES","COTISATIONS_SANTE",
 "FONCIER_SCOLAIRE","TAXES_CONSOMMATION","DROITS_PERMIS_REDEVANCES",
 "REVENUS_DIVERS","SOCIETES_ETAT","TRANSFERTS_FEDERAUX"];
const nonNovaKeys=["nova_income_net_yield_mcad","nova_haven_incremental_net_yield_mcad",
 "municipal_external_revenues_mcad","net_real_public_balance_mcad","source_evidence_uri"];
export function analyserG019(s){
 const errors=[],reject=x=>errors.push(x);
 if(!has(s)||["audit","assiettes","prevision","consolide","comptes","municipal","cadre"].some(k=>!has(s[k])))
 return {ok:false,errors:["SOURCES_ABSENTES"],pret_a_adopter:false};
 const {audit,assiettes,prevision,consolide,comptes,municipal,cadre}=s;
 if(audit.schema!=="nova-programme-completude-v1"||
  audit.scoring?.earned!==47||audit.scoring?.maximum!==100||
  audit.dimensions?.find(d=>d.id==="FINANCES")?.points!==3||
  audit.dimensions?.find(d=>d.id==="FINANCES")?.weight!==16)
 reject("AUDIT_SOURCE_MISMATCH");
 if(assiettes.schema!=="nova-g014-assiettes-fiscales/v1"||
    prevision.schema!=="nova-g016v-fiscal-framework-aug2026/v1" &&
    prevision.phase!=="G0.16v")
 reject("FISCAL_PROVENANCE_MISMATCH");
 if(consolide.schema!=="nova-g016z-consolidated-financing-and-transition-controls/v1"||
   comptes.schema!=="nova-g015-v02-v03-comptes-publics-reels/v1"||
   municipal.schema!=="nova-g017c-water-municipal-revenue-evidence/v1"||
   !Array.isArray(cadre.scenarios))
 reject("REGISTRES_RECONCILIATION_MISSING");

 const cats=assiettes.revenue_categories||[];
 if(cats.length!==9||!same(cats.map(x=>x.id),catIDs)||
    cats.some(x=>!whole(x.amount_mcad)))
 reject("ASSIETTES_CATEGORIES_INCOMPLETES");
 const sourceSum=cats.reduce((t,x)=>t+(whole(x.amount_mcad)?x.amount_mcad:0),0);
 const amount=id=>cats.find(x=>x.id===id)?.amount_mcad??NaN;
 const revenue2026=assiettes.baseline?.total_revenue;
 const projectedOutlays=assiettes.baseline?.total_expenditures;
 const reserve=assiettes.baseline?.contingency_reserve;
 const fund=assiettes.baseline?.generations_fund_deposits;
 const transfers=assiettes.baseline?.federal_transfers;
 const other=amount("DROITS_PERMIS_REDEVANCES")+amount("REVENUS_DIVERS")+amount("SOCIETES_ETAT");
 const taxCats=amount("IMPOT_PARTICULIERS")+amount("IMPOTS_SOCIETES")+
   amount("COTISATIONS_SANTE")+amount("FONCIER_SCOLAIRE")+amount("TAXES_CONSOMMATION");
 const bridgedAccountNeed=projectedOutlays+reserve-other-transfers;
 const bridgedFundNeed=bridgedAccountNeed+fund;
 const noFederalStress=bridgedAccountNeed+transfers;
 const exposure=amount("COTISATIONS_SANTE")+amount("FONCIER_SCOLAIRE")+amount("TAXES_CONSOMMATION");
 if(!whole(revenue2026)||!whole(projectedOutlays)||!whole(reserve)||!whole(fund)||
  !whole(transfers)||sourceSum!==revenue2026||sourceSum!==(other+taxCats+transfers)||
  assiettes.baseline.accounting_balance!==revenue2026-projectedOutlays-reserve||
  assiettes.baseline.budgetary_balance!==revenue2026-projectedOutlays-reserve-fund)
 reject("2026_BILAN_GOUVERNEMENTAL_INCOHERENT");
 if(other!==28182||taxCats!==107161||transfers!==33046||
  bridgedAccountNeed!==112369||bridgedFundNeed!==114851||
  noFederalStress!==145415||exposure!==41521||
  assiettes.mechanical_sensitivity?.removed_baseline_receipts!==exposure||
  assiettes.mechanical_sensitivity?.net_adjustment_needed_to_reach_zero_budgetary_balance!==49211)
 reject("2026_BRIDGE_ARITHMETIQUE_DIVERGENT");

 const yrs=prevision.government_reference?.fiscal_years_official||[];
 const series=consolide.official_reference_series||[];
 if(yrs.length!==5||series.length!==10)reject("HORIZON_REFERENCE_INCORRECT");
 const reconciled=[];
 for(let i=0;i<10;i++){
  const y=EXERCICES_G019[i],c=series[i],p=yrs[i];
  if(!has(c)||c.year!==y){reject("ANNEE_CONSOLIDATION_ABSENTE:"+y);continue;}
  if(i<5){
   const tax=p?.existing_tax_sources_mcad, nontax=p?.other_government_receipts_mcad,
    fed=p?.federal_transfers_mcad,spend=p?.government_expenditure_including_debt_service_mcad,
    prov=p?.contingency_provision_mcad,gen=p?.generations_fund_contribution_mcad;
   if(p?.fiscal_year!==y||!p.verifier_general_plausibility_review_2026_2028_only===undefined){} // pas de changement des périmètres
   if(p?.fiscal_year!==y||![tax,nontax,fed,spend,prov,gen].every(whole)||
     tax+nontax+fed!==p?.total_government_revenue_mcad||
     p.total_government_revenue_mcad!==c.provincial_revenue_mcad||
     spend!==c.provincial_expenses_including_debt_mcad||
     prov!==c.contingency_mcad||gen!==c.generations_fund_mcad||
     tax!==c.existing_tax_cats_mcad||nontax!==c.non_tax_receipts_assumed_mcad||
     fed!==c.federal_transfers_mcad||
     spend+prov-nontax-fed!==c.conditional_tax_need_to_balance_account_mcad||
     spend+prov+gen-nontax-fed!==c.conditional_tax_need_plus_fund_mcad||
     spend+prov-nontax!==p.conditional_no_federal_transfer_same_provincial_spending_mcad)
      reject("REFERENCE_ANNUELLE_NON_RECONCILIEE:"+y);
   reconciled.push({year:y,classification:"PREVISION_GOUVERNEMENT_QC_NON_NOVA",
      fiscal_reference_available:true,conditional_provincial_levies_mcad:c.conditional_tax_need_to_balance_account_mcad,
      conditional_with_generations_mcad:c.conditional_tax_need_plus_fund_mcad,
      no_transfer_same_spending_stress_mcad:p?.conditional_no_federal_transfer_same_provincial_spending_mcad,
      real_nova_balance_mcad:null});
  } else {
   if(c.source_available!==false||
     ["provincial_revenue_mcad","existing_tax_cats_mcad","federal_transfers_mcad",
      "non_tax_receipts_assumed_mcad","provincial_expenses_including_debt_mcad",
      "conditional_tax_need_to_balance_account_mcad","conditional_tax_need_plus_fund_mcad"]
        .some(k=>c[k]!==null))reject("PROJECTION_2031_2036_INVENTEE:"+y);
   reconciled.push({year:y,classification:"AUCUNE_PREVISION_OFFICIELLE_DANS_CETTE_SERIE",
      fiscal_reference_available:false,conditional_provincial_levies_mcad:null,
      conditional_with_generations_mcad:null,no_transfer_same_spending_stress_mcad:null,
      real_nova_balance_mcad:null});
  }
 }
 if(!Array.isArray(consolide.scenario_years)||consolide.scenario_years.length!==2||
    !Array.isArray(cadre.scenarios)||cadre.scenarios.length!==2)
 reject("SCENARIOS_CONSTITUTIONNELS_ABSENTS");
 const ids=["QUEBEC_CANADA","QUEBEC_SOUVERAIN"];
 for(let i=0;i<2;i++){
   const c=consolide.scenario_years?.[i],base=cadre.scenarios?.[i],p=prevision.scenarios?.[i];
   if(!c||!base||!p||c.id!==ids[i]||base.id!==ids[i]||p.id!==ids[i]||
       c.years?.length!==10||base.annual?.length!==10||p.years?.length!==10)
   {reject("SCENARIO_INCOMPLET:"+ids[i]);continue;}
   for(let n=0;n<10;n++){
    const year=EXERCICES_G019[n],cy=c.years[n],by=base.annual[n],py=p.years[n];
    if(cy?.year!==year||by?.year!==year||py?.fiscal_year!==year||
       nonNovaKeys.some(k=>cy?.[k]!==null)||
       cy.legal_review_passed!==false||cy.economic_stress_review_passed!==false||
       by.net_budgetary_balance!==null||by.independent_financial_audit_completed!==false||
       py.nova_annual_balance_mcad!==null||py.nova_external_fiscal_audit_passed!==false||
       py.nova_levy_effective_rate_pct!==null||py.nova_verified_tax_haven_levy_yield_mcad!==null)
      reject("SCENARIO_NOVA_NON_ETAYE:"+ids[i]+":"+year);
   }
 }
 if(prevision.scenarios?.[1]?.future_transfer_treatment!=="DO_NOT_AUTOMATICALLY_PRESUME_FEDERAL_TRANSFERS"||
    assiettes.constitutional_scenarios?.[1]?.baseline_federal_transfers_2026_2027!==null)
 reject("SOUVERAINETE_TRANSFERTS_IMPLICITES");
 if(comptes.annual?.length!==2||
    comptes.annual[1]?.year!=="2025-2026"||
    comptes.annual[1]?.total_revenues!==160428||
    comptes.annual[1]?.total_expenditures!==165930||
    comptes.annual[1]?.accounting_balance!==-5502||
    comptes.annual[1]?.total_revenues-comptes.annual[1]?.total_expenditures!==-5502||
    comptes.cross_reference_g014?.add_2025_2026_actuals_to_2026_2027_forecast!==false)
 reject("REEL_2025_2026_MELANGE_AVEC_PREVISION");
 const m=municipal.municipal||{},water=municipal.water||{};
 if(m.year!==2024||m.total_revenue_gcad!==31.3||
   Math.abs((m.components||[]).reduce((v,x)=>v+x.amount_gcad,0)-31.3)>1e-8||
   m.verified_raw_municipal_csv!==false||
   m.same_year_transfer_cancellation_verified!==false||
   water.year!==2023||water.calculated_illustrative_uncovered_full_cost_gcad!==3.6||
   water.illustrative_gap_is_not_annual_cash_deficit!==true||
   municipal.decision?.municipal_net_replacement_costed!==false)
 reject("MUNICIPAL_EAU_DOUBLE_COMPTAGE");
 if(assiettes.tax_design_constraints?.income_tax_rate_percent!==null||
   assiettes.tax_design_constraints?.offshore_revenue_incremental_after_overlap!==null||
   assiettes.decision?.nova_budget_certified!==false||
   consolide.decision?.ten_year_canada_balance_verified!==false||
   consolide.decision?.ten_year_sovereign_balance_verified!==false||
   prevision.program_is_financially_certified!==false)
 reject("DECLARATION_TAUX_OU_BUDGET_NON_PROUVEE");
 return {ok:errors.length===0,errors:[...new Set(errors)],
  baseline_date:"2026-11-08",unit:"M_CAD",scope:"ETAT_PROVINCIAL_QC_SEUL",
  audited_score:47,finance_dimension_points:3,
  official_forecast_years:5,total_planning_years_per_scenario:10,
  scenario_count:2,unsupported_nova_scenario_years:20,
  government_baseline_2026_27:{revenue_mcad:revenue2026,expenditure_mcad:projectedOutlays,
    receipts_in_current_tax_categories_mcad:taxCats,other_receipts_assumed_mcad:other,
    federal_transfers_forecast_mcad:transfers},
  frozen_mechanical_stresses_only:{
    three_categories_at_risk_mcad:exposure,
    remaining_adjustment_including_existing_deficit_mcad:49211,
    required_conditional_levies_for_accounting_balance_mcad:bridgedAccountNeed,
    required_conditional_levies_including_generations_mcad:bridgedFundNeed,
    without_federal_transfers_same_provincial_costs_mcad:noFederalStress
  },
  actual_2025_26_accounting_balance_mcad:-5502,
  municipal_2024_revenues_gcad:31.3,
  water_2023_full_cost_shortfall_not_cash_deficit_gcad:3.6,
  five_forecast_rows:reconciled,
  nova_tax_base_certified:false,nova_haven_incremental_revenue_certified:false,
  municipal_transfer_netting_completed:false,
  ten_year_budgets_certified:false,independent_audit_completed:false,
  pret_a_adopter:false,conclusion:"NO_GO_ETUDE_NON_ADOPTEE" };
}
