/**
 * Projet Nova G0.17d — sécurité du financement des services municipaux.
 * TECQ: enveloppe publique >3.3 G$, PAS encaissements.
 * Water 2024 XLSX: fichier annoncé par MAMH, octets non accessibles, valeurs INCONNUES.
 */
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const NO_TAX_RATE=null;
export function inspectG017d(d,upstream,z){
 const errors=[],bad=s=>errors.push(s);
 if(!obj(d)||d.schema!=="nova-g017d-water-tecq-funding-protection/v1"||!obj(d.tecq_2024_2028)||!obj(d.water_database_2024))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.17d"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.points_remaining!==53||d.assumptions_reviewed_independently!==false||d.legislation_adopted!==false||d.real_financing_confirmed!==false)bad("UNSUPPORTED_AUDIT_SCORE");
 if(upstream?.schema!=="nova-g017c-water-municipal-revenue-evidence/v1"||upstream?.score_after!==47||z?.schema!=="nova-g016z-consolidated-financing-and-transition-controls/v1"||z?.score_after!==47)bad("PRIOR_RECONCILIATION");
 const sources=d.official_sources;
 if(!Array.isArray(sources)||sources.length!==8||sources[0].url!=="https://www.quebec.ca/gouvernement/ministeres-organismes/affaires-municipales/publications/strategie-economie-potable/cartographie-avancement-strategie"||sources[0].publication_date!=="2026-07-30"||sources[0].binary_downloaded!==false||sources[0].spreadsheet_rows_read!==false||sources[1].url!=="https://www.quebec.ca/habitation-territoire/infrastructures-municipales/programmes/eau-potable-eaux-usees/programme-transfert-infrastructures-eau-collectives-quebec-tecq-2024-2028"||sources[1].known_as_envelope_not_cash!==true||sources[1].actual_paid_by_municipality_unknown!==true)bad("GOVERNMENT_PROVENANCE");
 const t=d.tecq_2024_2028;
 if(t.program_id!=="TECQ_2024_2028"||t.period_start!=="2024-01-01"||t.period_end!=="2028-12-31"||t.final_reporting_deadline!=="2029-06-30"||t.total_approved_support_lower_bound_mcad!==3300||t.federal_support_lower_bound_mcad!==2200||t.quebec_contribution_announced_mcad!==1000||t.exact_current_envelope_mcad!==null||t.exact_federal_component_mcad!==null||t.funding_disbursed_mcad!==null||t.recipient_by_recipient_bank_receipts_verified!==false||t.not_all_teqc_construction_is_water!==true||t.municipal_project_approval_required!==true||!eq(t.annual_program_update_window,{from_month_day:"10-01",to_month_day:"02-15"})||["preexisting_tecq_2019_2024_closing_required","local_public_infrastructure_ownership_or_qualifying_tenure_required","local_autonomous_investments_mandatory","final_invoice_and_audit_before_closure","cannot_add_teqc_envelope_to_water_2023_cost_as_incremental_revenue","cannot_add_federal_envelope_to_2026_quebec_provincial_budget_as_new_money","federal_share_not_guaranteed_in_sovereign_scenario","primeau_and_tecq_same_cost_double_claim_prohibited"].some(k=>t[k]!==true))bad("GRANT_ENVELOPE_NOT_CASH");
 const w=d.water_database_2024;
 if(w.listing_verified!==true||w.release_date!=="2026-07-30"||w.binary_file_download_attempted!==true||w.binary_file_downloaded!==false||w.source_version_hash_sha256!==null||w.download_error!=="NAME_RESOLUTION_FAILURE_IN_RUNTIME"||["water_2024_actual_full_cost_gcad","water_2024_actual_assigned_revenues_gcad","water_2024_actual_coverage_pct","water_2025_full_cost_gcad"].some(k=>w[k]!==null)||w.future_water_cost_indexation_model_validated!==false||w.cannot_copy_2023_40pct_as_2024_coverage!==true||w.source_year_and_report_year_distinct!==true)bad("WATER_2024_NOT_PARSED");
 const h=d.historical_context_from_g017c;
 if(!obj(h)||h.municipal_consolidated_revenue_2024_gcad!==upstream.municipal.total_revenue_gcad||h.municipal_federal_and_provincial_transfers_2024_gcad!==7.4||h.municipal_property_tax_2024_gcad!==15||h.water_2023_full_cost_approx_gcad!==upstream.water.reported_approx_full_service_cost_gcad||h.water_2023_water_allocated_revenue_approx_gcad!==upstream.water.reported_approx_annual_revenue_gcad||h.water_2023_uncovered_full_cost_approx_gcad!==upstream.water.calculated_illustrative_uncovered_full_cost_gcad||h.all_amounts_different_years_or_scopes!==true||h.municipal_2024_transfers_include_multiple_programmes_not_assigned_to_TECQ!==true||h.no_cash_gap_inferred_from_water_full_cost!==true)bad("HISTORICAL_ACCOUNTING_SCOPE");
 const p=d.conditional_policy_proposal;
 if(!obj(p)||p.status!=="DRAFT_CONDITIONAL_NOVA_POLICY_NOT_ADOPTED"||p.not_a_new_third_tax!==true||p.no_new_tariff_substituting_hidden_tax_without_legal_review!==true||p.ledger_eliminate_internal_province_municipal_transfer!==true||p.public_project_registry_and_receipt_audit_required!==true||p.no_cut_services_or_firing_local_workers_to_assume_balance!==true||p.benefit_for_households_untested!==true||p.formal_agreements_required!==true||p.permitted_financing_sources?.length!==4||p.allocation_basis?.length!==6)bad("NOT_APPROVED_MUNICIPAL_FUND");
 const steps=d.funding_trace_rules;
 if(!Array.isArray(steps)||steps.length!==8||steps.map(x=>x.id).join("|")!=="A|B|C|D|E|F|G|H"||steps.map(x=>x.step).join("|")!=="IDENTIFY_EXISTING_PROGRAM|ESTABLISH_LEGAL_ELIGIBILITY|CERTIFY_COMMITTED_AMOUNT|VERIFY_ACTUAL_EXPENDITURE|VERIFY_GOVERNMENT_CASH|VERIFY_MUNICIPAL_CASH|ELIMINATE_INTERNAL_TRANSFERS|GUARANTEE_SERVICE_AND_ASSETS")bad("TRACE_CHAIN");
 const sc=d.two_status_scenarios;
 if(!Array.isArray(sc)||sc.length!==2||sc[0].id!=="QUEBEC_CANADA"||sc[1].id!=="QUEBEC_SOUVERAIN"||sc[0].federal_support_continuation_per_applicable_law_and_agreements!=="UNVERIFIED_FOR_NOVA_REFORM"||sc[1].federal_support_after_sovereignty!=="NOT_AUTOMATIC"||sc[1].federal_envelope_imputed_as_new_cost_mcad!==null||sc[1].negotiated_legacy_funding_and_assigned_assets_verified!==false||sc.some(x=>x.new_nova_income_tax_rate_pct!==NO_TAX_RATE||x.verified_ten_year_balances!==null||x.municipal_service_continuity_certified!==false))bad("CONSTITUTIONAL_GAPS");
 if(d.tests_needed_before_score_increase?.length!==6||d.tests_needed_before_score_increase.some((x,i)=>x.id!=="T0"+(i+1)||x.passed!==false))bad("UNPASSED_AUDIT_GATES");
 const x=d.decisions;
 if(!obj(x)||x.official_water_2024_workbook_identified!==true||x.tecq_official_program_and_conditions_verified!==true||x.source_backed_policy_safeguards_drafted!==true||["actual_water_2024_workbook_read","tecq_payments_verified","federal_replacement_cost_certified","actual_provincial_municipal_net_2026_balance_certified","programme_score_rise_earned"].some(k=>x[k]!==false))bad("NO_UNEARNED_COMPLETENESS");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,minimum_tecq_envelope_mcad:3300,actual_tecq_cash_mcad:null,water_2024_cost_gcad:null,nova_10_year_balances_verified:false};
}
// Computes ONLY logical readiness from *declared* verified inputs, never an unverified amount.
// Accounting equality must compare the SAME period, scope and treatment of transfers.
export function checkContinuityGate(x){
 if(!obj(x)||x.mode!=="CONDITIONAL_HYPOTHETICAL_ONLY")throw Error("HYPOTHETICAL_ONLY");
 const flags=["source_immutable","year_and_scope_reconciled","provider_payments_verified","municipal_receipts_verified","transfers_eliminated_once","legal_power_checked","workers_protected","water_asset_maintenance_funded","household_incidence_checked","independent_audit_signed"];
 if(flags.some(k=>typeof x[k]!=="boolean"))throw Error("MISSING_VERIFICATION_BOOLEAN");
 const funded=flags.every(k=>x[k]===true);
 return {all_gates_satisfied:funded,proposal_approved:false,taxes_abolishable_now:false,official_money_paid_proven_by_this_function:false,missing_gates:flags.filter(k=>x[k]===false)};
}
