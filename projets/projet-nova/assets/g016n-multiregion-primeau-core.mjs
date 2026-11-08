// Projet Nova G0.16n — source MAMH 2025-082, sept cas, non representatifs.
// Les aides accordees et couts maximum admissibles ne sont ni des paiements
// ni le cout final des infrastructures.
export const OFFICIAL_MAMH_ROWS=Object.freeze([
["WARWICK","Warwick","Centre-du-Québec",15440948,14668901,"2025-05-20","2026-12-18",3],
["GATINEAU","Gatineau","Outaouais",75942667,56957000,"2024-09-02","2027-12-31",4],
["LAVAL","Laval","Laval",31004168,23253126,"2025-03-03","2028-12-31",4],
["PORT_DANIEL_GASCONS","Port-Daniel-Gascons","Gaspésie–Îles-de-la-Madeleine",44528918,42302472,"2024-04-01","2025-10-31",4],
["ILE_DANTICOSTI","L’Île-d’Anticosti","Côte-Nord",8354735,8354735,"2024-01-05","2025-03-28",4],
["VAL_DOR","Val-d’Or","Abitibi-Témiscamingue",12139163,10318289,"2024-04-01","2025-04-01",4],
["LA_DORE","La Doré","Saguenay–Lac-Saint-Jean",912270,866657,"2024-06-01","2024-10-31",4]
]);
export const OFFICIAL_PDF="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/demande_acces/2025/DAI_2025-082_subventions_primeau_2023_2033.pdf";
export const OFFICIAL_COUNCIL_PDF="https://munpdg.ca/wp-content/uploads/2025/07/proces-verbal-de-la-seance-ordinaire-du-9-juin.pdf";
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const ratio=(a,c)=>Math.round(a*10000/c)/100;
export function validateG016nMultiRegion(d,g016m){
 const errs=[],bad=k=>errs.push(k);
 if(!obj(d)||d.schema!=="nova-g016n-primeau-comparatif-cas-v1"||
   !obj(d.scope)||!Array.isArray(d.sources)||!Array.isArray(d.projects)||
   !obj(d.port_daniel_municipal_bylaw)||!obj(d.derived_summary)||
   !obj(d.fiscal_continuity)||!Array.isArray(d.unresolved_questions)||!obj(d.decision))
   return {ok:false,errors:["SCHEMA"],score:null};
 if(d.phase!=="G0.16n"||d.as_of!=="2026-11-07"||
    d.status!=="NON_RANDOM_PUBLIC_CASE_COMPARISON_NOT_NOVA_FISCAL_CERTIFICATION"||
    d.programme_score_before!==47||d.programme_score_after!==47||
    d.adopted!==false)bad("SCORE_NOT_PROVEN");
 const sc=d.scope;
 if(sc.list_date!=="2025-10-08"||
    sc.source_document_type!=="MAMH_ACCESS_TO_INFORMATION_AWARDED_PROJECT_LIST"||
    sc.selection!=="PURPOSIVE_SEVEN_REGIONS_SEVEN_PROJECTS_NOT_RANDOM_NOT_REPRESENTATIVE"||
    sc.selected_projects!==7||sc.distinct_municipalities!==7||sc.distinct_regions!==7||
    !same(sc.pdf_pages_verified_visually,[3,4])||
    ["region_count_eligible_for_other_projects_not_exhausted","subvention_announced_not_disbursed",
     "maximum_eligible_cost_not_total_project_cost","planned_construction_dates_not_actual_completion",
     "local_bylaw_not_actual_borrowing","copy_of_warwick_case_not_extra_project",
     "government_and_municipal_cost_scope_not_identical"].some(x=>sc[x]!==true))
   bad("SAMPLE_NOT_REPRESENTATIVE");
 if(!same(d.sources.map(s=>s?.id),
     ["MAMH_2025_082","PORT_DANIEL_COUNCIL","PORT_DANIEL_AWARD",
     "GATINEAU_AWARD","LAVAL_AWARD","ANTICOSTI_AWARD"])||
    d.sources[0]?.url!==OFFICIAL_PDF||
    !same(d.sources[0]?.visual_pdf_pages_zero_based,[3,4])||
    d.sources[1]?.url!==OFFICIAL_COUNCIL_PDF||
    d.sources[1]?.screenshot_cache_miss!==true||
    !same(d.sources[1]?.visual_pdf_pages_zero_based,[])||
    d.sources.some(s=>!s.url?.startsWith("https://")||!s.purpose||!s.publisher))
   bad("PROVENANCE_UNSUPPORTED");
 const ps=d.projects;
 if(ps.length!==7||ps.some((p,i)=>{
   const [id,name,region,cost,award,start,end,page]=OFFICIAL_MAMH_ROWS[i];
   return !obj(p)||!same([p.id,p.municipality,p.region,
       p.max_admissible_cost_cad,p.awarded_financial_aid_cad,
       p.scheduled_start_in_2025_list,p.scheduled_finish_in_2025_list,
       p.source_list_pdf_page_zero_based],
      [id,name,region,cost,award,start,end,page])||
     !p.title_as_mamh||!p.project_type||p.source_primary_id!=="MAMH_2025_082"||
     p.source_subprogramme!=="1.2"||
     p.ratio_award_to_max_eligible_cost_pct!==ratio(award,cost)||
     p.grant_status!=="LISTED_IN_MAMH_2025_AWARDED_OR_ONGOING_LIST_NOT_PAID_CONFIRMED"||
     p.actual_total_project_cost_cad!==null||p.actual_disbursement_cad!==null||
     p.actual_borrowed_cad!==null||p.completion_date_independently_verified!==null||
     p.independent_financial_audit!==false||
     p.prior_case_link!==(i===0?"projets/projet-nova/data/cas-municipal-reel-g0-16m-warwick-eau-2025-2026.json":null);
 }))bad("MAMH_ROW_MISMATCH");
 const local=d.port_daniel_municipal_bylaw;
 if(local.project_id!=="PORT_DANIEL_GASCONS"||
    local.municipal_pdf_url!==OFFICIAL_COUNCIL_PDF||
    local.municipal_council_meeting!=="2025-06-09"||
    local.resolution!=="2025-06-149"||local.bylaw!=="2025-01"||
    local.pdf_screenshot_observed!==false||
    local.pdf_text_retrieved!==true||local.pdf_screenshot_cache_miss!==true||
    local.planned_total_project_spending_cad!==56596000||
    local.promise_applied_to_financing_cad!==42302472||
    local.borrowing_authorized_cad!==14293528||
    local.borrowing_term_years!==40||
    local.government_promise_letter_mentioned!=="2025-06-03"||
    local.special_general_property_tax_share_borrowing_pct!==14||
    local.special_served_sector_tax_and_compensation_reported!==true||
    local.promise_applied_to_financing_cad+local.borrowing_authorized_cad!==local.planned_total_project_spending_cad||
    ["actual_borrowing_drawdown_cad","annual_special_tax_amount_cad",
     "interest_cost_cad","actual_final_project_spending_cad"].some(k=>local[k]!==null)||
    local.legal_entry_into_force_independently_verified!==false||
    local.need_to_reconcile_different_gov_cost_scope!==true)
   bad("MUNICIPAL_BYLAW_OR_DEBT_CONFUSION");
 const totals=(field)=>ps.reduce((s,p)=>s+p[field],0);
 const eligible=OFFICIAL_MAMH_ROWS.reduce((s,p)=>s+p[3],0);
 const awards=OFFICIAL_MAMH_ROWS.reduce((s,p)=>s+p[4],0);
 const sum=d.derived_summary;
 if(sum.case_count!==7||sum.distinct_regions!==7||
    sum.sum_max_eligible_cad!==eligible||
    sum.sum_awarded_cad!==awards||
    sum.sum_max_eligible_minus_awarded_cad!==eligible-awards||
    sum.min_award_ratio_pct!==Math.min(...OFFICIAL_MAMH_ROWS.map(p=>ratio(p[4],p[3])))||
    sum.max_award_ratio_pct!==Math.max(...OFFICIAL_MAMH_ROWS.map(p=>ratio(p[4],p[3])))||
    sum.sum_is_sample_only_not_quebec_total!==true||
    sum.award_less_than_eligible_not_municipal_total_cost_gap!==true||
    sum.confirmed_paid_sum_cad!==null||sum.budget_savings_nova_cad!==null||
    totals("max_admissible_cost_cad")!==eligible||totals("awarded_financial_aid_cad")!==awards)
   bad("DERIVED_SUMMARY_INCORRECT");
 const cf=d.fiscal_continuity;
 if(["actual_household_tax_per_project_cad","actual_debt_service_per_year_cad",
    "actual_salaries_and_pensions_cad","municipal_operations_annual_cost_cad",
    "total_project_lifecycle_cost_cad",
    "alternative_two_tax_replacement_verified_cad"].some(x=>cf[x]!==null)||
    cf.independent_review!==false||
    !same(cf.two_constitutional_scenarios?.map(s=>s.id),
      ["QUEBEC_CANADA","QUEBEC_SOUVERAIN"])||
    cf.two_constitutional_scenarios.some(s=>
      s.legality_confirmed!==false||s.financing_audited!==false||
      !Array.isArray(s.annual)||s.annual.length!==10||
      s.annual.some((y,i)=>y.year!==`${2026+i}-${2027+i}`||
         ["municipal_service_cost_cad","grants_paid_cad","local_tax_abolition_cad",
          "replacement_income_cad","borrowing_service_cad","worker_rights_cost_cad",
          "balance_cad"].some(k=>y[k]!==null))))
    bad("BUDGET_AND_WORKERS_UNFUNDED");
 if(d.unresolved_questions.length!==6||
    d.unresolved_questions.some((q,i)=>
      q.id!=="Q"+String(i+1).padStart(2,"0")||q.status!=="NOT_YET_VERIFIED"||!q.question))
    bad("PROOFS_NOT_REVIEWED");
 if(d.decision.real_multiple_regions_evidence_added!==true||
   ["all_quebec_municipal_project_population_covered",
    "individual_cash_payments_audited","two_tax_financing_proven",
    "external_legal_financial_review_complete","programme_complete"].some(x=>d.decision[x]!==false))
    bad("UNWARRANTED_REFORM_APPROVAL");
 if(g016m?.schema!=="nova-g016m-municipal-pilot/v1"||
    g016m.score_after!==47||
    g016m.cases?.[0]?.award?.amount_cad!==14668901||
    g016m.cases?.[0]?.award?.max_eligible_cost_cad!==15440948||
    g016m.cases?.[0]?.municipality!=="Warwick"||
    g016m.summary?.grant_cash_disbursements_verified_cad!==null)
    bad("G016M_PREDECESSOR_MISMATCH");
 return {ok:errs.length===0,errors:[...new Set(errs)],programme_score:47,
  projects_in_non_random_sample:7,regions:7,awarded_sum_cad:awards,
  eligible_max_sum_cad:eligible,verified_cash_sum_cad:null,
  port_daniel_authorised_loan_cad:14293528,
  legal_audit_complete:false};
}
