/**
 * G0.16b — références publiques descriptives, sans calibration fiscale.
 * Contrôle déterministe de la transcription des tableaux ISQ / Statistique Canada 2023.
 * L'existence de sources ne suffit PAS pour calculer un taux Nova.
 */
export const EXPECTED_DECILE_UPPER_BOUNDS_CAD=Object.freeze([
  25500,32300,39400,45700,52200,58800,66800,77300,94900,null
]);
export const SOURCE_URLS=Object.freeze({
  income:"https://statistique.quebec.ca/fr/produit/tableau/limite-superieure-deciles-revenu-repartition-menages-deciles-type-revenu-menage-revenu-ajuste-taille-menage",
  spending:"https://www150.statcan.gc.ca/n1/daily-quotidien/250521/t001a-fra.htm",
  tax_catalogue:"https://www.quebec.ca/gouvernement/ministeres-organismes/finances/publications",
  regional_catalogue:"https://statistique.quebec.ca/fr/document/revenu-disponible-par-habitant-regions-administratives-et-mrc"
});
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const n=x=>typeof x==="number"&&Number.isFinite(x);
const close=(a,b)=>n(a)&&Math.abs(a-b)<1e-9;
const unknownFields=["not_scenario_estimates","not_microsimulation","not_current_2026_household_values",
  "not_2026_tax_base","do_not_join_income_and_spending_by_decile"];
const gates=["independent_statistical_review_completed","legal_tax_base_verified","price_rebase_completed",
  "regional_model_complete","validation_of_15_g015_proofs_complete"];
