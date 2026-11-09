/**
 * Projet Nova–Sinjira G0.17g — two distinct 2025 municipality cases.
 * This is a two-case audit/consistency check, NOT a province-wide estimate.
 * Full-program financing, weights and transfer receipts remain unresolved.
 */
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const approx=(a,b)=>typeof a==="number"&&typeof b==="number"&&Math.abs(a-b)<1e-10;
const sum=o=>object(o)?Object.values(o).reduce((x,v)=>x+v,0):NaN;
const get=(o,fields)=>fields.map(k=>o?.[k]);
const match=(o,fields,values)=>get(o,fields).every((v,i)=>v===values[i]);
const allBool=(o,v)=>object(o)&&Object.values(o).every(x=>x===v);
const commonFields=["revenue","taxes","transfers","expenses","accrual_surplus","operating_revenue","investment_revenue",
"fiscal_operation","fiscal_investment","cash_begin","cash_operation","cash_investment","cash_portfolio","cash_financing","cash_change","cash_end","net_debt"];
const expectedPort=[25730544,4525681,20524044,7021908,18708636,5930672,19799872,68566,-1845312,549175,2095979,-16969080,0,16323277,1450176,1999351,10526722];
const expectedSag=[540158703,317831049,64741160,534427768,5730935,524797261,15361442,14079053,4755759,157390687,103120417,-107111111,514945,34662779,31187030,188577717,612200553];
const sagRevenue=[["taxes",317831049],["compensations",38074332],["transfers",64741160],["services",82281390],["droits",14973521],["amendes",5222292],["placements",7145173],["interets",4254267],["autres",5635519]];
const sagExpenses=[["administration",51165994],["securite",80673591],["transport",127276753],["hygiene",78946292],["sante",6413100],["amenagement",34451743],["loisirs",77257791],["electricite",49434754],["financement",28807750]];
const sagInvest=[["revenues",15361442],["capex",-110900628],["properties",-248049],["loans",-296500],["new_long_funding",93178956],["allocations",7660538]];
const sagFinancing=[["new_long_debt",148121000],["repayments",-116699801],["temp_borrowings",3204602],["deferred_fees",36978]];
const keysEq=(o,kv)=>object(o)&&kv.every(([k,v])=>o[k]===v);
const members=(o,arr)=>object(o)&&Object.keys(o).length===arr.length&&arr.every(([k,v])=>o[k]===v);
export function auditG017g(d,portPrior){
 const errors=[],bad=x=>errors.push(x);
 if(!object(d)||d.schema!=="nova-g017g-two-municipalities-2025-evidence/v1"||!Array.isArray(d.samples)||d.samples.length!==2)
 return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.17g"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.remaining_points!==53||d.scope!=="TWO_CONVENIENCE_2025_CASES_NOT_QUEBEC_TAX_BASE")bad("NO_SCORE_INCREASE");
 const [p,s]=d.samples;
 if(p.year!==2025||p.code!=="02047"||p.name!=="Port-Daniel–Gascons"||p.scope!=="MUNICIPAL_2025"||p.auditor!=="QUALIFIED_ASSET_RETIREMENT_OBLIGATIONS_UNQUANTIFIED"||!match(p,commonFields,expectedPort))bad("PORT_DATA");
 if(s.year!==2025||s.code!=="94068"||s.name!=="Saguenay"||s.scope!=="CONSOLIDATED_CONTROLLED_ENTITIES_AND_ELECTRICITY_NETWORK"||s.auditor!=="UNMODIFIED"||s.auditor_date!=="2026-06-02"||!match(s,commonFields,expectedSag))bad("SAG_DATA");
 const urls=d.sources;
 if(!Array.isArray(urls)||urls.length!==2||urls[0]?.code!=="02047"||urls[0]?.register_path!=="data/g017f-rapprochement-municipal-fonctionnement-investissement-tresorerie-2025.json"||urls[0]?.screenshot_success!==false||urls[0]?.immutable_sha256!==null||urls[1]?.code!=="94068"||urls[1]?.url!=="https://ville.saguenay.ca/files/medias/La-ville-et-vie-d%C3%A9mocratique/Publications/Budget/Rapports-financiers-consolid%C3%A9s/Rapport-financier-2025-consolid%C3%A9-final.pdf"||JSON.stringify(urls[1]?.visual_page_indices)!=="[6,7,8]"||urls[1]?.screenshot_other_pages_cache_miss!==true||urls[1]?.immutable_sha256!==null||urls[1]?.year2024_comparatives_restated!==true)bad("SOURCE_PROVENANCE");
 if(p.revenue-p.expenses!==p.accrual_surplus||s.revenue-s.expenses!==s.accrual_surplus||s.revenue-s.investment_revenue!==s.operating_revenue||p.revenue-p.investment_revenue!==p.operating_revenue)bad("ACCRUAL_AND_REVENUE_LANES");
 if(!members(s.revenues_by_nature,sagRevenue)||sum(s.revenues_by_nature)!==s.revenue||!members(s.expenses_by_function,sagExpenses)||sum(s.expenses_by_function)!==s.expenses||s.expenses_by_function.electricite!==49434754)bad("SAG_CONSOLIDATED_SCOPE");
 const a=s.fiscal_adjustments;
 if(!keysEq(a,[["operations_before",-9630507],["net_adjustments",23709560]])||a.operations_before!==s.operating_revenue-s.expenses||sum(a)!==s.fiscal_operation)bad("SAG_FISCAL_OPERATIONS");
 if(!members(s.fiscal_investment_bridge,sagInvest)||sum(s.fiscal_investment_bridge)!==s.fiscal_investment)bad("SAG_FISCAL_INVESTMENT");
 if(!members(s.financing_cash_components,sagFinancing)||sum(s.financing_cash_components)!==s.cash_financing)bad("SAG_FINANCING_DETAIL");
 for(const x of [p,s]){
  if(x.cash_operation+x.cash_investment+x.cash_portfolio+x.cash_financing!==x.cash_change||x.cash_begin+x.cash_change!==x.cash_end)bad("CASH_FLOW_IDENTITY");
 }
 if(s.liabilities-s.financial_assets!==s.net_debt||s.liabilities!==940042426||s.financial_assets!==327841873||s.capital_accrual!==110900628||s.capital_cash_acquisitions!==108303207||s.revenues_2024_restated!==536339341||s.expenses_2024_restated!==500756152)bad("SAG_DEBT_AND_PERIOD_SCOPE");
 if(portPrior?.schema!=="nova-g017f-municipal-2025-operating-investment-cash-bridge/v1"||portPrior?.score_after!==47||p.revenue!==portPrior.revenues?.total_cad||p.taxes!==portPrior.revenues?.operating_categories_cad?.[0]?.[1]||p.transfers!==portPrior.revenues?.total_grants_recognized_cad||p.expenses!==portPrior.expenses?.all_expenses_cad||p.fiscal_operation!==portPrior.fiscal_operations?.surplus_cad||p.cash_end!==portPrior.cashflow?.closing_cad||p.net_debt!==portPrior.balance_sheet?.net_debt_cad)bad("PORT_PRIOR_NOT_RECONCILED");
 const z=d.composition;
 if(!object(z)||!approx(z.port_transfer_share_of_2025_total_pct,100*p.transfers/p.revenue)||!approx(z.sag_transfer_share_of_2025_total_pct,100*s.transfers/s.revenue)||!approx(z.port_tax_share_of_2025_total_pct,100*p.taxes/p.revenue)||!approx(z.sag_tax_share_of_2025_total_pct,100*s.taxes/s.revenue)||z.denominator!=="EACH_2025_RECOGNIZED_TOTAL_REVENUE"||!keysEq(z,[["causal_evidence",false],["comparative_service_efficiency_proven",false],["year2026_fiscal_rate_derived",false]]))bad("REVENUE_SHARES_DESCRIPTIVE_ONLY");
 if(!allBool(d.cautions,true)||Object.keys(d.cautions).length!==16)bad("NONCOMPARABILITY_GUARDS");
 const cov=d.coverage;
 if(!object(cov)||cov.municipalities!==2||cov.method!=="CONVENIENCE_ORIGINAL_OFFICIAL_REPORTS"||!keysEq(cov,[["population_weights_verified",false],["mamh_2025_full_csv_imported",false],["complete_municipal_coverage",false],["nationwide_2025_public_balance_verified",false]]))bad("NO_GENERALIZATION");
 if(!Array.isArray(d.open_gates)||d.open_gates.length!==6||d.open_gates.some((x,i)=>x.id!=="G"+(i+1)||x.passed!==false))bad("UNFINISHED_EVIDENCE");
 const dec=d.decisions;
 if(!object(dec)||dec.added_second_real_municipal_statement!==true||dec.accounting_and_cash_reconciled!==true||dec.source_scope_difference_disclosed!==true||!keysEq(dec,[["municipal_population_representative",false],["nova_two_levy_funding_validated",false],["independent_programme_audit",false],["score_increment_earned",false]]))bad("NO_FALSE_FINANCING_PROOF");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,municipalities:2,
 port_transfers_pct:100*p.transfers/p.revenue,sag_transfers_pct:100*s.transfers/s.revenue,
 verified_nova_tax_replacement_cad:null,independent_fiscal_signoff:false};
}
/**
 * This output is descriptive only. No inference about policy impact or
 * municipal service efficiency, and no population weighting without source.
 */
export function municipalComposition(record,{mode}={}){
 if(mode!=="DESCRIPTIVE_CASE_ONLY"||!object(record)||!["02047","94068"].includes(record.code))throw Error("TWO_CASES_ONLY");
 if(!Number.isSafeInteger(record.revenue)||record.revenue<=0||!Number.isSafeInteger(record.taxes)||!Number.isSafeInteger(record.transfers)||record.taxes<0||record.transfers<0||record.taxes+record.transfers>record.revenue)throw Error("INVALID_REVENUE_BASE");
 return {tax_share_pct:record.taxes/record.revenue*100,transfer_share_pct:record.transfers/record.revenue*100,
 other_revenue_share_pct:(record.revenue-record.taxes-record.transfers)/record.revenue*100,
 representative_for_quebec:false,is_efficiency_rating:false,nova_tax_yield_verified_cad:null};
}
