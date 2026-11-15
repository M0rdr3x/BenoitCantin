// G0.15 V02 / V03 — contrôle des COMPTES PUBLICS réellement observés.
// Ces montants gouvernementaux ne certifient aucune réforme fiscale NOVA.
export const SOURCE_G015_V02_V03 =
 "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Comptes-publics/FR/CPTFR_vol1-2025-2026.pdf";
const EXPECTED=Object.freeze([
["2024-2025","COMPTES_PUBLICS_REELS_RECLASSES_COMPARATIFS",69081,28377,6191,16252,5689,125590,30498,156088,161263,-5175],
["2025-2026","COMPTES_PUBLICS_REELS_2025_2026",74115,29639,6708,14922,5241,130625,29803,160428,165930,-5502]
]);
const NUMS=["income_and_property_taxes","consumption_taxes","rights_permits_royalties",
 "miscellaneous_revenues","government_enterprises","own_revenues",
 "federal_transfers","total_revenues","total_expenditures","accounting_balance"];
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function inspectG015V02V03Actuals(d,g014,g015,discovery){
 const errors=[],bad=s=>errors.push(s);
 if(!obj(d)||!obj(d.source)||!Array.isArray(d.annual)||
    !obj(d.changes_2025_2026_minus_2024_2025)||
    !obj(d.cross_reference_g014)||!obj(d.evidence)||
    !obj(d.decision)||!Array.isArray(d.limits))
  return {ok:false,errors:["SCHEMA"],programme_score:null};
 if(d.schema!=="nova-g015-v02-v03-comptes-publics-reels/v1"||
    d.project!=="Projet Nova"||d.prepared_on!=="2026-11-08"||
    d.phase!=="G0.15-V02-V03"||
    d.status!=="MONTANTS_REELS_GOUVERNEMENT_PUBLICS_PREUVES_LEGALES_NOVA_NON_CERTIFIEES"||
    d.programme_score_before!==47||d.programme_score_after!==47||
    d.units!=="M_CAD")bad("FALSE_STATUS_OR_SCORE");
 const s=d.source;
 if(s.publisher!=="Ministère des Finances du Québec"||
    s.title!=="Comptes publics 2025-2026, volume 1, États financiers consolidés"||
    s.url!==SOURCE_G015_V02_V03||s.report_date!=="2026-07-17"||
    s.fiscal_year_end!=="2026-03-31"||
    s.pdf_page_index_zero_based_results!==11||s.printed_page_results!==5||
    s.pdf_page_index_zero_based_auditor_summary!==13||
    s.printed_page_auditor_summary!==7||
    s.government_accounts_vgq_unqualified_opinion!==true||
    s.reviewed_independently_for_nova!==false||
    s.source_values_read_as_consolidated_government_results!==true)
   bad("INVALID_PUBLIC_ACCOUNTS_SOURCE");
 if(d.annual.length!==2||d.annual.some((r,i)=>{
    if(!obj(r))return true;
    const actual=[r.year,r.classification,...NUMS.map(k=>r[k])];
    const own=NUMS.slice(0,5).reduce((sum,k)=>sum+r[k],0);
    return !same(actual,EXPECTED[i])||r.observed_municipal_taxes_included!==false||
      own!==r.own_revenues||
      r.own_revenues+r.federal_transfers!==r.total_revenues||
      r.total_revenues-r.total_expenditures!==r.accounting_balance;
  }))bad("ACTUALS_RECONCILIATION_FAILED");
 const [old,now]=d.annual;
 const change=d.changes_2025_2026_minus_2024_2025;
 if(!obj(old)||!obj(now)||!same(change,{
  rights_permits_royalties:517,miscellaneous_revenues:-1330,own_revenues:5035,
  total_revenues:4340,accounting_balance:-327
 })||!["rights_permits_royalties","miscellaneous_revenues","own_revenues",
      "total_revenues","accounting_balance"].every(k=>now[k]-old[k]===change[k]))
  bad("YEAR_ON_YEAR_RECONCILIATION");
 const cross=d.cross_reference_g014;
 const x=g014?.revenue_categories??[];
 if(cross.year!=="2026-2027"||
    cross.classification!=="PREVISION_GOUVERNEMENT_PAS_REALISATION_2025_2026"||
    cross.forecast_rights_permits_royalties_mcad!==6484||
    cross.forecast_miscellaneous_revenues_mcad!==15790||
    cross.forecast_total_revenues_mcad!==168389||
    cross.forecast_federal_transfers_mcad!==33046||
    cross.compare_years_without_reconciliation!==false||
    cross.add_2025_2026_actuals_to_2026_2027_forecast!==false||
    cross.nova_budget_financed!==false||
    g014?.programme_percent_after!==47||
    g014?.baseline?.total_revenue!==168389||
    x.find(c=>c.id==="DROITS_PERMIS_REDEVANCES")?.amount_mcad!==6484||
    x.find(c=>c.id==="REVENUS_DIVERS")?.amount_mcad!==15790)
   bad("FORECAST_ACTUALS_CONFUSED");
 const e=d.evidence;
 if(["v02_legal_source_allocation_complete",
  "v03_internal_transfer_elimination_complete",
  "rights_and_royalties_tax_share_identified",
  "miscellaneous_income_tax_share_identified",
  "g015_v02_independently_validated",
  "g015_v03_independently_validated",
  "tax_abolition_approved",
  "nova_external_fiscal_audit_complete"].some(k=>e[k]!==false)||
  e.review_document_2025_2026_available!==true||
  e.new_nova_revenue_mcad!==null||
  d.decision.g015_passed!==false||
  d.decision.programme_complete!==false||
  d.decision.budget_nova_certified!==false)
   bad("PREMATURE_NOVA_CERTIFICATION");
 const entries=discovery?.entries||[];
 const proofs=g015?.proofs||[];
 if(discovery?.programme_score_unchanged!==47||
    g015?.programme_score!==47||g015?.status!=="NON_FRANCHIE"||
    ["V02","V03"].some(id=>{
     const item=entries.find(v=>v.id===id),p=proofs.find(v=>v.id===id);
     return item?.statut_preuve_g015!=="A_DOCUMENTER"||
      item?.independently_reviewed!==false||
      !item?.candidats?.some(c=>c.url===SOURCE_G015_V02_V03&&
          c.statut==="SOURCE_PUBLIQUE_REPEREE_NON_AUDITEE")||
      p?.status!=="A_DOCUMENTER"||p?.primary_source!==null||
      p?.reviewed_independently!==false;
    }))
   bad("G015_V02_V03_STILL_UNVALIDATED");
 const limits=["audités","droits, permis et redevances","revenus divers",
  "2024-2025","2026-2027","transferts internes"];
 if(d.limits.length!==6||limits.some((word,i)=>typeof d.limits[i]!=="string"||
   !d.limits[i].toLowerCase().includes(word)))
   bad("DISCLOSURES_INCOMPLETE");
 return {ok:errors.length===0,errors:[...new Set(errors)],programme_score:47,
  rights_2025_2026_mcad:6708,miscellaneous_2025_2026_mcad:14922,
  confirmed_nova_new_revenues_mcad:null,govt_audited_year:"2025-2026",
  nova_independent_review:false,v02_v03_validated:false};
}
