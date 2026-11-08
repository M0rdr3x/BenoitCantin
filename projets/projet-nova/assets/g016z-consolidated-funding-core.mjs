/**
 * G0.16z — modèle de consolidation de financement Nova–Sinjira.
 * Aucune projection politique ou certification d'un système fiscal à deux prélèvements.
 * TOUT montant hypothétique doit être étiqueté SYNTHETIC_ONLY.
 */
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const N=Array(10).fill(null);
const getYear=i=>String(2026+i)+"-"+String(2027+i);
const keys=["nova_income_net_yield_mcad","nova_haven_incremental_net_yield_mcad","unchanged_provincial_nontax_justified_mcad","federal_transfer_in_canada_verified_mcad","municipal_external_revenues_mcad","consolidated_municipal_and_provincial_spending_mcad","school_and_social_continuity_effect_mcad","additional_sovereign_functions_cost_mcad","sovereign_assumed_federal_tax_revenue_mcad","debt_transition_pension_cost_mcad","credit_protections_cost_mcad","net_real_public_balance_mcad"];
const nullable=x=>x===null;
export function inspectG016z(d,V,W,X,Y){
 const errors=[],bad=x=>errors.push(x);
 if(!obj(d)||d.schema!=="nova-g016z-consolidated-financing-and-transition-controls/v1"||!Array.isArray(d.official_reference_series)||!Array.isArray(d.scenario_years)||!obj(d.baseline_current_provincial_finances))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.16z"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.missing_score_points!==53||d.status!=="WORKING_FINANCIAL_FRAMEWORK_NOT_ADOPTED")bad("FALSE_PREPAREDNESS");
 if(V?.schema!=="nova-g016v-two-levies-public-finance-reference/v1"||V.programme_audit_after!==47||W?.schema!=="nova-g016w-tax-bases-distribution-municipal-gates/v1"||W.score_after!==47||X?.schema!=="nova-g016x-multilevel-fiscal-concordance/v1"||X.score_after!==47||Y?.schema!=="nova-g016y-conditional-fiscal-transition-framework/v1"||Y.score_after!==47)bad("PREVIOUS_PHASES");
 if(!Array.isArray(d.references)||d.references.length!==6||d.references.slice(0,4).some((r,i)=>r.path!==["data/cadre-financier-fiscal-g0-16v-aout-2026.json","data/g016w-assiettes-fiscales-et-garanties-distributives-2023-2024.json","data/g016x-concordance-fiscale-multiniveau-2026.json","data/g016y-loi-cadre-et-conditions-arret-2026.json"][i]))bad("REFERENCE_CHAIN");
 const b=d.baseline_current_provincial_finances,old=V.conditional_accounting;
 if(b.year!=="2026-2027"||b.unit!=="MILLIONS_CAD"||b.government_scope!=="QUEBEC_PROVINCIAL_ONLY"||b.revenue_current_mcad!==168389||b.tax_cats_current_mcad!==107161||b.assumed_remaining_other_revenue_mcad!==28182||b.assumed_current_federal_transfers_mcad!==33046||b.spending_including_debt_mcad!==171597||b.contingency_mcad!==2000||b.generations_fund_mcad!==2482||b.account_balance_current_with_reserve_mcad!==-5208||b.conditional_two_levy_balance_target_mcad!==old.canada_provincial_two_levies_accounting_target_mcad||b.conditional_two_levy_target_with_generations_mcad!==114851||b.conditional_current_tax_to_balance_gap_mcad!==5208||b.this_is_not_nova_forecast!==true||b.other_receipts_continuity_not_proven!==true||b.municipal_school_and_federal_net_replacement_not_costed!==true||b.tax_cats_current_mcad+b.assumed_remaining_other_revenue_mcad+b.assumed_current_federal_transfers_mcad!==b.revenue_current_mcad||b.spending_including_debt_mcad+b.contingency_mcad-b.assumed_remaining_other_revenue_mcad-b.assumed_current_federal_transfers_mcad!==b.conditional_two_levy_balance_target_mcad)bad("PROVINCIAL_BRIDGE");
 const arr=d.official_reference_series;
 if(arr.length!==10)bad("TEN_YEARS_HORIZON");
 for(let i=0;i<10;i++){
  const z=arr[i],p=V.government_reference.fiscal_years_official[i]??null;
  if(!obj(z)||z.year!==getYear(i)||z.source_available!==(i<5)||z.classification!==(i<5?"OFFICIAL_GOVERNMENT_FORECAST":"NO_GOVERNMENT_REFERENCE_AVAILABLE")||z.provincial_revenue_mcad!==(p?.total_government_revenue_mcad??null)||z.existing_tax_cats_mcad!==(p?.existing_tax_sources_mcad??null)||z.non_tax_receipts_assumed_mcad!==(p?.other_government_receipts_mcad??null)||z.federal_transfers_mcad!==(p?.federal_transfers_mcad??null)||z.provincial_expenses_including_debt_mcad!==(p?.government_expenditure_including_debt_service_mcad??null)||z.contingency_mcad!==(p?.contingency_provision_mcad??null)||z.generations_fund_mcad!==(p?.generations_fund_contribution_mcad??null)||z.conditional_tax_need_to_balance_account_mcad!==(p?.conditional_levies_needed_canada_provincial_account_balance_mcad??null)||z.conditional_tax_need_plus_fund_mcad!==(p?.conditional_levies_needed_canada_plus_generations_fund_mcad??null)||[z.municipal_net_new_funding_need_mcad,z.school_net_new_funding_need_mcad,z.social_protection_transition_need_mcad,z.cross_government_consolidated_balance_mcad].some(x=>x!==null))bad("REFERENCE_YEAR_"+i);
 }
 const muni=d.municipal_historical_reference;
 if(!obj(muni)||muni.year!==2023||muni.total_municipal_organization_revenues_gcad!==W.municipal_2023.total_revenues_reported_gcad||muni.property_taxes_gcad!==W.municipal_2023.property_tax_gcad||muni.transfers_from_other_governments_gcad!==W.municipal_2023.transfers_gcad||muni.comparable_to_2026_27_provincial_amounts!==false||muni.cannot_sum_without_ledger_transfer_elimination!==true||muni.replacement_of_municipal_property_tax_costed_mcad!==null)bad("MUNICIPAL_NO_DOUBLE_COUNT");
 if(d.scenario_years.length!==2||d.scenario_years.map(x=>x.id).join("|")!=="QUEBEC_CANADA|QUEBEC_SOUVERAIN"||d.scenario_years[0].federal_tax_unilaterally_repealed!==false||d.scenario_years[0].federal_transfers_guaranteed!==false||d.scenario_years[1].federal_transfers_assumed_automatically!==false||d.scenario_years[1].sovereign_federal_tax_reallocation_verified!==false||d.scenario_years.some((sc,k)=>sc.years?.length!==10||sc.certified!==false||sc.years.some((yr,i)=>yr.year!==getYear(i)||keys.some(key=>yr[key]!==null)||yr.legal_review_passed!==false||yr.economic_stress_review_passed!==false||yr.source_evidence_uri!==null)))bad("NOVA_TEN_YEAR_UNKNOWN");
 if(!Array.isArray(d.stress_test_plan)||d.stress_test_plan.map(x=>x.id).join("|")!=="CENTRAL|DOWNSIDE|UPSIDE"||d.stress_test_plan.some(x=>x.classification!=="EMPTY_TEMPLATE_NOT_CALIBRATED"||x.revenue_shock_pct!==null||x.expenses_shock_pct!==null||x.interest_shock_pct!==null||!eq(x.all_results_mcad,N)||x.validated!==false))bad("STRESS_NOT_CALIBRATED");
 const g=d.evidence_gates;
 if(!Array.isArray(g)||g.length!==14||g.some((q,i)=>q.id!=="Z"+String(i+1).padStart(2,"0")||q.passed!==false||q.evidence_uri!==null||q.independent_signoff!==false||q.blocking!==true||!q.lead_role||q.article_ids.some(a=>!Y.articles.some(x=>x.id===a))))bad("EVIDENCE_GATES_NOT_CLEARED");
 if(!Array.isArray(d.risk_register)||d.risk_register.length!==10||d.risk_register.some((x,i)=>x.id!=="R"+String(i+1).padStart(2,"0")||x.status!=="OPEN"||x.probability_calibrated!==null||x.net_cost_mcad!==null||!g.some(q=>q.id===x.gate)))bad("OPEN_RISK_REGISTER");
 if(d.hard_stop_bridge?.source!=="data/g016y-loi-cadre-et-conditions-arret-2026.json"||d.hard_stop_bridge?.all_eight_stops_active!==Y.mandatory_stops.every(x=>x.block_active===true)||d.hard_stop_bridge?.external_signoffs_missing!==true||d.hard_stop_bridge?.no_tax_repeal_authorized!==true||d.hard_stop_bridge?.no_rate_enacted!==true)bad("EIGHT_STOPS");
 if(!obj(d.model_rules)||Object.keys(d.model_rules).length!==12||Object.values(d.model_rules).some(x=>x!==true))bad("FALSE_COST_ASSUMPTIONS");
 const z=d.decision;
 if(!obj(z)||z.annual_government_reference_computed!==true||["actual_two_levy_net_receipts_known","municipal_net_replacement_financed","ten_year_canada_balance_verified","ten_year_sovereign_balance_verified","external_fiscal_legal_audit_signed","programme_adopted","ready_to_implement","point_gain_earned"].some(k=>z[k]!==false))bad("FALSE_FINANCIAL_CERTIFICATION");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,remaining:53,official_forecast_years:5,unknown_horizon_years:5,evidence_gates_open:14,risks_open:10,provincial_conditional_2026_mcad:112369,actual_nova_tax_yield_mcad:null,implementation_allowed:false};
}
const moneyKeys=["nova_income_net_yield_mcad","nova_haven_incremental_net_yield_mcad","provincial_other_external_mcad","federal_transfer_to_province_mcad","municipal_own_external_mcad","additional_external_receipts_mcad","provincial_spending_including_municipal_transfer_mcad","municipal_spending_mcad","internal_transfer_paid_mcad","internal_transfer_received_mcad","service_additional_mcad","credits_and_social_guarantees_mcad","debt_pension_transition_mcad","national_functions_cost_mcad","federal_assigned_revenue_mcad"];
/**
 * Purely synthetic accounting exercise, no incorporation of actual 2023 local revenue
 * in the 2026-27 provincial accounts and no prediction of government finances.
 */
