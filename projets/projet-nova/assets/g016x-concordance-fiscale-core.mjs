/**
 * G0.16x — Contrôle de la concordance Nova–Sinjira.
 * Inventaire et règles de compétence, PAS une approbation de réforme.
 * Valeurs `null` = non vérifiées, jamais recettes nulles.
 */
const isObject=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const ids="QC_PIT,QC_CORP,QC_FSS,QC_TVQ,QC_FUEL,QC_TOBACCO,QC_ALCOHOL,QC_INSURANCE,QC_HOTEL,QC_TIRE,QC_WAGER,QC_SCHOOL,QC_QPP,QC_RQAP,QC_PHARMA,QC_CARBON,QC_RESOURCE,QC_LICENSE,QC_PUBLIC_COMPANIES,QC_MISC,MUNI_PROPERTY,MUNI_MUTATION,MUNI_WATER,MUNI_REG,MUNI_911,MUNI_TRANSFER,FED_PIT,FED_CORP,FED_GST,FED_EXCISE,FED_CUSTOMS,FED_EI,FED_MIN,FED_TRANSFER,NOVA_INCOME,NOVA_ANTIHAVEN".split(",");
const sources="CONST,POWERS,TAX,SOCIAL,MUNI,MUT,SCHOOL,QPP,PARENT,GLO,ECO,FED,QC,LOCAL".split(",");
const idActs={
"QC_PIT":"REWORK_INCOME","QC_CORP":"REWORK_INCOME",
"QC_FSS":"REPLACE_ONLY_IF_FUNDED","QC_TVQ":"REPLACE_ONLY_IF_FUNDED","QC_FUEL":"REPLACE_ONLY_IF_FUNDED","QC_TOBACCO":"REPLACE_ONLY_IF_FUNDED",
"QC_ALCOHOL":"REPLACE_ONLY_IF_FUNDED","QC_INSURANCE":"REPLACE_ONLY_IF_FUNDED","QC_HOTEL":"REPLACE_ONLY_IF_FUNDED","QC_TIRE":"CLASSIFY_THEN_DESIGN",
"QC_WAGER":"REPLACE_ONLY_IF_FUNDED","QC_SCHOOL":"REPLACE_ONLY_IF_FUNDED",
"QC_QPP":"PRESERVE_BENEFITS","QC_RQAP":"PRESERVE_BENEFITS","QC_PHARMA":"PRESERVE_BENEFITS",
"QC_CARBON":"CLASSIFY_THEN_DESIGN","QC_RESOURCE":"CLASSIFY_THEN_DESIGN","QC_LICENSE":"CLASSIFY_THEN_DESIGN",
"QC_PUBLIC_COMPANIES":"RETAIN_WITH_AUDIT","QC_MISC":"CLASSIFY_THEN_DESIGN",
"MUNI_PROPERTY":"REPLACE_ONLY_IF_FUNDED","MUNI_MUTATION":"REPLACE_ONLY_IF_FUNDED","MUNI_WATER":"CLASSIFY_THEN_DESIGN",
"MUNI_REG":"CLASSIFY_THEN_DESIGN","MUNI_911":"REPLACE_ONLY_IF_FUNDED","MUNI_TRANSFER":"PRESERVE_NO_DOUBLE_COUNT",
"FED_PIT":"FEDERAL_NOT_UNILATERAL","FED_CORP":"FEDERAL_NOT_UNILATERAL","FED_GST":"FEDERAL_NOT_UNILATERAL",
"FED_EXCISE":"FEDERAL_NOT_UNILATERAL","FED_CUSTOMS":"FEDERAL_NOT_UNILATERAL","FED_EI":"PRESERVE_BENEFITS",
"FED_MIN":"NO_DOUBLE_COUNT","FED_TRANSFER":"CONDITIONAL_INTERGOV_TRANSFER",
"NOVA_INCOME":"NOT_ENACTED","NOVA_ANTIHAVEN":"NOT_ENACTED"
};
const moneyMustRemainUnknown=["individual_revenue_2026_27_mcad","verifiable_net_replacement_mcad"];
export function inspectG016x(d,prior,priorW){
 const errors=[],bad=k=>errors.push(k);
 if(!isObject(d)||d.schema!=="nova-g016x-multilevel-fiscal-concordance/v1"||!Array.isArray(d.rows)||!isObject(d.macro)||!isObject(d.rules))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.16x"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.remaining!==53||d.independent_legal_and_fiscal_signoff!==false||d.political_adoption_verified!==false)bad("FALSE_COMPLETION");
 if(prior?.schema!=="nova-g016v-two-levies-public-finance-reference/v1"||prior?.programme_audit_after!==47||priorW?.schema!=="nova-g016w-tax-bases-distribution-municipal-gates/v1"||priorW?.score_after!==47)bad("SOURCE_CHAIN");
 const originalSources=d.sources;
 if(!Array.isArray(originalSources)||originalSources.length!==14||!same(originalSources.map(x=>x.id),sources)||originalSources.some((x,i)=>!x.url||x.kind!==(i>=12?"INTERNAL_SOURCE_BACKED_RECORD":"OFFICIAL_WEB"))||originalSources[0].url!=="https://laws-lois.justice.gc.ca/fra/const/TexteComplet.html?wbdisable=true"||originalSources[9].url!=="https://www.canada.ca/fr/services/impots/taxes-daccise-droits-et-prelevements/impot-minimum-mondial.html")bad("PROVENANCE");
 if(d.rows.length!==36||!same(d.rows.map(x=>x.id),ids)||new Set(d.rows.map(x=>x.id)).size!==36)bad("REGISTER_COVERAGE");
 for(const r of d.rows){
  if(!isObject(r)||!r.id||r.nova_decision_status!==idActs[r.id]||!r.label||!r.protected_service||r.source_ids?.length<1||r.source_ids.some(y=>!sources.includes(y))||moneyMustRemainUnknown.some(k=>r[k]!==null)||r.constitutional_review_passed!==false||r.municipal_service_continuity_proven!==false||r.distributive_audit_passed!==false)bad("ROW_UNAPPROVED_"+(r?.id||"unknown"));
  if(!isObject(r.quebec_in_canada)||!isObject(r.quebec_sovereign)||r.quebec_in_canada.legal_change_complete!==false||r.quebec_sovereign.tax_and_debt_succession_verified!==false||r.quebec_sovereign.program_continuity_verified!==false||r.quebec_sovereign.treaty_or_negotiation_status!=="UNVERIFIED")bad("STATUS_NOT_APPROVED_"+r.id);
  if(["FEDERAL","FEDERAL_SOCIAL"].includes(r.current_jurisdiction)&&r.quebec_in_canada.can_unilaterally_repeal!==false)bad("FEDERAL_SOVEREIGNTY_CONFUSION");
  if(r.current_jurisdiction==="PROPOSED"&&(r.quebec_in_canada.can_unilaterally_repeal!==false||r.nova_decision_status!=="NOT_ENACTED"))bad("PROPOSED_IS_NOT_ENACTED");
 }
 const m=d.macro;
 if(m.year!=="2026-2027"||m.unit!=="MILLIONS_CAD"||m.source_file!=="data/cadre-financier-fiscal-g0-16v-aout-2026.json"||m.qc_personal!==prior.government_reference.fiscal_years_official[0].person_income_tax_mcad||m.qc_corporate!==prior.government_reference.fiscal_years_official[0].corporate_income_tax_mcad||m.qc_fss!==prior.government_reference.fiscal_years_official[0].employer_health_contributions_mcad||m.qc_school!==prior.government_reference.fiscal_years_official[0].school_property_tax_mcad||m.qc_consumption_aggregate!==prior.government_reference.fiscal_years_official[0].consumption_taxes_mcad||m.qc_enterprises!==prior.government_reference.fiscal_years_official[0].government_enterprises_mcad||m.qc_rights_aggregate!==prior.government_reference.fiscal_years_official[0].rights_permits_royalties_mcad||m.qc_misc!==prior.government_reference.fiscal_years_official[0].miscellaneous_revenue_mcad||m.federal_transfers_to_qc!==prior.government_reference.fiscal_years_official[0].federal_transfers_mcad||m.qc_total_revenue!==168389||m.qc_expenditure!==171597||m.qc_reserve!==2000||m.conditional_two_levy_need!==112369)bad("PROVINCIAL_BUDGET_MISMATCH");
 const recomputed=m.qc_personal+m.qc_corporate+m.qc_fss+m.qc_school+m.qc_consumption_aggregate+m.qc_enterprises+m.qc_rights_aggregate+m.qc_misc+m.federal_transfers_to_qc;
 if(recomputed!==168389||m.qc_expenditure+m.qc_reserve-m.qc_enterprises-m.qc_rights_aggregate-m.qc_misc-m.federal_transfers_to_qc!==m.conditional_two_levy_need)bad("PROVINCIAL_MATH");
 const muni=m.distinct_2023_municipal;
 if(!isObject(muni)||muni.source_file!=="data/g016w-assiettes-fiscales-et-garanties-distributives-2023-2024.json"||muni.municipal_total_gcad!==priorW.municipal_2023.total_revenues_reported_gcad||muni.property_taxes_gcad!==priorW.municipal_2023.property_tax_gcad||muni.intergov_transfers_gcad!==priorW.municipal_2023.transfers_gcad||m.individual_specific_tax_revenues_NOT_SEPARATELY_KNOWN!==true||m.federal_2026_budget_QUEBEC_ALLOCATED_REVENUE!==null)bad("MUNICIPAL_SCOPE");
 const gates=d.gates;
 if(!Array.isArray(gates)||gates.length!==10||gates.some((g,i)=>g.id!=="G"+String(i+1).padStart(2,"0")||!g.verification_needed||g.verified!==false||g.validator!==null))bad("GATES_NOT_FINISHED");
 const s=d.scenarios;
 if(!Array.isArray(s)||s.map(x=>x.id).join("|")!=="QUEBEC_CANADA|QUEBEC_SOUVERAIN"||s[0].federal_taxes_repealed_by_quebec!==false||s[0].municipal_replacement_requires_statute!==true||s[1].federal_transfers_automatically_continued!==false||s[1].federal_functions_and_debt_costed!==false||s.some(x=>x.real_public_balance_for_10_years?.length!==10||x.real_public_balance_for_10_years.some(y=>y!==null)||x.legally_approved!==false))bad("SCENARIOS_NOT_APPROVED");
 if(Object.values(d.rules).length!==12||Object.values(d.rules).some(x=>x!==true))bad("NO_FALSE_CLAIMS_GATES");
 const z=d.decision;
 if(!isObject(z)||z.rows_verified_source_mapped!==36||["practical_repeal_of_all_existing_taxes_proven","anti_haven_extra_revenue_proven","household_purchasing_power_proven","two_tax_fiscal_sustainability_proven","score_point_earned"].some(x=>z[x]!==false))bad("FALSE_CERTIFICATION");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,missing:53,entries:36,unverified_legality:36,provisional_need_mcad:112369,verified_nova_rate_pct:null};
}

