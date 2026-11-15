// Projet Nova G0.16e — pont documentaire, ni simulation ni promesse fiscale.
// Un montant historique ou une recette budgétaire ne prouve pas un taux de réforme.
export const YEARS=Object.freeze(Array.from({length:10},(_,i)=>(2026+i)+"-"+(2027+i)));
export const PROOFS=Object.freeze(Array.from({length:15},(_,i)=>"V"+String(i+1).padStart(2,"0")));
export const CONTINUITY=Object.freeze(["RRQ","RQAP","FSS","MEDICAMENTS","EDUCATION","MUNICIPALITES","EMPLOIS","DETTE"]);
export const LEDGER=Object.freeze([
 ["PERSONAL_2023",2023,"ASSIETTE_IMPOSABLE","DECLARATIONS_FISCALES_PERSONNES",372261],
 ["CORPORATE_2021",2021,"ASSIETTE_IMPOSABLE","DECLARATIONS_FISCALES_SOCIETES",95784],
 ["FSS_PAYROLL_2021",2021,"MASSE_SALARIALE_COTISABLE","DECLARATIONS_FISCALES_SOCIETES",155850],
 ["PERSONAL_REVENUE_2026",2026,"RECETTE_PREVISIONNELLE","BUDGET_GOUVERNEMENTAL_2026_2027",50942],
 ["CORPORATE_REVENUE_2026",2026,"RECETTE_PREVISIONNELLE","BUDGET_GOUVERNEMENTAL_2026_2027",14698],
 ["FSS_REVENUE_2026",2026,"RECETTE_PREVISIONNELLE","BUDGET_GOUVERNEMENTAL_2026_2027",9538]
]);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const keys=(o,k)=>obj(o)&&Object.keys(o).length===k.length&&k.every(x=>Object.hasOwn(o,x));
const scenKeys=["nova_income_tax_revenue_mcad","net_haven_yield_mcad","other_retained_revenues_mcad",
"provincial_services_cost_mcad","federal_functions_cost_mcad","debt_service_mcad",
"social_continuity_cost_mcad","net_balance_mcad"];
const readG14=x=>x?.baseline;
const verifyAmounts=(a,b,fields)=>fields.every(([x,y])=>a?.[x]===b?.[y]);
export function verifyG016eBridge(d,corporate,personal,g14,g15){
 const errors=[],bad=x=>errors.push(x);
 if(!obj(d)||d.schema!=="nova-g016e-pont-financier/v1"||
    !obj(d.source_principles)||!Array.isArray(d.historic_and_forecast_ledger)||
    !obj(d.official_baseline_2026_2027)||!obj(d.revenue_exposure_illustration)||
    !Array.isArray(d.continuity)||!Array.isArray(d.scenarios)||!Array.isArray(d.required_g015_evidence_ids)||
    !Array.isArray(d.open_research)||!obj(d.decision))
    return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.phase!=="G0.16e"||d.status!=="RAPPROCHEMENT_DOCUMENTAIRE_NON_CALIBRE"||
    d.adopted!==false||d.programme_score_before!==47||d.programme_score_after!==47)
    bad("FALSE_PROGRAMME_STATUS");
 const p=d.source_principles;
 const bools=["fiscal_returns_are_not_budget_receipts","different_tax_years_cannot_be_summed",
 "taxable_profit_and_payroll_are_separate","provincial_federal_municipal_competences_separate",
 "government_baseline_is_not_nova_fiscal_plan","two_tax_system_is_hypothesis_not_adopted",
 "anti_haven_recovery_cannot_be_assumed","source_assumptions_need_external_audit"];
 if(bools.some(k=>p[k]!==true)||!p.government_report_url?.startsWith("https://cdn-contenu.quebec.ca/")||
    !p.independent_fiscal_comparison_method_url?.startsWith("https://cffp.recherche.usherbrooke.ca/"))
    bad("INVALID_PROVENANCE_OR_GUARDRAILS");
 if(!obj(corporate)||!obj(personal)||!obj(g14)||!obj(g15)||
    corporate.corporate_tax_base?.quebec_taxable_income_mcad!==95784||
    corporate.corporate_tax_base?.payroll_subject_to_fss_mcad!==155850||
    corporate.source?.year!==2021||
    personal.tax_return_aggregates_mcad?.taxable_income!==372261||personal.source_year!==2023||
    g15.programme_score!==47||g15.status!=="NON_FRANCHIE"||
    !Array.isArray(g15.proofs)||g15.proofs.length!==15||
    g15.proofs.some(x=>x.status!=="A_DOCUMENTER"))
    bad("PREDECESSOR_EVIDENCE_INVALID");
 const categories=g14?.revenue_categories??[];
 const fiscal=Object.fromEntries(categories.map(x=>[x.id,x.amount_mcad]));
 const expected=[372261,95784,155850,fiscal.IMPOT_PARTICULIERS,fiscal.IMPOTS_SOCIETES,fiscal.COTISATIONS_SANTE];
 if(d.historic_and_forecast_ledger.length!==6||
    d.historic_and_forecast_ledger.some((x,i)=>!obj(x)||
      !same([x.id,x.year,x.type,x.scope,x.amount_mcad],LEDGER[i])||
      x.amount_mcad!==expected[i]||x.can_directly_fund_nova!==false||
      !x.measure||!x.source))
     bad("HISTORIC_LEDGER_MISMATCH");
 const b=d.official_baseline_2026_2027,b14=readG14(g14);
 const link=[["own_revenue_mcad","own_source_revenue"],["federal_transfers_mcad","federal_transfers"],
 ["total_revenue_mcad","total_revenue"],["portfolio_expenditures_mcad","portfolio_expenditures"],
 ["debt_service_mcad","debt_service"],["total_expenditures_mcad","total_expenditures"],
 ["contingency_reserve_mcad","contingency_reserve"],["generations_fund_deposits_mcad","generations_fund_deposits"],
 ["accounting_balance_mcad","accounting_balance"],["budgetary_balance_mcad","budgetary_balance"]];
 if(!verifyAmounts(b,b14,link)||b.year!=="2026-2027"||
    b.status!=="GOUVERNEMENT_2026_PROJECTION_NOT_NOVA"||
    b.source!=="data/registre-assiettes-fiscales-g0-14-2026-2027.json"||
    b.own_revenue_mcad+b.federal_transfers_mcad!==b.total_revenue_mcad||
    b.portfolio_expenditures_mcad+b.debt_service_mcad!==b.total_expenditures_mcad||
    b.total_revenue_mcad-b.total_expenditures_mcad-b.contingency_reserve_mcad!==b.accounting_balance_mcad||
    b.accounting_balance_mcad-b.generations_fund_deposits_mcad!==b.budgetary_balance_mcad)
    bad("BUDGET_BASELINE_MISMATCH");
 const e=d.revenue_exposure_illustration;
 const removed=["COTISATIONS_SANTE","FONCIER_SCOLAIRE","TAXES_CONSOMMATION"];
 if(!same(e.removed_revenue_ids,removed)||
    e.fss_mcad!==fiscal.COTISATIONS_SANTE||
    e.school_tax_mcad!==fiscal.FONCIER_SCOLAIRE||
    e.consumption_taxes_mcad!==fiscal.TAXES_CONSOMMATION||
    e.fss_mcad+e.school_tax_mcad+e.consumption_taxes_mcad!==e.total_at_risk_mcad||
    e.total_at_risk_mcad!==41521||
    e.frozen_accounting_balance_mcad!==b.accounting_balance_mcad-e.total_at_risk_mcad||
    e.frozen_budgetary_balance_mcad!==b.budgetary_balance_mcad-e.total_at_risk_mcad||
    e.stability_replacement_needed_mcad!==e.total_at_risk_mcad||
    e.mechanical_zero_gap_mcad!==-e.frozen_budgetary_balance_mcad||
    e.status!=="HYPOTHETIQUE_ARITHMETIQUE_FIGEE_NON_PREVISION"||
    e.continuity_proven!==false||e.behavioural_response_estimated!==false||
    e.nova_policy_decided!==false)
     bad("EXPOSURE_NOT_A_FORECAST");
 if(!same(d.continuity.map(x=>x?.code),CONTINUITY)||
    d.continuity.some(x=>!obj(x)||x.assured_financing_mcad!==null||
      x.legal_review_done!==false||!x.source_type))
    bad("SOCIAL_CONTINUITY_UNVERIFIED");
 if(!same(d.scenarios.map(x=>x?.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"])||
    d.scenarios.some(s=>!obj(s)||s.legal_authority_verified!==false||
      s.independent_fiscal_review!==false||s.revenue_base_calibrated!==false||
      s.federal_transfers_assumed_retained!==false||!Array.isArray(s.annual)||
      s.annual.length!==10||s.annual.some((x,i)=>!obj(x)||x.year!==YEARS[i]||
        !keys(x,["year",...scenKeys,"external_audit_completed"])||
        !scenKeys.every(k=>x[k]===null)||x.external_audit_completed!==false)))
    bad("UNPROVEN_10_YEAR_BUDGET");
 if(!same(d.required_g015_evidence_ids,PROOFS)||
    d.open_research.length!==7||d.open_research.some(x=>x?.status!=="NON_ETABLI"))
    bad("EVIDENCE_GATES_INCOMPLETE");
 const gates=["g015_passed","g016e_passed","full_nova_budget_certified",
 "actual_savings_verified","finance_minimum_services_verified",
 "tax_rate_recommended","programme_ready_to_govern"];
 if(gates.some(k=>d.decision[k]!==false)||Object.keys(d.decision).length!==gates.length)
    bad("PREMATURE_APPROVAL");
 return {ok:errors.length===0,errors:[...new Set(errors)],programme_score:47,
  observed_tax_bases_are_incompatible_years:true,government_baseline_balances:true,
  budget_years_modelled_nova:0,confirmed_g015_proofs:0,finance_certified:false};
}
