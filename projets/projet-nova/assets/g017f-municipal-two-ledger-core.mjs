/**
 * Projet Nova G0.17f — double rapprochement de la municipalité 02047 en 2025.
 * Ressources affectées, comptes de fonctionnement, investissement et trésorerie
 * ne sont ni interchangeables ni une preuve de viabilité nationale.
 */
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const sum=a=>Array.isArray(a)?a.reduce((s,x)=>s+x[1],0):NaN;
const arrays={
 revenues:[["taxes",4525681],["compensations",63631],["transferts_fonctionnement",724172],["services",363935],["droits",51824],["amendes",952],["interets",39303],["autres",161174]],
 functions:[["administration",1175575],["securite",557471],["transport",1586898],["hygiene_milieu",1201826],["sante_bien_etre",33681],["amenagement",288714],["loisirs_culture",1509736],["financement",668007]],
 objects:[["remuneration",1476360],["charges_sociales",344428],["biens_services",2280274],["frais_financement",668007],["quotes_parts",769032],["amortissement",1483807]],
 capital:[["transport",678478],["hygiene_milieu",21542601],["sante_bien_etre",7035],["amenagement",34419],["loisirs_culture",318991]]
};
const keys=(a,k)=>k.map(x=>a?.[x]);
const all=(o,k,v)=>k.every(x=>o?.[x]===v);
const valueSets={
 revenues:[5930672,19799872,25730544,20524044],
 expenses:[7021908,1483807,5538101,1820788],
 operating:[5930672,7021908,-1091236,1483807,-560996,236991,1159802,68566],
 investing:[19799872,22581524,650000,286340,-1845312],
 cash:[549175,2095979,-16969080,650000,-1690200,17429000,-65523,16323277,1450176,1999351],
 capital:[22581524,5612444,16969080,22138647],
 position:[31671634,42198356,10526722,1999351,29672283,28617428,6145462,18571000,17430500]
};
export function auditG017f(d,p,e){
 const problems=[],fail=x=>problems.push(x);
 if(!obj(d)||d.schema!=="nova-g017f-municipal-2025-operating-investment-cash-bridge/v1")return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.17f"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.remaining!==53||d.municipality?.code!=="02047"||d.municipality?.year!==2025||d.municipality?.scope!=="ONE_MUNICIPALITY_NOT_QUEBEC")fail("SCORE_AND_SCOPE");
 if(p?.schema!=="nova-g016r-port-daniel-2025-audited-qualified/v1"||p?.score_after!==47||e?.schema!=="nova-g017e-tecq-2026-legal-eligibility-cash-gates/v1"||e?.score_after!==47)fail("UPSTREAM");
 const s=d.sources||{};
 if(s.official_report!=="https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2025-et-autres-02047.pdf"||s.screenshot_attempted!==true||s.screenshot_result!=="CACHE_MISS"||s.pdf_text_reexamined!==true||s.opinion!=="QUALIFIED_ASSET_RETIREMENT_OBLIGATIONS_UNQUANTIFIED"||s.auditor_date!=="2026-06-08"||s.nova_audit_verified!==false||s.upstream_prior_report_path!=="data/reconciliation-financiere-port-daniel-g0-16r-2025.json"||s.upstream_tecq_rules_path!=="data/g017e-tecq-guide-2026-depenses-admissibles-et-paiements.json"||s.pages_zero_index?.fiscal_operations!==28||s.pages_zero_index?.fiscal_investment!==29||s.pages_zero_index?.cash!==10)fail("OFFICIAL_PROVENANCE");
 const r=d.revenues||{};
 if(!same(r.operating_categories_cad,arrays.revenues)||sum(r.operating_categories_cad)!==5930672||!same(keys(r,["operating_cad","investment_transfers_cad","total_cad","total_grants_recognized_cad"]),valueSets.revenues)||r.operating_cad+r.investment_transfers_cad!==r.total_cad||r.operating_categories_cad?.[2]?.[1]+r.investment_transfers_cad!==r.total_grants_recognized_cad||r.capital_subsidy_cash_received_cad!==null||!all(r,["operating_transfers_are_not_own_source","capital_subsidy_cannot_be_assumed_for_regular_payroll"],true))fail("REVENUES_SPLIT");
 const x=d.expenses||{};
 if(!same(x.by_function_cad,arrays.functions)||!same(x.by_object_cad,arrays.objects)||sum(x.by_function_cad)!==7021908||sum(x.by_object_cad)!==7021908||!same(keys(x,["all_expenses_cad","depreciation_cad","non_depreciation_expenses_cad","remuneration_with_social_charges_cad"]),valueSets.expenses)||x.all_expenses_cad-x.depreciation_cad!==x.non_depreciation_expenses_cad||x.by_object_cad?.[0]?.[1]+x.by_object_cad?.[1]?.[1]!==x.remuneration_with_social_charges_cad||!all(x,["objects_and_functions_are_two_splits_of_same_expense","normal_payroll_is_not_a_tecq_grant"],true))fail("EXPENSES_LANES");
 const o=d.fiscal_operations||{};
 if(!same(keys(o,["revenues_cad","expenses_including_depreciation_cad","pre_fiscal_result_cad","add_back_depreciation_cad","debt_repayment_fiscal_cad","net_allocations_fiscal_cad","total_adjustments_cad","surplus_cad"]),valueSets.operating)||o.revenues_cad-o.expenses_including_depreciation_cad!==o.pre_fiscal_result_cad||o.add_back_depreciation_cad+o.debt_repayment_fiscal_cad+o.net_allocations_fiscal_cad!==o.total_adjustments_cad||o.pre_fiscal_result_cad+o.total_adjustments_cad!==o.surplus_cad||!all(o,["distinct_from_2025_operating_cashflow","not_spendable_cash"],true))fail("FISCAL_OPERATING_BRIDGE");
 const i=d.fiscal_investment||{};
 if(!same(i.accrual_capital_by_function_cad,arrays.capital)||sum(i.accrual_capital_by_function_cad)!==22581524||!same(keys(i,["capital_revenues_cad","accrual_additions_cad","new_long_term_funding_cad","allocations_cad","deficit_cad"]),valueSets.investing)||i.capital_revenues_cad-i.accrual_additions_cad+i.new_long_term_funding_cad+i.allocations_cad!==i.deficit_cad||!all(i,["deficit_is_not_cash_expense","environmental_investment_not_entirely_attributable_to_Gascons"],true))fail("FISCAL_CAPITAL_BRIDGE");
 const c=d.cashflow||{};
 if(!same(keys(c,["opening_cad","operating_flow_cad","capital_spend_cad","long_loan_issue_cad","long_loan_principal_repaid_cad","temporary_borrowings_net_cad","loan_deferred_fees_change_cad","financing_flow_cad","net_change_cad","closing_cad"]),valueSets.cash)||c.operating_flow_cad+c.capital_spend_cad+c.financing_flow_cad!==c.net_change_cad||c.opening_cad+c.net_change_cad!==c.closing_cad||c.long_loan_issue_cad+c.long_loan_principal_repaid_cad+c.temporary_borrowings_net_cad+c.loan_deferred_fees_change_cad!==c.financing_flow_cad||!all(c,["cash_flow_municipality_wide_not_specific_to_Gascons","capital_accrual_is_not_cash_flow"],true))fail("CASH_BRIDGE");
 const b=d.capital_bridge||{};
 if(!same(keys(b,["capital_additions_accrual_cad","capital_accounts_payable_cad","capital_cash_outflow_cad","works_in_progress_additions_cad"]),valueSets.capital)||b.capital_additions_accrual_cad-b.capital_accounts_payable_cad!==b.capital_cash_outflow_cad||b.unpaid_bills_are_not_cash!==true)fail("ACCRUAL_TO_CASH");
 const f=d.balance_sheet||{};
 if(!same(keys(f,["assets_financial_cad","liabilities_cad","net_debt_cad","cash_cad","receivables_cad","receivables_quebec_cad","accounts_payable_cad","short_borrowings_cad","long_debt_gross_cad"]),valueSets.position)||f.liabilities_cad-f.assets_financial_cad!==f.net_debt_cad||f.asset_retirement_liability_cad!==null||f.liability_unknown_is_not_zero!==true)fail("BALANCE_SHEET_AND_QUALIFIED_OPINION");
 if(p?.realized_2025?.revenues_total_cad!==r.total_cad||p?.realized_2025?.expenses_total_cad!==x.all_expenses_cad||p?.cash_flow_2025?.operating_cad!==c.operating_flow_cad||p?.cash_flow_2025?.capital_acquisition_outflow_cad!==-c.capital_spend_cad||p?.cash_flow_2025?.financing_cad!==c.financing_flow_cad||p?.cash_flow_2025?.closing_cash_cad!==c.closing_cad||p?.position_2025?.financial_net_debt_cad!==f.net_debt_cad)fail("PRIOR_2025_INCONSISTENT");
 if(Object.keys(d.fiscal_constraints||{}).length!==11||!Object.values(d.fiscal_constraints||{}).every(x=>x===true))fail("GOVERNANCE_GUARDS");
 const sc=d.nova_scenarios||[];
 if(sc.length!==2||sc.map(x=>x.id).join("|")!=="QUEBEC_CANADA|QUEBEC_SOUVERAIN"||sc.some(x=>x.ten_year_rows?.length!==10||x.municipal_levy_replacement_verified_cad!==null||x.independent_validation!==false||x.ten_year_rows.some((y,j)=>y.period!==String(2026+j)+"-"+String(2027+j)||y.external_audit_approved!==false||Object.entries(y).some(([k,v])=>k!=="period"&&k!=="external_audit_approved"&&v!==null))))fail("TEN_YEAR_NULL_WHILE_UNVERIFIED");
 if(d.evidence_gates?.length!==7||d.evidence_gates.some((x,j)=>x.code!=="F"+(j+1)||x.passed!==false)||d.decisions?.two_ledgers_reconciled!==true||d.decisions?.bank_cashflow_reconciled!==true||d.decisions?.expenses_by_nature_validated!==true||!all(d.decisions,["source_pdf_visual_screenshot_succeeded","accounting_qualification_resolved","program_fully_financed","bank_project_payments_verified","external_nova_audit_passed","score_increment_earned"],false))fail("NO_EARNED_CLOSURE");
 return {ok:problems.length===0,errors:[...new Set(problems)],score:47,fiscal_surplus_cad:68566,capital_fiscal_deficit_cad:-1845312,cash_end_cad:1999351,project_specific_tecq_cash_received_cad:null};
}
/** Isolated arithmetic exercise, *not* a cash forecast or finance authorization. */
export function illustrateSeparatedFundingLanes(input){
 if(!obj(input)||input.mode!=="SYNTHETIC_ONLY")throw Error("SYNTHETIC_ONLY");
 const names=["unrestricted_operating_receipts","annual_payroll","annual_maintenance","other_operating_costs","annual_debt_service","dedicated_capital_receipts","capital_cash_outlays"];
 if(!names.every(k=>Number.isSafeInteger(input[k])&&input[k]>=0))throw Error("CAD_NONNEGATIVE_INTEGERS_ONLY");
 if(input.capitalCashReceiptsVerified!==false)throw Error("NO_REAL_GRANT_PROVEN");
 return {operating_balance_cad:input.unrestricted_operating_receipts-input.annual_payroll-input.annual_maintenance-input.other_operating_costs-input.annual_debt_service,
 capital_balance_cad:input.dedicated_capital_receipts-input.capital_cash_outlays,capital_grant_for_regular_payroll_cad:0,
 no_actual_payment_established:true,budget_legally_approved:false,sovereign_and_canada_ten_year_models_verified:false};
}
