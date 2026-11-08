// Projet Nova–Sinjira G0.16v. Référence : rapport préélectoral Québec, août 2026.
// Note essentielle : scénario arithmétique conditionnel ≠ politique fiscale financée.
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const official=[
 ["2026-2027",50942,9538,14698,1301,30682,5908,6484,15790,33046,168389,171597,2000,2482,-5208,-7690,0],
 ["2027-2028",52841,9876,15252,1367,31632,6208,6928,16110,34011,174225,175919,1500,2501,-3194,-5695,0],
 ["2028-2029",54861,10327,15240,1426,32416,6909,7278,16744,33643,178844,178068,1500,2626,-724,-1500,1850],
 ["2029-2030",56867,10628,15835,1479,33206,6653,7586,17385,32802,182441,180151,1500,2790,790,0,2000],
 ["2030-2031",59006,10962,16875,1531,34035,7035,7823,17988,33757,189012,186333,1500,2929,1179,250,2000]
];
const keys=["fiscal_year","person_income_tax_mcad","employer_health_contributions_mcad","corporate_income_tax_mcad","school_property_tax_mcad","consumption_taxes_mcad","government_enterprises_mcad","rights_permits_royalties_mcad","miscellaneous_revenue_mcad","federal_transfers_mcad","total_government_revenue_mcad","government_expenditure_including_debt_service_mcad","contingency_provision_mcad","generations_fund_contribution_mcad","pre_gap_accounting_result_mcad","balanced_budget_act_result_mcad","remaining_adjustment_to_find_mcad"];
const emptyDecadeFields=["nova_personal_and_corporate_tax_base_mcad","nova_verified_tax_haven_levy_yield_mcad","nova_levy_effective_rate_pct","nova_operating_cost_complete_mcad","nova_municipal_replacement_cost_mcad","nova_federal_functions_cost_mcad","nova_debt_transition_and_pension_cost_mcad","nova_income_distribution_effects","nova_annual_balance_mcad"];
const forecast=(r,k)=>r[k];
export function inspectG016v(d,u){
 const errors=[],fail=k=>errors.push(k);
 if(!obj(d)||d.schema!=="nova-g016v-two-levies-public-finance-reference/v1"||!obj(d.government_reference)||!obj(d.nova_design_constraints)||!obj(d.conditional_accounting))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.16v"||d.date!=="2026-11-08"||d.programme_audit_before!==47||d.programme_audit_after!==47||d.program_is_financially_certified!==false||d.party_adoption!==false||d.quantitative_unit!=="millions_de_dollars_canadiens_mcad")fail("FALSE_PREPAREDNESS");
 if(u?.schema!=="nova-g016u-evidence-requests-and-completion-gates/v1"||u?.program_score_after!==47||u?.program_percent_remaining!==53)fail("AUDIT_47_SOURCE");
 if(!Array.isArray(d.reference_sources)||d.reference_sources.length!==5||d.reference_sources[0].url!=="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf"||!same(d.reference_sources[0].pdf_pages_checked_visually,[9,19,42])||d.reference_sources[1].type!=="EXTERNAL_REVIEW_OF_GOVERNMENT_PLAUSIBILITY_NOT_PROJET_NOVA"||d.reference_sources[3].path!=="data/g016u-plan-acces-preuves-et-fermeture-53-points.json")fail("OFFICIAL_PROVENANCE");
 const g=d.government_reference,ys=g.fiscal_years_official;
 if(!Array.isArray(ys)||ys.length!==5||!same(g.three_year_forecasts_externally_plausibility_reviewed,["2026-2027","2027-2028","2028-2029"])||g.horizons_later_than_2030_2031_official!==null)fail("HORIZON_SCOPE");
 for(let i=0;i<5;i++){
  const y=ys?.[i],fixed=official[i];
  if(!obj(y)){fail("OFFICIAL_YEAR_"+i);continue;}
  if(fixed.some((v,j)=>y[keys[j]]!==v)||y.classification!=="GOVERNMENT_FORECAST_NOT_NOVA_AND_NOT_REALIZED_ACTUAL"||y.verifier_general_plausibility_review_2026_2028_only!==(i<3))fail("OFFICIAL_YEAR_"+i);
  const T=y.person_income_tax_mcad+y.employer_health_contributions_mcad+y.corporate_income_tax_mcad+y.school_property_tax_mcad+y.consumption_taxes_mcad;
  const O=y.government_enterprises_mcad+y.rights_permits_royalties_mcad+y.miscellaneous_revenue_mcad;
  if(y.existing_tax_sources_mcad!==T||y.other_government_receipts_mcad!==O||y.revenue_components_reconciliation_mcad!==T+O+y.federal_transfers_mcad||y.total_government_revenue_mcad!==T+O+y.federal_transfers_mcad||y.pre_gap_accounting_result_mcad!==y.total_government_revenue_mcad-y.government_expenditure_including_debt_service_mcad-y.contingency_provision_mcad||y.balanced_budget_act_result_mcad!==y.pre_gap_accounting_result_mcad+y.remaining_adjustment_to_find_mcad-y.generations_fund_contribution_mcad)fail("FINANCE_RECONCILIATION_"+i);
  const need=y.government_expenditure_including_debt_service_mcad+y.contingency_provision_mcad-O-y.federal_transfers_mcad;
  if(y.conditional_levies_needed_canada_provincial_account_balance_mcad!==need||y.conditional_levies_needed_canada_plus_generations_fund_mcad!==need+y.generations_fund_contribution_mcad||y.conditional_no_federal_transfer_same_provincial_spending_mcad!==need+y.federal_transfers_mcad)fail("CONDITIONAL_GAPS_"+i);
  if(y.caveats?.length!==9)fail("MISSING_SCOPE_WARNINGS_"+i);
 }
 const constraints=d.nova_design_constraints;
 if(constraints.max_count_of_policy_tax_instruments!==2||constraints.instrument_1?.id!=="INCOME"||constraints.instrument_2?.id!=="TAX_HAVEN"||constraints.instrument_1.forecast_revenue_mcad!==null||constraints.instrument_2.forecast_revenue_mcad!==null||constraints.instrument_1.net_base_after_dividends_and_cross_border_adjustments_mcad!==null||constraints.instrument_2.verified_base_mcad!==null||constraints.instrument_2.verified_recovered_revenue_mcad!==null||constraints.other_government_revenue_preserved_assumption_not_validated!==true||constraints.expenses_and_services_preserved_assumption_not_validated!==true||constraints.no_retalitory_tariffs!==true||constraints.protect_workers!==true||constraints.protect_services!==true||constraints.municipal_property_tax_replacement_in_provincial_budget!==false||constraints.existing_federal_tax_abrogation_by_quebec_within_canada!==false||constraints.no_savings_assumed!==true||constraints.no_fake_foreign_levy_revenue!==true)fail("TWO_LEVY_SCOPE");
 if(!Array.isArray(d.scenarios)||d.scenarios.length!==2||d.scenarios.map(x=>x.id).join("|")!=="QUEBEC_CANADA|QUEBEC_SOUVERAIN"||d.scenarios[0].scope!=="PROVINCIAL_ONLY_REFERENCE_CASE"||d.scenarios[1].scope!=="INCOMPLETE_POST_SOVEREIGN_CONSTITUTIONAL_SCENARIO"||d.scenarios.some(x=>x.government_fiscal_reference_used!==true||x.years?.length!==10||x.years.some((y,i)=>y.fiscal_year!==String(2026+i)+"-"+String(2027+i)||y.official_quebec_forecast_available!==(i<5)||y.official_reference_total_revenue_mcad!==(i<5?ys[i].total_government_revenue_mcad:null)||y.official_reference_total_expenditure_mcad!==(i<5?ys[i].government_expenditure_including_debt_service_mcad:null)||y.nova_external_fiscal_audit_passed!==false||emptyDecadeFields.some(k=>y[k]!==null))))fail("DECADE_WITH_GAPS");
 const c=d.conditional_accounting,b=ys[0];
 if(c.first_fiscal_year!=="2026-2027"||c.current_tax_sources_mcad!==b.existing_tax_sources_mcad||c.remaining_non_tax_receipts_assumed_mcad!==b.other_government_receipts_mcad||c.federal_transfers_assumed_mcad!==b.federal_transfers_mcad||c.expenditure_plus_provision_mcad!==b.government_expenditure_including_debt_service_mcad+b.contingency_provision_mcad||c.canada_provincial_two_levies_accounting_target_mcad!==112369||c.canada_provincial_two_levies_target_with_generations_fund_mcad!==114851||c.sovereign_zero_federal_transfers_same_provincial_spending_stress_mcad!==145415||c.sovereign_stress_is_not_cost_of_full_sovereign_government!==true||c.tax_base_and_anti_haven_yield_are_not_verified!==true||c.no_nova_tax_rate_can_be_inferred!==true||c.no_proposed_tax_rate_pct!==null||c.zero_bank_cash_claims!==true)fail("FIRST_YEAR_STRESS_NOT_POLICY");
 if(!Array.isArray(d.open_gates)||d.open_gates.length!==9||d.open_gates.some((x,i)=>x.id!=="F"+String(i+1).padStart(2,"0")||x.verified!==false))fail("NINE_FINANCIAL_GATES");
 const decisions=d.decisions;
 if(!obj(decisions)||decisions.official_government_five_year_forecast_integrated!==true||decisions.independently_reviewed_official_government_assumptions_not_nova!==true||decisions.government_2026_27_accounting_reconciliation_verified!==true||["nova_income_taxable_base_estimated","nova_tax_haven_levy_yield_estimated","provincial_municipal_federal_fiscal_consolidation_done","costed_sovereignty_model_verified","nova_fiscal_rate_approved","independent_nova_financial_audit_done","score_increment_earned"].some(k=>decisions[k]!==false))fail("FALSE_CERTIFICATION");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,years_official:5,years_without_official_forecast:5,conditional_provincial_need_mcad:112369,verified_nova_tax_rate_pct:null};
}
// Sensibilité mathématique seulement : n'établit aucune assiette ni taux légal, ni l'égalité des incidences.
export function illustrativeEffectiveRate({required_mcad,tax_base_mcad,anti_haven_yield_mcad,mode}){
 if(mode!=="HYPOTHETICAL_ONLY"||![required_mcad,tax_base_mcad,anti_haven_yield_mcad].every(Number.isFinite)||required_mcad<0||tax_base_mcad<=0||anti_haven_yield_mcad<0||anti_haven_yield_mcad>required_mcad)throw new Error("HYPOTHETICAL_INPUTS_ONLY");
 return {hypothetical_effective_pct:Number(((required_mcad-anti_haven_yield_mcad)/tax_base_mcad*100).toFixed(4)),rate_approved:false,distribution_test_passed:false,legal_compliance_passed:false,can_be_used_as_government_rate:false};
}