/**
 * Purely hypothetical consolidation, eliminating transfers among Québec and municipalities.
 * This is NEVER a 2026-27 Nova fiscal projection, nor an estimate of effects on real families.
 */
export function consolidateSyntheticGovernment(x){
 if(!isObject(x)||x.mode!=="SYNTHETIC_ONLY"||!["QUEBEC_CANADA","QUEBEC_SOUVERAIN"].includes(x.scenario)||x.official_plan===true)throw Error("SYNTHETIC_ONLY_REQUIRED");
 const fields=["qc_own_external_revenue","federal_transfer_received","municipal_own_external_revenue","provincial_transfer_paid_to_muni","municipal_transfer_received_from_province","qc_expenditure_including_local_transfer","municipal_expenditure","additional_national_services_spending","reassigned_federal_tax_revenue"];
 if(fields.some(k=>!Number.isFinite(x[k])||x[k]<0))throw Error("INCOMPLETE_NONNEGATIVE_FIELDS");
 if(x.provincial_transfer_paid_to_muni!==x.municipal_transfer_received_from_province)throw Error("UNRECONCILED_INTERNAL_TRANSFER");
 if(x.scenario==="QUEBEC_CANADA"&&(x.reassigned_federal_tax_revenue!==0||x.additional_national_services_spending!==0))throw Error("NO_FEDERAL_TAX_TAKEOVER_IN_CANADA");
 if(x.scenario==="QUEBEC_SOUVERAIN"&&x.federal_transfer_received!==0&&x.verified_treaty_transfer!==true)throw Error("NO_AUTOMATIC_FEDERAL_TRANSFER");
 const receipt=x.qc_own_external_revenue+x.municipal_own_external_revenue+x.federal_transfer_received+x.reassigned_federal_tax_revenue;
 const expense=x.qc_expenditure_including_local_transfer+x.municipal_expenditure-x.provincial_transfer_paid_to_muni+x.additional_national_services_spending;
 return {classification:"SYNTHETIC_NOT_PUBLIC_BUDGET",consolidated_revenue:receipt,consolidated_spending:expense,consolidated_balance:receipt-expense,internal_transfer_eliminated:x.provincial_transfer_paid_to_muni,nova_plan_certified:false};
}
