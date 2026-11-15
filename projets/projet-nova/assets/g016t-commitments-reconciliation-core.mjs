// Nova G0.16t — préservation de l'écart entre autorisation, engagement, charge et paiement bancaire.
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const cents=x=>Math.round(x*100);
const nums=[2,3,4,5,6,7,8];
const NULL_ARR=Array(10).fill(null);
export function auditG016t(d,p){
 const errors=[],bad=s=>errors.push(s);
 if(!object(d)||d.schema!=="nova-g016t-gascons-certificate-and-grant-timing/v1"||!object(d.selected_series)||!object(d.provincial_commitment))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.16t"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.programme_adopted!==false||d.independent_nova_audit!==false)bad("COMPLETENESS");
 if(p?.schema!=="nova-g016s-gascons-contracts-and-payment-authorizations/v1"||p?.audit_completion_after!==47||d.from_prior?.file!=="data/contrats-et-autorisations-paiement-gascons-g0-16s-2025-2026.json"||!eq(d.from_prior.certificate_numbers,p.council_authorizations.rows.map(x=>Number(x.certificate_no)))||cents(d.from_prior.selected_sum_pre_tax_cad)!==cents(p.council_authorizations.numbered_selected_total_pre_tax_cad)||d.from_prior.unnumbered_invoice_august_pre_tax_cad!==undefined)bad("UPSTREAM");
 if(!Array.isArray(d.official_sources)||d.official_sources.length!==4||d.official_sources[0].url!=="https://munpdg.ca/wp-content/uploads/2026/02/proces-verbal-de-la-seance-ordinaire-du-12-janvier-2026.pdf"||d.official_sources[1].url!=="https://munpdg.ca/wp-content/uploads/2026/04/proces-verbal-seance-ordinaire-du-9-mars.pdf"||d.official_sources[2].reference!=="2036036"||d.official_sources.slice(0,3).some(s=>s.pdf_screenshot_attempted!==true||s.pdf_screenshot_success!==false))bad("PROVENANCE");
 const n=d.added_numbered_certificate_authorizations||[];
 if(n.length!==2||n[0].number!==6||n[0].date!=="2026-01-12"||n[0].resolution!=="2026-01-007"||cents(n[0].pre_tax_cad)!==261202717||n[0].source_id!=="JAN_2026"||n[1].number!==8||n[1].date!=="2026-03-09"||n[1].resolution!=="2026-03-068"||cents(n[1].pre_tax_cad)!==59748430||n[1].source_id!=="MAR_2026"||n.some(x=>x.bank_transfer_confirmed!==false))bad("CERTIFICATES_6_8");
 const z=d.selected_series;
 if(!eq(z.certificate_numbers,nums)||z.certificate_1_status!=="NOT_VERIFIED"||z.number_1_amount_pre_tax_cad!==null||z.selected_count!==7||cents(z.subtotal_prior_pre_tax_cad)!==1541222265||cents(z.subtotal_new_pre_tax_cad)!==320951147||cents(z.subtotal_all_selected_pre_tax_cad)!==1862173412||cents(z.subtotal_prior_pre_tax_cad+z.subtotal_new_pre_tax_cad)!==cents(z.subtotal_all_selected_pre_tax_cad)||cents(z.year_2025_selected_pre_tax_cad)!==1531363929||cents(z.year_2026_selected_pre_tax_cad)!==330809483||cents(z.year_2025_selected_pre_tax_cad+z.year_2026_selected_pre_tax_cad)!==cents(z.subtotal_all_selected_pre_tax_cad)||z.unnumbered_invoice_august_possible_overlap!==true||z.unnumbered_august_invoice_included!==false||z.actual_bank_paid_to_contractors_cad!==null||z.all_project_certificates_covered!==false||z.final_cost_of_project_cad!==null)bad("SELECTED_SUBTOTAL_ONLY");
 const supplier=d.related_other_supplier_authorizations_excluded_from_progex_subtotal||[];
 if(supplier.length!==3||!eq(supplier.map(x=>[x.id,x.pre_tax_cad,x.source_id]),[["TETRA_JAN",116313.5,"JAN_2026"],["TETRA_MAR",20176.15,"MAR_2026"],["ENGLOBE_MAR",637.5,"MAR_2026"]])||supplier.some(x=>x.bank_transfer_confirmed!==false))bad("OTHER_SUPPLIERS_NOT_DOUBLECOUNTED");
 const g=d.provincial_commitment;
 if(g.reference!=="2036036"||g.source_id!=="MAMH_JUN_2025"||g.programme!=="PRIMEAU 2023-2033"||g.total_committed_cad!==42302472||!eq(g.yearly_phasing.map(x=>[x.fiscal_year,x.budget_engagement_cad]),[["2025-2026",24700000],["2026-2027",17602472]])||g.yearly_phasing.reduce((s,x)=>s+x.budget_engagement_cad,0)!==g.total_committed_cad||g.yearly_phasing.some(x=>x.verified_cash_disbursement_cad!==null)||g.paid_to_beneficiary_in_bank_cad!==null||g.same_grant_announced_2025_not_additional_grant!==true||g.fiscal_year_vs_calendar_year_not_equivalent!==true||g.commitment_not_disbursement!==true||g.government_ledger_vs_municipal_bank_not_reconciled!==true)bad("COMMITMENTS_NOT_CASH");
 if(!object(d.controls)||Object.values(d.controls).some(x=>x!==true)||d.from_prior.unnumbered_august_invoice_pre_tax_cad!==450368.10||d.from_prior.excluded_from_numbered_sum!==true)bad("GUARDRAILS");
 if(!Array.isArray(d.additional_evidence_needed)||d.additional_evidence_needed.length!==8||d.additional_evidence_needed.some((x,i)=>x.id!=="E"+String(i+1).padStart(2,"0")||x.status!=="UNVERIFIED"))bad("GAPS");
 if(!Array.isArray(d.decade_scenarios)||d.decade_scenarios.map(x=>x.id).join("|")!=="QUEBEC_CANADA|QUEBEC_SOUVERAIN"||d.decade_scenarios.some(x=>x.validated!==false||!eq(x.annual_balance_cad,NULL_ARR)))bad("DECADE_MODEL_UNPROVEN");
 const dec=d.decision||{};
 if(dec.certificate_6_identified!==true||dec.certificate_8_identified!==true||dec.grant_commitment_fiscal_phasing_identified!==true||["complete_certificate_series_identified","bank_paid_to_contractors_verified","grant_paid_to_municipality_verified","nova_tax_plan_funded","score_rise_allowed"].some(x=>dec[x]!==false))bad("FALSE_APPROVAL");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,selected_pre_tax_authorizations_cad:18621734.12,committed_grant_cad:42302472,confirmed_bank_payments_cad:null};
}
