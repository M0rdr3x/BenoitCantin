// G0.15 — ventilation comptable publiée, sans approbation des politiques NOVA.
// Montants M$ des Comptes publics 2025-2026 du Québec, vol. 1, note 4, p. 102.
export const OFFICIAL_REVENUE_NOTE_URL=
 "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Comptes-publics/FR/CPTFR_vol1-2025-2026.pdf";
const ID_GROUPS=["V01","V02","V03"];
export const PUBLISHED_ROWS=Object.freeze({
 V01:[
 ["SALES",24650,25930,"FISCAL_SALES_NET_OF_CREDIT"],
 ["FUEL",2135,2158,"FISCAL_EXCISE"],
 ["TOBACCO",853,815,"FISCAL_EXCISE"],
 ["ALCOHOL",596,573,"FISCAL_EXCISE"],
 ["OTHER",143,163,"FISCAL_MIXED"]],
 V02:[
 ["VEHICLES",2055,2181,"REGULATORY_RIGHTS"],
 ["NATURAL_RESOURCES",1667,2229,"RESOURCE_ROYALTIES"],
 ["GHG",1329,1123,"EMISSIONS_ALLOWANCE_REVENUE"],
 ["OTHER",1140,1175,"MIXED_RIGHTS_AND_FEES"]],
 V03:[
 ["HEALTH_OTHER",1761,1857,"HEALTH_SERVICE_CHARGES"],
 ["DRUG_PREMIUMS",1672,1751,"DRUG_INSURANCE_PREMIUMS"],
 ["TUITION",627,655,"EDUCATION_FEES"],
 ["SCHOOL_CHILDCARE",522,544,"SCHOOL_SERVICE_FEES"],
 ["POLICE",427,455,"PUBLIC_SERVICE_CHARGES"],
 ["OTHER_SERVICES",3711,3870,"MIXED_SERVICE_FEES"],
 ["RECEIVABLES",1979,1566,"INTEREST_LOAN_INCOME"],
 ["PENALTIES",1176,1563,"ENFORCEMENT_AND_RECOVERIES"],
 ["DONATIONS",1180,1186,"DONATIONS"],
 ["INVESTMENTS",1218,1072,"INVESTMENT_INCOME"],
 ["OTHER",1979,403,"MIXED_MISC_INCOME"]]
});
const totals={"V01":[28377,29639],"V02":[6191,6708],"V03":[16252,14922]};
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const sum=(a,k)=>a.reduce((n,v)=>n+v[k],0);
export function inspectG015V01V03Subcategories(d,g014,g015,discovery,g015Actuals){
 const errors=[],fail=k=>errors.push(k);
 if(!obj(d)||!obj(d.source)||!Array.isArray(d.groups)||
    !obj(d.solidarity_credit)||!obj(d.crosswalk)||!obj(d.evidence)||
    !obj(d.decisions)||!Array.isArray(d.limitations))
  return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.schema!=="nova-g015-subcomponents-revenues/v1"||d.project!=="Projet Nova"||
    d.phase!=="G0.15-V01-V02-V03"||d.documented_on!=="2026-11-08"||
    d.status!=="PUBLIC_ACCOUNTS_DETAIL_RECONCILED_NO_NOVA_CERTIFICATION"||
    d.programme_score_before!==47||d.programme_score_after!==47)
  fail("FALSE_READINESS");
 const source=d.source;
 if(source.publisher!=="Ministère des Finances du Québec"||
    source.title!=="Comptes publics 2025-2026 — Volume 1"||
    source.url!==OFFICIAL_REVENUE_NOTE_URL||
    source.original_year_end!=="2026-03-31"||
    source.comparator_year_end!=="2025-03-31"||
    source.pdf_page_index_zero_based!==108||source.printed_page!==102||
    source.note!=="4. Revenus — Revenus autonomes par sources"||
    source.currency!=="M_CAD"||source.source_is_audited_government_account!==true||
    source.nova_reform_independently_audited!==false)
  fail("PROVENANCE_FALSE");
 if(!same(d.groups.map(x=>x?.id),ID_GROUPS))fail("GROUPS_OR_ORDER");
 for(const id of ID_GROUPS){
  const g=d.groups.find(x=>x?.id===id),expected=PUBLISHED_ROWS[id],sumExpected=totals[id];
  if(!obj(g)||!Array.isArray(g.categories)||g.categories.length!==expected.length||
     g.categories.some((r,i)=>!obj(r)||typeof r.label!=="string"||
       !same([r.id,r.year_2024_2025_mcad,r.year_2025_2026_mcad,r.treatment],expected[i]))||
     !same([g.year_2024_2025_total_mcad,g.year_2025_2026_total_mcad],sumExpected)||
     sum(g.categories,"year_2024_2025_mcad")!==sumExpected[0]||
     sum(g.categories,"year_2025_2026_mcad")!==sumExpected[1])
     fail("SUBCATEGORY_RECONCILIATION_"+id);
 }
 const v03=d.groups.find(x=>x?.id==="V03");
 if(!obj(v03)||!Array.isArray(v03.categories)||
    v03.services_rendered_subtotal_2024_2025_mcad!==8720||
    v03.services_rendered_subtotal_2025_2026_mcad!==9132||
    v03.categories.slice(0,6).some(x=>!obj(x))||
    sum(v03.categories.slice(0,6),"year_2024_2025_mcad")!==8720||
    sum(v03.categories.slice(0,6),"year_2025_2026_mcad")!==9132)
  fail("V03_SERVICE_SUBTOTAL");
 const credit=d.solidarity_credit;
 if(credit.id!=="CREDIT_SOLIDARITE"||
    credit.year_2024_2025_mcad!==1944||
    credit.year_2025_2026_mcad!==1996||
    credit.already_deducted_in_sales!==true||
    credit.add_again_as_new_expense!==false||
    credit.source_note_page!==102)
  fail("SOLIDARITY_CREDIT_DOUBLE_COUNT");
 const x=d.crosswalk,prev=g015Actuals;
 if(x.g015_prior_realized!=="data/comptes-publics-reels-g0-15-v02-v03-2025-2026.json"||
    x.g014_forecast_year!=="2026-2027"||
    x.g014_forecast_v01_mcad!==30682||x.g014_forecast_v02_mcad!==6484||
    x.g014_forecast_v03_mcad!==15790||
    x.totals_not_additional_to_government_revenue!==true||
    x.comparative_2024_2025_is_reclassified!==true||
    x.never_add_forecast_to_actuals!==true||x.nova_tax_reform_funded!==false||
    g014?.revenue_categories?.find(k=>k.id==="TAXES_CONSOMMATION")?.amount_mcad!==30682||
    g014?.revenue_categories?.find(k=>k.id==="DROITS_PERMIS_REDEVANCES")?.amount_mcad!==6484||
    g014?.revenue_categories?.find(k=>k.id==="REVENUS_DIVERS")?.amount_mcad!==15790||
    g014?.programme_percent_after!==47||
    prev?.annual?.find(k=>k.year==="2025-2026")?.rights_permits_royalties!==6708||
    prev?.annual?.find(k=>k.year==="2025-2026")?.miscellaneous_revenues!==14922||
    prev?.annual?.find(k=>k.year==="2024-2025")?.rights_permits_royalties!==6191||
    prev?.annual?.find(k=>k.year==="2024-2025")?.miscellaneous_revenues!==16252||
    prev?.programme_score_after!==47)
  fail("ACTUAL_FORECAST_CROSSCHECK");
 const e=d.evidence;
 const restrictions=[
 "v01_full_legal_breakdown_verified",
 "v02_full_legal_breakdown_verified",
 "v03_internal_transfers_eliminated_by_nova_review",
 "v01_reviewed_independently_for_nova",
 "v02_reviewed_independently_for_nova",
 "v03_reviewed_independently_for_nova",
 "all_15_g015_proofs_certified","policy_rates_authorized"];
 if(restrictions.some(k=>e[k]!==false)||
    ["v01_primary_detail_identified","v02_primary_detail_identified",
      "v03_primary_detail_identified"].some(k=>e[k]!==true)||
    e.financed_new_nova_revenue_mcad!==null||
    ["g015_passed","programme_complete","party_political_adoption"]
      .some(k=>d.decisions[k]!==false))
   fail("NOVA_UNPROVEN_APPROVAL");
 if(g015?.programme_score!==47||g015?.status!=="NON_FRANCHIE"||
    discovery?.programme_score_unchanged!==47||
    ID_GROUPS.some(id=>{
     const p=g015?.proofs?.find(x=>x.id===id),
       row=discovery?.entries?.find(x=>x.id===id);
     return p?.status!=="A_DOCUMENTER"||p?.primary_source!==null||
       p?.reviewed_independently!==false||row?.statut_preuve_g015!=="A_DOCUMENTER"||
       row?.independently_reviewed!==false||
       !row?.candidats?.some(s=>s.url===OFFICIAL_REVENUE_NOTE_URL&&
         s.statut==="SOURCE_PUBLIQUE_REPEREE_NON_AUDITEE");
    }))fail("G015_NOT_VALIDATED");
 if(d.limitations.length!==6||d.limitations.some(s=>typeof s!=="string"||s.length<65))
  fail("LIMITATIONS_MISSING");
 return {ok:errors.length===0,errors:[...new Set(errors)],programme_score:47,
   number_subcategories:20,source_public_page:102,
   groups_observed_2025_2026_mcad:[29639,6708,14922],
   legal_status_certified:false,additional_nova_revenue_mcad:null,
   nova_reform_audited:false};
}
