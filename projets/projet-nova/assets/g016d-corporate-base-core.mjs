// Projet Nova G0.16d : vérification déterministe des agrégats publics, non des taux Nova.
export const OFFICIAL_SOURCE="https://www.quebec.ca/gouvernement/finances-publiques/revenus/donnees-fiscales/statistiques-fiscales-societes";
export const FEDERAL_CONTEXT="https://www.canada.ca/fr/agence-revenu/programmes/a-propos-agence-revenu-canada-arc/statistiques-revenu-statistiques-tps-tvh/statistiques-societes-t2/tableaux-statistiques-societes-annees-imposition-2019-2024.html";
export const AMOUNTS=Object.freeze({quebec_taxable_income_mcad:95784,payroll_subject_to_fss_mcad:155850,
quebec_corporate_income_tax_mcad:10000,health_services_fund_contributions_mcad:5327,
gross_income_tax_and_fss_mcad:15327,tax_credits_mcad:2468,net_after_credits_mcad:12860});
export const COUNTS=Object.freeze({total_company_returns:564599,small_company_returns:542249,
medium_company_returns:14858,large_company_returns:7492,
company_returns_without_income_tax:322020,company_returns_without_income_tax_or_fss:239628});
export const SIZES=Object.freeze([[542249,2922,1173,4095],[14858,1525,1035,2560],[7492,5553,3119,8672]]);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const sum=x=>x.reduce((s,v)=>s+v,0);
const ids=["V04","V06","V13"];
const unknownNames=["corporate_rate_percent","personal_rate_percent","revenue_under_reform_mcad","additional_haven_compliance_yield_mcad",
 "fss_continuity_financed_mcad","net_employment_effect","small_business_distribution_effect",
 "quebec_sovereign_budget_balance_mcad","quebec_canada_budget_balance_mcad"];
