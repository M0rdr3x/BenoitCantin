/**
 * Projet Nova–Sinjira G0.17e
 * Guide officiel TECQ, édition juillet 2026.
 * Ne certifie ni encaissements, ni budgets Nova, ni taux d'impôt.
 */
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const ids=["E01","E02","E03","E04","E05","E06","E07","E08","E09"];
const periods=[
 ["2024-01-01","2025-03-31"],["2025-04-01","2026-03-31"],
 ["2026-04-01","2027-03-31"],["2027-04-01","2028-03-31"],["2028-04-01","2028-12-31"]
];
const guard=x=>Object.values(x||{}).every(v=>v===true);
export function inspectG017e(d,priorD,priorC){
 const errors=[],bad=k=>errors.push(k);
 if(!obj(d)||d.schema!=="nova-g017e-tecq-2026-legal-eligibility-cash-gates/v1"||!obj(d.tecq_envelope)||!obj(d.staged_commitment_not_cash))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.17e"||d.score_before!==47||d.score_after!==47||d.remaining!==53||d.date!=="2026-11-08"||d.scope!=="PROGRAMME_FUNDING_CONTINUITY_NOT_FULL_TAX_REFORM")bad("SCORE_AND_SCOPE");
 if(priorD?.schema!=="nova-g017d-water-tecq-funding-protection/v1"||priorD?.score_after!==47||priorC?.schema!=="nova-g017c-water-municipal-revenue-evidence/v1"||priorC?.score_after!==47)bad("UPSTREAM");
 const s=d.sources||[];
 if(s.length!==4||s[0].id!=="GUIDE_JUL_2026"||s[0].edition!=="FOURTH"||s[0].url!=="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/infrastructures/tecq/GUI_tecq_2024_2028_juillet_2026.pdf"||s[0].pdf_screenshots_succeeded!==true||!same(s[0].visual_pdf_pages_0_index,[4,5,6,7,11,13])||s[1]?.available_newest_guide!=="2026-07"||s[2]?.path!=="data/g017d-plan-continuite-eau-et-tecq-2024-2028.json")bad("OFFICIAL_2026_JULY_PROVENANCE");
 const e=d.tecq_envelope||{};
 if(e.guide_wording!=="près de"||e.total_envelope_approx_mcad!==3316||e.federal_envelope_approx_mcad!==2226||e.quebec_envelope_approx_mcad!==1090||e.quebec_buildings_basic_additional_included_mcad!==90||e.quebec_general_mcad_approx_excluding_basic_buildings!==1000||e.federal_envelope_approx_mcad+e.quebec_envelope_approx_mcad!==e.total_envelope_approx_mcad||e.quebec_envelope_approx_mcad-e.quebec_buildings_basic_additional_included_mcad!==e.quebec_general_mcad_approx_excluding_basic_buildings||e.never_add_buildings_90m_twice!==true||e.guide_values_approx_not_bank_reconciled!==true||e.recipient_amount_verified_cad!==null||e.actual_cash_disbursed_cad!==null||e.actual_cash_received_cad!==null)bad("APPROX_ENVELOPE_NOT_CASH");
 const a=d.municipal_base_allocation_formula_from_guide||{};
 if(a.population_reference_date!=="2024-01-01"||a.small_municipality_threshold_exclusive!==6500||a.small_lump_sum_cad!==500000||a.small_per_resident_cad!==215.27||a.large_per_resident_cad!==291.33||a.population_specific_2024_verified_for_example_municipality!==null||a.category_exceptions_may_apply!==true||a.do_not_use_as_cash_forecast!==true||a.do_not_apply_to_all_municipalities_without_mergers_or_exceptions!==true)bad("BASE_FORMULA_ONLY");
 const plan=d.staged_commitment_not_cash||{},tr=plan.percentage_intervals||[];
 if(tr.length!==5||tr.some((x,i)=>x.tranche!==i+1||x.period_start!==periods[i][0]||x.period_end!==periods[i][1]||x.planned_share_pct!==20||x.recipient_approved_amount_cad!==null||x.received_bank_amount_cad!==null||x.retained_cad!==null||x.conditions_verified!==false||x.statement_is_actual_cash!==false)||tr.reduce((sum,x)=>sum+x.planned_share_pct,0)!==100||plan.planned_total_pct!==100||["unreceived_portion_rolls_forward","government_payment_depends_on_approved_programme","quebec_component_depends_on_legislative_appropriations","may_withhold_until_final_accounting_and_independent_audit","may_recover_excess_amount_after_audit","zero_is_not_missing","all_actual_cash_values_unknown"].some(k=>plan[k]!==true))bad("SCHEDULE_NEVER_CASH");
 const costs=d.eligible_and_ineligible_categories||[];
 if(costs.length!==9||costs.some((x,i)=>x.id!==ids[i])||costs.filter(x=>x.eligible_in_principle===false).length!==6||costs.slice(0,3).some(x=>x.eligible_in_principle!==true||x.conditional!==true)||costs.slice(3).some(x=>x.eligible_in_principle!==false||x.requires_separate_finance!==true)||costs[4].category!=="REGULAR_MUNICIPAL_PAYROLL")bad("RECURRING_COST_EXCLUSION");
 const deadlines=d.mandatory_dates_and_reviews||{};
 if(deadlines.works_eligibility_start!=="2024-01-01"||deadlines.works_eligibility_end!=="2028-12-31"||deadlines.annual_programme_update_window_start!=="10-01"||deadlines.annual_programme_update_window_end!=="02-15"||deadlines.asset_management_5pct_step_deadline!=="2026-12-31"||deadlines.eco_bonus_up_to_pct!==10||deadlines.eco_first_stage_bonus_up_to_pct!==5||deadlines.eco_bonus_paid_verified_cad!==null||deadlines.final_reporting_deadline!=="2029-06-30"||deadlines.independent_auditor_report_due_months_after_ministry_acceptance!==6||deadlines.remaining_scheduled_holdback_as_actual_paid_cad!==null||deadlines.verified_independent_municipal_audit_for_sample_project!==false)bad("DEADLINES_NOT_PAYMENTS");
 const c=d.cumulative_aid_accounting||{};
 const gates=["tecq_project_costs_paid_by_other_aid_must_be_excluded_from_TECQ_base","private_contributions_must_be_excluded_from_TECQ_base","total_public_support_must_not_exceed_total_direct_eligible_cost","maintenance_and_regular_payroll_outside_TECQ_eligible","local_workers_and_water_services_still_need_separate_recurring_funding","no_addition_of_two_grants_for_same_paid_cost"];
 if(gates.some(k=>c[k]!==true)||c.same_year_provincial_municipal_transfer_elimination_unverified!==true||["same_year_reconciled_eligible_cost_cad","same_year_other_aid_allocated_to_same_cost_cad","same_year_tecq_cash_cad","same_year_regular_maintenance_cad","same_year_regular_payroll_cad"].some(k=>c[k]!==null))bad("ELIGIBLE_BASE_AND_DOUBLE_COUNTS");
 const bridge=d.municipal_bridge_template||{};
 if(bridge.common_unit!=="CAD"||Object.entries(bridge).some(([k,v])=>k==="common_unit"||k==="no_2024_municipal_and_2026_provincial_addition"?false:(k==="source_year_matched"||k==="independent_accounting_review"?v!==false:v!==null))||bridge.no_2024_municipal_and_2026_provincial_addition!==true)bad("BRIDGE_UNFILLED");
 if(d.policy_gates?.length!==7||d.policy_gates.some((x,i)=>x.id!=="P0"+(i+1)||x.completed!==false))bad("POLICY_NOT_SIGNED");
 const v=d.verification||{};
 if(v.latest_public_guide_identified!==true||v.pdf_visual_verified_relevant_pages!==true||v.historical_2023_water_full_cost_known_from_upstream!==true||v.native_github_actions_success_not_established!==false||["actual_water_2024_workbook_parsed","tecq_per_municipality_cash_confirmed","federal_post_sovereignty_commitments_guaranteed","nova_taxable_income_base_reconciled","two_fiscal_scenarios_financed","audit_score_increment_earned"].some(k=>v[k]!==false))bad("NO_FAKE_CERTIFICATION");
 const ci=v.native_github_actions_validation;
 if(!obj(ci)||ci.status!=="CONFIRMED_AT_TEST_COMMIT"||ci.run_id!==42536049965
   ||ci.run_url!=="https://github.com/M0rdr3x/BenoitCantin/actions/runs/42536049965"
   ||ci.commit_sha!=="01bb9b2de54918b9b1ac0e0622db719f322eb439"
   ||ci.workflow_file!==".github/workflows/nova-sinjira-finances-tests.yml"
   ||ci.event!=="push"||ci.conclusion!=="success"
   ||ci.node_version_in_workflow!=="22.23.2"||ci.job!=="verifications"
   ||ci.job_conclusion!=="success"||ci.step!=="Verifier les calculs et la provenance"
   ||ci.step_conclusion!=="success"
   ||ci.test_command!=="node --test projets/projet-nova/tests/*.test.mjs"
   ||ci.g017e_test_file_present_at_commit!==true||ci.independent_fiscal_audit!==false
   ||ci.actual_tecq_bank_payments_verified!==false||ci.future_commit_ci_not_automatically_proven!==true)bad("CI_VERIFIED_SCOPE");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,rounded_tecq_2024_28_envelope_mcad:3316,municipality_bank_paid_verified_cad:null,recurring_maintenance_and_payroll_funded:false};
}
/** Arithmetic demonstration ONLY: official guide rates, not an actual municipality award. */
export function illustrativeMunicipalBase({year2024Population,mode}){
 if(mode!=="ILLUSTRATION_ONLY"||!Number.isSafeInteger(year2024Population)||year2024Population<0)throw Error("ILLUSTRATION_ONLY");
 const amount=year2024Population<6500?500000+215.27*year2024Population:291.33*year2024Population;
 return {baseBeforeExceptionsCad:Number(amount.toFixed(2)),isAwardApproved:false,isCashReceived:false,hasIncludedEcoBonus:false};
}
/** Synthetic proposed cost ledger, not real TECQ eligibility determination. */
export function illustrativeTecqBase({directCostsCad,otherAidSameCostsCad,privateAidSameCostsCad,mode}){
 if(mode!=="SYNTHETIC_ONLY"||![directCostsCad,otherAidSameCostsCad,privateAidSameCostsCad].every(Number.isSafeInteger)||directCostsCad<0||otherAidSameCostsCad<0||privateAidSameCostsCad<0)throw Error("SYNTHETIC_LEDGER_ONLY");
 const residual=directCostsCad-otherAidSameCostsCad-privateAidSameCostsCad;
 if(residual<0)throw Error("AID_EXCEEDS_COST");
 return {residualEligibleCostCeilingCad:residual,tecqPaymentVerified:false,actualReimbursementCad:null,legalEligibilityCertified:false};
}
