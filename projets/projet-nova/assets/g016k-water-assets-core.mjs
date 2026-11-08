// Projet Nova G0.16k : séparation stricte entre stock d'actifs 2025,
// dépenses historiques de fonctionnement 2024 et budgets futurs non financés.
// Les 20,6 G$ d'actifs en classe D/E NE SONT PAS un coût de travaux à engager.
export const ASSET_TYPES=Object.freeze([
 ["POTABLE_PIPES","LINEAR",44571,"km",60.2],
 ["WASTEWATER_PIPES","LINEAR",36761,"km",64.3],
 ["STORMWATER_PIPES","LINEAR",19773,"km",35.2],
 ["POTABLE_FACILITIES","FACILITY",4593,"facilities",17.9],
 ["WASTEWATER_FACILITIES","FACILITY",6066,"facilities",20.0]
]);
export const SOURCE_IDS=Object.freeze(["CERIU_2025","GOV_PGA_2026","MAMH_EXPENSES_2024"]);
export const SCENARIOS=Object.freeze(["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const positiveSafe=x=>Number.isSafeInteger(x)&&x>0;
const annualAmountFields=["water_opex_cad","asset_renewal_capex_cad","local_repair_need_cad",
 "workers_pensions_cad","grants_net_cad","replacement_tax_revenue_cad",
 "borrowing_cad","net_balance_cad"];
export function inspectG016kWaterContinuity(d,g016j,g016h){
 const failures=[],fail=code=>failures.push(code);
 if(!obj(d)||d.schema!=="nova-g016k-water-assets-continuity/v1"||
    !Array.isArray(d.sources)||!obj(d.assets_2025)||
    !obj(d.municipal_water_operating_2024)||!obj(d.government_plans)||
    !Array.isArray(d.risk_register)||!obj(d.accounting_barriers)||
    !Array.isArray(d.continuity_scenarios)||!Array.isArray(d.unmet_evidence)||
    !obj(d.decisions))return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.stage!=="G0.16k"||d.record_date!=="2026-11-07"||
    d.programme_score_before!==47||d.programme_score_after!==47||
    d.status!=="ASSET_EXPOSURE_RECORDED_NOT_FUNDED"||
    d.adopted!==false)fail("FALSE_SCORE_OR_STATUS");
 if(!eq(d.sources.map(x=>x?.id),SOURCE_IDS)||
   d.sources.some(s=>!obj(s)||!s.url?.startsWith("https://")||
    !positiveSafe(s.year)||s.independently_reviewed_for_nova!==false)||
   d.sources[0].url!=="https://ceriu.qc.ca/system/files/2026-03/Portrait_infrastructures_eau_municipalites_Quebec-2025.pdf"||
   d.sources[1].url!=="https://www.quebec.ca/habitation-territoire/infrastructures-municipales/plan-gestion-actif-pga/eau"||
   d.sources[2].url!==g016h?.source?.url)
   fail("PROVENANCE_NOT_REVIEWED");
 const a=d.assets_2025;
 const assetNums=["total_replacement_gcad","prior_2024_replacement_gcad",
 "linear_subtotal_gcad","facility_subtotal_gcad","very_good_or_good_share_pct",
 "acceptable_share_pct","poor_very_poor_share_pct",
 "acceptable_replacement_gcad","poor_very_poor_replacement_gcad",
 "pipes_total_km","facilities_total","reporting_municipalities_since_2014",
 "municipality_share_reported_pct","represented_population_share_pct",
 "updated_2025_municipalities","water_pipe_reporting_municipalities",
 "approx_percent_values_assessed_age_or_judgment",
 "bad_assets_age_or_judgment_share_pct",
 "acceptable_assets_age_or_judgment_share_pct",
 "value_assessed_age_or_judgment_gcad",
 "poor_assets_age_or_judgment_gcad",
 "acceptable_assets_age_or_judgment_gcad",
 "poor_assets_in_cities_above_100k_gcad",
 "poor_assets_in_cities_above_100k_share_approx_pct"];
 const assetExpected=[197.6,188.5,159.7,37.9,67,23,10,44.9,20.6,
 101105,10659,938,85,99,666,903,75,43,87,147.9,8.8,39.1,14.8,72];
 if(!eq(assetNums.map(k=>a[k]),assetExpected)||
    !Array.isArray(a.asset_types)||a.asset_types.length!==5||
    a.asset_types.some((t,i)=>!eq([
     t.id,t.kind,t.count,t.units,t.replacement_gcad],ASSET_TYPES[i]))||
    Math.round(a.asset_types.reduce((sum,t)=>sum+t.replacement_gcad,0)*10)!==1976||
    a.asset_types.filter(t=>t.kind==="LINEAR").reduce((sum,t)=>sum+t.count,0)!==101105||
    a.asset_types.filter(t=>t.kind==="FACILITY").reduce((sum,t)=>sum+t.count,0)!==10659||
    a.very_good_or_good_share_pct+a.acceptable_share_pct+
      a.poor_very_poor_share_pct!==100||
    a.asset_types.length!==5)fail("ASSET_INVENTORY_UNCORROBORATED");
 // Correct field name is explicitly required; a misspelled flag must not silently pass.
 if(a.includes_road_reinstatement_on_trench_width!==true||
    a.replacement_value_is_not_2026_budget!==true||
    a.poor_assets_full_replacement_not_always_required!==true||
    a.data_scope_different_from_mamh_2024!==true||
    a.external_nova_audit_complete!==false)
    fail("ASSET_STOCK_NOT_FUTURE_CASH");
 const cost=d.municipal_water_operating_2024;
 const priorWater=g016j?.non_overlapping_observed_subsets?.find(x=>x.id==="EAU_EGOUTS");
 if(!obj(cost)||cost.source_id!=="MAMH_EXPENSES_2024"||
   cost.expense_cad!==2519426792||cost.expense_cad!==priorWater?.y2024||
   cost.municipalities_included!==1056||
   cost.expenses_already_in_mamh_2024_total!==true||
   cost.same_scope_as_ceriu_sample!==false||
   cost.expense_plus_asset_value_meaningful!==false||
   cost.derived_repair_backlog_cad!==null||
   cost.proved_renewal_funding_cad!==null||
   g016h?.annual?.[0]?.total_expenses_cad!==28366959822)
   fail("ANNUAL_EXPENSE_STOCK_CONFUSION");
 const p=d.government_plans;
 if(p.source_id!=="GOV_PGA_2026"||
   p.invited_commitment_deadline!=="2026-12-31"||
   p.engagement_is_final_pga_approval!==false||
   p.engagement_involves_municipal_resolution!==true||
   p.automatically_mandatory_for_all_municipalities!==false||
   p.municipal_plans_fully_submitted_verified!==null||
   p.future_10_year_renewal_budget_verified!==false)
   fail("PGA_DEADLINE_MISSTATED");
 const riskIds=["DRINKING_WATER","WASTEWATER","FLOODING","WORKERS",
 "INFLATION","DOUBLE_COUNT","FINANCING"];
 if(!eq(d.risk_register.map(x=>x?.id),riskIds)||
   d.risk_register.some(r=>!["CRITICAL","HIGH"].includes(r.priority)||
     !r.description||r.remediation_cost_cad!==null||
     r.decision_approved!==false))fail("ASSET_RISKS_NOT_FINANCED");
 const safeguards=["stock_2025_not_annual_flow_2024",
  "bad_condition_stock_not_due_replacement_cost","category_C_not_automatically_due",
  "road_trench_restoration_not_added_to_separate_total",
  "provincial_and_municipal_finances_not_simple_sum",
  "no_2026_to_2036_budget_inferred"];
 if(safeguards.some(k=>d.accounting_barriers[k]!==true))
   fail("ACCOUNTING_DOUBLE_COUNT_RISK");
 if(!eq(d.continuity_scenarios.map(x=>x?.id),SCENARIOS)||
   d.continuity_scenarios.some(s=>s.legal_authority_verified!==false||
     s.municipal_coverage_audited!==false||
     s.workforce_obligations_approved!==false||
     s.external_financial_audit!==false||
     !Array.isArray(s.annual)||s.annual.length!==10||
     s.annual.some((row,i)=>row?.year!==`${2026+i}-${2027+i}`||
       annualAmountFields.some(k=>row[k]!==null)||
       row.independently_verified!==false)))
    fail("DECADAL_BUDGET_INVENTED");
 if(d.unmet_evidence.length!==6||
   d.unmet_evidence.some((x,i)=>x.id!=="E"+String(i+1).padStart(2,"0")||
    x.status!=="MISSING"||typeof x.need!=="string"||!x.need))
    fail("PROOFS_UNSUPPORTED");
 const decisionFields=["full_g016k_gate_passed","tax_reduction_financed",
   "renewal_investments_funded","employee_rights_certified",
   "program_budget_complete","independent_review_obtained"];
 if(d.decisions.source_assessment_recorded!==true||
    decisionFields.some(k=>d.decisions[k]!==false)||
    Object.keys(d.decisions).length!==7)fail("APPROVAL_PREMATURE");
 if(g016j?.schema!=="nova-g016j-municipal-service-costs/v1"||
    g016j.score_after!==47||g016h?.schema!=="nova-g016h-finances-municipales-observees/v1"||
    g016h.programme_score_after!==47)
    fail("UPSTREAM_DATA_INCONSISTENT");
 return {ok:failures.length===0,errors:[...new Set(failures)],programme_score:47,
   observed_asset_replacement_gcad:197.6,poor_condition_asset_value_gcad:20.6,
   observed_2024_water_opex_cad:2519426792,municipalities_in_asset_data:938,
   verified_repair_cost_cad:null,certified_10_year_budgets:0};
}