export function inspectG016dCompanies(d,g15,personal){
 const errors=[],add=e=>errors.push(e);
 if(!obj(d)||d.schema!=="nova-g016d-societes-assiette-historique/v1"||
    !obj(d.source)||!obj(d.corporate_tax_base)||!obj(d.receipts)||!obj(d.population)||
    !Array.isArray(d.sizes)||!obj(d.proportions_reported)||!obj(d.cross_year_guardrails)||
    !obj(d.unknown_nova)||!obj(d.decision)||!obj(d.other_primary_source_context)||
    !obj(d.evidence_links))return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.phase!=="G0.16d"||d.status!=="SOURCE_OFFICIELLE_AGREGEE_TRANSCRITE_NON_AUDITEE"||
    d.programme_score!==47||d.adopted!==false||d.g015_proof_status_unchanged!==true)
    add("PREMATURE_PROGRAMME_STATUS");
 if(d.source.publisher!=="Ministère des Finances du Québec"||
    d.source.year!==2021||d.source.source_page_last_updated!=="2026-10-07"||
    d.source.url!==OFFICIAL_SOURCE||d.source.source_type!=="SOMMAIRE_HTML"||
    d.source.original_pdf_examined!==false||d.source.original_xlsx_imported!==false||
    d.source.independent_reviewer_signed!==false) add("SOURCE_INCORRECTE");
 if(d.reference_unit!=="MILLIONS_CAD_COURANTS_ANNEE_IMPOSITION_2021"||
    d.corporate_tax_base.quebec_taxable_income_mcad!==AMOUNTS.quebec_taxable_income_mcad||
    d.corporate_tax_base.payroll_subject_to_fss_mcad!==AMOUNTS.payroll_subject_to_fss_mcad||
    d.corporate_tax_base.worldwide_taxable_income_mcad!==null||
    d.corporate_tax_base.worldwide_taxable_income_is_quebec_base!==false||
    d.corporate_tax_base.loss_carryforwards_mcad!==null||
    d.corporate_tax_base.dividend_deductions_mcad!==null)
    add("TAX_BASES_MISREPRESENTED");
 const money=d.receipts;
 if(Object.entries(AMOUNTS).filter(([k])=>!["quebec_taxable_income_mcad","payroll_subject_to_fss_mcad"].includes(k)).some(([k,v])=>money[k]!==v)||
    money.rounding_tolerance_mcad!==1||Object.keys(money).length!==6||
    money.quebec_corporate_income_tax_mcad+money.health_services_fund_contributions_mcad!==money.gross_income_tax_and_fss_mcad||
    Math.abs(money.gross_income_tax_and_fss_mcad-money.tax_credits_mcad-money.net_after_credits_mcad)>1)
    add("TAX_AND_FSS_RECONCILIATION");
 if(!same(d.population,COUNTS)||
    d.population.small_company_returns+d.population.medium_company_returns+d.population.large_company_returns!==d.population.total_company_returns)
    add("DECLARATIONS_ALTERED");
 if(d.sizes.length!==3||d.sizes.some((x,i)=>!obj(x)||x.id!==["SMALL","MEDIUM","LARGE"][i]||
    !same([x.returns,x.income_tax_mcad,x.fss_mcad,x.combined_mcad],SIZES[i])||
    x.income_tax_mcad+x.fss_mcad!==x.combined_mcad))
    add("SIZE_DISTRIBUTION_ALTERED");
 if(d.sizes.length===3&&d.sizes.every(obj)){
    for(const k of ["income_tax_mcad","fss_mcad","combined_mcad"]){
      const t={income_tax_mcad:10000,fss_mcad:5327,combined_mcad:15327}[k];
      if(sum(d.sizes.map(x=>x[k]))!==t)add("SIZE_TOTALS_WRONG");
    }
 }
 if(!same(d.proportions_reported,{not_subject_to_corporate_income_tax_pct:57,
    no_income_tax_nor_fss_due_pct:42.4,large_business_share_of_total_gross_pct:56.6})||
    Math.abs(d.population.company_returns_without_income_tax/d.population.total_company_returns*100-57)>0.1||
    Math.abs(d.population.company_returns_without_income_tax_or_fss/d.population.total_company_returns*100-42.4)>0.1||
    Math.abs(d.sizes[2]?.combined_mcad/15327*100-56.6)>0.1)
    add("PERCENTAGES_NOT_RECONCILED");
 if(d.cross_year_guardrails["2021_corporate_returns_vs_2023_personal_returns"]!=="NOT_SAME_TAX_YEAR_OR_UNIT"||
    d.cross_year_guardrails["2021_corporate_returns_vs_2026_2027_approved_revenues"]!=="NOT_COMPARABLE_WITHOUT_RECONCILIATION"||
    d.cross_year_guardrails.taxable_income_quebec_vs_fss_payroll!=="DIFFERENT_TAX_BASES"||
    d.cross_year_guardrails.fss_contributions_vs_provincial_corporate_income_tax!=="DIFFERENT_LEGAL_INSTRUMENTS"||
    d.cross_year_guardrails.federal_cra_t2_vs_quebec_provincial_income_tax!=="NOT_SAME_REVENUE_JURISDICTION"||
    d.cross_year_guardrails.business_size_classes_are_tax_return_classifications!==true||
    d.cross_year_guardrails.gross_income_tax_and_fss_is_not_all_public_revenues!==true)
    add("BAD_PERIOD_OR_JURISDICTION");
 if(d.other_primary_source_context.url!==FEDERAL_CONTEXT||
    d.other_primary_source_context.imported!==false||
    d.other_primary_source_context.date_of_records!=="2026-06-30"||
    !d.other_primary_source_context.note?.includes("Québec"))
    add("FEDERAL_IS_NOT_QUEBEC_TAX");
 if(!same(d.evidence_links.candidate_proofs,ids)||
    d.evidence_links.g015_data!=="data/matrice-preuves-g0-15-fiscalite.json")add("PROOF_REFERENCES");
 if(Object.keys(d.unknown_nova).length!==unknownNames.length||
    unknownNames.some(k=>d.unknown_nova[k]!==null)||
    d.decision.source_transcription_present!==true||d.decision.scope_and_period_reconciled!==true||
    ["g015_evidence_independently_verified","corporate_baseline_current_verified","tax_design_approved",
     "independent_review_completed","full_ten_year_budget_certified"].some(k=>d.decision[k]!==false)||
    d.decision.programme_pct_after!==47)add("INVENTED_NOVA_OUTCOME");
 if(!obj(g15)||g15.programme_score!==47||g15.status!=="NON_FRANCHIE"||
    !Array.isArray(g15.proofs)||g15.proofs.length!==15||
    ids.some(id=>!g15.proofs.some(p=>p.id===id&&p.status==="A_DOCUMENTER"&&p.reviewed_independently===false)))
    add("G015_NOT_VERIFIED");
 if(!obj(personal)||personal.programme_percent!==47||personal.source_year!==2023||
    personal.tax_return_aggregates_mcad?.taxable_income!==372261||
    personal.decision?.microsimulation_calibrated!==false)add("G016C_NOT_VERIFIED");
 return {ok:errors.length===0,errors:[...new Set(errors)],year:2021,
  corporate_taxable_income_mcad:95784,fss_payroll_mcad:155850,
  companies:564599,documented_prerequisites_for_g015:0,
  rates_approved:false,programme_score:47};
}
