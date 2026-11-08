/** G0.16z — Enregistrer une divergence de versions sans inventer une résolution. */
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function inspectG016zDocumentConflict(d){
 const errors=[],bad=k=>errors.push(k);
 if(!obj(d)||d.schema!=="nova-g016z-mamh-document-version-conflict/v1"||!Array.isArray(d.observations)||!obj(d.conflict))return {ok:false,errors:["SCHEMA"]};
 if(d.date!=="2026-11-08"||d.phase!=="G0.16z-source-quality"||d.score_before!==47||d.score_after!==47||d.url!=="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/fiscalite/fiscalite_organismes_municipaux.pdf")bad("PROVENANCE");
 const [a,b]=d.observations;
 if(d.observations.length!==2||a?.id!=="SCREENSHOT_2025"||a.method!=="WEB_PDF_SCREENSHOT"||a.document_visible_edition!=="MARS 2025"||a.data_year!==2023||!eq(a.values_gcad,{total_revenues:29.3,property_taxes:14,government_transfers:6.2})||a.status!=="OBSERVED_VISUAL_2025_VERSION")bad("VISUAL_2025");
 if(b?.id!=="EXTRACT_2026"||b.method!=="WEB_PDF_TEXT_EXTRACTION"||b.document_text_edition!=="SEPTEMBRE 2026"||b.data_year!==2024||!eq(b.values_gcad,{total_revenues:31.3,property_taxes:15,government_transfers_reported:7.4})||b.status!=="OBSERVED_TEXT_2026_VERSION")bad("TEXT_2026");
 const c=d.conflict;
 if(c.same_original_url!==true||c.representations_differ!==true||c.directly_verified_2024_pdf_visual!==false||c.known_fixed_download_sha256_for_either_variant!==null||c.live_original_url_may_be_replaced!==true||c.cannot_state_current_pdf_visual_matches_2026_text!==true||c.cannot_conclude_one_version_incorrect!==true||c.year_2024_values_must_not_replace_year_2023_without_rebaselining!==true)bad("OPEN_CONFLICT");
 if(!Array.isArray(d.required_reconciliation)||d.required_reconciliation.length!==6||d.required_reconciliation.some((x,i)=>x.id!=="Q"+String(i+1).padStart(2,"0")||x.done!==false))bad("FROZEN_SOURCE_NOT_OBTAINED");
 if(d.impact?.prior_2023_reference_from_march2025_visual_kept!==true||d.impact?.new_2024_reference_not_added_to_nova_2026_model!==true||d.impact?.municipal_property_replacement_cost_2026_still_null!==true||d.impact?.no_change_to_2026_quebec_provincial_reference!==true||d.impact?.provisional_nova_tax_rate_still_null!==true||d.impact?.programme_point_gain_earned!==false||d.decision!=="OPEN_PROVENANCE_ANOMALY_REQUIRING_ARCHIVED_VERSION_AND_SAME_VERSION_REVIEW")bad("NO_FAKE_RESOLUTION");
 return {ok:errors.length===0,errors:[...new Set(errors)],source_conflict_open:true,source_url_versioned:false,years_compared:[2023,2024],score:47,ready_for_2026_municipal_replacement_cost:false};
}
