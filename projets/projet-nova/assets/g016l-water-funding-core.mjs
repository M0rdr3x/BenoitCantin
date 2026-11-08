// Projet Nova G0.16l — autorisations de financement séparées des enveloppes publiques.
// Aucune ligne municipale du registre de base n'est encore sourcée ou homologuée.
// Les calculs hypothétiques sont EXCLUSIVEMENT des exercices synthétiques.
export const VERIFIED_SOURCES=Object.freeze([
["PGA_EAU","https://www.quebec.ca/habitation-territoire/infrastructures-municipales/plan-gestion-actif-pga/eau"],
["PRIMEAU","https://www.quebec.ca/habitation-territoire/infrastructures-municipales/programmes/eau-potable-eaux-usees/programme-infrastructures-municipales-eau-primeau"],
["TECQ","https://www.quebec.ca/habitation-territoire/infrastructures-municipales/programmes/eau-potable-eaux-usees/programme-transfert-infrastructures-eau-collectives-quebec-tecq-2024-2028"]
]);
export const MILESTONES=Object.freeze([
["PGA_COMMIT","PGA_EAU","2026-12-31","UPCOMING"],
["PGA_PLAN","PGA_EAU",null,"NO_FIXED_COMPLETION_DATE"],
["PGA_FOLLOW_UP","PGA_EAU","2028-01-01","FUTURE"],
["PRIMEAU_CALL_2026","PRIMEAU","2026-10-30","PAST_WINDOW"],
["PRIMEAU_PRESELECT_LIMIT","PRIMEAU","2028-03-31","FUTURE"],
["PRIMEAU_GRANT_LIMIT","PRIMEAU","2031-03-31","FUTURE"],
["TECQ_UPDATE_WINDOW","TECQ","2027-02-15","OPEN_WINDOW"],
["TECQ_WORK_ELIGIBILITY_END","TECQ","2028-12-31","FUTURE"],
["TECQ_FINAL_ACCOUNTING","TECQ","2029-06-30","FUTURE"]
]);
export const STAGES=Object.freeze(["ANNOUNCED_PROGRAMME","ELIGIBILITY_UNCHECKED",
"APPLICATION_SUBMITTED","SELECTION_PENDING","PROMISE_DOCUMENTED","PAYMENT_DOCUMENTED"]);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const allFalse=(obj,keys)=>keys.every(k=>obj?.[k]===false);
const allTrue=(obj,keys)=>keys.every(k=>obj?.[k]===true);
const amounts=["municipal_capex_cad","verified_tecq_awards_cad",
"verified_primeau_awards_cad","verified_other_financing_cad","local_tax_replacement_cad",
"worker_costs_cad","operating_impact_cad","net_gap_cad"];

