// G0.15 / V10 — transfert municipal annoncé, sans créer de nouvelle recette NOVA.
// Le montant public 2027 n'est ni un versement observé ni un financement de réforme.
export const SOURCE_V10_2027 =
  "https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/preparation-budget";
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
export function inspectG015V10MunicipalTVQ2027(d,discovery,proofs,g016h){
  const errors=[],fail=code=>errors.push(code);
  if(!obj(d)||!obj(d.source)||!obj(d.announced_allocation)||
     !obj(d.budget_treatment)||!obj(d.missing_evidence)||
     !obj(d.decisions)||!Array.isArray(d.methodological_limits))
    return {ok:false,errors:["SCHEMA"],programme_score:null};
  if(d.schema!=="nova-g015-v10-transfert-tvq-municipal-2027/v1"||
     d.project!=="Projet Nova"||d.phase!=="G0.15-V10"||
     d.compiled_on!=="2026-11-08"||
     d.status!=="REFERENCE_PUBLIQUE_2027_NON_CERTIFIEE_POUR_NOVA"||
     d.programme_score_before!==47||d.programme_score_after!==47)
    fail("STATUS_OR_SCORE_UNSUPPORTED");
  const source=d.source;
  if(source.publisher!=="Gouvernement du Québec (Affaires municipales)"||
     source.page_title!=="Préparation du budget municipal 2027"||
     source.url!==SOURCE_V10_2027||
     source.last_updated!=="2026-10-26"||
     source.checked_on!=="2026-11-08"||
     source.based_on_data_through!=="2026-09"||
     source.official_page_checked!==true||
     source.independent_nova_review!==false)
    fail("PUBLIC_SOURCE_INVALID");
  const a=d.announced_allocation;
  if(a.reference_year!==2027||a.unit!=="M_CAD"||
     a.program!=="Répartition de la croissance d’une partie de la TVQ"||
     a.total_mcad!==821||a.component_I_share_pct!==93.5||
     a.component_II_share_pct!==6.5||
     a.component_I_share_pct+a.component_II_share_pct!==100||
     a.amount_is_estimate!==true||
     a.component_amounts_source_verified!==false||
     a.payments_reconciled!==false||
     a.allocations_are_nova_revenue!==false)
    fail("ANNOUNCED_AMOUNT_OR_SCOPE");
  const b=d.budget_treatment;
  if(b.government_origin!=="EXISTING_TVQ_GROWTH"||
     b.recipient!=="QUEBEC_LOCAL_GOVERNMENTS"||
     b.flow!=="INTERGOVERNMENTAL_TRANSFER"||
     b.add_to_provincial_revenues!==false||
     b.add_to_2024_municipal_revenues!==false||
     b.replace_municipal_taxes_without_new_proof!==false||
     b.all_2027_municipal_transfers_covered!==false||
     b.forecast_is_actual_payment!==false||
     b.zero_duplicate_counting_required!==true)
    fail("DOUBLE_COUNT_OR_TRANSFERS_MISCLASSIFIED");
  const missing=d.missing_evidence;
  if(["destination_level_amounts_verified",
      "reconciliation_to_provincial_taxes",
      "reconciliation_to_municipal_financial_statements",
      "legal_continuity_review",
      "financing_of_new_nova_policy"].some(k=>missing[k]!==false)||
     missing.additional_nova_revenue_mcad!==null||
     missing.municipal_tax_replacement_mcad!==null)
    fail("UNFOUNDED_FINANCING_OR_REVIEW");
  if(["v10_independently_validated","two_tax_policy_certified",
      "programme_complete","adopted"].some(k=>d.decisions[k]!==false))
    fail("APPROVAL_INVENTED");
  const e=discovery?.entries?.find(v=>v.id==="V10");
  const p=proofs?.proofs?.find(v=>v.id==="V10");
  if(discovery?.programme_score_unchanged!==47||
     e?.statut_preuve_g015!=="A_DOCUMENTER"||
     e?.independently_reviewed!==false||
     !e?.candidats?.some(s=>s.url===SOURCE_V10_2027&&
       s.statut==="SOURCE_PUBLIQUE_REPEREE_NON_AUDITEE")||
     proofs?.programme_score!==47||
     p?.status!=="A_DOCUMENTER"||
     p?.primary_source!==null||p?.reviewed_independently!==false)
    fail("G015_V10_NOT_YET_VALIDATED");
  // Reprendre uniquement le périmètre de G0.16h : transferts déjà inclus
  // dans les recettes 2024, sans ajouter la prévision 2027.
  const h=g016h?.annual?.find(v=>v.year===2024);
  if(g016h?.programme_score_after!==47||
     g016h?.source?.reviewed_independently_for_nova!==false||
     h?.government_transfers_cad!==5330360838||
     h?.total_revenues_cad!==32109026468||
     h?.government_transfers_cad>=h?.total_revenues_cad)
    fail("MUNICIPAL_2024_CROSSCHECK");
  const words=["821 M$","septembre 2026","volets I et II",
    "2027 et 2024","financement municipal","non franchie"];
  if(d.methodological_limits.length!==6||
     words.some((word,i)=>typeof d.methodological_limits[i]!=="string"||
       !d.methodological_limits[i].includes(word)))
    fail("METHOD_LIMITS_MISSING");
  return {
    ok:errors.length===0,errors:[...new Set(errors)],programme_score:47,
    declared_tvq_growth_transfer_2027_mcad:821,
    confirmed_new_nova_revenue_mcad:null,
    historic_municipal_transfers_2024_cad:5330360838,
    v10_independently_validated:false
  };
}
