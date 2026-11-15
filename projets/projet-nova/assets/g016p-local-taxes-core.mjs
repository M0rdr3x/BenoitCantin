// G0.16p : contrôles de fiscalité municipale. Aucun taux Nova ni facture réelle estimés.
const isObj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const cashKeys=["property_tax_replacement_cad","municipal_service_costs_cad","employees_and_pensions_cad","debt_service_cad","grants_cash_verified_cad","replacement_revenue_cad","balance_cad"];
export function lavalSynthetic(input){
 if(!isObj(input)||input.mode!=="SYNTHETIC_PARTIAL_ONLY"||input.approved!==true||input.category!=="BASE"||!Number.isSafeInteger(input.assessment)||input.assessment<0||input.assessment>1000000000)throw Error("SYNTHETIC_ONLY_NO_REAL_BILL");
 const r=0.4973+0.0111+0.0825;
 return {selected_rate_per_100:Number(r.toFixed(4)),partial_cad:Number((input.assessment*r/100).toFixed(2)),actual_bill_cad:null,nova_savings_cad:null,all_charges_included:false};
}
export function inspectG016p(d){
 const errors=[],fail=x=>errors.push(x);
 if(!isObj(d)||d.schema!=="nova-g016p-municipal-tax-comparison-v1"||!Array.isArray(d.sources)||!Array.isArray(d.cities))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.16p"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.adopted!==false)fail("SCORE_NOT_EARNED");
 if(d.sources.length!==3||d.sources[0].url!=="https://www.laval.ca/wp-content/uploads/2026/02/evolution-taux-taxation-tarification.pdf"||d.sources[1].url!=="https://www.gatineau.ca/docs/guichet_municipal/administration_municipale/budget/budget_2026/budget.fr-CA.pdf"||d.sources[0].pdf_visual_verified!==true||d.sources[1].pdf_visual_verified!==false)fail("SOURCES");
 if(d.cities.length!==3||d.cities.map(x=>x.id).join("|")!=="WARWICK|LAVAL|GATINEAU")fail("CITIES");
 const [w,l,g]=d.cities;
 if(w?.general_residual_rate_per_100!==0.575||w?.tax_year!==2026)fail("WARWICK");
 if(!l||[l.general_base_rate_per_100,l.water_special_base_rate_per_100,l.artm_special_base_rate_per_100,l.selected_base_sum_per_100,l.six_plus_general_rate_per_100].join("|")!=="0.4973|0.0111|0.0825|0.5909|0.6629"||l.additional_charges_unknown!==true)fail("LAVAL_RATES");
 const m=g?.municipal_median_model;
 if(!g||g.ordinary_residential_general_rate_per_1000!==null||g.by_neighbourhood!==true||g.six_plus_general_rate_per_1000!==6.964||g.transit_rate_per_1000!==1.417||g.new_city_debt_rate_per_1000!==0.830||g.waste_rate_per_logis!==178.83||m?.assessed_value_cad!==454600||m.selected_subtotal_cad!==3575.15||Number((m.general_cad+m.transit_cad+m.waste_cad+m.debt_cad).toFixed(2))!==3575.15||m.actual_bill_cad!==null||m.sector_extras_excluded!==true)fail("GATINEAU_SCOPE");
 if(d.cities.some(x=>x.full_bill_verified_cad!==null||x.cash_revenue_verified_cad!==null))fail("NO_ACTUAL_BILLS");
 if(!Array.isArray(d.missing_proofs)||d.missing_proofs.length!==8||d.missing_proofs.some((x,i)=>x.id!=="P"+(i+1)||x.status!=="NOT_VERIFIED"))fail("PROOFS_UNVERIFIED");
 const b=d.boundaries||{};
 if(b.same_tax_year!==true||["comparable_total_bills","assessed_value_is_household_income","selected_rates_are_full_tax_bill","city_budget_is_audited_cash","grant_award_is_cash_payment","flat_gatineau_residential_rate_available","tax_savings_nova_calculated","sovereignty_federal_transfers_presumed"].some(k=>b[k]!==false))fail("FALSE_COMPARISON");
 if(!Array.isArray(d.scenarios)||d.scenarios.map(s=>s.id).join("|")!=="QUEBEC_CANADA|QUEBEC_SOUVERAIN"||d.scenarios.some(s=>s.independently_audited!==false||s.years?.length!==10||s.years.some((y,i)=>y.year!==2026+i||cashKeys.some(k=>y[k]!==null))))fail("TEN_YEAR_BUDGET_UNKNOWN");
 const v=d.decision||{};
 if(v.municipal_schedules_expanded!==true||["real_paid_household_bills_audited","primeau_payments_verified","reform_funded","program_complete"].some(k=>v[k]!==false))fail("FALSE_DECISION");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,new_cities:2,verified_household_bills:0,verified_cash_payments:0};
}
