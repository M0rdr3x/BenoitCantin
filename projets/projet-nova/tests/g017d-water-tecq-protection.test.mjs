import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG017d,checkContinuityGate} from "../assets/g017d-water-tecq-protection-core.mjs";
const read=async name=>JSON.parse(await readFile(new URL("../data/"+name,import.meta.url),"utf8"));
const [d,c,z]=await Promise.all([
 read("g017d-plan-continuite-eau-et-tecq-2024-2028.json"),
 read("g017c-recettes-municipales-2024-et-couts-eau-2023.json"),
 read("g016z-financement-consolide-et-protections-2026-2036.json")
]);
const reject=(mut,key)=>{const x=structuredClone(d);mut(x);const o=inspectG017d(x,c,z);assert.equal(o.ok,false,o.errors.join("|"));assert.ok(o.errors.includes(key),o.errors.join("|"));};
const flags={
 mode:"CONDITIONAL_HYPOTHETICAL_ONLY",
 source_immutable:true,year_and_scope_reconciled:true,provider_payments_verified:true,municipal_receipts_verified:true,
 transfers_eliminated_once:true,legal_power_checked:true,workers_protected:true,water_asset_maintenance_funded:true,
 household_incidence_checked:true,independent_audit_signed:true
};
test("G0.17d source and fiscal controls pass",()=>assert.equal(inspectG017d(d,c,z).ok,true));
test("Program score remains 47",()=>assert.equal(inspectG017d(d,c,z).score,47));
test("Fifty-three points still unearned",()=>assert.equal(d.points_remaining,53));
test("Water 2024 data officially published in 2026",()=>assert.equal(d.water_database_2024.release_date,"2026-07-30"));
test("2024 water XLSX is listed",()=>assert.equal(d.water_database_2024.listing_verified,true));
test("Water workbook was not downloaded",()=>assert.equal(d.water_database_2024.binary_file_downloaded,false));
test("Water workbook SHA-256 unknown",()=>assert.equal(d.water_database_2024.source_version_hash_sha256,null));
test("Water 2024 full costs remain unknown",()=>assert.equal(d.water_database_2024.water_2024_actual_full_cost_gcad,null));
test("Water 2024 coverage not inherited from 2023",()=>assert.equal(d.water_database_2024.water_2024_actual_coverage_pct,null));
test("Water 2025 costs also remain unknown",()=>assert.equal(d.water_database_2024.water_2025_full_cost_gcad,null));
test("TECQ timeframe starts 2024",()=>assert.equal(d.tecq_2024_2028.period_start,"2024-01-01"));
test("TECQ timeframe ends 2028",()=>assert.equal(d.tecq_2024_2028.period_end,"2028-12-31"));
test("TECQ reporting June 2029",()=>assert.equal(d.tecq_2024_2028.final_reporting_deadline,"2029-06-30"));
test("TECQ > 3.3G announced—not 3.3G in cash",()=>assert.equal(d.tecq_2024_2028.total_approved_support_lower_bound_mcad,3300));
test("Federal > 2.2G announced—not sovereign guaranteed",()=>assert.equal(d.tecq_2024_2028.federal_support_lower_bound_mcad,2200));
test("Quebec 1.0G component described",()=>assert.equal(d.tecq_2024_2028.quebec_contribution_announced_mcad,1000));
test("No precise disbursed TECQ amount recorded",()=>assert.equal(d.tecq_2024_2028.funding_disbursed_mcad,null));
test("No exact federal component invented",()=>assert.equal(d.tecq_2024_2028.exact_federal_component_mcad,null));
test("Municipal program update is annual",()=>assert.deepEqual(d.tecq_2024_2028.annual_program_update_window,{from_month_day:"10-01",to_month_day:"02-15"}));
test("No double program cost claiming with PRIMEAU",()=>assert.equal(d.tecq_2024_2028.primeau_and_tecq_same_cost_double_claim_prohibited,true));
test("Water 2023 6G remains only historical context",()=>assert.equal(d.historical_context_from_g017c.water_2023_full_cost_approx_gcad,6));
test("Municipal 2024 31.3G remains only historical context",()=>assert.equal(d.historical_context_from_g017c.municipal_consolidated_revenue_2024_gcad,31.3));
test("TECQ share cannot be equated to 2024 transfers",()=>assert.equal(d.historical_context_from_g017c.municipal_2024_transfers_include_multiple_programmes_not_assigned_to_TECQ,true));
test("Draft municipal fund is not adopted",()=>assert.equal(d.conditional_policy_proposal.status,"DRAFT_CONDITIONAL_NOVA_POLICY_NOT_ADOPTED"));
test("No concealed third fiscal instrument",()=>assert.equal(d.conditional_policy_proposal.not_a_new_third_tax,true));
test("Independent review must protect labor",()=>assert.equal(d.conditional_policy_proposal.no_cut_services_or_firing_local_workers_to_assume_balance,true));
test("Public spending must eliminate internal transfers",()=>assert.equal(d.conditional_policy_proposal.ledger_eliminate_internal_province_municipal_transfer,true));
test("Fiscal commitments not treated as taxpayer benefits",()=>assert.equal(d.conditional_policy_proposal.benefit_for_households_untested,true));
test("Proof chain has eight stages",()=>assert.equal(d.funding_trace_rules.length,8));
test("Canada case not prevalidated",()=>assert.equal(d.two_status_scenarios[0].municipal_service_continuity_certified,false));
test("Sovereignty case does not automatically inherit federal transfers",()=>assert.equal(d.two_status_scenarios[1].federal_support_after_sovereignty,"NOT_AUTOMATIC"));
test("No imputed federal replacement cost",()=>assert.equal(d.two_status_scenarios[1].federal_envelope_imputed_as_new_cost_mcad,null));
test("No 10-year fiscal balance invented",()=>assert.ok(d.two_status_scenarios.every(x=>x.verified_ten_year_balances===null)));
test("Six independent validations not passed",()=>assert.ok(d.tests_needed_before_score_increase.length===6&&d.tests_needed_before_score_increase.every(x=>!x.passed)));
test("Partial synthetic gates refuse readiness",()=>assert.equal(checkContinuityGate({...flags,provider_payments_verified:false}).all_gates_satisfied,false));
test("Missing proof category listed",()=>assert.ok(checkContinuityGate({...flags,source_immutable:false}).missing_gates.includes("source_immutable")));
test("Even all synthetic flags never authorize tax abolition",()=>assert.equal(checkContinuityGate(flags).taxes_abolishable_now,false));
test("Even all synthetic flags never certify a program",()=>assert.equal(checkContinuityGate(flags).proposal_approved,false));
test("No synthetic claim of confirmed bank payment",()=>assert.equal(checkContinuityGate(flags).official_money_paid_proven_by_this_function,false));
test("Calling with policy authorization mode is rejected",()=>assert.throws(()=>checkContinuityGate({...flags,mode:"APPROVED_LAW"}),/HYPOTHETICAL_ONLY/));
test("Missing gate boolean is rejected",()=>assert.throws(()=>checkContinuityGate({...flags,source_immutable:null}),/MISSING_VERIFICATION_BOOLEAN/));
test("Reject score of 48 without audit",()=>reject(x=>x.score_after=48,"UNSUPPORTED_AUDIT_SCORE"));
test("Reject invented 2024 workbook download",()=>reject(x=>x.water_database_2024.binary_file_downloaded=true,"WATER_2024_NOT_PARSED"));
test("Reject fake 2024 water cost",()=>reject(x=>x.water_database_2024.water_2024_actual_full_cost_gcad=6.5,"WATER_2024_NOT_PARSED"));
test("Reject false current TECQ exact envelope",()=>reject(x=>x.tecq_2024_2028.exact_current_envelope_mcad=3300,"GRANT_ENVELOPE_NOT_CASH"));
test("Reject falsely paid grant amount",()=>reject(x=>x.tecq_2024_2028.funding_disbursed_mcad=3300,"GRANT_ENVELOPE_NOT_CASH"));
test("Reject automatic federal sovereign funding",()=>reject(x=>x.two_status_scenarios[1].federal_support_after_sovereignty="GUARANTEED","CONSTITUTIONAL_GAPS"));
test("Reject invented federal replacement calculation",()=>reject(x=>x.two_status_scenarios[1].federal_envelope_imputed_as_new_cost_mcad=2200,"CONSTITUTIONAL_GAPS"));
test("Reject double-count with PRIMEAU",()=>reject(x=>x.tecq_2024_2028.primeau_and_tecq_same_cost_double_claim_prohibited=false,"GRANT_ENVELOPE_NOT_CASH"));
test("Reject hidden new tax substituted as fee",()=>reject(x=>x.conditional_policy_proposal.no_new_tariff_substituting_hidden_tax_without_legal_review=false,"NOT_APPROVED_MUNICIPAL_FUND"));
test("Reject removal of salary protection",()=>reject(x=>x.conditional_policy_proposal.no_cut_services_or_firing_local_workers_to_assume_balance=false,"NOT_APPROVED_MUNICIPAL_FUND"));
test("Reject fictitious sign-off",()=>reject(x=>x.tests_needed_before_score_increase[0].passed=true,"UNPASSED_AUDIT_GATES"));
test("Reject certified program without independent audit",()=>reject(x=>x.decisions.programme_score_rise_earned=true,"NO_UNEARNED_COMPLETENESS"));
