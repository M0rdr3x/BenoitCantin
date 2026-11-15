// Projet Nova G0.17a — Source MAMH : le PDF mutable montre 2024 en capture et 2025 en texte.
// Ce module empêche l'usage public d'une variation construite sur deux éditions non réconciliées.
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const rows24=[
 ["LT_2000",79665308,32404720,17580024,357746,29244080,68137,10601],
 ["2000_9999",89521975,62289357,4994468,1821487,20014459,355300,46904],
 ["10000_24999",74014520,53383394,1696631,13977045,4957450,0,0],
 ["25000_99999",109859973,82761508,1167581,18903537,7027347,0,0],
 ["GE_100000",222544163,214161020,109720,2940187,5333236,0,0]
];
const rows25=[
 ["LT_2000",98723832,50614171,17705802,361432,30042427],
 ["2000_9999",121319437,92287179,5210610,2503031,21318617],
 ["10000_24999",99150089,77244725,1831016,13338707,6735641],
 ["25000_99999",143855063,118473624,1077255,18850384,5453800],
 ["GE_100000",314776282,308380313,0,2946450,3449519]
];
const sum=(rows,col)=>rows.reduce((s,r)=>s+r[col],0);
export function auditG017a(d,prior,financing){
 const errors=[],fail=s=>errors.push(s);
 if(!obj(d)||d.schema!=="nova-g017a-mamh-municipal-fiscal-transfer-source-version/v1"||!obj(d.version2024_visual)||!obj(d.version2025_text_quarantined)||!obj(d.source))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.17a"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.remaining_score_points!==53||d.independent_audit_completed!==false||d.party_adoption_done!==false)fail("NO_SCORE_GROWTH");
 if(prior?.schema!=="nova-g016z-mamh-document-version-conflict/v1"||prior?.conflict?.representations_differ!==true||prior?.score_after!==47||financing?.schema!=="nova-g016z-consolidated-financing-and-transition-controls/v1"||financing?.score_after!==47)fail("UPSTREAM_AUDITS");
 const u=d.source;
 if(u.url!=="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/SOM_transferts_fiscaux.pdf"||u.web_page_lists_2025!==true||u.extraction_text_title_year!==2025||u.screenshot_title_year!==2024||u.same_url_content_versions_conflict!==true||u.immutable_pdf_bytes_available!==false||u.immutable_pdf_sha256!==null||u.direct_download_failed!==true||u.version_conflict_resolved!==false)fail("SOURCE_YEAR_CONFLICT");
 const a=d.version2024_visual,b=d.version2025_text_quarantined;
 if(a.year!==2024||a.screenshot_page_zero_based!==2||a.source_method!=="WEB_PDF_SCREENSHOT_VISUAL"||!equal(a.rows,rows24)||!equal(a.columns,["cohort","total_cad","tvq_share_cad","public_land_cad","resource_royalty_cad","equalization_cad","equalization_neutrality_cad","compensation_neutrality_cad"])||a.total_of_selected_programmes_cad!==575605939||a.tvq_share_component_cad!==444999999||a.other_selected_programmes_cad!==130605940||sum(a.rows,1)!==a.total_of_selected_programmes_cad||sum(a.rows,2)!==a.tvq_share_component_cad||a.rows.some(x=>x.slice(2).reduce((s,y)=>s+y,0)!==x[1])||a.represents_all_municipal_funding!==false||a.individual_bank_confirmation!==false||a.pdf_bytes_immutable_sha256!==null)fail("VISUAL_2024_RECONCILIATION");
 if(b.year!==2025||b.source_method!=="WEB_PDF_EXTRACTED_TEXT_CONFLICTS_WITH_SCREENSHOT"||!equal(b.rows,rows25)||b.text_only_aggregate_cad!==777824703||b.text_only_tvq_cad!==647000012||sum(b.rows,1)!==b.text_only_aggregate_cad||sum(b.rows,2)!==b.text_only_tvq_cad||b.rows.some(x=>x.slice(2).reduce((s,y)=>s+y,0)!==x[1])||b.usable_verified_total_cad!==null||b.usable_verified_tvq_cad!==null||b.eligible_for_growth_claim!==false||b.different_categories_from_2024!==true||b.pdf_visual_match!==false)fail("QUARANTINE_2025_TEXT");
 const c=d.controls,comparisons=d.comparisons;
 if(!obj(c)||c.existing_tvq_share_2024_cad!==444999999||Object.entries(c).some(([k,v])=>k!=="existing_tvq_share_2024_cad"&&v!==true)||!obj(comparisons)||Object.values(comparisons).some(x=>x!==null))fail("NO_IMPUTED_SAVINGS");
 if(!Array.isArray(d.related_sources)||d.related_sources.length!==4||d.related_sources[1].rows_imported!==false||!d.related_sources[0].url.startsWith("https://www.quebec.ca/"))fail("PUBLIC_DATA_PENDING");
 if(!Array.isArray(d.verification_needed)||d.verification_needed.length!==6||d.verification_needed.some((x,i)=>x.id!=="Q"+String(i+1).padStart(2,"0")||x.complete!==false))fail("UNCLOSED_GATES");
 if(!Array.isArray(d.scenarios)||d.scenarios.length!==2||d.scenarios.map(x=>x.id).join("|")!=="QUEBEC_CANADA|QUEBEC_SOUVERAIN"||d.scenarios.some(x=>x.verified_financially_complete!==false||x.year2026_municipal_replacement_cad!==null))fail("SCENARIOS_UNFINANCED");
 const k=d.decision||{};
 if(k.visually_supported_year2024_subtotal!==true||k.quarantine_year2025_extraction!==true||["closed_version_conflict","verified_year2025_spending","verified_bank_payments","nova_financed","score_increase_earned"].some(key=>k[key]!==false))fail("NOT_CERTIFIED");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,documented_2024_programmes_cad:575605939,of_which_tvq_cad:444999999,verified_2025_transfer_total_cad:null,comparative_growth_pct:null};
}
export function consolidateInternalTransfer({province_to_municipality_cad,municipal_receipt_cad,mode}){
 if(mode!=="SYNTHETIC_ONLY"||!Number.isSafeInteger(province_to_municipality_cad)||!Number.isSafeInteger(municipal_receipt_cad)||province_to_municipality_cad<0||municipal_receipt_cad<0)throw Error("SYNTHETIC_VALUES_ONLY");
 if(province_to_municipality_cad!==municipal_receipt_cad)throw Error("UNMATCHED_TRANSFER");
 return {eliminated_internal_transfer_cad:province_to_municipality_cad,new_consolidated_revenue_cad:0,verified_nova_receipt:false};
}
