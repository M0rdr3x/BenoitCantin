// Projet Nova G0.16f: intégrité des repères légaux/sociaux; aucune simulation.
export const IDS=Object.freeze(["RRQ_RATES","RRQ_ACTUARIAL","RQAP_RATES","RQAP_FUND",
"RQAP_TRANSFER","RAMQ_NUMBERS","HEALTH_FINANCING"]);
export const URLS=Object.freeze([
"https://www.retraitequebec.gouv.qc.ca/fr/programmes/regime-rentes-quebec/travail-et-cotisations/revenus-travail-admissibles-et-cotisations",
"https://www.retraitequebec.gouv.qc.ca/fr/publications/programmes/regime-rentes-quebec-rrq/evaluations-actuarielles/resume-rapport-modifiant-evaluation-actuarielle-2024-rrq",
"https://www.quebec.ca/entreprises-et-travailleurs-autonomes/administrer-gerer/embauche-gestion-personnel/assurance-parentale/taux-cotisations",
"https://www.quebec.ca/gouvernement/ministeres-organismes/conseil-gestion-assurance-parentale/mission-mandats/fonds-dassurance-parentale",
"https://www.quebec.ca/gouvernement/ministeres-organismes/conseil-gestion-assurance-parentale",
"https://www.ramq.gouv.qc.ca/fr/donnees-statistiques/ramq-quelques-chiffres",
"https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/ressources-financieres-systeme-sante-services-sociaux"
]);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const near=(x,y)=>typeof x==="number"&&Math.abs(x-y)<0.00001;
const ids=["V07","V08","V09"];
export function verifyG016fSocialContinuity(d,g015,g016e,g014){
 const errors=[],fail=x=>errors.push(x);
 if(!obj(d)||d.schema!=="nova-g016f-continuite-regimes/v1"||
    !Array.isArray(d.sources)||!obj(d.rrq)||!obj(d.rqap)||!obj(d.ramq)||
    !obj(d.health_system)||!obj(d.cross_year_reference)||!obj(d.decision)||
    !Array.isArray(d.required_g015_proofs)||!Array.isArray(d.remaining_continuity_to_finance))
  return {ok:false,errors:["SCHEMA"],programme_percent:null};
 if(d.status!=="REPÈRES_PUBLICS_SANS_FINANCEMENT_NOVA_CERTIFIÉ"||
    d.phase!=="G0.16f"||d.adopted!==false||
    d.programme_percent_before!==47||d.programme_percent_after!==47||
    d.source_research_status!=="PARTIAL_PRIMARY_WEBSITE_REVIEW_WITHOUT_SIGNED_AUDIT")
  fail("UNVERIFIED_STAGE");
 if(d.sources.length!==IDS.length||d.sources.some((s,i)=>!obj(s)||s.id!==IDS[i]||
    s.url!==URLS[i]||s.reviewed_externally_for_nova!==false||
    typeof s.publisher!=="string"||!s.publisher||
    typeof s.scope!=="string"||!s.scope))fail("SOURCE_PROVENANCE");
 const q=d.rrq;
 if(q.year!==2026||q.contribution_exemption_cad!==3500||
    q.maximum_pensionable_earnings_cad!==74600||q.additional_maximum_pensionable_earnings_cad!==85000||
    !near(q.employee_first_bracket_pct,6.3)||!near(q.employer_first_bracket_pct,6.3)||
    !near(q.employee_second_bracket_pct,4)||!near(q.employer_second_bracket_pct,4)||
    q.source_id!=="RRQ_RATES"||
    q.actuarial_source_id!=="RRQ_ACTUARIAL"||
    !near(q.actuarial_base_contribution_rate_total_pct,10.6)||
    !near(q.actuarial_base_required_rate_pct,10.48)||
    !near(q.actuarial_base_margin_pct_points,0.12)||
    !near(q.earlier_margin_pct_points,0.33)||
    !near(q.actuarial_base_contribution_rate_total_pct-q.actuarial_base_required_rate_pct,
      q.actuarial_base_margin_pct_points)||
    q.replacement_financing_mcad!==null||q.rights_maintained_under_nova!==null||
    q.independent_actuary_nova_review!==false)fail("RRQ_RATES_ACTUARIAL_OR_RIGHTS");
 const p=d.rqap;
 if(p.year!==2026||!near(p.employee_rate_pct,0.430)||
    !near(p.employer_rate_pct,0.602)||!near(p.self_employed_rate_pct,0.764)||
    p.source_id!=="RQAP_RATES"||p.fund_source_id!=="RQAP_FUND"||
    p.fund_character!=="FONDS_FIDUCIAIRE_NON_BUDGETAIRE"||
    p.roles_transferred_to!=="Retraite Québec"||
    p.roles_transferred_effective!=="2026-05-01"||p.roles_source_id!=="RQAP_TRANSFER"||
    p.fund_current_assets_mcad!==null||p.annual_benefits_mcad!==null||
    p.actuarial_projection_under_nova!==null||p.continuity_financed_under_nova!==false)
    fail("RQAP_FUND_AND_TRANSFER");
 const r=d.ramq;
 const a=r.financing_mcad,b=r.program_cost_mcad;
 if(r.fiscal_year!=="2024-2025"||r.source_id!=="RAMQ_NUMBERS"||
    r.scope!=="RAMQ_ADMINISTERED_PROGRAMS_NOT_WHOLE_HEALTH_SYSTEM"||
    !obj(a)||a.fss!==8937||a.drug_insurance_fund!==4354||
    a.other!==1250||a.published_total!==14542||a.component_rounding_tolerance!==1||
    Math.abs(a.fss+a.drug_insurance_fund+a.other-a.published_total)>1||
    !obj(b)||b.physician_remuneration!==8662||b.pharmacy_drugs_services!==4469||
    b.other!==1101||b.published_total!==14232||
    b.physician_remuneration+b.pharmacy_drugs_services+b.other!==b.published_total||
    !near(r.insured_health_millions,8.6)||!near(r.insured_public_drug_millions,3.9)||
    r.difference_financing_costs_not_identified_as_surplus!==true||
    r.costs_covered_after_nova_tax_reform!==null||
    r.independent_service_continuity_review!==false)
    fail("RAMQ_SCOPE_OR_RECONCILIATION");
 const h=d.health_system;
 if(h.calendar_year!==2024||h.estimated_total_spending_billion_cad!==81||
    h.estimated_public_spending_billion_cad!==59||
    h.values_approximate!==true||h.source_id!=="HEALTH_FINANCING"||
    h.scope!=="ALL_HEALTH_SPENDING_PUBLIC_AND_PRIVATE_NATIONAL_ACCOUNTS_NOT_RAMQ_SUBSET"||
    h.do_not_sum_with_ramq_total!==true||h.not_single_provincial_budget_line!==true)
    fail("HEALTH_SYSTEM_DOUBLE_COUNT");
 if(d.cross_year_reference.fss_revenue_2026_2027_mcad!==9538||
    d.cross_year_reference.source!=="data/registre-assiettes-fiscales-g0-14-2026-2027.json"||
    d.cross_year_reference.not_equivalent_to_ramq_fss_financing_2024_2025!==true||
    d.cross_year_reference.not_automatic_fss_replacement_cost!==true||
    g014?.revenue_categories?.find(x=>x.id==="COTISATIONS_SANTE")?.amount_mcad!==9538)
    fail("FSS_MILLENNIUM_MISMATCH");
 if(!same(d.required_g015_proofs,ids)||
    !same(d.remaining_continuity_to_finance,["EDUCATION","MUNICIPALITES","EMPLOIS","DETTE"])||
    g015?.status!=="NON_FRANCHIE"||g015?.programme_score!==47||
    !Array.isArray(g015.proofs)||ids.some(id=>!g015.proofs.some(x=>x.id===id&&x.status==="A_DOCUMENTER"&&x.reviewed_independently===false)))
    fail("UNPASSED_SOURCE_PROOFS");
 if(g016e?.schema!=="nova-g016e-pont-financier/v1"||
    g016e.programme_score_after!==47||
    g016e.decision?.finance_minimum_services_verified!==false||
    g016e.continuity?.length!==8)
    fail("BUDGET_PREDECESSOR_MISMATCH");
 const gates=["g016f_completed","all_health_services_financed","rrq_funding_substitution_approved",
    "rqap_funding_substitution_approved","fss_abolition_financed","drug_insurance_rights_assured",
    "tax_rates_authorized","programme_certified","scenarios_financially_certified"];
 if(d.decision.g015_proofs_independently_verified!==0||
    gates.some(k=>d.decision[k]!==false)||Object.keys(d.decision).length!==10)
    fail("FICTIONAL_AUTHORIZATION");
 return {ok:errors.length===0,errors:[...new Set(errors)],programme_percent:47,
     primary_pages_cited:7,plans_financed:0,independent_reviews:0,
     retained_services_certified:false,can_remove_fss:false};
}
