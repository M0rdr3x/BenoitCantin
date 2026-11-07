// Projet Nova G0.16h — contrôle des comptes municipaux de référence, non une simulation de réforme.
export const PDF_SOURCE="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/rapports_financiers_organismes_municipaux/2024/RAP_financier_2024_sommation_municipalites_locales.pdf";
export const HISTORICAL=Object.freeze([
 [2024,17188134046,14970167302,13214586392,2199032000,18934744,
  32109026468,28366959822,3742066646,5330360838,4226149581,1559339417,1332060734],
 [2023,16081032867,13985227756,12412062137,2076317336,19487775,
  29764058791,26469048805,3295009986,4822974261,4005032444,1245951214,1181427913]
]);
const names=["year","taxes_cad","property_base_taxes_cad","property_general_tax_cad",
"other_base_taxes_cad","business_taxes_cad","total_revenues_cad","total_expenses_cad",
"operating_surplus_cad","government_transfers_cad","services_provided_revenue_cad",
"rights_levies_revenue_cad","financing_charges_cad"];
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const share=(n,d)=>Math.round(10000*n/d)/100;
export function inspectG016hMunicipalData(d,g016g,g014){
 const errors=[],fail=x=>errors.push(x);
 if(!object(d)||d.schema!=="nova-g016h-finances-municipales-observees/v1"||
  !object(d.source)||!Array.isArray(d.annual)||!object(d.observed_reconciliation)||
  !object(d.cross_status)||!Array.isArray(d.scenarios)||!object(d.decision)||
  !Array.isArray(d.source_limitations))
  return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.phase!=="G0.16h"||d.status!=="TRANSCRIPTION_SOMMATION_GOUVERNEMENTALE_PARTIELLE_NON_AUDIT_NOVA"||
   d.adopted!==false||d.programme_score_before!==47||d.programme_score_after!==47)
   fail("STATUS_PREMATURE");
 const s=d.source;
 if(s.publisher!=="Ministère des Affaires municipales et de l'Habitation (MAMH)"||
    s.url!==PDF_SOURCE||s.report_year!==2024||s.comparison_year!==2023||
    s.reporting_units!=="DOLLARS_CAD_COURANTS_ENTIERS"||
    s.pdf_page_index_financials!==7||s.pdf_page_index_tax_breakdown!==39||
    s.pdf_page_label_financials!=="S7 / 3"||s.pdf_page_label_tax_breakdown!=="S27 / 35"||
    s.municipalities_included!==1056||s.scope_as_of!=="2026-03-17"||
    ["municipalities_absent_from_aggregate",
     "northern_indigenous_and_other_exclusions_described_in_ministry_notes",
     "consolidated_totals_already_include_subsidiary_activities",
     "detail_tax_analysis_is_marked_non_audited",
     "source_observations_from_pdf_not_from_csv"].some(k=>s[k]!==true)||
    s.reviewed_independently_for_nova!==false)
    fail("SCOPE_SOURCE_INCORRECT");
 if(d.annual.length!==2||d.annual.some((item,i)=>{
   if(!object(item)||!same(names.map(k=>item[k]),HISTORICAL[i]))return true;
   if(!Object.keys(item).every(k=>[...names,"interest_and_debt_financing_included_in_expenses","credit_for_future_nova_reform_cad"].includes(k)))return true;
   if(item.interest_and_debt_financing_included_in_expenses!==true||
     item.credit_for_future_nova_reform_cad!==null)return true;
   return item.property_base_taxes_cad+item.other_base_taxes_cad+item.business_taxes_cad!==item.taxes_cad||
     item.property_general_tax_cad>item.property_base_taxes_cad||
     item.total_revenues_cad-item.total_expenses_cad!==item.operating_surplus_cad;
 }))fail("PDF_LEDGER_NOT_RECONCILED");
 const x=d.annual[0],old=d.annual[1],r=d.observed_reconciliation;
 const computed={
  year:2024,taxes_cad:17188134046,
  property_tax_share_of_all_municipal_taxes_pct:share(14970167302,17188134046),
  property_tax_share_of_total_revenues_pct:share(14970167302,32109026468),
  taxes_share_of_total_revenues_pct:share(17188134046,32109026468),
  tax_yoy_growth_pct:Math.round(10000*(17188134046/16081032867-1))/100,
  rounded_percent_derived_not_source_published:true,
  rounding_decimals:2,scope_not_equivalent_umq_70_pct:true
 };
 if(!same(r,computed)||x?.year!==2024||old?.year!==2023)
  fail("DERIVED_PCT_UNVERIFIED");
 const required=[
  "Somme des municipalités locales","section détaillée S27","taxes sur la valeur foncière",
  "taxes sur une autre base","taxe foncière scolaire","transferts entre administrations",
  "UMQ de 70 %","2023 et 2024"
 ];
 if(required.some(word=>!d.source_limitations.some(s=>typeof s==="string"&&s.includes(word))))
  fail("MISSING_DISCLOSURES");
 const cross=d.cross_status;
 const falseNames=["prior_csv_imported_and_validated","independent_audit_completed",
  "municipal_compensation_legally_approved","all_municipal_finance_data_exhaustive",
  "two_tax_policy_certified","g015_v10_independently_verified",
  "g015_v14_independently_verified","g015_v15_independently_verified"];
 if(cross.g014_school_property_tax_2026_2027_mcad!==1301||
   cross.school_property_tax_separate_from_municipal_property_taxes!==true||
   cross.g016g_prior_csv_source!=="PF-2024-2024-Prov.csv"||
   cross.prior_csv_contains_indicators_not_amounts!==true||
   cross.new_source_pdf_summation_transcribed!==true||
   cross.municipal_tax_transition_replacement_2026_mcad!==null||
   falseNames.some(k=>cross[k]!==false))fail("FALSE_REFORM_PROOF");
 if(!same(d.scenarios.map(x=>x?.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"])||
   d.scenarios.some(x=>["revenue_replacement_2026_2027_mcad",
       "municipal_services_continuity_mcad","tax_reform_net_cost_mcad"].some(k=>x[k]!==null)||
       x.legal_review!==false||x.external_review!==false))
    fail("SCENARIO_UNFOUNDED");
 const gates=["g016h_full_proof_passed","municipal_taxes_abolition_approved",
  "two_tax_budget_balanced","programme_complete"];
 if(d.decision.g016h_data_transcription_complete!==true||
    gates.some(k=>d.decision[k]!==false))fail("GATE_INVENTED");
 if(g016g?.schema!=="nova-g016g-education-municipalites-travail-dette/v1"||
   g016g.programme_score_after!==47||
   g016g.source_facts?.municipalities?.aggregate_property_tax_revenue_mcad!==null||
   g016g.source_facts?.municipalities?.aggregate_2024_csv_status!=="SOURCE_CATALOGUE_IDENTIFIEE_NON_IMPORTEE"||
   g014?.revenue_categories?.find(v=>v.id==="FONCIER_SCOLAIRE")?.amount_mcad!==1301)
    fail("PREDECESSOR_CONTEXT");
 return {ok:errors.length===0,errors:[...new Set(errors)],
  programme_score:47,year:2024,local_municipalities_reported:1056,
  municipal_all_taxes_cad:17188134046,
  municipal_property_base_taxes_cad:14970167302,
  municipal_revenue_cad:32109026468,
  municipal_tax_share_pct:computed.taxes_share_of_total_revenues_pct,
  certified_nova_replacement:false,verified_municipal_tax_policies:0};
}
