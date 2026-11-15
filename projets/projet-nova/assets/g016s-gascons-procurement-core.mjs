// G0.16s — contrôleur fiscal et documentaire : autorisé ≠ payé; contrats ≠ facture finale.
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const cents=x=>Math.round(x*100);
const awards=[50484372.75,2440775.53,754236];
const certificates=[
 {id:"D02",num:"2",date:"2025-09-08",amount:2715347.20,source:"S04_SEP"},
 {id:"D03",num:"3",date:"2025-10-01",amount:2446515.19,source:"S05_OCT"},
 {id:"D04",num:"4",date:"2025-11-10",amount:4683742.36,source:"S06_NOV"},
 {id:"D05",num:"5",date:"2025-12-08",amount:5468034.54,source:"S07_DEC"},
 {id:"D07",num:"7",date:"2026-02-10",amount:98583.36,source:"S08_FEB"}
];
const total=certificates.reduce((s,x)=>s+cents(x.amount),0)/100;
export function auditG016s(d,r){
 const errors=[],fail=k=>errors.push(k);
 if(!object(d)||d.schema!=="nova-g016s-gascons-contracts-and-payment-authorizations/v1"||!object(d.contract_awards)||!object(d.council_authorizations)||!object(d.funding_and_scope))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.16s"||d.date!=="2026-11-08"||d.audit_completion_before!==47||d.audit_completion_after!==47||d.program_adopted!==false||d.independent_program_audit!==false)fail("FALSE_COMPLETENESS");
 if(r?.schema!=="nova-g016r-port-daniel-2025-audited-qualified/v1"||r?.score_after!==47||r?.case!=="PORT_DANIEL_GASCONS_02047")fail("PRIOR_FINANCIAL_RECORD");
 if(d.municipality!=="Port-Daniel–Gascons"||!Array.isArray(d.sources)||d.sources.length!==12||d.sources[0].url!=="https://munpdg.ca/wp-content/uploads/2025/07/proces-verbal-de-la-seance-extraordinaire-du-16-juin.pdf"||d.sources.slice(0,8).some(s=>s.pdf_screenshot!=="CACHE_MISS"||s.text_extract_seen!==true)||d.sources[8].updated!=="2026-03-18")fail("SOURCE_TRACEABILITY");
 const a=d.contract_awards;
 if(a.council_date!=="2025-06-16"||!equal(a.municipal_resolution_numbers,["2025-06-164","2025-06-165","2025-06-166"])||a.amount_basis!=="CAD_GROSS_INCLUDING_TAXES"||!Array.isArray(a.items)||a.items.length!==3||a.items.some((x,i)=>x.id!=="A0"+(i+1)||cents(x.award_cad)!==cents(awards[i])||x.source_id!=="S01_JUNE_AWARDS")||cents(a.selected_awards_sum_cad)!==cents(53679384.28)||cents(a.items.reduce((s,x)=>s+x.award_cad,0))!==cents(a.selected_awards_sum_cad)||a.total_lifetime_project_cost_cad!==null||a.amount_paid_against_contracts_cad!==null||a.amendments_and_change_orders_verified!==false||a.contract_tax_recoverability_verified!==false||a.awards_are_not_paid_expenditure!==true)fail("CONTRACT_AWARD_NOT_CASH");
 const c=d.council_authorizations;
 if(c.classification!=="COUNCIL_AUTHORISATIONS_BASIS_PRE_TAX_NOT_BANK_CONFIRMED"||!Array.isArray(c.rows)||c.rows.length!==5||c.rows.some((x,i)=>x.id!==certificates[i].id||x.certificate_no!==certificates[i].num||x.date!==certificates[i].date||cents(x.amount_pre_tax_cad)!==cents(certificates[i].amount)||x.source_id!==certificates[i].source||x.paid_bank_confirmed!==false)||cents(c.numbered_selected_total_pre_tax_cad)!==cents(total)||cents(c.rows.reduce((s,x)=>s+x.amount_pre_tax_cad,0))!==cents(total))fail("PROGRESS_AUTHORISATIONS");
 const u=c.unnumbered_sample;
 if(!object(u)||u.date!=="2025-08-11"||u.resolution!=="2025-08-202"||u.source_id!=="S03_AUG"||u.certificate_no!==null||u.amount_pre_tax_cad!==450368.10||u.included_in_numbered_total!==false||u.possible_overlap_not_ruled_out!==true||u.paid_bank_confirmed!==false||!equal(c.missing_certificate_numbers,[1,6])||c.all_progress_certificates_verified!==false||c.total_invoice_value_to_date_cad!==null||c.project_bank_cash_outflow_verified_cad!==null||c.vendor_bank_receipts_verified_cad!==null||c.authorization_is_not_proof_of_payment!==true||c.different_2025_2026_periods_do_not_prove_2025_total!==true)fail("NOT_BANK_VERIFIED");
 const f=d.funding_and_scope,g=f?.government_dashboard;
 if(!object(f)||f.bylaw_draft_resolution_date!=="2025-06-05"||f.regulation!=="2025-01"||f.works_and_envelope_cad!==56596000||f.proposed_long_term_borrowing_cad!==14293528||f.proposed_primeau_commitment_cad!==42302472||f.proposed_long_term_borrowing_cad+f.proposed_primeau_commitment_cad!==f.works_and_envelope_cad||f.source_id!=="S02_JUNE_BYLAW_DRAFT"||f.debt_drawn_by_project_cad!==null||f.primeau_disbursed_by_project_cad!==null||!object(g)||g.project_number!==1321||g.updated!=="2026-03-18"||g.status!=="EN_REALISATION"||g.planned_full_service!=="2026-12"||g.cost_approved_cad!==44500000||g.quebec_contribution_approved_cad!==42300000||g.partners_contribution_approved_cad!==2200000||g.cost_approved_cad!==g.quebec_contribution_approved_cad+g.partners_contribution_approved_cad||g.scope_comparability_verified!==false||g.equals_municipal_bylaw_scope!==false||g.equals_construction_contract_scope!==false||g.verified_paid_cad!==null||["costs_not_interchangeable","bylaw_and_dashboard_different_approved_baselines","contract_gross_vs_dashboard_basis_unconfirmed","project_not_proven_in_service","grant_awarded_not_received_cash"].some(k=>f[k]!==true))fail("NONCOMPARABLE_COST_BASELINES");
 const u2025=d.upstream_financial_2025;
 if(u2025?.previous_file!=="data/reconciliation-financiere-port-daniel-g0-16r-2025.json"||u2025.total_municipal_cash_capex_outflow_cad!==r.cash_flow_2025.capital_acquisition_outflow_cad||u2025.full_municipal_financial_statements_have_qualified_opinion!==true||u2025.no_assignment_of_municipal_cash_to_selected_vendors!==true||u2025.no_subtracting_council_authorizations_from_2025_cash_outflow!==true)fail("UPSTREAM_CASH_AGGREGATE");
 if(!object(d.controls)||Object.values(d.controls).some(x=>x!==true))fail("ANTI_HALLUCINATION_CONTROLS");
 if(!Array.isArray(d.remaining_proofs)||d.remaining_proofs.length!==8||d.remaining_proofs.some((x,i)=>x.id!=="K"+String(i+1).padStart(2,"0")||x.status!=="NOT_VERIFIED"))fail("PROOF_GAPS");
 if(!Array.isArray(d.scenario_ten_year)||d.scenario_ten_year.map(x=>x.id).join("|")!=="QUEBEC_CANADA|QUEBEC_SOUVERAIN"||d.scenario_ten_year.some(x=>x.costs_and_revenue_verified!==false||x.annual_balance_cad?.length!==10||x.annual_balance_cad.some(y=>y!==null)))fail("TEN_YEAR_MODELS");
 const decision=d.decisions||{};
 if(decision.project_specific_awards_verified_from_official_minutes!==true||decision.project_specific_council_authorizations_found!==true||["verified_paid_contracts_in_bank","verified_primeau_project_cash_receipt","project_final_cost_certified","funding_scenarios_certified","score_point_earned"].some(k=>decision[k]!==false))fail("FALSE_APPROVAL");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,numbered_authorisations_pre_tax_cad:total,contract_awards_gross_cad:53679384.28,paid_by_bank_proven_cad:null,primeau_cash_receipt_proven_cad:null};
}
