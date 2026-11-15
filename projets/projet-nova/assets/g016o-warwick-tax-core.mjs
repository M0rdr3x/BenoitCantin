// Nova G0.16o — les taux de Warwick 2026 ne sont PAS des taux d'impot Nova.
// Exemple partiel strictement fictif: jamais une facture reelle ni une economie future.
export const OBSERVED_RATES=Object.freeze([
["RESIDENCE_BASE","2.1",0.575,true],
["SPECIAL_FIREHALL_165_2012","3.4",0.0123,true],
["SPECIAL_FIRETRUCK_233_2017","3.5",0.0061,true],
["SPECIAL_FIRETRUCK_305_2020","3.6",0.0035,true],
["SPECIAL_ROADS_2026","3.7",0.025,true],
["SPECIAL_STREETS_357_2022","3.9",0.0155,true],
["SPECIAL_SANITATION","3.1",0.101,false],
["SPECIAL_BASIN_229_2017","3.3",0.0056,false],
["SPECIAL_STREETS_357_2022_WATER","3.8",0.0114,false],
["SPECIAL_MRC_RURAL_WATERCOURSE","3.2",0.0155,false]
]);
export const FLAT_CHARGES=Object.freeze([
["WATER_RESIDENTIAL",102],["SEWER_RESIDENTIAL",31.25],
["WASTE_URBAN",283],["WASTE_RURAL",267]
]);
export const SOURCE_URLS=Object.freeze([
"https://villedewarwick.quebec/wp-content/uploads/2026/02/R415-2025-Taux-de-taxes-et-compensations-2026.pdf",
"https://villedewarwick.quebec/wp-content/uploads/2026/02/R416-2025-Tarification-pour-lexercice-2026.pdf",
"https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/infrastructures/primeau/GUI_primeau_aout_2026.pdf",
"https://villedewarwick.quebec/wp-content/uploads/2025/03/R404-2025-Emprunt-usine-eau-potable-et-filiere-traitement-version-finale.pdf"
]);
const isObj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const equal=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const unknown=["property_tax_replaced_cad","net_grants_received_cad","municipal_services_cost_cad",
"loan_service_cost_cad","worker_obligations_cost_cad","replacement_funding_cad","net_budget_cad"];
const flags=[
"taxes_municipal_in_existing_canada_scenario_not_identical_to_provincial_income_tax",
"warwick_local_2026_rates_not_quebec_wide_rates",
"removing_property_tax_requires_legal_replacement_funding_and_borrowing_continuity",
"published_property_rate_not_household_ability_to_pay","tax_per_100_assessed_not_tax_per_100_income",
"rates_are_not_all_cumulative_for_all_homes","grant_announcement_not_cash_received",
"grant_rules_not_project_specific_payment_proof",
"lack_of_documentary_payment_evidence_not_proof_of_no_payment",
"jurisdiction_review_not_done","independent_audit_not_done"
];
export function calculateSyntheticWarwickPart(input){
 if(!isObj(input)||input.mode!=="SYNTHETIC_PARTIAL_EXAMPLE"||
    input.approved_example!==true||!Number.isSafeInteger(input.assessed_value_cad)||
    input.assessed_value_cad<0||input.assessed_value_cad>1000000000||
    input.property_class!=="RESIDUAL_RESIDENTIAL"||
    input.urban_waste_collection!==true||input.one_unit!==true||
    input.water_connected!==true||input.sewer_connected!==true)
    throw new Error("SYNTHETIC_ONLY_NOT_ACTUAL_BILL");
 const sumRate=OBSERVED_RATES.filter(x=>x[3]).reduce((s,x)=>s+x[2],0);
 const property=Number((input.assessed_value_cad/100*sumRate).toFixed(2));
 const fixed=102+31.25+283;
 return {property_tax_rate_sum_cad_per_100:Number(sumRate.toFixed(4)),
 property_tax_subtotal_cad:property,selected_fixed_services_subtotal_cad:fixed,
 partial_example_subtotal_cad:Number((property+fixed).toFixed(2)),
 actual_total_tax_bill_cad:null,assumed_404_2025_project_tax_cad:null,
 includes_all_special_tax_rates:false,real_tax_saving_nova_cad:null};
}
export function inspectG016oWarwickTaxes(d,m,n){
 const errors=[],fail=k=>errors.push(k);
 if(!isObj(d)||d.schema!=="nova-g016o-warwick-2026-taxes-grant-proof/v1"||
    !Array.isArray(d.sources)||!isObj(d.observed_2026_tax_rules)||
    !isObj(d.synthetic_household_example)||!isObj(d.primeau_current_guide_rules)||
    !Array.isArray(d.sample_cash_evidence)||!isObj(d.fiscal_interpretation)||
    !Array.isArray(d.ten_year_unfunded_scenarios)||!isObj(d.decision))
   return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.phase!=="G0.16o"||d.date!=="2026-11-07"||
   d.status!=="REAL_2026_TAX_RULES_AND_GRANT_CLAIMS_NOT_CASH_AUDIT"||
   d.programme_score_before!==47||d.programme_score_after!==47||d.adopted!==false)
   fail("FALSE_PROGRAMME_STATUS");
 if(!equal(d.sources.map(s=>s?.url),SOURCE_URLS)||
   !equal(d.sources.map(s=>s?.id),
       ["WARWICK_R415_2026","WARWICK_R416_2026",
        "MAMH_PRIMEAU_GUIDE_2026_08","WARWICK_404_2025"])||
   d.sources.some(s=>s.text_read!==true||s.visual_screen_verified!==false)||
   d.sources[0].entered_into_force!=="2026-01-14"||
   d.sources[0].council_adopted!=="2026-01-12"||
   d.sources[2].version_date!=="2026-08")
   fail("ACTUAL_SOURCE_SCOPE");
 const o=d.observed_2026_tax_rules;
 if(o.municipality!=="Warwick"||o.fiscal_year!==2026||
   o.published_tax_regulation!=="415-2025"||
   !equal(o.tax_rates_cad_per_100_assessment?.map(x=>[
       x.id,x.article,x.rate_cad_per_100,x.mandatory_for_illustrative_residence
      ]),OBSERVED_RATES)||
   o.tax_rates_cad_per_100_assessment.some(x=>x.linked_to_404_2025!==false)||
   !equal(o.fixed_compensations_cad_per_unit?.map(x=>[x.id,x.amount_cad]),FLAT_CHARGES))
   fail("TAX_RATES_WRONG_OR_UNJUSTIFIED");
 const rulesFalse=["ordinary_property_assessment_extracted_for_a_specific_home"];
 const rulesTrue=["r415_does_not_name_404_2025_explicitly",
   "lack_of_named_404_rate_does_not_prove_zero_liability",
   "other_municipal_by_laws_may_create_additional_charges",
   "property_classification_and_sector_matter",
   "all_applicable_special_rates_unknown_for_any_particular_home"];
 if(rulesFalse.some(k=>o[k]!==false)||rulesTrue.some(k=>o[k]!==true)||
   o.actual_bill_paid_for_a_specific_home_cad!==null||
   o.new_plant_404_2025_specific_2026_tax_rate_cad_per_100!==null||
   o.user_taxes_2026_paid_aggregate_cad!==null)
   fail("ACTUAL_HOUSEHOLD_BILL_NOT_PROVEN");
 const e=d.synthetic_household_example;
 const calculated=calculateSyntheticWarwickPart({
  mode:"SYNTHETIC_PARTIAL_EXAMPLE",approved_example:true,
  assessed_value_cad:300000,property_class:"RESIDUAL_RESIDENTIAL",
  urban_waste_collection:true,one_unit:true,water_connected:true,sewer_connected:true});
 if(e.strictly_hypothetical!==true||e.real_person_or_property!==false||
   e.assessed_value_cad!==300000||e.property_class!=="RESIDUAL_RESIDENTIAL"||
   ["urban_waste_collection","one_unit","water_connected","sewer_connected",
    "conditional_sanitation_tax_not_included",
    "conditional_sector_specific_debt_taxes_not_included",
    "new_404_2025_taxes_not_included_as_unverified"].some(k=>e[k]!==true)||
   Object.keys(calculated).slice(0,4).some(k=>e[k]!==calculated[k])||
   e.water_flat_cad!==102||e.sewer_flat_cad!==31.25||
   e.urban_waste_flat_cad!==283||
   e.actual_total_tax_bill_cad!==null||
   e.source_for_2026_assessed_value!=="SYNTHETIC_EXAMPLE_NO_ASSESSMENT_ROLL"||
   e.full_bill_guaranteed!==false||
   e.distributive_burden_claim!==false||e.nova_tax_saving_predicted_cad!==null)
   fail("SYNTHETIC_EXAMPLE_MISREPRESENTED");
 const g=d.primeau_current_guide_rules;
 if(g.guide_date!=="2026-08"||
   g.source_id!=="MAMH_PRIMEAU_GUIDE_2026_08"||
   g.partial_claim_maximum_share_pct!==90||
   ["applicability_to_existing_2025_awards_requires_convention_review",
    "prior_subprogramme_1_2_keeps_original_claim_cycle_per_government_site",
    "partially_paid_only_after_approved_claims_not_automatic",
    "partial_claim_limit_is_not_confirmed_paid_pct",
    "final_claim_requires_cost_records_and_paid_invoices",
    "up_to_ten_percent_may_be_held_on_selected_final_audits",
    "initial_payment_only_if_agreement_so_provides",
    "certain_projects_may_have_ministerial_final_verification"].some(k=>g[k]!==true)||
   ["ten_percent_holdback_applies_to_every_project",
    "any_initial_payment_verified_for_sample",
    "applies_only_after_individual_agreement_checked"].some(k=>g[k]!==false))
   fail("PRIMEAU_GUIDE_NOT_PAYMENT");
 if(d.sample_cash_evidence.length!==6||
   d.sample_cash_evidence.some((x,i)=>
      x.id!=="E"+(i+1)||x.status!=="NOT_VERIFIED"||!x.required))
   fail("CASH_AUDIT_STILL_MISSING");
 if(flags.some(k=>d.fiscal_interpretation[k]!==true)||
    d.warwick_case_link!=="data/cas-municipal-reel-g0-16m-warwick-eau-2025-2026.json"||
    d.regional_portfolio_link!=="data/comparatif-cas-reels-primeau-g0-16n-2025.json")
   fail("FISCAL_DISTINCTIONS");
 if(!equal(d.ten_year_unfunded_scenarios.map(x=>x?.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"])||
  d.ten_year_unfunded_scenarios.some(s=>s.legally_reviewed!==false||
    s.independently_verified!==false||s.years.length!==10||
    s.years.some((y,i)=>y.year!==`${2026+i}-${2027+i}`||
      unknown.some(k=>y[k]!==null))))
   fail("FINANCING_SCENARIO_NOT_PROVEN");
 const decision=d.decision;
 if(decision.g016o_actual_local_tax_rates_recorded!==true||
   decision.g016o_partial_synthetic_bill_reproducible!==true||
   ["g016o_actual_household_tax_bills_verified","g016o_individual_grant_cash_verified",
   "g016o_404_tax_in_current_bill_confirmed","g016o_fiscal_sustainability_audited",
   "programme_complete"].some(k=>decision[k]!==false))
   fail("UNWARRANTED_POLICY_APPROVAL");
 if(m?.schema!=="nova-g016m-municipal-pilot/v1"||m.score_after!==47||
    m.cases?.[0]?.award?.amount_cad!==14668901||
    m.cases?.[0]?.award?.cash_paid_verified_cad!==null||
    n?.schema!=="nova-g016n-primeau-comparatif-cas-v1"||
    n.programme_score_after!==47||n.derived_summary?.sum_awarded_cad!==156721180||
    n.derived_summary?.confirmed_paid_sum_cad!==null)
   fail("UPSTREAM_CASES_NOT_CASH_VERIFIED");
 return {ok:errors.length===0,errors:[...new Set(errors)],programme_score:47,
   verified_2026_tax_rates:10,synthetic_partial_subtotal_cad:2328.45,
   legal_2026_bills_audited:0,grants_cash_disbursements_audited:0};
}