export function inspectG016lFundingSources(d,g016k){
 const errors=[],bad=x=>errors.push(x);
 if(!obj(d)||d.schema!=="nova-g016l-eau-financement-preuves/v1"||
  !obj(d.underlying_evidence)||!Array.isArray(d.sources)||
  !Array.isArray(d.official_milestones)||!Array.isArray(d.programme_funding)||
  !Array.isArray(d.grant_evidence_stages)||!Array.isArray(d.project_register)||
  !obj(d.project_schema_contract)||!obj(d.decision_rules)||
  !obj(d.regional_readiness)||!Array.isArray(d.constitutional_models)||
  !Array.isArray(d.unmet_conditions)||!obj(d.decisions))
    return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.phase!=="G0.16l"||d.as_of!=="2026-11-07"||
    d.status!=="OFFICIAL_RULES_REGISTERED_NO_LOCAL_GRANTS_VERIFIED"||
    d.programme_score_before!==47||d.programme_score_after!==47)
    bad("PROGRAMME_STATUS_UNVERIFIED");
 const e=d.underlying_evidence;
 if(e.g016k!=="data/continuite-actifs-eau-g0-16k-2025.json"||
    e.g016j!=="data/ventilation-charges-municipales-g0-16j-2024.json"||
    e.stock_2025_replacement_gcad!==197.6||
    e.poor_condition_asset_replacement_gcad!==20.6||
    e.historical_water_and_sewer_cost_2024_cad!==2519426792||
    e.underfunding_for_nova_cad!==null||
    e.not_annual_repair_funding!==true||e.not_same_municipalities_or_year!==true||
    g016k?.schema!=="nova-g016k-water-assets-continuity/v1"||
    g016k?.programme_score_after!==47||
    g016k?.assets_2025?.total_replacement_gcad!==197.6||
    g016k?.assets_2025?.poor_very_poor_replacement_gcad!==20.6||
    g016k?.municipal_water_operating_2024?.expense_cad!==2519426792)
    bad("SOURCE_ASSETS_AND_COSTS_MIXED");
 if(!same(d.sources.map(x=>[x?.id,x?.url]),VERIFIED_SOURCES)||
    d.sources.some(x=>x.checked_on!=="2026-11-07"||!x.issuer||
    !x.type))bad("SOURCE_URLS_NOT_VERIFIED");
 if(!same(d.official_milestones.map(x=>[
     x?.id,x?.source,x?.date,x?.as_of_status]),MILESTONES)||
    d.official_milestones.some(x=>!x.fact||
      x.automatically_mandatory_for_every_city!==false||
      typeof x.constitutes_final_plan!=="boolean")||
    d.official_milestones.find(x=>x.id==="PRIMEAU_CALL_2026")?.open_date!=="2026-08-31"||
    d.official_milestones.find(x=>x.id==="TECQ_UPDATE_WINDOW")?.open_date!=="2026-10-01"||
    d.official_milestones.find(x=>x.id==="PGA_PLAN")?.constitutes_final_plan!==true||
    d.official_milestones.find(x=>x.id==="PGA_COMMIT")?.constitutes_final_plan!==false)
    bad("IMPORTANT_DATES_FALSIFIED");
 const funds=d.programme_funding;
 if(funds.length!==2||funds[0]?.id!=="PRIMEAU"||
    funds[0]?.announced_envelope_cad!==2400000000||
    funds[0]?.amount_relation!=="EQUAL_ANNOUNCED_ENVELOPE"||
    funds[0]?.start_year!==2023||funds[0]?.end_year!==2033||
    funds[1]?.id!=="TECQ"||
    funds[1]?.announced_envelope_floor_cad!==3300000000||
    funds[1]?.amount_relation!=="MORE_THAN"||
    funds[1]?.start_year!==2024||funds[1]?.end_year!==2028||
    funds.some(x=>x.grant_to_nova_cad!==null||
      x.municipality_specific_awards_verified_cad!==null||
      x.awaiting_project_approval!==true||x.not_auto_approved!==true))
    bad("ENVELOPE_MISREPRESENTED_AS_AWARD");
 if(!same(d.grant_evidence_stages,STAGES)||
    !Array.isArray(d.project_register)||d.project_register.length!==0||
    Object.keys(d.project_schema_contract).length!==7||
    !same(d.project_schema_contract.required_grant_fields,
      ["programme","stage","amount_cad","award_document_url","verified_against_issuer"]))
    bad("PROJECT_DATA_CANNOT_BE_FABRICATED");
 const truths=["published_envelope_never_considered_awarded_to_project",
   "eligibility_is_not_application","application_is_not_award",
   "promise_is_not_cash_disbursement","no_tax_removal_until_replacement_financing_verified",
   "project_cost_without_documentation_not_known","no_project_cost_from_197_6b_stock",
   "avoid_double_count_tecq_primeau_same_expense",
   "federal_tecq_not_automatic_sovereign_funding",
   "fiscal_years_are_local_and_scenario_specific","missing_cost_is_null_not_zero",
   "legal_and_external_review_still_required"];
 if(!allTrue(d.decision_rules,truths))bad("KEY_FUNDING_DISTINCTIONS_LOST");
 const r=d.regional_readiness;
 if(!r||r.municipality_level_project_costs_imported!==0||
    r.municipality_level_approved_awards_verified!==0||
    r.municipality_level_submitted_pga_documents_verified!==0||
    r.all_municipalities_covered!==false||
    r.critical_facilities_with_verified_risk_scores!==0||
    r.real_2026_2036_investment_gap_cad!==null)
    bad("UNSUBSTANTIATED_MUNICIPAL_READINESS");
 const ss=d.constitutional_models;
 if(!same(ss.map(x=>x?.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"])||
    ss.some(s=>s.approved!==false||s.independently_audited!==false||
      !Array.isArray(s.budget_years)||s.budget_years.length!==10||
      s.budget_years.some((y,i)=>y?.year!==`${2026+i}-${2027+i}`||
        y.constitutional_transfer_legality_reviewed!==false||
        amounts.some(k=>y[k]!==null))))
    bad("TEN_YEAR_BUDGET_UNSUBSTANTIATED");
 if(d.unmet_conditions.length!==6||
    !same(d.unmet_conditions.map(x=>x?.id),
      ["GATE_01","GATE_02","GATE_03","GATE_04","GATE_05","GATE_06"])||
    d.unmet_conditions.some(x=>x.status!=="NO_EVIDENCE"||!x.requirement))
    bad("MISSING_DOCUMENTARY_PROOFS");
 if(d.decisions.official_programme_rules_documented!==true||
    !allFalse(d.decisions,["local_awards_verified","g016l_financing_certified",
      "programme_complete","legal_tax_changes_adopted","external_audit_signed"]))
    bad("PREMATURE_CONCLUSION");
 return {ok:errors.length===0,errors:[...new Set(errors)],
   programme_score:47,official_milestones:9,
   verified_municipal_awards:0,approved_tax_replacement_cad:null,
   two_scenarios_funded:false};
}

// Pure sandbox arithmetic only, not verification or calculation of actual municipal grants.
// A genuine application must be separately examined against source documents.
export function calculateSyntheticFundingExercise(p){
 if(!obj(p)||p.mode!=="SYNTHETIC_EXERCISE"||
    p.synthetic_label!==true||!Number.isSafeInteger(p.total_cost_cad)||
    p.total_cost_cad<0||!Array.isArray(p.commitments))
    throw new Error("SYNTHETIC_ONLY_NOT_REAL_FUNDING");
 const promises=new Set(),allowed=["PRIMEAU","TECQ","OTHER"];
 let pledged=0,paid=0;
 for(const c of p.commitments){
   if(!obj(c)||!allowed.includes(c.programme)||
      !["PROMISE_DOCUMENTED","PAYMENT_DOCUMENTED"].includes(c.stage)||
      !Number.isSafeInteger(c.amount_cad)||c.amount_cad<0||
      typeof c.synthetic_reference!=="string"||!c.synthetic_reference||
      promises.has(c.synthetic_reference))
      throw new Error("INVALID_SYNTHETIC_COMMITMENT");
   promises.add(c.synthetic_reference);
   pledged+=c.amount_cad;
   if(c.stage==="PAYMENT_DOCUMENTED")paid+=c.amount_cad;
 }
 if(!Number.isSafeInteger(pledged)||!Number.isSafeInteger(paid)||
    pledged>p.total_cost_cad)
    throw new Error("OVERFUNDED_OR_UNSAFE_SYNTHETIC_CASE");
 return {
  mode:"SYNTHETIC_EXERCISE",not_real_awards:true,
  total_cost_cad:p.total_cost_cad,
  synthetic_promises_cad:pledged,
  synthetic_paid_cad:paid,
  promised_but_not_paid_cad:pledged-paid,
  gap_after_promises_cad:p.total_cost_cad-pledged,
  gap_after_cash_payments_cad:p.total_cost_cad-paid,
  project_legally_funded:false,
  independent_validation:false
 };
}