const allowedScenario=["id","model_estimated","annual_household_gain_cad","annual_fiscal_balance_mcad","proposed_tax_rate_pct"];
export function inspectG016bBenchmarks(d,proofs,plan){
 const errors=[];
 if(!obj(d)||d.schema!=="nova-g016b-reperes-publics/v1"||
    !obj(d.datasets)||!obj(d.measurement_limits)||!Array.isArray(d.scenarios)||
    !obj(d.decision)||!Array.isArray(d.candidates))
   return {ok:false,errors:["SCHEMA"],documentary_benchmarks:0,can_calibrate:false};
 if(d.status!=="REPERES_HISTORIQUES_PUBLICS_NON_CALIBRES"||
    d.phase!=="G0.16b"||d.programme_percent!==47||d.adopted!==false||
    d.approved_for_microsimulation!==false||d.individual_data_collected!==false||
    d.source_spreadsheets_imported!==false||
    !unknownFields.every(k=>d.measurement_limits[k]===true)||
    !gates.every(k=>d.measurement_limits[k]===false)) errors.push("FALSE_CALIBRATION_STATUS");
 const income=d.datasets.household_decile_thresholds;
 if(!obj(income)||income.source_id!=="ISQ_ECR_2023_EQUIVALIZED_AFTER_TAX_DECILES"||
    income.source_url!==SOURCE_URLS.income||income.reference_year!==2023||
    income.publication_date!=="2025-10-20"||
    income.variable!=="REVENU_APRES_IMPOT_AJUSTE_TAILLE_MENAGE"||
    income.unit!=="CAD_COURANTS_2023_PAR_EQUIVALENT_MENAGE"||
    income.statistic!=="LIMITE_SUPERIEURE_DE_DECILE"||
    !Array.isArray(income.deciles)||income.deciles.length!==10||
    income.imported_original_binary!==false||income.second_reviewer_signed_off!==false||
    income.fit_for_tax_calibration!==false)
  errors.push("ISQ_METADATA");
 if(Array.isArray(income?.deciles)&&income.deciles.length===10){
  for(let i=0;i<10;i++){
   const a=income.deciles[i];
   if(!obj(a)||Object.keys(a).length!==3||a.decile!==i+1||
      a.upper_bound_cad!==EXPECTED_DECILE_UPPER_BOUNDS_CAD[i]||
      a.published_marker!==(i===9?"x":null)){
    errors.push("ISQ_DECILE:"+String(i+1));break;
   }
  }
 }
 const spend=d.datasets.household_spending_provincial;
 if(!obj(spend)||spend.source_id!=="STATCAN_SHS_2023_QUEBEC_EXPENDITURE"||
    spend.source_url!==SOURCE_URLS.spending||spend.reference_year!==2023||
    spend.publication_date!=="2025-05-21"||
    spend.geography!=="QUEBEC"||
    spend.unit!=="CAD_COURANTS_2023_PAR_MENAGE"||
    spend.statistic!=="DEPENSES_MOYENNES_DES_MENAGES_EN_BIENS_ET_SERVICES"||
    spend.average_spending_cad!==65344||!obj(spend.shares_pct)||
    !close(spend.shares_pct?.housing,27.1)||!close(spend.shares_pct?.transport,16.9)||
    !close(spend.shares_pct?.food,17.3)||
    spend.by_income_decile!==false||spend.by_region!==false||
    spend.fit_for_tax_calibration!==false||
    spend.imported_original_binary!==false||spend.second_reviewer_signed_off!==false)
  errors.push("STATCAN_EXPENDITURES");
 if(!Array.isArray(d.candidates)||d.candidates.length!==2||
    d.candidates[0]?.source_id!=="QUEBEC_FINANCES_FISCAL_2023"||
    d.candidates[0]?.source_url!==SOURCE_URLS.tax_catalogue||
    d.candidates[0]?.latest_examined_tax_year!==2023||
    d.candidates[1]?.source_id!=="ISQ_REGIONAL_INCOME_2024"||
    d.candidates[1]?.source_url!==SOURCE_URLS.regional_catalogue||
    d.candidates[1]?.latest_examined_tax_year!==2024||
    d.candidates.some(x=>x.content_imported!==false||x.assiettes_verified!==false))
  errors.push("CANDIDATE_CATALOGUES");
 if(!Array.isArray(d.scenarios)||d.scenarios.length!==2||
    d.scenarios[0]?.id!=="QUEBEC_CANADA"||d.scenarios[1]?.id!=="QUEBEC_SOUVERAIN"||
    d.scenarios.some(s=>!obj(s)||Object.keys(s).length!==allowedScenario.length||
      !Object.keys(s).every(k=>allowedScenario.includes(k))||
      s.model_estimated!==false||s.annual_household_gain_cad!==null||
      s.annual_fiscal_balance_mcad!==null||s.proposed_tax_rate_pct!==null))
   errors.push("PREMATURE_POLICY_ESTIMATE");
 const decision=d.decision;
 if(decision.g016b_benchmark_transcription_present!==true||
    ["g016b_calibration_complete","g016_preflight_passed","policy_rate_authorized",
     "new_nova_revenue_estimated","new_nova_savings_estimated","ready_to_govern"].some(k=>decision[k]!==false)||
    decision.programme_percent_after!==47)errors.push("PREMATURE_DECISION");
 if(!obj(proofs)||!Array.isArray(proofs.proofs)||proofs.proofs.length!==15||
    proofs.proofs.some((x,i)=>x.id!=="V"+String(i+1).padStart(2,"0"))||
    proofs.programme_score!==47)
   errors.push("PREDECESSOR_G015_MISMATCH");
 if(!obj(plan)||plan.schema!=="nova-g016-incidence-distributive/v1"||
    plan.programme_score!==47||plan.status!=="CADRAGE_NON_CALIBRE"||
    !Array.isArray(plan.scenarios)||plan.scenarios.length!==2||
    plan.scenarios.some(s=>!Array.isArray(s.distribution)||s.distribution.length!==10||
      s.distribution.some(row=>row.net_change_cad!==null)))
   errors.push("PREDECESSOR_G016_MISMATCH");
 return {ok:errors.length===0,errors:[...new Set(errors)],
   documentary_benchmarks:2,candidate_catalogues:2,
   historical_year:2023,decile_boundaries_transcribed:9,
   spending_2023_québec_cad:65344,
   records_for_policy_simulation:0,can_calibrate:false,
   g016b_completed:false,programme_percent:47};
}
