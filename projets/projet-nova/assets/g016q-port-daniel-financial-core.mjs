// Nova–Sinjira G0.16q. Vérification de source : prévision budgétaire ≠ preuve de trésorerie.
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const revenues={taxes:4619646,payments_in_lieu:41200,transfers:725626,other_local:447285,services:679247,rights_and_interest:67650};
const rates={residential:0.4,six_plus:0.4,non_residential:1.1785,industrial:1.2585,agriculture_forestry:0.4};
const fees={water_port_daniel:102.64,sewer_port_daniel:273.49,water_gascons:439.25,clsc_arena_water:10,waste_residential_1_to_4:350,waste_5_plus_and_ici:360,gascons_water_research:24.06};
const yearKeys=["revenus_reformes_cad","cout_services_cad","dette_tiree_cad","service_dette_cad","transferts_verifies_cad","cout_main_oeuvre_cad","solde_cad"];
export function inspectG016q(d,p){
 const errors=[],fail=k=>errors.push(k);
 if(!obj(d)||d.schema!=="nova-g016q-port-daniel-budget-2026/v1"||!obj(d.budget)||!obj(d.taxes)||!obj(d.capital_plan))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.16q"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.adopted!==false||d.financial_audit_nova!==false)fail("SCORE_NOT_EARNED");
 if(p?.schema!=="nova-g016p-municipal-tax-comparison-v1"||p.score_after!==47)fail("UPSTREAM");
 if(!Array.isArray(d.sources)||d.sources.length!==4||d.sources[0].url!=="https://munpdg.ca/wp-content/uploads/2026/02/Document-explicatif-budget-2026.pdf"||!same(d.sources[0].pages_checked_visually,[0,1])||d.sources[0].classification!=="OFFICIAL_FORECAST_NOT_ACTUAL"||d.sources[1].classification!=="INDEX_REGULATIONS_2026_01_AND_02_NOT_FULL_TEXT"||d.sources[2].classification!=="FINANCIAL_REPORT_LINK_PUBLISHED_PDF_NOT_READABLE")fail("SOURCE_SCOPE");
 if(d.municipality!=="Port-Daniel–Gascons"||d.fiscal_year!==2026)fail("MUNICIPALITY");
 const b=d.budget;
 if(b.type!=="ADOPTED_FORECAST_NOT_ACTUAL"||!same(b.revenues,revenues)||Object.values(b.revenues).reduce((s,n)=>s+n,0)!==6580654||b.total_revenue_cad!==6580654||b.operating_spending_cad!==6631925||b.appropriations_cad!==-51271||b.operating_spending_cad+b.appropriations_cad!==b.total_revenue_cad||b.balanced_forecast_cad!==0||b.actual_receipts_cad!==null||b.actual_expenses_cad!==null||b.primeau_cash_receipts_verified_cad!==null)fail("BUDGET_NOT_CASH");
 const t=d.taxes;
 if(t.source!=="OFFICIAL_TWO_PAGE_BUDGET_EXPLANATION"||t.full_regulations_reviewed!==false||!same(t.rates_cad_per_100,rates)||!same(t.fees_cad_per_unit,fees)||t.actual_tax_bill_cad!==null||t.territorial_conditions_apply!==true||t.other_special_taxes_not_all_checked!==true)fail("TAX_CONDITIONS");
 const c=d.capital_plan;
 if(c.period!=="2026-2028"||c.total_cad!==33100000||!same(c.by_year_cad,{"2026":30200000,"2027":1000000,"2028":1900000})||Object.values(c.by_year_cad).reduce((s,n)=>s+n,0)!==33100000||c.gascons_water_sewer_2026_cad!==30000000||c.final_spending_paid_cad!==null||c.capital_grants_received_cad!==null||c.loan_drawn_cad!==null||c.not_additive_to_2025_borrowing_authorization!==true)fail("PTI_NOT_CASH");
 if(!obj(d.verification_rules)||Object.values(d.verification_rules).some(v=>v!==true))fail("FALSE_CASH_CLASSIFICATION");
 if(!Array.isArray(d.open_proofs)||d.open_proofs.length!==8||d.open_proofs.some((x,i)=>x.id!=="C"+String(i+1).padStart(2,"0")||x.status!=="NOT_VERIFIED"))fail("PROOFS_ABSENT");
 if(!Array.isArray(d.ten_year_scenarios)||d.ten_year_scenarios.map(x=>x.id).join("|")!=="QUEBEC_CANADA|QUEBEC_SOUVERAIN"||d.ten_year_scenarios.some(s=>s.audited!==false||s.years?.length!==10||s.years.some((y,i)=>y.year!==2026+i||yearKeys.some(k=>y[k]!==null))))fail("SCENARIOS_NOT_FUNDED");
 const dec=d.decision||{};
 if(dec.official_budget_documented!==true||["cash_paid_verified","debt_balance_verified","primeau_payment_verified","nova_reform_funded","score_raised"].some(k=>dec[k]!==false))fail("FALSE_APPROVAL");
 return {ok:errors.length===0,errors:[...new Set(errors)],programme_score:47,official_operating_budget_total_cad:6580654,pti_total_cad:33100000,cash_disbursements_verified:0};
}
export function selectedPortDanielFictiveExample(x){
 if(!obj(x)||x.mode!=="SYNTHETIC_PARTIAL_ONLY"||x.authorized!==true||!Number.isSafeInteger(x.assessed_cad)||x.assessed_cad<0||x.assessed_cad>1000000000||x.sector!=="PORT_DANIEL"||x.one_unit!==true||x.water!==true||x.sewer!==true||x.waste!==true)throw Error("NO_REAL_BILL_SIMULATION");
 const general=Number((x.assessed_cad*0.4/100).toFixed(2));
 return {general_cad:general,selected_services_cad:736.13,partial_total_cad:Number((general+736.13).toFixed(2)),actual_bill_cad:null,all_special_taxes_included:false,nova_savings_cad:null};
}
