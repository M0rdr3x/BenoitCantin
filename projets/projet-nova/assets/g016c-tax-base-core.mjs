/** G0.16c: controle des statistiques publiques 2023, sans supposer une réforme financée. */
export const SOURCE_PAGES=Object.freeze({
 A7:"https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-comp-impot.asp",
 A3:"https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/resume.asp",
 T4:"https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/tableau-4.asp"
});
export const TAX_2023_MCAD=Object.freeze({
 total_declared_income:427915,net_income_deductions:40892,net_income:387023,
 taxable_income_deductions:14761,taxable_income:372261,tax_on_taxable_income:62148,
 nonrefundable_credits_applied:21358,income_tax_payable:40790,
 refundable_credits_applied:9305,income_tax_payable_less_refundable_credits:31485
});
export const TAXPAYER_COUNTS=Object.freeze({all_returns:7220140,taxable_returns:4910844,nontaxable_returns:2309296});
export const QUINTILE_SHARES=Object.freeze([
 [3.43,0.03],[8.91,1.46],[14.99,8.64],[22.57,20.45],[50.10,69.41]
]);
export const QUINTILE_BRACKETS=Object.freeze([
 "Moins de 19 713 $","19 713 $ à 34 580 $","34 581 $ à 54 178 $",
 "54 179 $ à 82 785 $","82 786 $ ou plus"
]);
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const sameKeys=(x,reference)=>Object.keys(x).length===Object.keys(reference).length&&Object.keys(reference).every(k=>Object.hasOwn(x,k));
const sum=xs=>xs.reduce((a,b)=>a+b,0);
const truthyKeys=["is_historical_declared_tax_base","does_not_include_complete_corporate_tax_base",
"does_not_include_all_federal_taxation","does_not_prove_net_haven_recovery",
"five_quintiles_not_ten_household_deciles","cannot_join_with_isq_household_deciles",
"cannot_join_with_statcan_average_expenses","not_a_ten_year_balanced_budget",
"no_automatic_personal_tax_rate_calculation","no_automatic_tax_repeal","not_authorized_to_calibrate_nova"];
const falseKeys=["is_projected_2026_2027_tax_revenue","is_2026_tax_base","is_proposed_nova_tax_base"];
export function validateG016cTaxBase(doc,g015,g016b){
 const errors=[],fail=e=>errors.push(e);
 if(!object(doc)||doc.schema!=="nova-g016c-assiette-particuliers-2023/v1"||
    !object(doc.tax_return_aggregates_mcad)||!object(doc.taxpayer_counts)||
    !Array.isArray(doc.sources)||!Array.isArray(doc.quintiles_of_tax_filers_by_total_income)||
    !object(doc.rounding)||!object(doc.comparison_constraints)||!object(doc.unverified)||
    !object(doc.decision)||!object(doc.links))
  return {ok:false,errors:["INVALID_SCHEMA"],programme_percent:null};
 if(doc.status!=="AGREGATS_FISCAUX_PUBLICS_TRANSCRITS_NON_CALIBRES"||doc.phase!=="G0.16c"||
    doc.source_year!==2023||doc.programme_percent!==47||doc.adopted!==false||
    doc.unit!=="millions CAD courants 2023 sauf contribuables et pourcentages")
  fail("UNSUPPORTED_STATUS");
 if(doc.sources.length!==3||Object.keys(SOURCE_PAGES).some((id,i)=>{
    const s=doc.sources[i];return !object(s)||s.id!==id||s.publisher!=="Ministère des Finances du Québec"||
      s.url!==SOURCE_PAGES[id]||s.year!==2023||
      s.original_binary_imported!==false||s.second_reviewer_signed_off!==false||
      s.table!==(id==="T4"?"4 (ligne 1, 2, 3)":id.replace("A","A."));
 }))fail("UNVERIFIED_PROVENANCE");
 const a=doc.tax_return_aggregates_mcad;
 if(!sameKeys(a,TAX_2023_MCAD)||Object.keys(TAX_2023_MCAD).some(k=>a[k]!==TAX_2023_MCAD[k]))
  fail("ALTERED_TAX_AGGREGATES");
 if(a.total_declared_income-a.net_income_deductions!==a.net_income||
    Math.abs(a.net_income-a.taxable_income_deductions-a.taxable_income)>doc.rounding.million_cad_tolerance||
    a.tax_on_taxable_income-a.nonrefundable_credits_applied!==a.income_tax_payable||
    a.income_tax_payable-a.refundable_credits_applied!==a.income_tax_payable_less_refundable_credits||
    doc.reported_mean_tax_rate_percent!==9.5||
    Math.abs(100*a.income_tax_payable/a.total_declared_income-9.5)>.05)
  fail("FISCAL_RECONCILIATION");
 const t=doc.taxpayer_counts;
 if(!sameKeys(t,TAXPAYER_COUNTS)||Object.keys(TAXPAYER_COUNTS).some(k=>t[k]!==TAXPAYER_COUNTS[k])||
    t.taxable_returns+t.nontaxable_returns!==t.all_returns)
  fail("TAXPAYER_COUNTS");
 const q=doc.quintiles_of_tax_filers_by_total_income;
 if(q.length!==5||q.some((x,i)=>!object(x)||Object.keys(x).length!==4||
    x.quintile!==i+1||x.income_bracket!==QUINTILE_BRACKETS[i]||
    x.income_share_pct!==QUINTILE_SHARES[i][0]||
    x.tax_payable_share_pct!==QUINTILE_SHARES[i][1]))
  fail("QUINTILE_SOURCE_ALTERED");
 if(q.length===5&&q.every(object)&&(
    Math.abs(sum(q.map(x=>x.income_share_pct))-100)>doc.rounding.percentage_points_tolerance||
    Math.abs(sum(q.map(x=>x.tax_payable_share_pct))-100)>doc.rounding.percentage_points_tolerance))
  fail("QUINTILE_RECONCILIATION");
 if(doc.rounding.million_cad_tolerance!==1||
    doc.rounding.percentage_points_tolerance!==0.02)fail("ROUNDING_POLICY");
 if(truthyKeys.some(k=>doc.comparison_constraints[k]!==true)||
    falseKeys.some(k=>doc.comparison_constraints[k]!==false)||
    Object.keys(doc.comparison_constraints).length!==truthyKeys.length+falseKeys.length)
  fail("FISCAL_SCOPE_MISREPRESENTED");
 if(Object.keys(doc.unverified).length!==8||
    Object.values(doc.unverified).some(x=>x!==null)||
    doc.decision.partial_source_transcription_completed!==true||
    ["all_proofs_g015_completed","external_validation_completed","microsimulation_calibrated",
     "new_rates_authorized"].some(k=>doc.decision[k]!==false)||
    doc.decision.programme_pct_after!==47)
  fail("INVENTED_POLICY_OUTCOME");
 if(!object(g015)||g015.schema!=="nova-g015-preuves-fiscalite/v1"||
    g015.status!=="NON_FRANCHIE"||g015.programme_score!==47||
    !Array.isArray(g015.proofs)||g015.proofs.length!==15||
    g015.proofs.some(x=>!object(x)||x.status!=="A_DOCUMENTER"))
  fail("G015_NOT_PASSED");
 if(!object(g016b)||g016b.schema!=="nova-g016b-reperes-publics/v1"||
    g016b.programme_percent!==47||
    g016b.approved_for_microsimulation!==false||
    g016b.datasets?.household_decile_thresholds?.reference_year!==2023||
    g016b.datasets?.household_spending_provincial?.reference_year!==2023)
  fail("G016B_MISMATCH");
 if(doc.links?.unverified_source_proof!=="V05"||
    doc.links?.source_work!=="data/reperes-publics-g0-16b-2023.json")
  fail("EVIDENCE_LINKS");
 return {ok:errors.length===0,errors:[...new Set(errors)],
  programme_percent:47,historical_taxable_income_mcad:TAX_2023_MCAD.taxable_income,
  fiscal_quintiles:5,taxpayer_count:TAXPAYER_COUNTS.all_returns,
  independent_review:false,new_nova_tax_rate:null,eligible_for_policy_simulation:false};
}
