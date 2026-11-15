// G0.17c – chiffres historiques MAMH et interdiction des doubles comptes.
const okObj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const exact=(x,y)=>Math.round(x*10)===Math.round(y*10);
const vals=[["PROPERTY",15.0],["GOVERNMENT_TRANSFERS",7.4],["SALES",3.2],["TARIFF",2.2],["TRANSFER_DUTY",1.3],["OTHER",2.2]];
export function auditG017c(d,b,v){
 const errors=[],bad=x=>errors.push(x);
 if(!okObj(d)||d.schema!=="nova-g017c-water-municipal-revenue-evidence/v1"||!okObj(d.municipal)||!okObj(d.water))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.17c"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.points_remaining!==53||d.decision?.score_point_earned!==false||d.decision?.programme_certified!==false)bad("NO_FALSE_COMPLETENESS");
 if(b?.schema!=="nova-g017b-mamh-2024-2025-import-contract/v1"||b?.score_after!==47||b?.datasets?.some(x=>x.local_csv_imported!==false)||v?.schema!=="nova-g016v-two-levies-public-finance-reference/v1"||v?.programme_audit_after!==47)bad("UPSTREAM");
 const src=d.sources;
 if(!Array.isArray(src)||src.length!==3||src[0].id!=="M24"||src[0].source_year!==2024||src[0].source_method!=="PDF_TEXT_EXTRACTION"||src[0].screenshot_succeeded!==false||src[0].csv_crosscheck_done!==false||src[1].id!=="W23"||src[1].source_year!==2023||src[1].screenshot_page_index_20_succeeded!==true||src[2].raw_rows_imported!==false)bad("SOURCE_LIMITATIONS");
 const m=d.municipal;
 if(m.year!==2024||m.scope!=="QUEBEC_CONSOLIDATED_MUNICIPAL_ORGANIZATIONS"||m.unit!=="BILLION_CAD_1_DECIMAL_ROUNDED"||!exact(m.total_revenue_gcad,31.3)||!Array.isArray(m.components)||m.components.length!==6||m.components.some((x,i)=>x.id!==vals[i][0]||!exact(x.amount_gcad,vals[i][1]))||!exact(m.components.reduce((s,x)=>s+x.amount_gcad,0),m.total_revenue_gcad)||!exact(m.nontransfer_own_source_revenue_approx_gcad,23.9)||m.source_official_property_tax_share_pct!==47.8||m.source_official_own_revenue_share_pct!==76.5||m.verified_raw_municipal_csv!==false||m.actual_total_year_2025_gcad!==null||m.actual_total_year_2026_gcad!==null||m.municipal_replacement_year_2026_gcad!==null||m.same_year_transfer_cancellation_verified!==false)bad("MUNICIPAL_HISTORICAL_ONLY");
 const w=d.water;
 if(w.year!==2023||w.municipal_reports!==669||w.eligible_municipalities!==849||w.population_served_coverage_pct!==96||!exact(w.reported_approx_annual_revenue_gcad,2.4)||!exact(w.reported_approx_full_service_cost_gcad,6.0)||w.reported_coverage_pct!==40||!exact(w.calculated_illustrative_uncovered_full_cost_gcad,3.6)||Math.abs(w.reported_approx_annual_revenue_gcad/w.reported_approx_full_service_cost_gcad-0.4)>1e-9||!okObj(w.revenue_mix_pct)||w.revenue_mix_pct.volumetric!==7||w.revenue_mix_pct.nonvolumetric!==36||w.revenue_mix_pct.property!==50||w.revenue_mix_pct.other!==7||Object.values(w.revenue_mix_pct).reduce((s,x)=>s+x,0)!==100||w.full_cost_contains_operations_and_average_ten_year_asset_investment_needs!==true||w.illustrative_gap_is_not_annual_cash_deficit!==true||w.actual_full_cost_year_2026_gcad!==null)bad("WATER_2023_NOT_DEFICIT");
 if(!okObj(d.controls)||Object.values(d.controls).some(x=>x!==true))bad("GUARDRAILS");
 if(!Array.isArray(d.scenarios)||d.scenarios.length!==2||d.scenarios[0].id!=="QUEBEC_CANADA"||d.scenarios[1].id!=="QUEBEC_SOUVERAIN"||d.scenarios[0].conditional_provincial_need_mcad!==v.conditional_accounting.canada_provincial_two_levies_accounting_target_mcad||d.scenarios[1].partial_no_federal_transfers_stress_mcad!==v.conditional_accounting.sovereign_zero_federal_transfers_same_provincial_spending_stress_mcad||d.scenarios.some(x=>x.municipal_net_replacement_mcad!==null||x.validated!==false)||d.scenarios[1].full_national_cost_mcad!==null)bad("NO_FINANCED_NOVA_RATE");
 if(d.next_checks?.length!==6||d.decision?.historical_official_totals_integrated!==true||d.decision?.raw_2024_2025_csv_imported!==false||d.decision?.municipal_net_replacement_costed!==false)bad("OPEN_GATES");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,municipal_2024_revenue_gcad:31.3,water_2023_approx_cost_gcad:6,year2026_rate_pct:null,year2025_revenue_verified_gcad:null};
}
// Illustrative arithmetic only, no statement about a cash deficit or projected 2026 funding.
export function approximateWaterHistoricalFullCostGap(revenue_gcad,cost_gcad,{mode}={}){
 if(mode!=="HISTORICAL_2023_ONLY"||!Number.isFinite(revenue_gcad)||!Number.isFinite(cost_gcad)||revenue_gcad<0||cost_gcad<=0||revenue_gcad>cost_gcad)throw Error("HISTORICAL_INPUTS_ONLY");
 return {uncovered_full_cost_approx_gcad:Number((cost_gcad-revenue_gcad).toFixed(2)),isActualMunicipalDeficit:false,is2026RequiredTaxRevenue:false};
}