export function consolidateSyntheticZ(x){
 if(!obj(x)||x.mode!=="SYNTHETIC_ONLY"||x.unit!=="MILLIONS_CAD"||!["QUEBEC_CANADA","QUEBEC_SOUVERAIN"].includes(x.scenario)||x.claims_real_government_model!==false)throw Error("SYNTHETIC_ONLY");
 if(moneyKeys.some(k=>!Number.isFinite(x[k])||x[k]<0))throw Error("INVALID_MONETARY_INPUTS");
 if(x.internal_transfer_paid_mcad!==x.internal_transfer_received_mcad)throw Error("INTERNAL_TRANSFER_MISMATCH");
 if(x.internal_transfer_paid_mcad>x.provincial_spending_including_municipal_transfer_mcad)throw Error("IMPOSSIBLE_INTERNAL_TRANSFER");
 if(x.scenario==="QUEBEC_CANADA"&&(x.federal_assigned_revenue_mcad!==0||x.national_functions_cost_mcad!==0))throw Error("FEDERAL_JURISDICTION_NOT_TRANSFERRED");
 if(x.scenario==="QUEBEC_SOUVERAIN"&&x.federal_transfer_to_province_mcad!==0&&x.signed_transfer_treaty_proven!==true)throw Error("SOVEREIGN_TRANSFERS_NOT_PROVEN");
 const receipts=x.nova_income_net_yield_mcad+x.nova_haven_incremental_net_yield_mcad+x.provincial_other_external_mcad+x.federal_transfer_to_province_mcad+x.municipal_own_external_mcad+x.additional_external_receipts_mcad+x.federal_assigned_revenue_mcad;
 const expense=x.provincial_spending_including_municipal_transfer_mcad+x.municipal_spending_mcad-x.internal_transfer_paid_mcad+x.service_additional_mcad+x.credits_and_social_guarantees_mcad+x.debt_pension_transition_mcad+x.national_functions_cost_mcad;
 return {classification:"SYNTHETIC_ONLY_NOT_FORECAST",total_external_receipts_mcad:Math.round(receipts*100)/100,consolidated_spending_mcad:Math.round(expense*100)/100,internal_transfer_removed_mcad:x.internal_transfer_paid_mcad,balance_mcad:Math.round((receipts-expense)*100)/100,real_nova_policy_financed:false,legal_approval:false,purchasing_power_verified:false};
}
export function stressSyntheticZ(base,shocks){
 if(!obj(shocks)||shocks.mode!=="SYNTHETIC_ONLY"||!Number.isFinite(shocks.income_receipts_shock_pct)||!Number.isFinite(shocks.total_spending_shock_pct)||!Number.isFinite(shocks.additional_debt_service_mcad)||shocks.income_receipts_shock_pct< -100||shocks.income_receipts_shock_pct>100||shocks.total_spending_shock_pct< -100||shocks.total_spending_shock_pct>100||shocks.additional_debt_service_mcad<0)throw Error("INVALID_HYPOTHETICAL_STRESS");
 const x={...base,nova_income_net_yield_mcad:base.nova_income_net_yield_mcad*(1+shocks.income_receipts_shock_pct/100),provincial_spending_including_municipal_transfer_mcad:base.provincial_spending_including_municipal_transfer_mcad*(1+shocks.total_spending_shock_pct/100),debt_pension_transition_mcad:base.debt_pension_transition_mcad+shocks.additional_debt_service_mcad};
 const result=consolidateSyntheticZ(x);
 return {...result,classification:"SYNTHETIC_STRESS_ONLY_NOT_FORECAST",shock_assumptions:shocks};
}
