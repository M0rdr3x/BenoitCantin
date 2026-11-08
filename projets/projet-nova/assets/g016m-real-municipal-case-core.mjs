// Projet Nova G0.16m — un projet municipal réel; pas une recette fiscale Nova.
// Toute promesse, autorisation d'emprunt et programmation de dépenses conserve
// son périmètre juridique/comptable et ne devient pas un versement attesté.
export const S_IDS=Object.freeze(["GOV_AWARD","GOV_PRIMEAU_LIST","GOV_COMMITMENTS",
"CITY_PTI","CITY_BYLAW","CITY_MINUTES","CITY_PROGRESS"]);
export const PAGES=Object.freeze([
"https://www.quebec.ca/nouvelles/actualites/details/le-gouvernement-du-quebec-accorde-plus-de-146-m-a-warwick-63958",
"https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/demande_acces/2025/DAI_2025-082_subventions_primeau_2023_2033.pdf",
"https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2025/LIS_engagements_juin_2025.pdf",
"https://villedewarwick.quebec/wp-content/uploads/2025/12/Programme-triennal-des-immobilisations-2026-2027-2028.pdf",
"https://villedewarwick.quebec/wp-content/uploads/2025/03/R404-2025-Emprunt-usine-eau-potable-et-filiere-traitement-version-finale.pdf",
"https://villedewarwick.quebec/wp-content/uploads/2025/08/Proces-verbal-1er-juillet-2025.pdf",
"https://villedewarwick.quebec/etape-majeure-usine-eau-potable-warwick/"
]);
export const UNMET=Object.freeze([
"reconcile_2025_authorization_and_2026_plan","verify_grant_cash_paid",
"verify_loan_draws_and_interest","audit_final_work_cost",
"verify_service_quality_and_staff","assess_special_tax_effect_on_households"
]);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const unfilled=["local_cost_cad","award_paid_cad","borrowing_service_cad",
"household_tax_effect_cad","workforce_cost_cad","net_balance_cad"];
export function inspectG016mWarwickPilot(d,g016l){
 const errors=[],fail=x=>errors.push(x);
 if(!obj(d)||d.schema!=="nova-g016m-municipal-pilot/v1"||
    !Array.isArray(d.sources)||!Array.isArray(d.cases)||!obj(d.guards)||
    !obj(d.summary)||!Array.isArray(d.constitutional_budget)||!obj(d.decision))
    return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.phase!=="G0.16m"||d.date!=="2026-11-07"||
    d.status!=="ONE_VERIFIABLE_REAL_PUBLIC_PROJECT_NOT_FINANCIAL_CERTIFICATION"||
    d.adopted!==false||d.score_before!==47||d.score_after!==47)
    fail("PROGRAMME_MATURITY_NOT_PROVEN");
 if(!eq(d.sources.map(x=>x?.id),S_IDS)||
    !eq(d.sources.map(x=>x?.url),PAGES)||
    d.sources.some(x=>x.viewed_text!==true||
      x.pdf_visual_verified!==(x.id==="GOV_PRIMEAU_LIST")||
      x.other_pdf_screenshot_failed!==(x.id!=="GOV_PRIMEAU_LIST"&&x.url.endsWith(".pdf"))||
      typeof x.date!=="string"||!x.kind))
    fail("SOURCE_TRACEABILITY");
 if(d.cases.length!==1||!obj(d.cases[0]))return {ok:false,errors:["SINGLE_REAL_CASE_REQUIRED"],programme_score:47};
 const c=d.cases[0],a=c.award,p=c.city_2026_capital_plan,
 b=c.city_2025_bylaw,v=c.progress;
 if(c.id!=="WARWICK_GERARD_LAROCHE_WATER_PLANT"||c.municipality!=="Warwick"||
    c.region!=="Centre-du-Québec"||c.official_municipality_code!==null||
    c.asset!=="new_drinking_water_treatment_plant"||
    c.historically_confirmed_one_project!==true||
    c.fully_costed_for_nova_reform!==false)
    fail("PROJECT_IDENTITY");
 if(!obj(a)||a.programme!=="PRIMEAU_2023_2033"||
    a.status!=="AWARDED_NOT_PAYMENT_VERIFIED"||
    a.amount_cad!==14668901||a.max_eligible_cost_cad!==15440948||
    a.rounded_share_eligible_pct!==95||
    Math.round(100*a.amount_cad/a.max_eligible_cost_cad)!==95||
    a.government_date!=="2025-06-26"||
    a.letter_referenced_by_city_date!=="2025-06-09"||
    a.cash_paid_verified_cad!==null||a.commitments_not_disbursements!==true||
    a.beneficiary!=="VILLE_DE_WARWICK_NOT_NOVA"||
    !eq(a.government_commitments,[
      {fiscal:"2025-2026",committed_cad:9779266},
      {fiscal:"2026-2027",committed_cad:4889635}
    ])||
    a.government_commitments.reduce((s,x)=>s+x.committed_cad,0)!==a.amount_cad)
    fail("GRANT_COMMITMENT_NOT_PAYMENT");
 if(!obj(p)||p.source_id!=="CITY_PTI"||
    p.scope!=="YEAR_2026_CONSTRUCTION_LINE_NOT_TOTAL_LIFETIME"||
    p.project_cost_line_cad!==20074664||p.same_primeau_award_cad!==14668901||
    p.water_fund_budgeted_cad!==336823||p.borrowing_budgeted_cad!==5068940||
    p.actual_paid_or_borrowed_verified_cad!==null||
    p.same_primeau_award_cad+p.water_fund_budgeted_cad+p.borrowing_budgeted_cad!==p.project_cost_line_cad)
    fail("CITY_2026_PLAN_NOT_RECONCILED");
 if(!obj(b)||b.regulation!=="404-2025"||
    b.authorised_total_spending_cad!==27988101||
    b.gross_borrowing_authorization_cad!==27988101||
    b.building_scope_cad!==24677387||
    b.pretreatment_equipment_scope_cad!==2465614||
    b.hardness_equipment_scope_cad!==845100||
    b.loan_duration_years!==30||
    b.building_scope_cad+b.pretreatment_equipment_scope_cad+
      b.hardness_equipment_scope_cad!==b.authorised_total_spending_cad||
    b.special_tax_on_water_served_properties_in_bylaw!==true||
    b.outstanding_debt_verified_cad!==null||
    b.identical_scope_to_2026_pti!==false)
    fail("BYLAW_BORROWING_VERSUS_ACTUAL_DEBT");
 if(!obj(v)||v.municipal_update_date!=="2026-06-25"||
    v.reported_budget_used_percent!==50||
    v.reported_additions_percent!==0.39||
    v.planned_operation_month!=="2027-06"||
    v.independent_final_cost_verified!==false||
    v.finished_as_of_november_verified!==false)
    fail("NON_FINAL_CONSTRUCTION_STATUS");
 if(!eq(c.missing_proofs?.map(x=>x.id),UNMET)||
    c.missing_proofs.some(x=>x.status!=="OPEN"))
    fail("PROOFS_FALSELY_CLOSED");
 const safeguardKeys=["different_years_different_scopes","grant_promised_not_payment",
  "commitment_schedule_not_bank_payment","bylaw_gross_borrowing_not_outstanding_debt",
  "do_not_sum_pti_and_bylaw","eligible_grant_cost_not_lifetime_full_cost",
  "no_grant_to_nova","unverified_cash_is_null",
  "special_local_tax_may_have_household_effect",
  "no_extrapolation_from_one_project"];
 if(safeguardKeys.some(k=>d.guards[k]!==true)||Object.keys(d.guards).length!==safeguardKeys.length)
    fail("SCOPES_AND_FISCAL_PROTECTION");
 const t=d.summary;
 if(t.real_cases_documented!==1||t.awarded_primeau_cases!==1||
    t.awarded_total_cad!==14668901||
    t.grant_cash_disbursements_verified_cad!==null||
    t.actual_debt_cad!==null||t.net_cost_of_nova_reform_cad!==null||
    t.independent_fiscal_audit!==false)
    fail("FALSELY_AGGREGATED_PROJECT_MONEY");
 if(!eq(d.constitutional_budget.map(x=>x.id),
  ["QUEBEC_CANADA","QUEBEC_SOUVERAIN"])||
    d.constitutional_budget.some(s=>s.verified!==false||
       !Array.isArray(s.years)||s.years.length!==10||
       s.years.some((y,i)=>y?.year!==`${2026+i}-${2027+i}`||
         unfilled.some(k=>y[k]!==null))))
    fail("DECADAL_BUDGET_UNAUDITED");
 if(d.decision.g016m_real_project_researched!==true||
    ["municipal_cashflows_verified","new_fiscal_policy_approved",
     "independent_legal_audit","programme_complete"].some(k=>d.decision[k]!==false))
    fail("PREMATURE_GOVERNMENT_READINESS");
 if(g016l?.schema!=="nova-g016l-eau-financement-preuves/v1"||
    g016l.programme_score_after!==47||
    g016l.decisions?.g016l_financing_certified!==false)
    fail("INHERITED_G0_16L_NOT_CERTIFIED");
 return {ok:errors.length===0,errors:[...new Set(errors)],
  programme_score:47,real_source_backed_projects:1,
  confirmed_municipal_primeau_awards_cad:14668901,
  paid_cash_verified_cad:null,municipal_2026_plan_reconciled:true,
  independently_audited_nova_budget:false};
}
