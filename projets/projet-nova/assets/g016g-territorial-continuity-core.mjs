// Projet Nova — G0.16g. Contrôleur déterministe et fail-closed.
// Des données officielles de référence ne certifient pas la réforme Nova.
export const REQUIRED_ORIGINS=Object.freeze([
"G014_AUG2026","EDU_FISCAL_RULES","MUNICIPAL_RF","MUNICIPAL_OPEN_DATA",
"MUNICIPAL_UMQ","CONST_92","CONST_FULL","DEBT_FUND",
"EDU_BUDGET_RULES","EDU_STAFF","RETRAITE_EMPLOYES"
]);
export const REQUIRED_CONTINUITY=Object.freeze([
"E01","E02","M01","M02","M03","W01","W02","D01","D02"
]);
export const REQUIRED_COMPETENCES=Object.freeze([
["PROVINCIAL_DIRECT_TAXATION","92(2)"],["PROVINCIAL_BORROWING","92(3)"],
["MUNICIPAL_INSTITUTIONS","92(8)"],["EDUCATION","93"]
]);
export const REQUIRED_PROOFS=Object.freeze(["V10","V14","V15"]);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function verifyG016gTerritorialContinuity(d,g014,g015,g016e,g016f){
 const errors=[],fail=x=>errors.push(x);
 if(!obj(d)||d.schema!=="nova-g016g-education-municipalites-travail-dette/v1"||
  !Array.isArray(d.origins)||!obj(d.source_facts)||!Array.isArray(d.legal_competences)||
  !Array.isArray(d.critical_continuity)||!Array.isArray(d.scenarios)||
  !obj(d.cross_checks)||!Array.isArray(d.required_proofs)||!Array.isArray(d.unresolved_issues)||
  !obj(d.decision))return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.phase!=="G0.16g"||d.status!=="EXAMEN_DOCUMENTAIRE_NON_AUDITE"||
  d.adopted!==false||d.programme_score_before!==47||d.programme_score_after!==47)
   fail("FALSE_PROGRAMME_STATUS");
 if(!same(d.origins.map(s=>s?.id),REQUIRED_ORIGINS)||d.origins.some(s=>
  !obj(s)||typeof s.publisher!=="string"||!s.publisher||
  !s.url?.startsWith("https://")||s.reviewed_independently_for_nova!==false||
  !["PRIMARY_GOVERNMENT","PRIMARY_LAW","STAKEHOLDER_ASSOCIATION"].includes(s.source_type)||
  typeof s.scope!=="string"||!s.scope))
   fail("SOURCE_PROVENANCE");
 const originType=Object.fromEntries(d.origins.map(s=>[s.id,s.source_type]));
 if(originType.MUNICIPAL_UMQ!=="STAKEHOLDER_ASSOCIATION"||
  originType.CONST_92!=="PRIMARY_LAW"||originType.CONST_FULL!=="PRIMARY_LAW")
   fail("SOURCE_CLASSIFICATION");
 const k=g014?.revenue_categories??[];
 const school=k.find(x=>x.id==="FONCIER_SCOLAIRE")?.amount_mcad;
 const debt=g014?.baseline?.debt_service;
 const facts=d.source_facts;
 const e=facts.school_property_tax,m=facts.municipalities,
       ed=facts.education,t=facts.debt,w=facts.workers;
 if(!obj(e)||e.amount_mcad!==1301||e.amount_mcad!==school||
   e.year!=="2026-2027"||e.scope!=="PROVINCIAL_SCHOOL_TAX_REVENUE"||
   e.source_id!=="G014_AUG2026"||e.same_as_municipal_property_tax!==false||
   e.entire_education_cost!==false||e.proposed_abolition_approved!==false||
   e.replacement_proven_mcad!==null)fail("SCHOOL_TAX_NOT_SCHOOL_COST");
 if(!obj(m)||m.aggregate_property_tax_revenue_mcad!==null||m.year!==null||
   !same(m.source_ids,["MUNICIPAL_RF","MUNICIPAL_OPEN_DATA"])||
   m.umq_claim_property_share_pct!==70||m.umq_claim_source_id!=="MUNICIPAL_UMQ"||
   m.umq_claim_is_independent_audited_nova_data!==false||
   m.municipal_taxation_not_in_provincial_1301_mcad!==true||
   m.funding_transition_estimate_mcad!==null||
   m.aggregate_2024_resource_page!=="https://www.donneesquebec.ca/recherche/dataset/profil-financier-des-municipalites-locales/resource/5dec077d-4ef9-4e22-99e9-0c4f3a6dd52d"||
   m.aggregate_2024_csv_source!=="https://mamh.gouv.qc.ca/fichiersdonneesouvertes/PF-2024-2024-Prov.csv"||
   m.aggregate_2024_csv_status!=="SOURCE_CATALOGUE_IDENTIFIEE_NON_IMPORTEE")
   fail("MUNICIPAL_TAX_INCOMPLETE");
 if(!obj(ed)||ed.ministry_and_school_budget_reconciled_mcad!==null||
   ed.year!=="2026-2027"||
   !same(ed.source_ids,["EDU_FISCAL_RULES","EDU_BUDGET_RULES"])||
   ed.school_fiscal_equalization_in_rules!==true||
   ed.special_status_school_funding_separately_reviewed!==false||
   ed.student_service_continuity_certified!==false)fail("EDUCATION_COST_UNKNOWN");
 if(!obj(t)||t.government_service_2026_2027_mcad!==10516||
   t.government_service_2026_2027_mcad!==debt||
   t.source_id!=="G014_AUG2026"||
   t.net_debt_share_gdp_march_2026_pct!==38.1||
   t.source_id_for_share!=="DEBT_FUND"||
   t.fund_generations_balance_2026_bcad!==16.6||
   t.net_debt_not_same_as_annual_service!==true||
   !["debt_stock_actual_mcad","sovereign_debt_share_allocation_mcad",
     "debt_service_financing_nova_mcad","net_borrowing_nova_mcad"].every(k=>t[k]===null))
   fail("DEBT_STOCK_VS_SERVICE");
 if(!obj(w)||w.public_workforce_baseline_full_time_equivalents!==null||
   w.collective_agreements_reviewed!==false||w.pensions_actuarial_cost_mcad!==null||
   w.protect_current_workforce_in_transition!==true||
   w.no_displacement_or_wage_loss_proven!==false||
   !same(w.source_ids,["EDU_STAFF","RETRAITE_EMPLOYES"]))
   fail("WORKER_RIGHTS_UNVERIFIED");
 if(!same(d.legal_competences.map(x=>[x?.id,x?.section]),REQUIRED_COMPETENCES)||
   d.legal_competences.some(x=>x.scenario!=="QUEBEC_CANADA"||
   x.independent_legal_review!==false||!x.current_rule))fail("LEGAL_COMPETENCES_NOT_CERTIFIED");
 if(!same(d.critical_continuity.map(x=>x?.id),REQUIRED_CONTINUITY)||
   d.critical_continuity.some(x=>!["EDUCATION","MUNICIPALITES","EMPLOIS","DETTE"].includes(x.sector)||
    !x.requirement||x.baseline_cost_mcad!==null||x.replacement_mcad!==null||
    x.legal_signoff!==false||x.staff_signoff!==false))
    fail("SERVICE_CONTINUITY_UNFUNDED");
 const scenarioKeys=["municipal_tax_authority_certified","education_competence_reviewed",
  "independent_audit","federal_funding_or_inherited_debt_assumed"];
 const scenAmounts=["school_budget_continuity_mcad","municipal_budget_continuity_mcad",
  "public_workforce_guarantee_cost_mcad","pension_rights_cost_mcad","debt_service_mcad"];
 if(!same(d.scenarios.map(x=>x?.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"])||
   d.scenarios.some(x=>scenarioKeys.some(k=>x?.[k]!==false)||
   scenAmounts.some(k=>x?.[k]!==null)))
   fail("FICTIONAL_CONSTITUTIONAL_BUDGET");
 const c=d.cross_checks;
 const constraints=["no_double_count_school_municipal","g016f_workers_education_municipal_debt_unfunded",
 "nations_incanada_and_sovereign_distinct","zero_fiscal_tax_rates_recommended"];
 if(c.g014_school_tax_mcad!==school||c.g014_debt_service_mcad!==debt||
    c.g016e_years_unfunded!==20||
    constraints.some(x=>c[x]!==true)||
    c.claims_70pct_umq_as_verified_federal_statistic!==false)
   fail("ACCOUNTING_DOUBLE_COUNT_RISK");
 if(!same(d.required_proofs,REQUIRED_PROOFS)||
   g015?.programme_score!==47||g015?.status!=="NON_FRANCHIE"||
   !Array.isArray(g015?.proofs)||REQUIRED_PROOFS.some(id=>
   !g015.proofs.some(p=>p.id===id&&p.status==="A_DOCUMENTER")))
   fail("G015_EVIDENCE_UNPASSED");
 if(g016e?.schema!=="nova-g016e-pont-financier/v1"||
   g016e.programme_score_after!==47||g016e.scenarios?.length!==2||
   g016e.scenarios.some(s=>s.annual?.length!==10||
      s.annual.some(y=>y.net_balance_mcad!==null))||
   g016f?.schema!=="nova-g016f-continuite-regimes/v1"||
   g016f.programme_percent_after!==47||
   !same(g016f.remaining_continuity_to_finance,["EDUCATION","MUNICIPALITES","EMPLOIS","DETTE"]))
   fail("PREDECESSOR_GATES_UNPASSED");
 if(d.unresolved_issues.length!==6||d.unresolved_issues.some(x=>x.responsible_party!==null||
   x.cost_mcad!==null||x.independent_review!==false||x.deadline!==null))
   fail("ISSUES_PREMATURELY_CLOSED");
 const statusFields=["g015_passed","g016g_passed","municipal_property_tax_abolition_financed",
    "school_property_tax_abolition_financed","staffing_savings_verified",
    "pension_rights_preserved_verified","debt_continuity_financed",
    "sovereign_budget_certified","two_tax_programme_approved","programme_complete"];
 if(statusFields.some(k=>d.decision[k]!==false)||Object.keys(d.decision).length!==statusFields.length)
   fail("PREMATURE_APPROVAL");
 return {ok:errors.length===0,errors:[...new Set(errors)],programme_score:47,
  legal_reviews_completed:0,certified_scenarios:0,
  sourced_school_tax_mcad:school,sourced_debt_service_mcad:debt,
  municipal_funding_gap_quantified:false};
}
