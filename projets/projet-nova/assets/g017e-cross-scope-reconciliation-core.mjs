/**
 * G0.17e — rapprochement de quatre sources DE PERIMETRES DISTINCTS.
 * Les montants sont ceux déjà référencés dans le dépôt; ils ne certifient pas la réforme Nova.
 */
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const fixed1=x=>Math.round(x*10)/10;
const integer=x=>Number.isSafeInteger(x);
export const EXPECTED_MUNICIPAL_IDS=Object.freeze([
 "PROPERTY","GOVERNMENT_TRANSFERS","SALES","TARIFF","TRANSFER_DUTY","OTHER"
]);
export const TEN_YEARS=Object.freeze(Array.from({length:10},(_,i)=>`${2026+i}-${2027+i}`));
const equals=(a,b)=>a===b;
const allNull=(x,fields)=>fields.every(k=>x?.[k]===null);
const number=x=>typeof x==="number"&&Number.isFinite(x);
export function inspecterConcordanceG017e(c,v,g13,actual){
 const errors=[],error=x=>errors.push(x);
 if(!object(c)||!object(v)||!object(g13)||!object(actual)||
   !object(c.municipal)||!object(c.water)||!object(v.government_reference)||
   !Array.isArray(g13.budget_reference)||!Array.isArray(actual.annual))
   return {ok:false,errors:["SCHEMA_INVALIDE"],score_authorized_increment:0,validation_independante:false};
 if(c.schema!=="nova-g017c-water-municipal-revenue-evidence/v1"||
   v.schema!=="nova-g016v-two-levies-public-finance-reference/v1"||
   g13.schema!=="nova-g013-fiscal-readiness/v1"||
   actual.schema!=="nova-g015-v02-v03-comptes-publics-reels/v1")
   error("SCHEMA_SOURCE_INCOHERENT");
 const muni=c.municipal,water=c.water;
 const parts=muni.components;
 if(muni.year!==2024||muni.scope!=="QUEBEC_CONSOLIDATED_MUNICIPAL_ORGANIZATIONS"||
    muni.unit!=="BILLION_CAD_1_DECIMAL_ROUNDED"||!Array.isArray(parts)||
    parts.length!==EXPECTED_MUNICIPAL_IDS.length||
    new Set(parts.map(x=>x?.id)).size!==EXPECTED_MUNICIPAL_IDS.length||
    EXPECTED_MUNICIPAL_IDS.some((id,i)=>parts[i]?.id!==id)||
    parts.some(x=>!number(x.amount_gcad)||x.amount_gcad<0))
   error("PERIMETRE_MUNICIPAL_INVALIDE");
 const byId=id=>parts?.find(x=>x.id===id)?.amount_gcad;
 const sum=Array.isArray(parts)?fixed1(parts.reduce((n,p)=>n+(number(p.amount_gcad)?p.amount_gcad:0),0)):null;
 const own=fixed1((muni.total_revenue_gcad??0)-(byId("GOVERNMENT_TRANSFERS")??0));
 const property=fixed1((byId("PROPERTY")??0)+(byId("TRANSFER_DUTY")??0));
 if(sum!==31.3||!equals(muni.total_revenue_gcad,sum)||
    !equals(own,muni.nontransfer_own_source_revenue_approx_gcad)||
    muni.verified_raw_municipal_csv!==false||
    muni.actual_total_year_2026_gcad!==null||
    muni.municipal_replacement_year_2026_gcad!==null||
    muni.same_year_transfer_cancellation_verified!==false)
   error("AGREGATS_MUNICIPAUX_NON_HOMOLOGUES");
 if(water.year!==2023||water.scope!=="NETWORK_SERVICES_WATER"||
    water.reported_approx_annual_revenue_gcad!==2.4||
    water.reported_approx_full_service_cost_gcad!==6||
    fixed1(water.reported_approx_full_service_cost_gcad-water.reported_approx_annual_revenue_gcad)!==3.6||
    water.illustrative_gap_is_not_annual_cash_deficit!==true||
    water.full_cost_contains_operations_and_average_ten_year_asset_investment_needs!==true||
    water.actual_full_cost_year_2026_gcad!==null)error("PERIMETRE_EAU_INVALIDE");
 const forecast=v.government_reference.fiscal_years_official;
 if(!Array.isArray(forecast)||forecast.length!==5||g13.budget_reference.length!==10)
   error("HORIZON_NON_COMPARABLE");
 const computed=[];
 for(let i=0;i<5;i++){
   const p=forecast?.[i],q=g13.budget_reference[i],yr=TEN_YEARS[i];
   if(!object(p)||!object(q)||p.fiscal_year!==yr||q.year!==yr){
     error("ANNEE_ABSENTE:"+yr);continue;
   }
   const inputs=[
     p.existing_tax_sources_mcad,p.other_government_receipts_mcad,
     p.federal_transfers_mcad,p.total_government_revenue_mcad,
     p.government_expenditure_including_debt_service_mcad,
     p.contingency_provision_mcad,p.generations_fund_contribution_mcad,
     p.conditional_levies_needed_canada_provincial_account_balance_mcad
   ];
   if(inputs.some(x=>!integer(x))||
      p.existing_tax_sources_mcad+p.other_government_receipts_mcad+
        p.federal_transfers_mcad!==p.total_government_revenue_mcad||
      p.government_expenditure_including_debt_service_mcad+
        p.contingency_provision_mcad-p.other_government_receipts_mcad-
        p.federal_transfers_mcad!==p.conditional_levies_needed_canada_provincial_account_balance_mcad||
      p.conditional_levies_needed_canada_plus_generations_fund_mcad!==
       p.conditional_levies_needed_canada_provincial_account_balance_mcad+
       p.generations_fund_contribution_mcad||
      q.total_revenue!==p.total_government_revenue_mcad||
      q.federal_transfers!==p.federal_transfers_mcad||
      q.total_expenditures!==p.government_expenditure_including_debt_service_mcad||
      q.contingency_reserve!==p.contingency_provision_mcad)
      error("CONCORDANCE_PROVINCIALE:"+yr);
   computed.push({
     year:yr,
     provincial_levies_needed_conditionally_mcad:
       p.government_expenditure_including_debt_service_mcad+
       p.contingency_provision_mcad-
       p.other_government_receipts_mcad-p.federal_transfers_mcad,
     provincial_levies_plus_generations_mcad:
       p.conditional_levies_needed_canada_plus_generations_fund_mcad,
     scope:"PROVINCIAL_FORECAST_CONDITIONAL_NOT_NOVA"
   });
 }
 for(let i=5;i<10;i++){
   const r=g13.budget_reference[i];
   if(!object(r)||r.year!==TEN_YEARS[i]||
     !allNull(r,["own_revenue","federal_transfers","total_revenue",
                   "total_expenditures","contingency_reserve",
                   "accounting_balance_before_gap","budgetary_balance_after_assumed_gap"]))
      error("INCONNU_SUBSTITUE_PAR_ZERO:"+TEN_YEARS[i]);
 }
 const realized=actual.annual.find(r=>r?.year==="2025-2026");
 if(!object(realized)||realized.classification!=="COMPTES_PUBLICS_REELS_2025_2026"||
    !integer(realized.total_revenues)||!integer(realized.total_expenditures)||
    realized.total_revenues-realized.total_expenditures!==realized.accounting_balance||
    realized.accounting_balance!==-5502||
    actual.evidence?.nova_external_fiscal_audit_complete!==false)
   error("REALE_VS_PREVISION_CONFONDUS");
 const controls=c.controls||{};
 for(const key of [
  "do_not_add_2024_municipal_to_2026_provincial_budget",
  "do_not_add_2023_water_revenue_twice",
  "do_not_compare_unaligned_years_as_growth",
  "do_not_treat_2023_full_cost_gap_as_booked_cash_loss",
  "separate_school_property_tax_and_municipal_property_tax",
  "no_independent_programme_certification_claim"
 ])if(controls[key]!==true)error("REGLE_DE_PERIMETRE_MANQUANTE:"+key);
 return {
  ok:errors.length===0,errors:[...new Set(errors)],
  provenance:"MONTANTS_DEJA_DOCUMENTES_DANS_DEPOT",
  municipales_2024_revenus_approximatifs_gcad:muni.total_revenue_gcad,
  municipales_2024_transferts_gcad:byId("GOVERNMENT_TRANSFERS")??null,
  municipales_2024_revenus_hors_transferts_approximatifs_gcad:own,
  municipales_2024_foncier_et_mutation_exposes_si_abolis_gcad:property,
  foncier_et_mutation_2024_est_cout_net_2026:false,
  eau_2023_ecart_couverture_cout_complet_gcad:3.6,
  eau_2023_est_deficit_tresorerie:false,
  eau_2023_est_additionnable_aux_recettes_2024:false,
  budgets_provinciaux_officiels_previsions:computed,
  annees_suivantes_sans_prevision_officielle:5,
  comptabilite_reelle_2025_2026_resultat_mcad:realized?.accounting_balance??null,
  montant_2024_ajoutable_au_besoin_provincial_2026_mcad:null,
  montant_net_taxes_nova_2026_mcad:null,
  rendement_anti_paradis_certifie_mcad:null,
  scenario_souverain_finance:false,
  validation_independante:false,
  score_authorized_increment:0
 };
}
